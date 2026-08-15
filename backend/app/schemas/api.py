from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    source_type: Literal["text", "url"]
    text: str | None = None
    url: str | None = None
    channel: str | None = None


class GenerateResponse(BaseModel):
    task_id: str
    status: str
    quiz_id: str | None = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: str
    stage: str
    quiz_id: str | None = None
    question_count: int | None = None
    error: str | None = None


class QuotaOut(BaseModel):
    used: int
    limit: int
    reset_at: datetime


class PrimaryTaskOut(BaseModel):
    type: Literal["retest", "continue", "create"]
    quiz_id: str | None = None
    material_id: str | None = None
    title: str | None = None
    wrong_count: int | None = None
    current_ordinal: int | None = None
    question_count: int | None = None


class RecentItemOut(BaseModel):
    quiz_id: str
    material_id: str
    title: str
    status: Literal["active", "completed", "retest"]
    correct: int | None = None
    total: int | None = None
    wrong_count: int | None = None
    current_ordinal: int | None = None
    created_at: datetime


class MeStats(BaseModel):
    streak_days: int
    stars: int
    completed_count: int
    retest_count: int = 0


class HomeResponse(BaseModel):
    quota: QuotaOut
    primary_task: PrimaryTaskOut
    recent: list[RecentItemOut]
    me: MeStats


class EventRequest(BaseModel):
    name: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AnswerRequest(BaseModel):
    attempt_id: str | None = None
    question_id: str
    chosen_index: int


class FeedbackRequest(BaseModel):
    error_type: Literal["no_evidence", "wrong_answer", "ambiguous", "too_easy"]


class HealthResponse(BaseModel):
    status: Literal["ok"]


class OkResponse(BaseModel):
    ok: bool


class QuestionOut(BaseModel):
    question_id: str
    question_type: Literal["single", "true_false"]
    stem: str
    options: list[str]
    answer_index: int
    explanation: str
    source_span: str
    quality_status: Literal["passed", "degraded"]
    knowledge_point: str = ""
    ordinal: int = 0


class QuizResult(BaseModel):
    correct: int
    total: int
    duration_seconds: int
    wrong_question_ids: list[str]


class AnswerResponse(BaseModel):
    is_correct: bool
    chosen_index: int
    correct_index: int
    explanation: str
    source_span: str
    attempt_id: str
    next_question_id: str | None = None
    finished: bool
    result: QuizResult | None = None


class QuizResponse(BaseModel):
    id: str
    material_id: str
    title: str = ""
    question_count: int
    is_degraded: bool
    is_retest: bool
    parent_quiz_id: str | None = None
    questions: list[QuestionOut]
    ai_notice: str


class RecentListResponse(BaseModel):
    items: list[RecentItemOut]
