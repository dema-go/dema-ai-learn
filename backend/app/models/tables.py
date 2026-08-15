from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def new_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    openid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    stars: Mapped[int] = mapped_column(Integer, default=0)

    materials: Mapped[list[Material]] = relationship(back_populates="user")


class Material(Base):
    __tablename__ = "material"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(16))
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    expire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="materials")
    quizzes: Mapped[list[Quiz]] = relationship(back_populates="material")
    tasks: Mapped[list[Task]] = relationship(back_populates="material")


class Task(Base):
    __tablename__ = "task"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), index=True)
    material_id: Mapped[str] = mapped_column(ForeignKey("material.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    progress: Mapped[str] = mapped_column(String(80), default="正在理解原文")
    stage: Mapped[str] = mapped_column(String(32), default="extracting")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    quota_charged: Mapped[bool] = mapped_column(Boolean, default=True)
    quota_day: Mapped[str] = mapped_column(String(10), default="", index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    quiz_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    material: Mapped[Material] = relationship(back_populates="tasks")


class Quiz(Base):
    __tablename__ = "quiz"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    material_id: Mapped[str] = mapped_column(ForeignKey("material.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), index=True)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    is_degraded: Mapped[bool] = mapped_column(Boolean, default=False)
    is_retest: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_quiz_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    material: Mapped[Material] = relationship(back_populates="quizzes")
    questions: Mapped[list[Question]] = relationship(
        back_populates="quiz", order_by="Question.ordinal"
    )
    attempts: Mapped[list[Attempt]] = relationship(back_populates="quiz")


class Question(Base):
    __tablename__ = "question"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quiz.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    question_type: Mapped[str] = mapped_column(String(16))
    stem: Mapped[str] = mapped_column(Text)
    options_json: Mapped[list] = mapped_column(JSON)
    answer_index: Mapped[int] = mapped_column(Integer)
    source_span: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    quality_status: Mapped[str] = mapped_column(String(16), default="passed")
    knowledge_point: Mapped[str] = mapped_column(String(200), default="")

    quiz: Mapped[Quiz] = relationship(back_populates="questions")


class Attempt(Base):
    __tablename__ = "attempt"
    __table_args__ = (
        Index("uq_attempt_user_quiz", "user_id", "quiz_id", unique=True),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quiz.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    current_ordinal: Mapped[int] = mapped_column(Integer, default=1)

    quiz: Mapped[Quiz] = relationship(back_populates="attempts")
    answers: Mapped[list[Answer]] = relationship(back_populates="attempt")


class Answer(Base):
    __tablename__ = "answer"
    __table_args__ = (
        Index("uq_answer_attempt_question", "attempt_id", "question_id", unique=True),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempt.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("question.id"), index=True)
    chosen_index: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    attempt: Mapped[Attempt] = relationship(back_populates="answers")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    question_id: Mapped[str] = mapped_column(ForeignKey("question.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), index=True)
    error_type: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Event(Base):
    __tablename__ = "event"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
