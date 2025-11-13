from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from domain.watering.entities import TaskStatus, WateringTask
from domain.watering.ports import WateringTaskRepository

from db import db_tasks


def _as_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")


class SqlAlchemyWateringTaskRepository(WateringTaskRepository):
    def add(
        self, duration: int, status: str, created_at: Optional[datetime] = None
    ) -> str:
        return db_tasks.add_task(duration, status, created_at)

    def get(self, task_id: str) -> Optional[WateringTask]:
        task = db_tasks.get_task(task_id)
        if not task:
            return None
        return self._to_entity(task)

    def get_active_task(self) -> Optional[WateringTask]:
        tasks = db_tasks.get_tasks_by_status(TaskStatus.IN_PROGRESS.value)
        if not tasks:
            return None
        return self._to_entity(tasks[0])

    def list_all(self) -> List[WateringTask]:
        return [self._to_entity(task) for task in db_tasks.get_all_tasks()]

    def update_status(
        self, task_id: str, status: str, error: Optional[str] = None
    ) -> None:
        db_tasks.update_status(task_id, status)

    def clear_active_tasks(self) -> None:
        for task in db_tasks.get_tasks_by_status(TaskStatus.IN_PROGRESS.value):
            db_tasks.update_status(task.id, TaskStatus.CANCELED.value)

    def _to_entity(self, task) -> WateringTask:
        return WateringTask(
            id=str(task.id),
            duration=int(task.duration),
            status=TaskStatus(task.status)
            if task.status in TaskStatus._value2member_map_
            else TaskStatus.ERROR,
            created_at=_as_datetime(task.created_at),
            updated_at=_as_datetime(task.updated_at),
            error=getattr(task, "error", None),
        )
