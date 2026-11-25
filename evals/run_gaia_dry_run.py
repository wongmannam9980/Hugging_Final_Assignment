"""Run a small number of official GAIA questions locally, NEVER submit.

Usage: python evals/run_gaia_dry_run.py --limit 2
Downloaded attachments and results stay in ignored local directories.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api import get_questions, download_attachment
from app import error_status, run_question

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=2)
    parser.add_argument('--output', type=Path, default=ROOT / 'evals' / 'local_results' / 'gaia_dry_run.jsonl')
    parser.add_argument('--resume', action='store_true', help='Continue the single run already in the output file')
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 20:
        parser.error('--limit must be between 1 and 20')
    tasks = get_questions()
    task_ids = [task["task_id"] for task in tasks]
    if len(tasks) != 20 or len(set(task_ids)) != len(task_ids):
        parser.error("Expected 20 unique official tasks")
    run_id = uuid4().hex
    completed = set()
    if args.resume:
        previous = [json.loads(line) for line in args.output.read_text(encoding='utf-8').splitlines() if line]
        run_ids = {record['run_id'] for record in previous}
        completed = {record['task_id'] for record in previous}
        if len(run_ids) != 1 or len(completed) != len(previous) or not completed <= set(task_ids[:args.limit]):
            parser.error('Resume requires one run with unique task IDs from the selected tasks')
        run_id = run_ids.pop()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    attachment_dir = ROOT / 'evals' / 'local_attachments'
    with args.output.open('a', encoding='utf-8') as stream:
        for index, task in enumerate(tasks[:args.limit], start=1):
            if task['task_id'] in completed:
                continue
            print(f"\n[{index}/{args.limit}] {task['task_id']}", flush=True)
            print(task['question'], flush=True)
            started = time.monotonic()
            record = {'task_id': task['task_id'], 'run_id': run_id,
                      'run_at_utc': datetime.now(timezone.utc).isoformat()}
            phase = 'attachment'
            try:
                attachment = download_attachment(task, attachment_dir)
                phase = 'graph'
                result = run_question(task['question'], attachment)
                record.update(answer=result['answer'], status=result['status'],
                              findings=[{'agent': f['agent'], 'status': f['status']}
                                        for f in result['findings']],
                              delegations=result['delegations'],
                              tool_calls=result.get('tool_calls', 0))
            except Exception as exc:
                status = error_status(exc)
                if phase == 'attachment' and status == 'execution_error':
                    status = 'attachment_error'
                record.update(answer='', status=status, phase=phase, error_type=type(exc).__name__)
            record['elapsed_s'] = round(time.monotonic() - started, 2)
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')
            stream.flush()
            print(f"{record['task_id']}: {record['status']} elapsed={record['elapsed_s']}s")
    print('DRY RUN ONLY: nothing was submitted. Scoring requires the official submission flow.')

if __name__ == '__main__':
    main()
