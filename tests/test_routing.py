from types import SimpleNamespace

from langchain_core.messages import AIMessage
import app
from app import _parse_route

def test_parse_json_route():
    assert _parse_route('{"route":"research"}') == "research"

def test_parse_unknown_route_fallback():
    assert _parse_route('{"route":"browse"}') == "reasoning"

def test_strip_thinking_text():
    assert _parse_route('<think>choose route</think>{"route":"calculator"}') == "calculator"


def test_repeated_lookup_stops_and_final_text_is_normalized(monkeypatch):
    calls = []
    route = AIMessage(content='{"route":"research"}')
    answer = AIMessage(content=[
        {"type": "reasoning", "reasoning": "Ignore this block"},
        {"type": "text", "text": "**FINAL ANSWER:** 2007"},
    ])
    manager_replies = iter([route, route, answer])
    monkeypatch.setattr(app, "model", lambda: SimpleNamespace(invoke=lambda _: next(manager_replies)))
    tool = SimpleNamespace(name="wikipedia_retrieve", invoke=lambda args: calls.append(args) or "Release: 2007")
    monkeypatch.setitem(app.SPECIALISTS, "research", ([tool], "Research"))
    lookup = AIMessage(content="", tool_calls=[
        {"name": tool.name, "args": {"topic": "iPhone", "question": "When?"}, "id": "a"},
        {"name": tool.name, "args": {"topic": "  iPhone ", "question": "When?"}, "id": "b"},
    ])
    monkeypatch.setattr(app, "specialist", lambda _: SimpleNamespace(invoke=lambda _: lookup))
    result = app.run_question("When?")
    assert result["answer"] == "2007"
    assert result["delegations"] == 1
    assert result["findings"][0]["status"] == "repeated_tool_call"
    assert result["findings"][0]["result"] == "Release: 2007"
    assert len(calls) == 1


def test_budget_is_shared_across_specialists(monkeypatch):
    manager_replies = iter(AIMessage(content=text) for text in [
        '{"route":"research"}', '{"route":"calculator"}', '{"route":"answer"}', "ABSTAIN",
    ])
    monkeypatch.setattr(app, "model", lambda: SimpleNamespace(invoke=lambda _: next(manager_replies)))
    monkeypatch.setattr(app, "MAX_TOOL_CALLS", 1)
    tool = SimpleNamespace(name="fake", invoke=lambda _: "evidence")
    for name in ("research", "calculator"):
        monkeypatch.setitem(app.SPECIALISTS, name, ([tool], name))
    def client(name):
        replies = iter([AIMessage(content="", tool_calls=[
            {"name": "fake", "args": {"topic": name}, "id": name},
        ]), AIMessage(content="evidence")])
        return SimpleNamespace(invoke=lambda _: next(replies))
    monkeypatch.setattr(app, "specialist", client)
    result = app.run_question("Test shared budget")
    assert result["tool_calls"] == 1
    assert result["answer"] == ""
    assert result["status"] == "tool_budget_exhausted"


def test_finalizer_can_use_passage_omitted_by_research_summary(monkeypatch):
    passage = "Source: archival catalog. The exhibit opened in 1978."
    tool = SimpleNamespace(name="lookup", invoke=lambda _: passage)
    monkeypatch.setitem(app.SPECIALISTS, "research", ([tool], "Research"))
    specialist_replies = iter([
        AIMessage(content="", tool_calls=[
            {"name": tool.name, "args": {}, "id": "lookup"},
        ]),
        AIMessage(content="Insufficient evidence."),
    ])
    monkeypatch.setattr(app, "specialist", lambda _: SimpleNamespace(
        invoke=lambda _: next(specialist_replies)
    ))
    routes = iter(['{"route":"research"}', '{"route":"answer"}'])

    def invoke(messages):
        if messages[0].content.startswith("You manage"):
            return AIMessage(content=next(routes))
        return AIMessage(content="1978" if passage in messages[-1].content else "ABSTAIN")

    monkeypatch.setattr(app, "model", lambda: SimpleNamespace(invoke=invoke))
    assert app.answer_question("What year did the exhibit open?") == "1978"


def test_attachment_tool_uses_only_trusted_path(monkeypatch, tmp_path):
    attachment = tmp_path / "provided.txt"
    attachment.write_text("evidence")
    paths = []
    tool = SimpleNamespace(name="inspect_file", invoke=lambda args: paths.append(args["path"]) or "evidence")
    monkeypatch.setitem(app.SPECIALISTS, "files", ([tool], "Read file"))
    replies = iter([AIMessage(content="", tool_calls=[
        {"name": tool.name, "args": {"path": ".env"}, "id": "file"},
    ]), AIMessage(content="evidence")])
    monkeypatch.setattr(app, "specialist", lambda _: SimpleNamespace(invoke=lambda _: next(replies)))
    model_replies = iter([AIMessage(content='{"route":"files"}'), AIMessage(content="evidence")])
    monkeypatch.setattr(app, "model", lambda: SimpleNamespace(invoke=lambda _: next(model_replies)))
    assert app.answer_question("Read the file", attachment) == "evidence"
    assert paths == [str(attachment.resolve())]


def test_expired_task_skips_model(monkeypatch):
    monkeypatch.setattr(app, "TASK_SECONDS", 0)
    monkeypatch.setattr(app, "model", lambda: (_ for _ in ()).throw(AssertionError("unexpected model call")))
    result = app.run_question("Time budget already exhausted")
    assert result["answer"] == ""
    assert result["status"] == "timeout"


def test_normalization_preserves_answer_format():
    assert app.normalize_answer("```text\nFinal answer: Smith, Jones\n```") == "Smith, Jones"
    assert app.normalize_answer("**$1,200.50**") == "$1,200.50"


def test_reversed_sentence_reaches_model_in_reading_order(monkeypatch):
    question = 'Write the opposite of "up" as your answer.'
    replies = iter(['{"route":"answer"}', "down"])

    def invoke(messages):
        assert messages[-1].content.startswith(f"Question: {question}\n")
        return AIMessage(content=next(replies))

    monkeypatch.setattr(app, "model", lambda: SimpleNamespace(invoke=invoke))
    assert app.answer_question(question[::-1]) == "down"


def test_operation_table_compares_mirrored_cells_by_label(monkeypatch):
    monkeypatch.setattr(app, "model", lambda: (_ for _ in ()).throw(AssertionError("unexpected model call")))
    question = """Which subset of elements proves the operation is not commutative?
Give a comma separated answer in alphabetical order.

|*|z|m|a|
|---|---|---|---|
|m|a|m|a|
|a|m|a|a|
|z|z|z|m|
"""
    assert app.answer_question(question) == "m, z"
