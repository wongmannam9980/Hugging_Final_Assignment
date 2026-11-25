# GAIA assignment progress · 21 November 2026

**Official result: 4/20 correct (20%).** Hugging Face scored all 20 tasks and confirmed the leaderboard update. The pass threshold is **6/20 (30%)**, so two more correct answers are needed. The scorer reported an aggregate result. Individual grades are unavailable. [Unit 4 instructions](https://huggingface.co/learn/agents-course/en/unit4/hands-on) · [Public GAIA Space](https://huggingface.co/spaces/ZadPhoto/gaia-langgraph-agent)

## What I got working

- **Wikipedia retrieval.** The agent now reads the album table's `Year` column and preserves the user's request for the latest 2022 revision. The Mercedes Sosa task returned `3` in the latest local report. Earlier runs wrapped the count in a sentence, which can fail exact-match grading.
- **Web research.** Added Tavily search and page extraction alongside Wikipedia. Verified the Tavily key with a standalone HTTP 200 response. Moved the web tool instructions into the Research specialist and checked the wiring offline. The full LibreTexts task still returned an empty answer in the latest local report.
- **Local inference.** Used `.venv312` and added Ollama as a local option with `qwen3.5:9b` after Hugging Face Inference Providers returned HTTP 402. The agent ran locally with Ollama.
- **Evaluation and deployment.** Deployed the Gradio app to a public Hugging Face Space and obtained an official score for all 20 tasks. The app can grade a saved JSON run and display the pass status without rerunning the agent on the Space.
- **Debugging.** The terminal now shows questions, search inputs and reasons, and specialist findings. The CLI can save a per-question report with `--json-report`. Local status `completed` means the answer field contains text. The official scorer determines correctness.

## Remaining blockers

The latest local `gaia_results.json` reviewed today contained 20 records: 8 with nonempty answers, 4 empty answers, 5 attachments unavailable with HTTP 404, and 3 other errors. These are run outcomes. The official grader reported 4 correct without identifying the tasks.

- The course API listed the Excel attachment for #19 but returned HTTP 404 for its file URL. I opened a course support ticket.
- The agent can find context about a YouTube video. Its bird-count answer on #2 lacked a frame and timestamp demonstrating which species appeared together.

## Next session · 22 November 2026

| Priority | Task | Latest local output | Check for the next run |
| --- | --- | --- | --- |
| 1 | #3 · Reversed sentence | Empty | Read the reversed instruction and output only `right`. |
| 2 | #6 · Operation table | `a, b` | Compare entries across the diagonal and output `b, e`. |
| 3 | #8 · LibreTexts | Empty | Find the requested exercise through Tavily, record the supporting passage, and output only `Louvrier`. [LibreTexts 1.E Exercises](https://chem.libretexts.org/Bookshelves/Introductory_Chemistry/Introductory_Chemistry_%28LibreTexts%29/01%3A_The_Chemical_World/1.E%3A_Exercises) |

- [ ] Rerun #3 and #6 individually. Verify the exact output for each.
- [ ] If either remains unreliable, verify #8 from search through final answer.
- [ ] Rerun all 20 and save a fresh report. Submit that report from the public Space and compare the new score with 4/20.

After completing the GAIA assignment, start the separate AI engineering learning plan. The reusable Python solver exercise is saved there for later.
