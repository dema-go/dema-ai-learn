from sqlalchemy.orm import Session

from app.models.tables import User


def get_or_create_user(db: Session, openid: str, channel: str | None = None) -> User:
    user = db.query(User).filter(User.openid == openid).one_or_none()
    if user is None:
        user = User(openid=openid, channel=channel)
        db.add(user)
        db.flush()
        return user
    if channel and not user.channel:
        user.channel = channel
        db.flush()
    return user
