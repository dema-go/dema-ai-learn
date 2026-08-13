from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.tables import User
from app.services.users import get_or_create_user


def get_openid(
    x_dev_openid: Annotated[str | None, Header()] = None,
) -> str:
    settings = get_settings()
    openid = (x_dev_openid or "").strip()
    return openid or settings.default_openid


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    openid: Annotated[str, Depends(get_openid)],
) -> User:
    return get_or_create_user(db, openid)
