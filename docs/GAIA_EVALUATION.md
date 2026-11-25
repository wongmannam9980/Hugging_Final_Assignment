# My GAIA learning journal

My first GAIA evaluation score was **4/20 (20%)**. My best run scored **8/20 (40%)**, above the course's passing threshold of 6/20. A later run scored 5/20, so I still need to make the improvements more consistent. The [evaluation notes](GAIA_PROGRESS_2026-11-23.md) record the scores and run details.

## The album research question

The album research question was the first one I tried. I spent a few hours on it, revising prompts and saving attempts in JSON so I could compare what happened. Some runs came back with too little evidence. Others exhausted the research budget, hit a `GraphRecursionError`, or failed to access an API. Reading the logs helped me see whether to check the sources, the graph's stopping conditions, or the tool's API access.

## What I changed

I had to decide which tools each specialist could access and when it should use them. For research, I used Tavily to find web sources and BM25 to rank text chunks by how closely they matched the question.

When the first search left a gap, I adjusted the manager's prompt so it could call the research agent again with a narrower question based on what it already knew. The manager identified the missing evidence, and the research agent chose how to look for it. In the album run I reviewed, the steps followed a clearer sequence, and the research agent returned enough evidence for the manager to check its answer.

## What I learned

The JSON log became the starting point for deciding what to change. I could look at the evidence the agent returned and decide whether it needed a sharper follow-up question, a different tool, or a better stopping rule. For my next run, I want to compare the evidence and the final answer format across repeated attempts so I can see which improvements hold up.
