from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, List, Optional

from domain.watering.entities import TankLevelSnapshot, WateringTask


class DeviceController(ABC):
    @abstractmethod
    def setup(self) -> None:
        ...

    @abstractmethod
    def open_water(self) -> None:
        ...

    @abstractmethod
    def close_water(self) -> None:
        ...

    @abstractmethod
    def get_level(self) -> float:
        ...

    @abstractmethod
    def debug_water_levels(self) -> Iterable[int]:
        ...

    @abstractmethod
    def cleanup(self) -> None:
        ...


class WateringTaskRepository(ABC):
    @abstractmethod
    def add(self, duration: int, status: str, created_at: Optional[datetime] = None) -> str:
        ...

    @abstractmethod
    def get(self, task_id: str) -> Optional[WateringTask]:
        ...

    @abstractmethod
    def get_active_task(self) -> Optional[WateringTask]:
        ...

    @abstractmethod
    def list_all(self) -> List[WateringTask]:
        ...

    @abstractmethod
    def update_status(self, task_id: str, status: str, error: Optional[str] = None) -> None:
        ...


class TankLevelSensor(ABC):
    @abstractmethod
    def snapshot(self) -> TankLevelSnapshot:
        ...
