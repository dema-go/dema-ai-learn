from __future__ import annotations

from collections.abc import Callable

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.adapters.quiz_model import QuizModel
from app.graphs.state import QuizGraphState, WorkerState
from app.graphs.validate import GeneratedQuestion, validate_question

ProgressCb = Callable[[str, int], None]


def build_quiz_graph(
    model: QuizModel, on_progress: ProgressCb | None = None
):
    def notify(stage: str, n: int = 1) -> None:
        if on_progress:
            on_progress(stage, n)

    def extract(state: QuizGraphState) -> dict:
        notify("extracting")
        text = " ".join(state["source_text"].split())
        return {
            "source_text": text,
            "title": text[:30] or "未命名材料",
            "progress_stage": "extracting",
            "retry_count": state.get("retry_count", 0),
            "raw_questions": [],
            "rejected": [],
            "valid_questions": [],
        }

    def plan(state: QuizGraphState) -> dict:
        notify("planning")
        result = model.plan(state["source_text"])
        return {
            "points": result.points,
            "title": result.title or state.get("title", ""),
            "progress_stage": "planning",
        }

    def assign_workers(state: QuizGraphState) -> list[Send]:
        return [
            Send("generate", {"point": point, "source_text": state["source_text"]})
            for point in state["points"]
        ]

    def generate(state: WorkerState) -> dict:
        notify("generating", 1)
        question = model.generate_question(state["source_text"], state["point"])
        data = question.model_dump()
        data["knowledge_point"] = state["point"]
        return {"raw_questions": [GeneratedQuestion.model_validate(data)]}

    def validate(state: QuizGraphState) -> dict:
        notify("validating")
        latest: dict[str, GeneratedQuestion] = {}
        for question in state.get("raw_questions", []):
            latest[question.knowledge_point] = question
        valid: list[GeneratedQuestion] = []
        rejected: list[dict] = []
        for point in state.get("points", []):
            question = latest.get(point)
            if question is None:
                rejected.append({"point": point, "reasons": ["missing"]})
                continue
            reasons = validate_question(question, state["source_text"])
            if reasons:
                rejected.append({"point": point, "reasons": reasons})
            else:
                valid.append(question)
        retry_count = state.get("retry_count", 0)
        if rejected:
            retry_count += 1
        return {
            "valid_questions": valid,
            "rejected": rejected,
            "retry_count": retry_count,
            "progress_stage": "validating",
        }

    def route_after_validate(state: QuizGraphState) -> str:
        if state.get("rejected") and state.get("retry_count", 0) <= 1:
            return "retry"
        return "finalize"

    def assign_retry(state: QuizGraphState) -> list[Send]:
        return [
            Send(
                "generate",
                {"point": item["point"], "source_text": state["source_text"]},
            )
            for item in state.get("rejected", [])
        ]

    def finalize(state: QuizGraphState) -> dict:
        valid = state.get("valid_questions", [])[:7]
        if len(valid) >= 5:
            status = "succeeded"
        elif len(valid) >= 3:
            status = "degraded"
        else:
            status = "failed"
        return {"valid_questions": valid, "status": status}

    builder = StateGraph(QuizGraphState)
    builder.add_node("extract", extract)
    builder.add_node("plan", plan)
    builder.add_node("generate", generate)
    builder.add_node("validate", validate)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "extract")
    builder.add_edge("extract", "plan")
    builder.add_conditional_edges("plan", assign_workers, ["generate"])
    builder.add_edge("generate", "validate")
    builder.add_conditional_edges(
        "validate",
        route_after_validate,
        {"retry": "retry_generate", "finalize": "finalize"},
    )
    builder.add_node("retry_generate", lambda state: {})
    builder.add_conditional_edges("retry_generate", assign_retry, ["generate"])
    builder.add_edge("finalize", END)
    return builder.compile()
