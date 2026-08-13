from __future__ import annotations

from typing import Annotated, TypedDict

from app.graphs.validate import GeneratedQuestion


def add_questions(
    left: list[GeneratedQuestion], right: list[GeneratedQuestion]
) -> list[GeneratedQuestion]:
    return (left or []) + (right or [])


class QuizGraphState(TypedDict, total=False):
    source_text: str
    title: str
    points: list[str]
    raw_questions: Annotated[list[GeneratedQuestion], add_questions]
    valid_questions: list[GeneratedQuestion]
    rejected: list[dict]
    retry_count: int
    status: str
    progress_stage: str


class WorkerState(TypedDict):
    point: str
    source_text: str
    raw_questions: Annotated[list[GeneratedQuestion], add_questions]
