from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from domain.watering.policies import WateringPolicy
from domain.watering.ports import WateringTaskRepository
from app.utils.serializer import task_to_dict


@dataclass(slots=True)
class CurrentTaskQuery:
    pass


@dataclass(slots=True)
class ListTasksQuery:
    pass


@dataclass(slots=True)
class ClassifyWateringQuery:
    temperature: Optional[float]


class WateringQueries:
    def __init__(
        self,
        repository: WateringTaskRepository,
        policy_provider: Callable[[], WateringPolicy],
    ) -> None:
        self._repository = repository
        self._policy_provider = policy_provider

    def current_task(self) -> dict | None:
        task = self._repository.get_active_task()
        if not task:
            return None
        return task_to_dict(task)

    def list_tasks(self) -> List[dict]:
        return [task_to_dict(task) for task in self._repository.list_all()]

    def classify_watering(self, temperature: Optional[float]) -> str:
        if temperature is None:
            return "unknown"
        return self._policy_provider().classify_temperature(temperature)
