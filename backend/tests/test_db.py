import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, event, inspect, text

from app.db import init_db
from app.models.tables import Base, User


def test_init_db_creates_user_table(db_session):
    user = User(openid="o1", channel="dev")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
    loaded = db_session.query(User).filter_by(openid="o1").one()
    assert loaded.channel == "dev"
    assert loaded.streak_days == 0
    assert loaded.stars == 0


def _legacy_database_without_identity_indexes(url: str = "sqlite://"):
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP INDEX uq_answer_attempt_question")
        connection.exec_driver_sql("DROP INDEX uq_attempt_user_quiz")
    return engine


def test_init_db_rejects_legacy_duplicate_attempts_and_answers():
    engine = _legacy_database_without_identity_indexes()
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                """INSERT INTO attempt
                (id, quiz_id, user_id, started_at, completed_at, score, current_ordinal)
                VALUES
                ('a1', 'q1', 'u1', CURRENT_TIMESTAMP, NULL, 0, 1),
                ('a2', 'q1', 'u1', CURRENT_TIMESTAMP, NULL, 0, 1)"""
            )
            connection.exec_driver_sql(
                """INSERT INTO answer
                (id, attempt_id, question_id, chosen_index, is_correct, created_at)
                VALUES
                ('r1', 'a1', 'question-1', 0, 1, CURRENT_TIMESTAMP),
                ('r2', 'a1', 'question-1', 1, 0, CURRENT_TIMESTAMP)"""
            )

        with pytest.raises(RuntimeError) as error:
            init_db(engine)

        message = str(error.value)
        assert "duplicate attempt identities" in message
        assert "duplicate answer identities" in message
        assert "backup" in message.lower()
        assert "uq_attempt_user_quiz" not in {
            item["name"] for item in inspect(engine).get_indexes("attempt")
        }
        assert "uq_answer_attempt_question" not in {
            item["name"] for item in inspect(engine).get_indexes("answer")
        }
    finally:
        engine.dispose()


def test_init_db_versions_identity_indexes_and_repeated_startup_is_clean():
    engine = _legacy_database_without_identity_indexes()
    created_identity_indexes: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def record_identity_ddl(_connection, _cursor, statement, _parameters, _context, _many):
        normalized = " ".join(statement.lower().split())
        if normalized.startswith("create unique index uq_"):
            created_identity_indexes.append(normalized)

    try:
        init_db(engine)
        init_db(engine)

        attempt_index = next(
            item
            for item in inspect(engine).get_indexes("attempt")
            if item["name"] == "uq_attempt_user_quiz"
        )
        answer_index = next(
            item
            for item in inspect(engine).get_indexes("answer")
            if item["name"] == "uq_answer_attempt_question"
        )
        assert attempt_index["unique"] == 1
        assert attempt_index["column_names"] == ["user_id", "quiz_id"]
        assert answer_index["unique"] == 1
        assert answer_index["column_names"] == ["attempt_id", "question_id"]
        assert sum("uq_attempt_user_quiz" in ddl for ddl in created_identity_indexes) == 1
        assert sum("uq_answer_attempt_question" in ddl for ddl in created_identity_indexes) == 1

        with engine.connect() as connection:
            applied_versions = connection.execute(
                text("SELECT version FROM schema_migration ORDER BY version")
            ).scalars().all()
        assert applied_versions == [1]
    finally:
        engine.dispose()


def test_init_db_recovers_when_two_startups_apply_the_same_migration(tmp_path):
    engine = _legacy_database_without_identity_indexes(
        f"sqlite:///{tmp_path / 'migration.sqlite3'}"
    )
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE schema_migration (version INTEGER PRIMARY KEY, name VARCHAR(120) NOT NULL)"
        )

    version_barrier = threading.Barrier(2)
    ddl_barrier = threading.Barrier(2)
    local = threading.local()

    @event.listens_for(engine, "after_cursor_execute")
    def synchronize_version_read(
        _connection, _cursor, statement, _parameters, _context, _many
    ):
        normalized = " ".join(statement.lower().split())
        if (
            "select schema_migration.version" in normalized
            and not getattr(local, "read_version", False)
        ):
            local.read_version = True
            version_barrier.wait(timeout=5)

    @event.listens_for(engine, "before_cursor_execute")
    def synchronize_identity_ddl(
        _connection, _cursor, statement, _parameters, _context, _many
    ):
        normalized = " ".join(statement.lower().split())
        if (
            normalized.startswith("create unique index uq_attempt_user_quiz")
            and not getattr(local, "created_identity", False)
        ):
            local.created_identity = True
            ddl_barrier.wait(timeout=5)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(init_db, engine) for _ in range(2)]
            for future in futures:
                future.result(timeout=10)

        indexes = {
            item["name"]: item for table in ("attempt", "answer")
            for item in inspect(engine).get_indexes(table)
        }
        assert indexes["uq_attempt_user_quiz"]["column_names"] == [
            "user_id",
            "quiz_id",
        ]
        assert indexes["uq_answer_attempt_question"]["column_names"] == [
            "attempt_id",
            "question_id",
        ]
        with engine.connect() as connection:
            versions = connection.execute(
                text("SELECT version FROM schema_migration")
            ).scalars().all()
        assert versions == [1]
    finally:
        engine.dispose()
