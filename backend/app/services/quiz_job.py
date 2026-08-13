from sqlalchemy.orm import Session

from app.adapters.quiz_model import get_quiz_model
from app.adapters.url_extract import extract_public_url
from app.errors import DomainError
from app.graphs.quiz_graph import build_quiz_graph
from app.models.tables import Material, Question, Quiz, Task
from app.services.events import track_event
from app.services.tasks import update_task_progress


def run_quiz_job(db: Session, task_id: str) -> Task:
    task = db.query(Task).filter(Task.id == task_id).one()
    material = db.query(Material).filter(Material.id == task.material_id).one()
    try:
        source = _resolve_source(task, material)
        update_task_progress(task, status="planning", stage="planning")
        db.flush()

        def on_progress(stage: str, n: int = 1) -> None:
            status = {
                "extracting": "extracting",
                "planning": "planning",
                "generating": "generating",
                "validating": "validating",
            }.get(stage, task.status)
            update_task_progress(task, status=status, stage=stage, n=n)

        graph = build_quiz_graph(get_quiz_model(), on_progress=on_progress)
        result = graph.invoke({"source_text": source, "retry_count": 0})
        status = result["status"]
        questions = result.get("valid_questions") or []
        if status == "failed" or not questions:
            update_task_progress(
                task,
                status="failed",
                stage="validating",
                error="这篇材料没法稳定出题。请换一段观点更完整的文字。",
            )
            db.flush()
            return task

        quiz = Quiz(
            material_id=material.id,
            user_id=task.user_id,
            question_count=len(questions),
            is_degraded=status == "degraded",
        )
        db.add(quiz)
        db.flush()
        for ordinal, item in enumerate(questions, start=1):
            db.add(
                Question(
                    quiz_id=quiz.id,
                    ordinal=ordinal,
                    question_type=item.question_type,
                    stem=item.stem,
                    options_json=item.options,
                    answer_index=item.answer_index,
                    source_span=item.source_span,
                    explanation=item.explanation,
                    quality_status="degraded" if status == "degraded" else "passed",
                    knowledge_point=item.knowledge_point,
                )
            )
        if not material.title:
            material.title = result.get("title") or material.title
        elif material.title in {material.source_url, ""}:
            material.title = result.get("title") or material.title
        update_task_progress(
            task,
            status=status,
            stage="validating",
            quiz_id=quiz.id,
        )
        track_event(db, task.user_id, "generation_success", {"quiz_id": quiz.id})
        db.flush()
        return task
    except DomainError as exc:
        update_task_progress(task, status="failed", stage=task.stage, error=exc.message)
        db.flush()
        return task


def _resolve_source(task: Task, material: Material) -> str:
    if material.source_type == "url":
        update_task_progress(task, status="extracting", stage="extracting")
        result = extract_public_url(material.source_url or "")
        if not result.ok:
            message = {
                "URL_LOGIN_WALL": "这个网页没法读取，可能需要登录、付费或验证码。请改用粘贴文本。",
                "URL_TOO_SHORT": "抽到的正文太短，换一篇或改用粘贴文本。",
                "URL_FETCH_FAILED": "网页读取失败，请改用粘贴文本。",
            }.get(result.error_code or "", "网页读取失败，请改用粘贴文本。")
            raise DomainError(result.error_code or "URL_FETCH_FAILED", message)
        material.raw_text = result.text
        material.title = result.title or material.title
        return result.text
    text = (material.raw_text or "").strip()
    if not text:
        raise DomainError("TEXT_EMPTY", "材料原文已不可用。")
    return text


def get_quiz_for_user(db: Session, quiz_id: str, user_id: str) -> Quiz:
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == user_id)
        .one_or_none()
    )
    if quiz is None:
        raise DomainError("QUIZ_NOT_FOUND", "找不到这场闯关。", status_code=404)
    return quiz
