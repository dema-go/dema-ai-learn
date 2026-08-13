from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models.tables import Task
from app.timeutil import shanghai_date, utcnow

STAGE_COPY = {
    "extracting": "正在理解原文",
    "planning": "正在抓住重点",
    "generating": "正在生成第 {n} 题",
    "validating": "正在检查答案",
}


def progress_text(stage: str, n: int = 1) -> str:
    template = STAGE_COPY.get(stage, "正在理解原文")
    return template.format(n=n)


def create_task(
    db: Session,
    user_id: str,
    material_id: str,
    *,
    quota_charged: bool,
    status: str = "pending",
    stage: str = "extracting",
) -> Task:
    task = Task(
        user_id=user_id,
        material_id=material_id,
        status=status,
        stage=stage,
        progress=progress_text(stage),
        quota_charged=quota_charged,
        quota_day=shanghai_date(),
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(task)
    db.flush()
    return task


def get_task_for_user(db: Session, task_id: str, user_id: str) -> Task:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user_id)
        .one_or_none()
    )
    if task is None:
        raise DomainError("TASK_NOT_FOUND", "找不到这个任务。", status_code=404)
    return task


def update_task_progress(
    task: Task,
    *,
    status: str | None = None,
    stage: str | None = None,
    n: int = 1,
    error: str | None = None,
    quiz_id: str | None = None,
) -> None:
    if status is not None:
        task.status = status
    if stage is not None:
        task.stage = stage
        task.progress = progress_text(stage, n)
    if error is not None:
        task.error = error
    if quiz_id is not None:
        task.quiz_id = quiz_id
    task.updated_at = utcnow()
