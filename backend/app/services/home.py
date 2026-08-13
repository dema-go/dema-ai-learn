from sqlalchemy.orm import Session

from app.models.tables import User
from app.services.records import build_home as build_home_payload


def build_home(db: Session, user: User) -> dict:
    return build_home_payload(db, user)
