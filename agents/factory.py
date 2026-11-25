"""Build and cache model-driven specialists; no LangGraph edges belong here."""
import os
from functools import lru_cache
from huggingface_hub import get_token
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from tools import tools as tool_registry

MODEL_ID = os.getenv("HF_MODEL_ID", "Qwen/Qwen3.8-27B")

@lru_cache(maxsize=1)
def model():
    token = get_token()
    if not token:
        raise RuntimeError("Run `hf auth login` or set HF_TOKEN before starting the agent.")
    endpoint = HuggingFaceEndpoint(
        repo_id=MODEL_ID, huggingfacehub_api_token=token, max_new_tokens=1024, timeout=30
    )
    return ChatHuggingFace(llm=endpoint)

SPECIALISTS = {
    "research": (
        tool_registry["research"],
        "You are a research agent. For factual questions, use wikipedia_retrieve. "
        "Derive the topic from the user's question and pass the full question to the tool. "
        "You may search another topic. Report evidence and source URLs. "
        "For counts, list the matching items. Say when evidence is insufficient."
    ),
    "calculator": (
        tool_registry["calculator"],
        "You are a calculation agent. Use calculate for arithmetic. "
        "Use supplied findings as data. Report expression, result, and assumptions. "
        "Do not invent missing numbers."
    ),
    "files": (
        tool_registry["files"],
        "You are a file agent. Use inspect_file on the supplied attachment path. "
        "Report relevant evidence, filename, and any format limitation."
    ),
    "reasoning": (
        tool_registry["reasoning"],
        "You are a reasoning agent. Analyze the question and other findings. "
        "Explain ambiguity or missing evidence. Do not claim you searched "
        "or read anything you have not seen."
    ),
}

@lru_cache(maxsize=4)
def specialist(name: str):
    tools, _ = SPECIALISTS[name]
    return model().bind_tools(tools) if tools else model()
