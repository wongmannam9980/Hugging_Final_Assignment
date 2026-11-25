"""Access the Hugging Face Agents Course GAIA question API."""

from pathlib import Path
import requests

BASE_URL = "https://agents-course-unit4-scoring.hf.space"


def get_questions() -> list[dict]:
    """Download the public list of GAIA course questions."""
    response = requests.get(f"{BASE_URL}/questions", timeout=30)
    response.raise_for_status()
    return response.json()


def get_question(task_id: str) -> dict:
    """Find one GAIA question by its task ID."""
    for task in get_questions():
        if task["task_id"] == task_id:
            return task
    raise ValueError(f"GAIA task not found: {task_id}")


def download_attachment(task: dict, directory: Path) -> Path | None:
    """Save the task's attached file locally, or return None if it has no file."""
    if not task.get("file_name"):
        return None
    response = requests.get(f"{BASE_URL}/files/{task['task_id']}", timeout=60)
    response.raise_for_status()
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{task['task_id']}_{Path(task['file_name']).name}"
    destination.write_bytes(response.content)
    return destination


if __name__ == "__main__":
    # Running api.py alone previews one question; it does not start the agent.
    tasks = get_questions()
    print(f"Loaded {len(tasks)} questions")
    if tasks:
        print(tasks[0]["task_id"])
        print(tasks[0]["question"])
