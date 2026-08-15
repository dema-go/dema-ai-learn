from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models.tables import Answer, Base

_settings = get_settings()
connect_args = {}
if _settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(_settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(bind: Engine = engine) -> None:
    Base.metadata.create_all(bind=bind)
    answer_identity_index = next(
        index for index in Answer.__table__.indexes if index.name == "uq_answer_attempt_question"
    )
    answer_identity_index.create(bind=bind, checkfirst=True)


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
