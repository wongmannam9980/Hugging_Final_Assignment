---
title: GAIA LangGraph Agent
sdk: gradio
sdk_version: 5.25.2
python_version: "3.12"
app_file: space_app.py
hf_oauth: true
---

# GAIA LangGraph Agent

A **separate copy** adapted from your uploaded `Final_unit.zip`, preserving the original manager + four specialist agents and Wikipedia/BM25 research approach.

**Status:** starter refactor with new tests and a local evaluation runner. It has **not** been shown to pass the official Hugging Face GAIA assessment.

## Architecture

`START -> manager -> [research | calculator | files | reasoning] -> manager -> ... -> final_answer -> END`

- **Manager:** chooses an eligible specialist at most once, or finishes. `MAX_DELEGATIONS` (default 5) caps dispatches.
- **Execution:** `MAX_TOOL_CALLS` (default 6) caps outbound tool calls per question. Duplicate calls reuse results and a repeated batch ends the specialist. `TASK_SECONDS` (default 120) is checked between calls. An in-flight request can finish after the deadline.
- **Research:** Wikipedia API with optional historical revision and BM25 chunks, not general web search.
- **Calculator:** restricted arithmetic parser (does not blindly trust model math).
- **Files:** text, CSV/TSV, JSON, PDF text, DOCX, XLSX. No image/audio parsing.
- **Reasoning:** can combine evidence from the other agents.

## Setup (PowerShell)

```powershell
cd GAIA_LangGraph_Agent
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
hf auth login
python -m pytest -q
python app.py "What is 12 * 13?"
```

A model supporting compatible tool calls through the configured Hugging Face inference provider is required. `HF_MODEL_ID` defaults to the model used in the uploaded original; change it if unavailable.

## Local evaluations

```powershell
python evals/run_local.py evals/sample_questions.jsonl
```

Run from the project root. This writes `evals/results.jsonl` for local debugging.
Add an `expected` field to any authorized case to include it in the local exact-match
score. Review `status`, `findings`, `delegations`, and `answer` to diagnose mistakes.

Run `python evals/run_gaia_dry_run.py --limit 20` for the course tasks, or add
`--resume` to continue an interrupted run with the same output path. Use a new
output path for each independent run. For a local GAIA exact-match score, run
`python evals/grade_gaia_local.py <results.jsonl>` with `pyarrow` installed and
a Hugging Face account already authorized for GAIA validation data.

## Fetch one course task

```powershell
python app.py --gaia-task-id YOUR_TASK_ID
```

See `api.py` for question retrieval and attachment download.

## Hugging Face Space

Use the project root as the Space repository. Include the Python modules,
`agents/`, `README.md`, and `requirements.txt`. Set `HF_TOKEN` as a Space Secret
with inference access and set `HF_MODEL_ID` as a Space Variable if your provider
requires a different tool-capable model. The app uses the runtime `SPACE_ID`
to build its public code URL. Space OAuth handles sign-in.

Run the evaluation first and review the task statuses. The separate
**Submit to the course leaderboard** button sends the stored answers and
displays the official score. Keep credentials, local evaluation output and
downloaded attachments out of the public repository.

See [the development journal](docs/DEVELOPMENT_JOURNAL.md) for evaluation results and the next-session backlog.

## Course / security caveats

Keep secrets out of ZIPs and Git. A public source or a web page is **untrusted evidence**, not instructions for the agent. File contents, tool output, and model responses may be adversarial. Verify model availability and current Hugging Face course requirements before assuming compatibility or passing.

## Learning patch (Stage 0)

This package is a *small update to the first ZIP*. `agents/factory.py` contains LLM and specialist construction; `app.py` keeps graph state, nodes, edges, and querying. Existing tool modules and CLI commands still work.

On Windows PowerShell, from your existing extracted folder:

```powershell
python -m pytest tests -q
python app.py "What is 12 * 13?"
python evals/run_gaia_dry_run.py --limit 2
```

See `docs/LEARNING_PATH.md` for stage gates. The dry-run needs network, Hugging Face authentication and an available model/tool-calling inference provider. It **does not score or submit** and cannot prove a pass. Files and detailed logs are excluded from Git.
