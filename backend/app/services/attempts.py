from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models.tables import Answer, Attempt, Question, Quiz, User
from app.services.events import track_event
from app.timeutil import utcnow


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _duration_seconds(started_at: datetime | None, completed_at: datetime | None) -> int:
    start = _as_utc(started_at)
    end = _as_utc(completed_at)
    if start is None or end is None:
        return 0
    return max(int((end - start).total_seconds()), 0)


def get_open_attempt(db: Session, quiz: Quiz, user_id: str) -> Attempt | None:
    return (
        db.query(Attempt)
        .filter(
            Attempt.quiz_id == quiz.id,
            Attempt.user_id == user_id,
            Attempt.completed_at.is_(None),
        )
        .order_by(Attempt.started_at.desc())
        .first()
    )


def get_latest_attempt(db: Session, quiz: Quiz, user_id: str) -> Attempt | None:
    return (
        db.query(Attempt)
        .filter(Attempt.quiz_id == quiz.id, Attempt.user_id == user_id)
        .order_by(Attempt.started_at.desc())
        .first()
    )


def _answer_response(
    db: Session,
    quiz: Quiz,
    question: Question,
    attempt: Attempt,
    answer: Answer,
) -> dict:
    answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    finished = len(answers) >= quiz.question_count
    result = None
    next_question_id = None
    if finished:
        wrong_ids = [item.question_id for item in answers if not item.is_correct]
        result = {
            "correct": attempt.score,
            "total": quiz.question_count,
            "duration_seconds": _duration_seconds(attempt.started_at, attempt.completed_at),
            "wrong_question_ids": wrong_ids,
        }
    else:
        answered_ids = {item.question_id for item in answers}
        remaining = [
            item
            for item in sorted(quiz.questions, key=lambda row: row.ordinal)
            if item.id not in answered_ids
        ]
        if remaining:
            next_question_id = remaining[0].id
    return {
        "is_correct": answer.is_correct,
        "correct_index": question.answer_index,
        "explanation": question.explanation,
        "source_span": question.source_span,
        "attempt_id": attempt.id,
        "next_question_id": next_question_id,
        "finished": finished,
        "result": result,
    }


def submit_answer(
    db: Session,
    quiz: Quiz,
    user: User,
    question_id: str,
    chosen_index: int,
    attempt_id: str | None = None,
) -> dict:
    question = (
        db.query(Question)
        .filter(Question.id == question_id, Question.quiz_id == quiz.id)
        .one_or_none()
    )
    if question is None:
        raise DomainError("QUESTION_NOT_FOUND", "找不到这道题。", status_code=404)

    attempt = None
    if attempt_id:
        attempt = (
            db.query(Attempt)
            .filter(Attempt.id == attempt_id, Attempt.user_id == user.id, Attempt.quiz_id == quiz.id)
            .one_or_none()
        )
        if attempt is None:
            raise DomainError("ATTEMPT_NOT_FOUND", "找不到这次作答。", status_code=404)
    else:
        attempt = get_open_attempt(db, quiz, user.id)
        if attempt is None:
            latest = get_latest_attempt(db, quiz, user.id)
            if latest is not None:
                replayed = (
                    db.query(Answer)
                    .filter(Answer.attempt_id == latest.id, Answer.question_id == question.id)
                    .one_or_none()
                )
                if replayed is not None:
                    return _answer_response(db, quiz, question, latest, replayed)
        if attempt is None:
            attempt = Attempt(quiz_id=quiz.id, user_id=user.id, current_ordinal=question.ordinal)
            db.add(attempt)
            db.flush()

    answered_before = db.query(Answer).filter(Answer.attempt_id == attempt.id).count()
    is_correct = chosen_index == question.answer_index
    answer = Answer(
        attempt_id=attempt.id,
        question_id=question.id,
        chosen_index=chosen_index,
        is_correct=is_correct,
    )
    try:
        with db.begin_nested():
            db.add(answer)
            db.flush()
    except IntegrityError:
        replayed = (
            db.query(Answer)
            .filter(Answer.attempt_id == attempt.id, Answer.question_id == question.id)
            .one_or_none()
        )
        if replayed is None:
            raise
        return _answer_response(db, quiz, question, attempt, replayed)

    if answered_before == 0:
        track_event(db, user.id, "quiz_started", {"quiz_id": quiz.id})
    if is_correct:
        attempt.score += 1
        user.stars += 1
    attempt.current_ordinal = min(question.ordinal + 1, quiz.question_count)
    db.flush()
    answered_count = db.query(Answer).filter(Answer.attempt_id == attempt.id).count()
    if answered_count >= quiz.question_count:
        attempt.completed_at = utcnow()
        if not quiz.is_retest:
            user.streak_days = max(user.streak_days, 1)
        track_event(
            db,
            user.id,
            "quiz_completed",
            {"quiz_id": quiz.id, "score": attempt.score},
        )
    db.flush()
    return _answer_response(db, quiz, question, attempt, answer)


def create_retest(db: Session, quiz: Quiz, user: User) -> Quiz:
    attempt = (
        db.query(Attempt)
        .filter(
            Attempt.quiz_id == quiz.id,
            Attempt.user_id == user.id,
            Attempt.completed_at.is_not(None),
        )
        .order_by(Attempt.completed_at.desc())
        .first()
    )
    if attempt is None:
        raise DomainError("NO_WRONG_ANSWERS", "还没有完成的闯关，无法复测。")
    wrong_answers = [item for item in attempt.answers if not item.is_correct]
    if not wrong_answers:
        raise DomainError("NO_WRONG_ANSWERS", "这关没有错题，可以直接再考一篇。")
    retest = Quiz(
        material_id=quiz.material_id,
        user_id=user.id,
        question_count=len(wrong_answers),
        is_degraded=False,
        is_retest=True,
        parent_quiz_id=quiz.id,
    )
    db.add(retest)
    db.flush()
    for ordinal, answer in enumerate(wrong_answers, start=1):
        source = db.query(Question).filter(Question.id == answer.question_id).one()
        db.add(
            Question(
                quiz_id=retest.id,
                ordinal=ordinal,
                question_type=source.question_type,
                stem=source.stem,
                options_json=source.options_json,
                answer_index=source.answer_index,
                source_span=source.source_span,
                explanation=source.explanation,
                quality_status=source.quality_status,
                knowledge_point=source.knowledge_point,
            )
        )
    track_event(db, user.id, "retest_started", {"quiz_id": retest.id, "parent_quiz_id": quiz.id})
    db.flush()
    return retest
