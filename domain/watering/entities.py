from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"
    CANCELED = "canceled"
    ERROR = "error"


@dataclass(slots=True)
class WateringTask:
    id: str
    duration: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = field(default=None)

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)
        self.error = None

    def mark_canceled(self) -> None:
        self.status = TaskStatus.CANCELED
        self.updated_at = datetime.now(timezone.utc)
        self.error = None

    def mark_error(self, message: str) -> None:
        self.status = TaskStatus.ERROR
        self.error = message
        self.updated_at = datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        return self.status == TaskStatus.IN_PROGRESS


@dataclass(slots=True)
class TankLevelSnapshot:
    level_percent: float
    measured_at: datetime

    def has_water(self) -> bool:
        return self.level_percent > 0
