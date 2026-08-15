from collections.abc import Generator
import time

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    inspect,
    insert,
    select,
)
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models.tables import Answer, Attempt, Base

_settings = get_settings()
connect_args = {}
if _settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(_settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

_migration_metadata = MetaData()
_schema_migration = Table(
    "schema_migration",
    _migration_metadata,
    Column("version", Integer, primary_key=True),
    Column("name", String(120), nullable=False),
)
_IDENTITY_MIGRATION_VERSION = 1


class SchemaMigrationError(RuntimeError):
    """Raised when startup cannot safely migrate legacy application data."""


def _duplicate_identities(
    connection: Connection,
    table: Table,
    column_names: tuple[str, str],
) -> list[tuple[object, ...]]:
    columns = [table.c[name] for name in column_names]
    statement = (
        select(*columns, func.count().label("row_count"))
        .group_by(*columns)
        .having(func.count() > 1)
        .order_by(*columns)
        .limit(3)
    )
    return [tuple(row) for row in connection.execute(statement)]


def _apply_identity_migration(connection: Connection) -> None:
    duplicate_attempts = _duplicate_identities(
        connection,
        Attempt.__table__,
        ("user_id", "quiz_id"),
    )
    duplicate_answers = _duplicate_identities(
        connection,
        Answer.__table__,
        ("attempt_id", "question_id"),
    )
    if duplicate_attempts or duplicate_answers:
        findings = []
        if duplicate_attempts:
            findings.append(f"duplicate attempt identities: {duplicate_attempts}")
        if duplicate_answers:
            findings.append(f"duplicate answer identities: {duplicate_answers}")
        raise SchemaMigrationError(
            "Schema migration 1 cannot add quiz idempotency indexes because "
            + "; ".join(findings)
            + ". Create a database backup, resolve the listed duplicate rows, then restart. "
            "No legacy rows were changed."
        )

    attempt_identity_index = next(
        index for index in Attempt.__table__.indexes if index.name == "uq_attempt_user_quiz"
    )
    answer_identity_index = next(
        index for index in Answer.__table__.indexes if index.name == "uq_answer_attempt_question"
    )
    attempt_identity_index.create(bind=connection, checkfirst=True)
    answer_identity_index.create(bind=connection, checkfirst=True)


def _identity_migration_is_complete(bind: Engine) -> bool:
    with bind.connect() as connection:
        version_applied = connection.execute(
            select(_schema_migration.c.version).where(
                _schema_migration.c.version == _IDENTITY_MIGRATION_VERSION
            )
        ).scalar_one_or_none()
        if version_applied is None:
            return False

        expected_indexes = {
            "attempt": ("uq_attempt_user_quiz", ["user_id", "quiz_id"]),
            "answer": (
                "uq_answer_attempt_question",
                ["attempt_id", "question_id"],
            ),
        }
        for table_name, (index_name, column_names) in expected_indexes.items():
            index = next(
                (
                    item
                    for item in inspect(connection).get_indexes(table_name)
                    if item["name"] == index_name
                ),
                None,
            )
            if (
                index is None
                or not index["unique"]
                or index["column_names"] != column_names
            ):
                return False
    return True


def _wait_for_competing_migration(bind: Engine) -> bool:
    for _ in range(50):
        try:
            if _identity_migration_is_complete(bind):
                return True
        except SQLAlchemyError:
            pass
        time.sleep(0.01)
    return False


def _run_migrations(bind: Engine) -> None:
    try:
        _migration_metadata.create_all(bind=bind, tables=[_schema_migration])
        with bind.begin() as connection:
            applied_versions = set(
                connection.execute(select(_schema_migration.c.version)).scalars()
            )
            if _IDENTITY_MIGRATION_VERSION not in applied_versions:
                _apply_identity_migration(connection)
                connection.execute(
                    insert(_schema_migration).values(
                        version=_IDENTITY_MIGRATION_VERSION,
                        name="quiz_attempt_and_answer_identity",
                    )
                )
    except SQLAlchemyError:
        if _wait_for_competing_migration(bind):
            return
        raise


def init_db(bind: Engine = engine) -> None:
    Base.metadata.create_all(bind=bind)
    _run_migrations(bind)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
