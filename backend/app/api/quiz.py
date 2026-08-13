from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.tables import Question, Quiz, User
from app.schemas.api import AnswerRequest, GenerateRequest, GenerateResponse, TaskResponse
from app.services.attempts import create_retest, submit_answer
from app.services.generate import submit_generate
from app.services.quiz_job import get_quiz_for_user, run_quiz_job
from app.services.records import list_recent
from app.services.tasks import get_task_for_user

AI_NOTICE = "AI 依据你的材料生成，可能有误"

router = APIRouter()


@router.post("/api/quiz/generate", response_model=GenerateResponse)
def generate_quiz(
    payload: GenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    task = submit_generate(db, user, payload)
    if task.status in {"pending", "extracting", "planning", "generating", "validating"}:
        run_quiz_job(db, task.id)
        db.refresh(task)
    return {"task_id": task.id, "status": task.status, "quiz_id": task.quiz_id}


@router.get("/api/quiz/task/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    task = get_task_for_user(db, task_id, user.id)
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "stage": task.stage,
        "quiz_id": task.quiz_id,
        "error": task.error,
    }


@router.get("/api/quiz/recent")
def recent_quizzes(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    filter: str = "all",
) -> dict:
    return {"items": list_recent(db, user.id, filter)}


@router.get("/api/quiz/{quiz_id}")
def get_quiz(
    quiz_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    quiz = get_quiz_for_user(db, quiz_id, user.id)
    return serialize_quiz(quiz)


@router.post("/api/quiz/{quiz_id}/answer")
def answer_question(
    quiz_id: str,
    payload: AnswerRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    quiz = get_quiz_for_user(db, quiz_id, user.id)
    return submit_answer(
        db,
        quiz,
        user,
        payload.question_id,
        payload.chosen_index,
        payload.attempt_id,
    )


@router.post("/api/quiz/{quiz_id}/retest", response_model=GenerateResponse)
def retest_quiz(
    quiz_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    quiz = get_quiz_for_user(db, quiz_id, user.id)
    retest = create_retest(db, quiz, user)
    return {"task_id": retest.id, "status": "succeeded", "quiz_id": retest.id}


def serialize_quiz(quiz: Quiz) -> dict:
    questions = sorted(quiz.questions, key=lambda item: item.ordinal)
    return {
        "id": quiz.id,
        "material_id": quiz.material_id,
        "title": quiz.material.title if quiz.material else "",
        "question_count": quiz.question_count,
        "is_degraded": quiz.is_degraded,
        "is_retest": quiz.is_retest,
        "parent_quiz_id": quiz.parent_quiz_id,
        "ai_notice": AI_NOTICE,
        "questions": [serialize_question(item) for item in questions],
    }


def serialize_question(question: Question) -> dict:
    return {
        "question_id": question.id,
        "question_type": question.question_type,
        "stem": question.stem,
        "options": question.options_json,
        "answer_index": question.answer_index,
        "explanation": question.explanation,
        "source_span": question.source_span,
        "quality_status": question.quality_status,
        "knowledge_point": question.knowledge_point,
        "ordinal": question.ordinal,
    }
