from __future__ import annotations

import re
from collections import defaultdict
from typing import Protocol

from pydantic import BaseModel, Field

from app.config import get_settings
from app.graphs.validate import GeneratedQuestion, span_in_source


class KnowledgePlan(BaseModel):
    title: str
    points: list[str] = Field(min_length=5, max_length=7)


class QuizModel(Protocol):
    def plan(self, source: str) -> KnowledgePlan: ...

    def generate_question(self, source: str, point: str) -> GeneratedQuestion: ...


class FakeQuizModel:
    def __init__(
        self,
        plan: KnowledgePlan,
        questions: dict[str, GeneratedQuestion | list[GeneratedQuestion]],
    ) -> None:
        self._plan = plan
        self._questions = questions
        self.generate_calls: dict[str, int] = defaultdict(int)

    def plan(self, source: str) -> KnowledgePlan:
        return self._plan

    def generate_question(self, source: str, point: str) -> GeneratedQuestion:
        self.generate_calls[point] += 1
        payload = self._questions[point]
        if isinstance(payload, list):
            index = min(self.generate_calls[point] - 1, len(payload) - 1)
            return payload[index]
        return payload


class FixtureQuizModel:
    def plan(self, source: str) -> KnowledgePlan:
        spans = _source_spans(source, 5)
        return KnowledgePlan(
            title=_title(source),
            points=[f"要点{i + 1}" for i in range(len(spans))],
        )

    def generate_question(self, source: str, point: str) -> GeneratedQuestion:
        spans = _source_spans(source, 5)
        try:
            index = int(point.replace("要点", "")) - 1
        except ValueError:
            index = 0
        span = spans[min(max(index, 0), len(spans) - 1)]
        if not span_in_source(span, source):
            span = source[:40]
        return GeneratedQuestion(
            knowledge_point=point,
            question_type="true_false",
            stem=f"材料是否提到与「{span[:10]}」相关的内容？",
            options=["正确", "错误"],
            answer_index=0,
            source_span=span[:120],
            explanation="这道题只依据你提供的材料判断。",
        )


def get_quiz_model() -> QuizModel:
    settings = get_settings()
    if settings.deepseek_api_key:
        from app.adapters.deepseek_model import DeepSeekQuizModel

        return DeepSeekQuizModel(api_key=settings.deepseek_api_key)
    return FixtureQuizModel()


def _title(source: str) -> str:
    compact = re.sub(r"\s+", " ", source).strip()
    return compact[:30] or "未命名材料"


def _source_spans(source: str, count: int) -> list[str]:
    parts = [part.strip() for part in re.split(r"[。！？\n]", source) if len(part.strip()) >= 8]
    if len(parts) >= count:
        return parts[:7]
    cleaned = re.sub(r"\s+", "", source)
    if not cleaned:
        return [source[:40] or "材料内容"] * count
    size = max(16, min(40, max(len(cleaned) // count, 16)))
    spans: list[str] = []
    for i in range(count):
        start = min(i * size, max(len(cleaned) - size, 0))
        spans.append(cleaned[start : start + size])
    return spans
