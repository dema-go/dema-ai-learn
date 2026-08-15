import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

os.environ["KAOWOYIXIA_ENV_FILE"] = ""
os.environ["DEEPSEEK_API_KEY"] = ""

from app.models.tables import Answer, Attempt, Base, Material, Question, Quiz, User
from app.services.attempts import submit_answer
from app.timeutil import utcnow


def _database(tmp_path, *, with_first_answer: bool = False):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'answers.sqlite3'}",
        connect_args={"check_same_thread": False, "timeout": 5},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with factory.begin() as db:
        user = User(id="user-1", openid="concurrent-user", stars=0)
        material = Material(
            id="material-1",
            user_id=user.id,
            source_type="text",
            title="并发测试材料",
            content_hash="hash",
            raw_text="测试材料",
            expire_at=utcnow() + timedelta(days=1),
        )
        quiz = Quiz(
            id="quiz-1",
            material_id=material.id,
            user_id=user.id,
            question_count=2,
        )
        first = Question(
            id="question-1",
            quiz_id=quiz.id,
            ordinal=1,
            question_type="single_choice",
            stem="第一题",
            options_json=["对", "错"],
            answer_index=0,
            source_span="测试材料",
            explanation="第一题解析",
        )
        second = Question(
            id="question-2",
            quiz_id=quiz.id,
            ordinal=2,
            question_type="single_choice",
            stem="第二题",
            options_json=["对", "错"],
            answer_index=0,
            source_span="测试材料",
            explanation="第二题解析",
        )
        db.add_all([user, material, quiz, first, second])
        if with_first_answer:
            user.stars = 1
            attempt = Attempt(
                id="attempt-1",
                quiz_id=quiz.id,
                user_id=user.id,
                started_at=utcnow() - timedelta(seconds=45),
                score=1,
                current_ordinal=2,
            )
            db.add_all(
                [
                    attempt,
                    Answer(
                        id="answer-1",
                        attempt_id=attempt.id,
                        question_id=first.id,
                        chosen_index=0,
                        is_correct=True,
                    ),
                ]
            )
    return engine, factory


def _synchronize_identity_statement(engine, table: str):
    barrier = threading.Barrier(2)
    local = threading.local()

    def synchronize():
        if getattr(local, "synchronized", False):
            return
        local.synchronized = True
        barrier.wait(timeout=5)

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(_connection, _cursor, statement, _parameters, _context, _many):
        normalized = " ".join(statement.lower().split())
        if normalized.startswith(f"insert into {table}"):
            synchronize()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(_connection, _cursor, statement, _parameters, _context, _many):
        normalized = " ".join(statement.lower().split())
        if table == "attempt" and "from attempt" in normalized and "completed_at is null" in normalized:
            synchronize()


def _submit(factory, question_id: str, *, attempt_id: str | None = None) -> dict:
    with factory() as db:
        quiz = db.get(Quiz, "quiz-1")
        user = db.get(User, "user-1")
        assert quiz is not None and user is not None
        response = submit_answer(
            db,
            quiz,
            user,
            question_id,
            chosen_index=0,
            attempt_id=attempt_id,
        )
        db.commit()
        return response


def test_concurrent_first_answer_acquires_one_attempt_and_scores_once(tmp_path):
    engine, factory = _database(tmp_path)
    _synchronize_identity_statement(engine, "attempt")
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_submit, factory, "question-1") for _ in range(2)]
            responses = [future.result(timeout=10) for future in futures]

        assert responses[0] == responses[1]
        with factory() as db:
            attempts = db.query(Attempt).all()
            answers = db.query(Answer).all()
            user = db.get(User, "user-1")
            assert len(attempts) == 1
            assert len(answers) == 1
            assert attempts[0].score == 1
            assert user is not None and user.stars == 1
    finally:
        engine.dispose()


def test_concurrent_final_answer_reloads_finished_attempt_after_collision(tmp_path):
    engine, factory = _database(tmp_path, with_first_answer=True)
    _synchronize_identity_statement(engine, "answer")
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(_submit, factory, "question-2", attempt_id="attempt-1")
                for _ in range(2)
            ]
            responses = [future.result(timeout=10) for future in futures]

        first, second = responses
        assert first["attempt_id"] == second["attempt_id"] == "attempt-1"
        assert first["finished"] is second["finished"] is True
        assert first["result"] == second["result"]
        assert first["result"]["correct"] == 2
        assert first["result"]["duration_seconds"] >= 45

        with factory() as db:
            attempt = db.get(Attempt, "attempt-1")
            user = db.get(User, "user-1")
            assert attempt is not None and attempt.completed_at is not None
            assert attempt.score == 2
            assert user is not None and user.stars == 2
            assert db.query(Answer).filter(Answer.attempt_id == attempt.id).count() == 2
    finally:
        engine.dispose()
