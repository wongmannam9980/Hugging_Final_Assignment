"""Gradio entry point for the Hugging Face Agents Course Space."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import gradio as gr
import requests

from api import BASE_URL, download_attachment, get_questions
from app import error_status, run_question


def evaluate(profile: gr.OAuthProfile | None):
    if profile is None:
        return "Sign in to run the evaluation.", [], []
    try:
        tasks = get_questions()
        if len(tasks) != 20 or len({task["task_id"] for task in tasks}) != 20:
            return "The course API did not provide 20 unique tasks.", [], []
    except (requests.RequestException, TypeError, ValueError, KeyError) as exc:
        return f"Could not load tasks ({type(exc).__name__}).", [], []

    rows = []
    answers = []
    with TemporaryDirectory() as directory:
        for index, task in enumerate(tasks, start=1):
            print(f"\n[{index}/{len(tasks)}] {task['task_id']}", flush=True)
            print(task['question'], flush=True)
            phase = "attachment"
            try:
                attachment = download_attachment(task, Path(directory))
                phase = "graph"
                result = run_question(task["question"], attachment)
                answer, status = result["answer"], result["status"]
            except Exception as exc:
                answer, status = "", error_status(exc)
                if phase == "attachment" and status == "execution_error":
                    status = "attachment_error"
            rows.append([task["task_id"], status, answer, "Ungraded"])
            answers.append({"task_id": task["task_id"], "submitted_answer": answer})
    answered = sum(bool(item["submitted_answer"]) for item in answers)
    return f"Run finished. {answered}/20 produced answers. Correctness has not been checked.", rows, answers


def submit(answers: list[dict], profile: gr.OAuthProfile | None) -> str:
    space_id = os.getenv("SPACE_ID")
    if profile is None or not space_id:
        return "Sign in on the deployed Space to submit."
    if len(answers) != 20 or not any(item["submitted_answer"] for item in answers):
        return "Run an evaluation that produces at least one answer."
    try:
        response = requests.post(
            f"{BASE_URL}/submit",
            json={"username": profile.username, "agent_code": f"https://huggingface.co/spaces/{space_id}/tree/main",
                  "answers": answers},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return (
            f"Official score {result['score']}% ({result['correct_count']}/{result['total_attempted']}). "
            "The official response gives a total score only."
        )
    except (requests.RequestException, ValueError, KeyError) as exc:
        return f"Submission failed ({type(exc).__name__})."


def build_demo():
    with gr.Blocks() as demo:
        gr.Markdown("# GAIA Level 1 Evaluation")
        gr.LoginButton()
        answers = gr.State([])
        run = gr.Button("Run local evaluation", variant="primary")
        status = gr.Textbox(label="Evaluation status", interactive=False)
        table = gr.Dataframe(
            headers=["Task ID", "Run status", "Answer", "Correctness"], interactive=False
        )
        send = gr.Button("Submit to the course leaderboard")
        score = gr.Textbox(label="Submission status", interactive=False)
        run.click(evaluate, outputs=[status, table, answers], api_name=False)
        send.click(submit, inputs=[answers], outputs=[score], api_name=False)
    return demo


if __name__ == "__main__":
    build_demo().queue().launch()
