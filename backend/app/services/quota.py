from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import DomainError
from app.models.tables import Task
from app.timeutil import next_reset_at, shanghai_date, utcnow


def count_today_generations(db: Session, user_id: str, now: datetime | None = None) -> int:
    day = shanghai_date(now)
    return (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            Task.quota_charged.is_(True),
            Task.quota_day == day,
        )
        .count()
    )


def assert_quota_available(db: Session, user_id: str, now: datetime | None = None) -> None:
    settings = get_settings()
    used = count_today_generations(db, user_id, now)
    if used >= settings.daily_generate_limit:
        reset = next_reset_at(now or utcnow())
        local = reset.astimezone().strftime("%m-%d %H:%M")
        raise DomainError(
            "QUOTA_EXCEEDED",
            f"今日生成次数已用完，将于 {local} 恢复。你可以先复测错题或查看记录。",
            status_code=429,
        )


def quota_payload(db: Session, user_id: str, now: datetime | None = None) -> dict:
    settings = get_settings()
    current = now or utcnow()
    return {
        "used": count_today_generations(db, user_id, current),
        "limit": settings.daily_generate_limit,
        "reset_at": next_reset_at(current),
    }
