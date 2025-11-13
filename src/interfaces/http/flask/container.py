from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from application.configuration.service import ConfigurationService
from application.weather.queries import WeatherQueries
from application.watering.handlers import (
    StartManualWateringHandler,
    StopWateringHandler,
)
from application.watering.runtime import WateringRuntime
from application.watering.queries import WateringQueries
from domain.watering.policies import WateringPolicy
from domain.watering.ports import DeviceController
from domain.watering.services import WateringTaskManager
from datetime import timedelta

from domain.weather.services import ForecastService
from infrastructure.configuration.file_repository import FileConfigurationRepository
from infrastructure.devices.controllers import (
    DeviceTankLevelSensor,
    create_device_controller,
)
from infrastructure.external.open_meteo_client import OpenMeteoClient
from infrastructure.persistence.watering_task_repository import (
    SqlAlchemyWateringTaskRepository,
)
from infrastructure.persistence.weather_repository import SqlForecastCache


@dataclass(slots=True)
class ServiceContainer:
    configuration_service: ConfigurationService
    device_controller: DeviceController
    watering_repository: SqlAlchemyWateringTaskRepository
    forecast_service: ForecastService
    watering_runtime: WateringRuntime
    watering_queries: WateringQueries
    start_watering_handler: StartManualWateringHandler
    stop_watering_handler: StopWateringHandler
    weather_queries: WeatherQueries
    ttl_provider: Callable[[], timedelta] | None


def build_container(
    ttl: timedelta | None = None,
    ttl_provider: Callable[[], timedelta] | None = None,
) -> ServiceContainer:
    configuration_repository = FileConfigurationRepository()
    configuration_service = ConfigurationService(configuration_repository)

    controller = create_device_controller()
    tank_sensor = DeviceTankLevelSensor(controller)

    watering_repository = SqlAlchemyWateringTaskRepository()
    watering_repository.clear_active_tasks()

    forecast_cache = SqlForecastCache()
    forecast_provider = OpenMeteoClient()
    forecast_service = ForecastService(
        forecast_provider,
        forecast_cache,
        ttl=ttl or timedelta(minutes=30),
    )

    runtime = WateringRuntime(controller, watering_repository)

    def build_policy() -> WateringPolicy:
        config = configuration_service.load()
        enabled_months = config.get("enabled_months", list(range(1, 13)))
        watering = config.get("watering", {})
        min_temp = float(config.get("min_temperature", 5.0))
        return WateringPolicy(enabled_months, watering, min_temp)

    def manager_factory() -> WateringTaskManager:
        return WateringTaskManager(watering_repository, build_policy(), tank_sensor)

    watering_queries = WateringQueries(watering_repository, build_policy)
    weather_queries = WeatherQueries(
        forecast_service,
        configuration_service,
        ttl_provider,
    )

    start_handler = StartManualWateringHandler(
        manager_factory, runtime, weather_queries
    )
    stop_handler = StopWateringHandler(runtime, controller)

    return ServiceContainer(
        configuration_service=configuration_service,
        device_controller=controller,
        watering_repository=watering_repository,
        forecast_service=forecast_service,
        watering_runtime=runtime,
        watering_queries=watering_queries,
        start_watering_handler=start_handler,
        stop_watering_handler=stop_handler,
        weather_queries=weather_queries,
        ttl_provider=ttl_provider,
    )
