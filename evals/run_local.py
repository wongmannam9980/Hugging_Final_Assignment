"""Run a user-provided JSONL evaluation set and store traces, without submitting to GAIA.

Input lines: {"task_id": "local-1", "question": "...", "attachment_path": ""}
Never put hidden benchmark reference answers or access tokens into public logs.
"""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import error_status, run_question


def main():
    p = argparse.ArgumentParser()
    p.add_argument("dataset", type=Path)
    p.add_argument("--output", type=Path, default=Path("evals/results.jsonl"))
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    statuses = Counter()
    correct = graded = 0
    with args.dataset.open(encoding="utf-8") as stream, args.output.open("a", encoding="utf-8") as output:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            case = json.loads(line)
            record = {"task_id": case.get("task_id", str(number)),
                      "time_utc": datetime.now(timezone.utc).isoformat()}
            print(f"\n{record['task_id']}", flush=True)
            print(case["question"], flush=True)
            try:
                result = run_question(case["question"], case.get("attachment_path"))
                record.update(answer=result["answer"], status=result["status"],
                              findings=[{"agent": finding["agent"], "status": finding["status"]}
                                        for finding in result["findings"]],
                              delegations=result["delegations"])
            except Exception as exc:
                record.update(answer="", status=error_status(exc), error_type=type(exc).__name__)
            statuses[record["status"]] += 1
            if "expected" in case:
                graded += 1
                record["correct"] = record["status"] == "answered" and record["answer"] == str(case["expected"])
                correct += record["correct"]
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
            print(record["task_id"], record["status"])
    print(f"Outcomes: {dict(statuses)}")
    print(f"Local exact match: {correct}/{graded} ({correct / graded:.1%})" if graded else "Local accuracy unavailable: no references supplied.")


if __name__ == "__main__":
    main()
