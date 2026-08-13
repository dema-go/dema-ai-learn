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
