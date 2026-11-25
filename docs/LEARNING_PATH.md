# GAIA certification — learn-by-building plan

This is the FIRST VERSION project with a small structural refactor, not a replacement.
No official passing score has been demonstrated.

## Stage 0: establish baseline (today)
- Read `app.py` and `agents/factory.py`; sketch the manager -> specialist -> manager flow.
- Install dependencies, run `python -m pytest tests -q`.
- Run `python app.py "What is 12 * 13?"` and explain which nodes were visited.
- Run `python evals/run_gaia_dry_run.py --limit 2`.
- Evidence: test result, no-crash local trace, two task IDs and failure categories.

## Stage 1: reliable routing
- Add tests for malformed routes and repeat delegation.
- Add structured manager route schema and a no-progress safeguard.
- Evidence: tests show unknown route cannot loop indefinitely.

## Stage 2: grounded research and counting
- Fix first-hit-only Wikipedia selection; compare multiple candidates.
- For count questions, retrieve all eligible rows, not only BM25 top eight.
- Add exhaustive row-count and historical-revision tests.
- Evidence: deterministic tests with known counts and cited source revision.

## Stage 3: tool coverage
- Add grounded web search only as needed, with sources and rate limits.
- Add attachment coverage based on observed question types.
- Evidence: at least one end-to-end test per tool family.

## Stage 4: answer and evaluation quality
- Short final answer without analysis/prefix; trace source and uncertainty separately.
- Categorize each miss: retrieval, selection, reasoning, math, file, formatting, runtime.
- Re-run authorized test cases after each change; avoid tuning on a single question.
- Evidence: repeatable logs and measurable accuracy on independently labeled data.

## Stage 5: Hugging Face submission
- Verify latest course API and OAuth/Space requirements.
- Integrate a submission interface in a separate module; keep normal testing non-submitting.
- Publish Space publicly and submit only on explicit user action.
- Evidence: score returned by official evaluation, target >=30%.

## Mentor rules
For every stage: hypothesize failure -> write test -> implement smallest change -> run tests -> document result.
Do not add five new agents before measuring what the current ones can do.
