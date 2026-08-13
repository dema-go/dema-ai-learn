import hashlib
import re
from datetime import timedelta
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import DomainError
from app.models.tables import Material, Task
from app.timeutil import shanghai_date, utcnow

MAX_CHARS = 8000
MIN_URL_TEXT = 200


def count_chars(text: str) -> int:
    return len(text)


def hash_content(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def infer_title(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return "未命名材料"
    return compact[:30]


def validate_generate_input(source_type: str, text: str | None, url: str | None) -> None:
    if source_type == "text":
        raw = (text or "").strip()
        if not raw:
            raise DomainError("TEXT_EMPTY", "还没有内容。请粘贴一段完整的文字。")
        if count_chars(raw) > MAX_CHARS:
            raise DomainError(
                "TEXT_TOO_LONG",
                "超过 8000 字，请截取重点段落后再试。系统不会静默截断。",
            )
        return
    if source_type == "url":
        value = (url or "").strip()
        if not value:
            raise DomainError("URL_REQUIRED", "请粘贴公开网页链接。")
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise DomainError("URL_INVALID", "这不像有效的网页链接，请检查后重试。")
        return
    raise DomainError("INVALID_SOURCE", "只支持粘贴文本或公开网页链接。")


def find_cached_material(db: Session, user_id: str, content_hash: str) -> Material | None:
    now = utcnow()
    material = (
        db.query(Material)
        .filter(
            Material.user_id == user_id,
            Material.content_hash == content_hash,
            Material.raw_text.is_not(None),
        )
        .order_by(Material.created_at.desc())
        .first()
    )
    if material is None:
        return None
    expire_at = material.expire_at
    if expire_at.tzinfo is None:
        from datetime import timezone

        expire_at = expire_at.replace(tzinfo=timezone.utc)
    if expire_at <= now:
        return None
    return material


def create_material(
    db: Session,
    user_id: str,
    source_type: str,
    text: str,
    source_url: str | None = None,
    title: str | None = None,
) -> Material:
    settings = get_settings()
    material = Material(
        user_id=user_id,
        source_type=source_type,
        source_url=source_url,
        title=title or infer_title(text),
        content_hash=hash_content(text),
        raw_text=text,
        expire_at=utcnow() + timedelta(days=settings.material_ttl_days),
    )
    db.add(material)
    db.flush()
    return material


def latest_task_for_material(db: Session, material_id: str) -> Task | None:
    return (
        db.query(Task)
        .filter(Task.material_id == material_id)
        .order_by(Task.created_at.desc())
        .first()
    )
