from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.tables import User
from app.schemas.api import HomeResponse, MeStats
from app.services.home import build_home

router = APIRouter()


@router.get("/api/home", response_model=HomeResponse)
def home(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return build_home(db, user)


@router.get("/api/me", response_model=MeStats)
def me(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return build_home(db, user)["me"]
