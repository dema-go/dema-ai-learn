from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models.tables import Answer, Attempt, Feedback, Material, Question, Quiz, Task, User
from app.services.attempts import get_latest_attempt
from app.services.quota import quota_payload


def list_recent(db: Session, user_id: str, filter_name: str = "all") -> list[dict]:
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == user_id)
        .order_by(Quiz.created_at.desc())
        .all()
    )
    items = [_recent_item(db, quiz) for quiz in quizzes]
    if filter_name == "active":
        return [item for item in items if item["status"] == "active"]
    if filter_name == "retest":
        return [item for item in items if item["status"] == "retest"]
    return items


def _recent_item(db: Session, quiz: Quiz) -> dict:
    attempt = get_latest_attempt(db, quiz, quiz.user_id)
    status = "active"
    correct = None
    wrong_count = 0
    current_ordinal = 1
    if attempt and attempt.completed_at is not None:
        correct = attempt.score
        wrong_count = db.query(Answer).filter(
            Answer.attempt_id == attempt.id, Answer.is_correct.is_(False)
        ).count()
        status = "retest" if wrong_count else "completed"
        current_ordinal = quiz.question_count
    elif attempt:
        current_ordinal = attempt.current_ordinal
    return {
        "quiz_id": quiz.id,
        "material_id": quiz.material_id,
        "title": quiz.material.title if quiz.material else "",
        "status": status,
        "correct": correct,
        "total": quiz.question_count,
        "wrong_count": wrong_count,
        "current_ordinal": current_ordinal,
        "created_at": quiz.created_at,
    }


def build_home(db: Session, user: User) -> dict:
    recent = list_recent(db, user.id)
    primary = {"type": "create"}
    retest_item = next((item for item in recent if item["status"] == "retest"), None)
    active_item = next((item for item in recent if item["status"] == "active"), None)
    if retest_item:
        primary = {
            "type": "retest",
            "quiz_id": retest_item["quiz_id"],
            "material_id": retest_item["material_id"],
            "title": retest_item["title"],
            "wrong_count": retest_item["wrong_count"],
            "question_count": retest_item["total"],
        }
    elif active_item:
        primary = {
            "type": "continue",
            "quiz_id": active_item["quiz_id"],
            "material_id": active_item["material_id"],
            "title": active_item["title"],
            "current_ordinal": active_item["current_ordinal"],
            "question_count": active_item["total"],
        }
    completed = (
        db.query(Attempt)
        .filter(Attempt.user_id == user.id, Attempt.completed_at.is_not(None))
        .count()
    )
    retests = db.query(Quiz).filter(Quiz.user_id == user.id, Quiz.is_retest.is_(True)).count()
    return {
        "quota": quota_payload(db, user.id),
        "primary_task": primary,
        "recent": recent[:5],
        "me": {
            "streak_days": user.streak_days,
            "stars": user.stars,
            "completed_count": completed,
            "retest_count": retests,
        },
    }


def delete_material(db: Session, material_id: str, user_id: str) -> None:
    material = (
        db.query(Material)
        .filter(Material.id == material_id, Material.user_id == user_id)
        .one_or_none()
    )
    if material is None:
        raise DomainError("MATERIAL_NOT_FOUND", "找不到这份材料。", status_code=404)
    quizzes = db.query(Quiz).filter(Quiz.material_id == material.id).all()
    quiz_ids = [quiz.id for quiz in quizzes]
    question_ids = [
        item.id
        for item in db.query(Question).filter(Question.quiz_id.in_(quiz_ids)).all()
    ] if quiz_ids else []
    attempt_ids = [
        item.id
        for item in db.query(Attempt).filter(Attempt.quiz_id.in_(quiz_ids)).all()
    ] if quiz_ids else []
    if attempt_ids:
        db.query(Answer).filter(Answer.attempt_id.in_(attempt_ids)).delete(synchronize_session=False)
        db.query(Attempt).filter(Attempt.id.in_(attempt_ids)).delete(synchronize_session=False)
    if question_ids:
        db.query(Feedback).filter(Feedback.question_id.in_(question_ids)).delete(
            synchronize_session=False
        )
        db.query(Question).filter(Question.id.in_(question_ids)).delete(synchronize_session=False)
    db.query(Task).filter(Task.material_id == material.id).delete(synchronize_session=False)
    if quiz_ids:
        db.query(Quiz).filter(Quiz.id.in_(quiz_ids)).delete(synchronize_session=False)
    db.delete(material)
    db.flush()


def submit_feedback(db: Session, question_id: str, user_id: str, error_type: str) -> None:
    question = db.query(Question).filter(Question.id == question_id).one_or_none()
    if question is None:
        raise DomainError("QUESTION_NOT_FOUND", "找不到这道题。", status_code=404)
    existing = (
        db.query(Feedback)
        .filter(
            Feedback.question_id == question_id,
            Feedback.user_id == user_id,
            Feedback.error_type == error_type,
        )
        .one_or_none()
    )
    if existing is None:
        db.add(Feedback(question_id=question_id, user_id=user_id, error_type=error_type))
        from app.services.events import track_event

        track_event(
            db,
            user_id,
            "question_error_reported",
            {"question_id": question_id, "error_type": error_type},
        )
        db.flush()
