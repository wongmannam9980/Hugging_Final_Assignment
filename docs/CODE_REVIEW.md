# Review of uploaded `Final_unit.zip` (November 18, 2026)

## What already worked conceptually
- `app.py`: actual LangGraph StateGraph with manager -> specialist -> manager loop, not just an unimplemented proposal.
- Four specialist agents (research, calculator, files, reasoning), each with scoped tools.
- `retrieve_tools.py`: Wikipedia API, article revisions, table-row preservation, BM25 ranking.
- `math_tools.py`: arithmetic AST allow-list instead of arbitrary `eval`.
- `api.py`: question retrieval and attachment download.

## Problems and limitations (evidence from original sources)
1. `retrieve_tools.py::_article_for_topic()` always chooses first Wikipedia search hit; ambiguous terms can retrieve the wrong article.
2. `retrieve_tools.py::_relevant_chunks()` filters by best section match, and returns at most eight BM25 chunks outside detected year-range tables. This may exclude necessary rows; counting must not be inferred from incomplete samples.
3. `file_tools.py::inspect_file()` cannot handle images/audio and returns only the first 24,000 characters; GAIA questions may require visual/audio analysis or material later in a file.
4. `app.py::manager()` routes with free-form model JSON parsed via regex rather than a validated schema; malformed routing can repeatedly send the same question to `reasoning`.
5. `app.py::_run_specialist()` originally raised on tool/model failures, terminating the workflow rather than recording a recoverable failure. **Improved in this copy** with a summarized failure result.
6. `app.py::answer_question()` originally resolved non-existent paths without checking they existed. **Improved in this copy**.
7. `api.py` handles getting questions and attachments, but has no submission client. A local evaluation runner is **added in this copy**, intentionally without posting answers.
8. No tests existed in the uploaded ZIP. **Initial unit tests added**, but they are not a complete benchmark or proof of GAIA passing.

## Suggested next engineering steps (not yet implemented)
- Add a web search tool that can cite sources, with bounded timeout and rate limiting.
- Make Wikipedia article selection explicit; support multiple candidate articles and add a confidence gate.
- Separate extraction of all matching data rows from BM25 summary retrieval; never count a partial sample.
- Validate manager output with structured JSON/schema, plus no-progress detection.
- Support image/audio attachments through an authorized multimodal model or dedicated tool.
- Restrict `inspect_file` to the single file provided by a trusted caller.
- Add a real evaluation dataset and investigate errors per task; don't optimize only on memorized examples.
- Implement course submission endpoint only after checking its latest official contract.
