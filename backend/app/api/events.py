from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.tables import User
from app.schemas.api import EventRequest, OkResponse
from app.services.events import track_event

ALLOWED = {
    "generation_success",
    "quiz_started",
    "quiz_completed",
    "retest_started",
    "question_error_reported",
    "second_creation_7d",
}

router = APIRouter()


@router.post("/api/events", response_model=OkResponse)
def create_event(
    payload: EventRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    name = payload.name if payload.name in ALLOWED else payload.name
    track_event(db, user.id, name, payload.payload)
    return {"ok": True}
