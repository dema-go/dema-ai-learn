from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.tables import User
from app.services.records import delete_material

router = APIRouter()


@router.delete("/api/material/{material_id}")
def remove_material(
    material_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    delete_material(db, material_id, user.id)
    return {"ok": True}
