from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Dict
import sys

from application.weather.queries import WeatherQueries
from domain.watering.ports import DeviceController
from domain.watering.services import WateringTaskManager

from .commands import StartManualWateringCommand, StopWateringCommand
from .runtime import WateringRuntime


@dataclass(slots=True)
class StartManualWateringHandler:
    manager_factory: Callable[[], WateringTaskManager]
    runtime: WateringRuntime
    weather_queries: WeatherQueries

    def handle(self, command: StartManualWateringCommand) -> Dict[str, str]:
        forecast_data = None
        app_module = sys.modules.get("app")
        compat_getter = getattr(app_module, "get_minmax_temperature_precip", None)
        if callable(compat_getter):
            try:
                response, status = compat_getter()
                if not status or status < 400:
                    forecast_data = response.get_json() if hasattr(response, "get_json") else response
            except Exception:  # pragma: no cover - compat fallback
                forecast_data = None

        if forecast_data is None:
            forecast_data, _ = self.weather_queries.daily_forecast(date.today())

        min_temp = float(forecast_data["temperature_2m_min"])
        manager = self.manager_factory()
        task = manager.start_manual_watering(
            command.duration_seconds,
            date.today(),
            min_temp,
        )
        self.runtime.start(task)
        return {"task_id": task.id, "status": task.status.value}


@dataclass(slots=True)
class StopWateringHandler:
    runtime: WateringRuntime
    controller: DeviceController

    def handle(self, command: StopWateringCommand) -> Dict[str, str]:
        cancelled_ids = self.runtime.stop_all()
        if cancelled_ids:
            self.controller.close_water()
            return {"message": f"Task {cancelled_ids} terminated"}
        self.controller.close_water()
        return {"error": "Water is already closed"}
