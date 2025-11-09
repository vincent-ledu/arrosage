from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List

from domain.shared.exceptions import DomainError
from domain.watering.entities import TankLevelSnapshot, TaskStatus, WateringTask
from domain.watering.policies import WateringPolicy
from domain.watering.ports import TankLevelSensor, WateringTaskRepository


@dataclass(slots=True)
class WateringTaskManager:
    repository: WateringTaskRepository
    policy: WateringPolicy
    tank_sensor: TankLevelSensor

    max_manual_duration_seconds: int = 300

    def start_manual_watering(
        self,
        duration_seconds: int,
        today: date,
        min_temperature: float,
    ) -> WateringTask:
        if duration_seconds <= 0 or duration_seconds > self.max_manual_duration_seconds:
            raise DomainError("Invalid duration")

        active_task = self.repository.get_active_task()
        if active_task and active_task.is_active:
            raise DomainError("Watering is already in progress.")

        tank_snapshot = self.tank_sensor.snapshot()
        self.policy.ensure_can_start(today, min_temperature, tank_snapshot)

        task_id = self.repository.add(duration_seconds, TaskStatus.IN_PROGRESS.value)
        task = self.repository.get(task_id)
        if not task:
            raise DomainError("Unable to create watering task.")
        return task

    def get_active_task(self) -> WateringTask | None:
        return self.repository.get_active_task()

    def list_tasks(self) -> List[WateringTask]:
        return self.repository.list_all()

    def mark_completed(self, task_id: str) -> None:
        self.repository.update_status(task_id, TaskStatus.COMPLETED.value)

    def mark_canceled(self, task_id: str) -> None:
        self.repository.update_status(task_id, TaskStatus.CANCELED.value)

    def mark_error(self, task_id: str, error: str) -> None:
        self.repository.update_status(task_id, f"error: {error}")
