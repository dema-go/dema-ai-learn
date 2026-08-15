from sqlalchemy import create_engine, inspect

from app.db import init_db
from app.models.tables import User


def test_init_db_creates_user_table(db_session):
    user = User(openid="o1", channel="dev")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
    loaded = db_session.query(User).filter_by(openid="o1").one()
    assert loaded.channel == "dev"
    assert loaded.streak_days == 0
    assert loaded.stars == 0


def test_init_db_adds_answer_identity_index_to_existing_table():
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                """
                CREATE TABLE answer (
                    id VARCHAR(32) PRIMARY KEY,
                    attempt_id VARCHAR(32) NOT NULL,
                    question_id VARCHAR(32) NOT NULL,
                    chosen_index INTEGER NOT NULL,
                    is_correct BOOLEAN NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )

        init_db(engine)

        indexes = inspect(engine).get_indexes("answer")
        identity_index = next(
            item for item in indexes if item["name"] == "uq_answer_attempt_question"
        )
        assert identity_index["unique"] == 1
        assert identity_index["column_names"] == ["attempt_id", "question_id"]
    finally:
        engine.dispose()
