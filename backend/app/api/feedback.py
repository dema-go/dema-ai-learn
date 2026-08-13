from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.tables import User
from app.schemas.api import FeedbackRequest
from app.services.records import submit_feedback

router = APIRouter()


@router.post("/api/question/{question_id}/feedback")
def create_feedback(
    question_id: str,
    payload: FeedbackRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    submit_feedback(db, question_id, user.id, payload.error_type)
    return {"ok": True}
