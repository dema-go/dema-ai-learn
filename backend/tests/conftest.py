import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["KAOWOYIXIA_ENV_FILE"] = ""
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DEEPSEEK_API_KEY"] = ""

from app.adapters.quiz_model import FixtureQuizModel
from app.db import get_db
from app.main import create_app
from app.models.tables import Base


@pytest.fixture(autouse=True)
def use_fixture_quiz_model(monkeypatch):
    """单元测试默认不打真实 DeepSeek，避免消耗额度与网络抖动。"""
    monkeypatch.setattr(
        "app.services.quiz_job.get_quiz_model",
        lambda: FixtureQuizModel(),
    )


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def db_session(db_engine) -> Session:
    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    app = create_app()

    def _override_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
