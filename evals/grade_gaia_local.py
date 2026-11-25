"""Join dry-run results to the gated GAIA validation references locally."""

import argparse
import json
from collections import Counter
from io import BytesIO
from pathlib import Path

import requests
from huggingface_hub import get_token


def validation_references() -> dict[str, str]:
    # The gated data stays in memory and is never passed to the agent.
    import pyarrow.parquet as parquet

    token = get_token()
    if not token:
        raise PermissionError("Sign in with an account that already has access to GAIA.")
    response = requests.get(
        "https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/validation/metadata.level1.parquet",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    table = parquet.read_table(BytesIO(response.content), columns=["task_id", "Final answer"])
    return {row["task_id"]: str(row["Final answer"]) for row in table.to_pylist()
            if row["Final answer"] is not None}


def load_results(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    records = json.loads(text) if text.lstrip().startswith("[") else [
        json.loads(line) for line in text.splitlines() if line.strip()
    ]
    if not records or any(
        not isinstance(row, dict)
        or not isinstance(row.get("task_id"), str)
        or not row["task_id"]
        or not isinstance(row.get("submitted_answer", row.get("answer")), str)
        for row in records
    ):
        raise ValueError("Each task needs a task ID and a text answer, which may be blank.")
    if len({row["task_id"] for row in records}) != len(records):
        raise ValueError("Use a single run with unique task IDs.")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="Gradio JSON or CLI JSONL from one run")
    args = parser.parse_args()
    try:
        records = load_results(args.results)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    try:
        references = validation_references()
    except requests.HTTPError as exc:
        parser.exit(1, f"GAIA references unavailable (HTTP {exc.response.status_code}).\n")
    except (requests.RequestException, ImportError, PermissionError) as exc:
        parser.exit(1, f"GAIA references unavailable ({type(exc).__name__}).\n")
    grades = Counter()
    for index, row in enumerate(records, start=1):
        task_id = row["task_id"]
        answer = row.get("submitted_answer", row.get("answer"))
        if task_id not in references:
            verdict = "Reference unavailable"
        elif not answer.strip():
            verdict = "Unanswered"
        else:
            verdict = "Correct" if answer == references[task_id] else "Incorrect"
        grades[verdict] += 1
        print(f"{index:>2}. {verdict:<21} {task_id}  {answer!r}")

    graded = len(records) - grades["Reference unavailable"]
    if graded:
        correct = grades["Correct"]
        print(f"Local exact match: {correct}/{graded} ({correct / graded:.1%})")
    print(f"Reference coverage: {graded}/{len(records)} tasks. Grades: {dict(grades)}")


if __name__ == "__main__":
    main()
