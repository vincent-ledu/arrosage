from __future__ import annotations

import threading
import time
from typing import Dict

from domain.watering.entities import TaskStatus, WateringTask
from domain.watering.ports import DeviceController, WateringTaskRepository


class WateringRuntime:
    def __init__(
        self, controller: DeviceController, repository: WateringTaskRepository
    ) -> None:
        self._controller = controller
        self._repository = repository
        self._cancel_events: Dict[str, threading.Event] = {}

    def start(self, task: WateringTask) -> None:
        cancel_event = threading.Event()
        self._cancel_events[task.id] = cancel_event
        thread = threading.Thread(
            target=self._run_task,
            args=(task, cancel_event),
            daemon=True,
        )
        thread.start()

    def stop_all(self) -> list[str]:
        cancelled: list[str] = []
        for task_id, event in list(self._cancel_events.items()):
            event.set()
            cancelled.append(task_id)
            self._repository.update_status(task_id, TaskStatus.CANCELED.value)
            self._cancel_events.pop(task_id, None)
        return cancelled

    def _run_task(self, task: WateringTask, cancel_event: threading.Event) -> None:
        try:
            interval = 1
            elapsed = 0
            self._controller.open_water()
            while elapsed < task.duration:
                if cancel_event.is_set():
                    self._controller.close_water()
                    self._repository.update_status(task.id, "canceled")
                    return

                if self._controller.get_level() * 25 <= 0:
                    self._controller.close_water()
                    self._repository.update_status(task.id, "canceled")
                    return

                time.sleep(interval)
                elapsed += interval

            self._controller.close_water()
            self._repository.update_status(task.id, "completed")
        except Exception as exc:  # pragma: no cover - defensive
            self._controller.close_water()
            self._repository.update_status(task.id, f"error: {exc}")
        finally:
            self._cancel_events.pop(task.id, None)

    def cancel_task(self, task_id: str) -> bool:
        event = self._cancel_events.get(task_id)
        if not event:
            return False
        event.set()
        return True
