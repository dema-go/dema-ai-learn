from sqlalchemy.orm import Session

from app.models.tables import Event


def track_event(db: Session, user_id: str, name: str, payload: dict | None = None) -> Event:
    event = Event(user_id=user_id, name=name, payload_json=payload or {})
    db.add(event)
    db.flush()
    return event
