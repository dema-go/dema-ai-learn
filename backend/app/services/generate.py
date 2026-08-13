from sqlalchemy.orm import Session

from app.models.tables import Task, User
from app.schemas.api import GenerateRequest
from app.services.materials import (
    create_material,
    find_cached_material,
    hash_content,
    validate_generate_input,
)
from app.services.quota import assert_quota_available
from app.services.tasks import create_task
from app.services.users import get_or_create_user


def submit_generate(db: Session, user: User, payload: GenerateRequest) -> Task:
    validate_generate_input(payload.source_type, payload.text, payload.url)
    if payload.channel:
        get_or_create_user(db, user.openid, payload.channel)

    if payload.source_type == "url":
        # URL 正文抽取在后续任务接通；此处只接受合法 URL 形态并先建任务。
        text = ""
        content_hash = hash_content(payload.url or "")
        cached = find_cached_material(db, user.id, content_hash)
        if cached is not None:
            existing = cached.tasks[-1] if cached.tasks else None
            if existing is not None:
                return existing
        assert_quota_available(db, user.id)
        material = create_material(
            db,
            user.id,
            "url",
            text=payload.url or "",
            source_url=payload.url,
            title=payload.url,
        )
        return create_task(db, user.id, material.id, quota_charged=True)

    text = (payload.text or "").strip()
    content_hash = hash_content(text)
    cached = find_cached_material(db, user.id, content_hash)
    if cached is not None:
        from app.services.materials import latest_task_for_material

        existing = latest_task_for_material(db, cached.id)
        if existing is not None:
            return existing
        return create_task(db, user.id, cached.id, quota_charged=False)

    assert_quota_available(db, user.id)
    material = create_material(db, user.id, "text", text)
    return create_task(db, user.id, material.id, quota_charged=True)
