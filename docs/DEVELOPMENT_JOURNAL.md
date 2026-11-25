# GAIA development journal

The [21 November progress note](GAIA_PROGRESS_2026-11-21.md) records the later
official score from the Desktop template and the priorities for the next run.
The entries below describe the earlier workspace-copy work.

## 21 November 2026 · Execution and evaluation

Worked on a copy of the Desktop project to preserve the original. Used the
existing `.venv312` environment (Python 3.12.10) and installed pytest into the
workspace's ignored `.venv/test-deps` directory.

| Finding | Change and verification |
| --- | --- |
| `tests/test_math.py` invoked a bare `ToolNode` at import time, blocking baseline collection in Python 3.12. | Exercise the album-count tool directly and assert range boundaries and deduplication. |
| `app.py` allowed repeated dispatch and each specialist could burn its own recursive graph limit. The live baseline reproduced `GraphRecursionError` inside specialists. | Keep the manager and four specialists. Use a shared tool budget, an eligible-route check, and a deadline checked between calls. Regression tests cover repeated lookup, a shared budget, and expiry. |
| `app.py` stringified message content and did not distinguish silence, abstention and execution failure. | Extract text blocks, remove common answer wrappers, preserve answer punctuation, and carry status separately. |
| `retrieve_tools.py::_article_chunks` dropped valid years in separate columns. `_relevant_chunks` could also return no evidence for count requests without a range. | Preserve year and title metadata, deduplicate studio rows, and use BM25 where no structured album range applies. The fixture covers boundary years, duplicates, live albums and unknown years. |
| `file_tools.py::inspect_file` accepted a model-selected path. | Bind the call to the caller-provided attachment. A regression test tries to substitute a different path. |

For the live local fixtures, arithmetic scored **1/1**, the factual lookup
returned `retrieval_error`, and the album question returned `empty_answer`.
Overall local exact match was **1/3 (33.3%)**. These three references are
independent of the course scoring endpoint.

The separate local GAIA grading command joins by task ID and keeps gated
references in memory. The validation download returned HTTP 403 with the
available credential, so GAIA accuracy remains unverified.

## GAIA Level 1 tool coverage

- **Retrieval.** Wikipedia search, revision lookup and table extraction support
  some factual questions and dated discographies. Search still selects the first
  article. General web, historical sources outside Wikipedia, and video evidence
  remain gaps. BM25 samples evidence outside the structured album path.
- **Calculator.** The arithmetic tool handles restricted numeric expressions.
  Unit conversion and formatting need representative cases. The album-count
  helper is tested directly and is outside the active tool registry.
- **Attachments.** The tool extracts text, CSV/TSV, JSON, PDF text, DOCX and
  XLSX within size and output limits. It reads Python source as text. Scanned
  PDFs, images, spreadsheets requiring formula evaluation, audio and video
  require additional capabilities.

The official target is **6/20**. The course grader matches submitted short
answers and updates the leaderboard. The Space layout uses a separate scoring
button and reads its inference credential from the environment.
[Unit 4 instructions](https://huggingface.co/learn/agents-course/en/unit4/hands-on) ·
[Official template](https://huggingface.co/spaces/agents-course/Final_Assignment_Template/tree/main)

## Next session

1. **P0 · Diagnose empty final answers.** Record provider finish reason and
   response block types without logging raw provider payloads. Verify whether
   the configured model consumes its completion budget before emitting text.
   Try a short non-reasoning finalizer and rerun the same task IDs.
2. **P0 · Investigate attachment download and retrieval failures.** Record
   upstream HTTP status and parser type. Confirm the first iPhone lookup and
   reproduce the pinned album revision end to end.
3. **P1 · Expand external evidence.** Add a general web retriever with source
   URLs and test it on historical sources beyond Wikipedia. Prioritize media
   formats using attachment frequencies from the 20-task manifest.
4. **P1 · Verify hosted behavior and score.** Build the public Space with
   runtime secrets and verify OAuth and the dry-run callback. Use the course
   scoring action after reviewing the predictions.
