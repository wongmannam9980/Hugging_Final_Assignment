# GAIA development progress · 23 November 2026

## Evaluation results

The Desktop GAIA agent reached an official **8/20 (40%)** and updated the leaderboard, improving on the previous **4/20 (20%)**. The passing threshold is **6/20 (30%)**. A later official submission scored **5/20 (25%)**, so 8/20 remains the best verified result and the baseline for the next comparison.

The 8/20 run generated **10 answers**, left **5 blank**, and hit **5 attachment download failures**. The 5/20 run generated **7 answers**, left **7 blank**, recorded **1 execution error**, and hit the same **5 attachment download failures**. The official grader reported aggregate scores, so the logs identify changed outputs and failure modes but cannot attribute the three-point drop to specific questions.

## What we built and learned

- **Evaluate locally, grade through the Space.** Ran the agent in Gradio with Python 3.12 and Ollama, then uploaded a saved 20-question JSON report to the Hugging Face Space for official grading. Gradio now distinguishes a generated answer from a verified grade. A separate local grader can read the report, but the available Hugging Face credential received HTTP 403 from the gated validation dataset.
- **Use deterministic code when the question supplies all the data.** Question 6 compares mirrored operation-table cells and returns `b, e`. Question 3 reverses the text before the model interprets it and returns `right`. Both were verified through the agent's local entry points.
- **Count research calls separately from graph steps.** Wikipedia, Tavily search, and page reading share a four-call budget per question. The manager can request one follow-up with the unused calls. The passing run had no research recursion errors. A duplicate lookup can be blocked without making a new external request and still count as an attempted call in the current accounting.
- **Keep evidence through the handoff.** Saved research tool results separately from the model's summary. Long tool results caused Ollama context errors in both the manager and the nested research agent. Both now receive bounded excerpts. The terminal shows research passes, retrieval methods, tool results, and remaining calls.
- **Diagnose source discovery and extraction separately.** For question 18, the official 2023 roster lists Yoshida, Tamai, and Uehara at numbers 18, 19, and 20. A direct page-reader test returned all three rows. The autonomous run still struggled to reach that source. For question 5, a live diagnostic found FunkMonk in Tavily's raw extract but missing from the page-reader excerpt. We added section-aware reading and improved passage ranking to favor visible text over Markdown link destinations. Simulated tests passed. A correct end-to-end answer from the updated agent is still unverified for both questions.
- **Treat an answer format as an example.** Question 18 once emitted the literal placeholders `Pitcher Before, Pitcher After`. A guard now clears a copied format example when research reports insufficient evidence. This caught the placeholder in a simulated test. Verifying that actual names come from dated evidence remains a research task.

## Regressions to check next

| Question | What changed in the later run | Next check |
| --- | --- | --- |
| 1 · Album count | `3` changed to `three`. | Verify that count answers retain the numeric format expected by the grader. |
| 9 · Grocery list | A generated list became a `ResponseError`. | Reproduce the task and capture the underlying Ollama error message. |
| 13 · Yankees stats | The earlier `595` became a blank answer. | Check whether extraction preserves the full batting table and its walks and at-bats columns. |
| 15 · NASA award | The earlier award-number answer became blank after four searches and no page reads. | Verify that the agent opens the article and its linked paper, then finds the award in the acknowledgment. |

**Latest code change:** After Tavily returns candidate links, the next tool turn is restricted to page reading. At the budget limit, the research model gets a final turn with tools disabled. A simulated LangChain run completed search, article read, linked paper read, and final synthesis within three calls. The live question 15 result and the effect on the official score are still unverified.

The live changes were made in the Desktop template under `GAIA_Final_Assignment_Template/huggingface_space/agent_project`. This note is stored in the workspace copy with the earlier progress notes.
