from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Mapping

from typing import Callable

from application.configuration.service import ConfigurationService
from domain.weather.services import ForecastService


@dataclass(slots=True)
class PartDayForecastQuery:
    pass


@dataclass(slots=True)
class DailyForecastQuery:
    target_date: date


class WeatherQueries:
    def __init__(
        self,
        service: ForecastService,
        configuration: ConfigurationService,
        ttl_provider: Callable[[], timedelta] | None = None,
    ) -> None:
        self._service = service
        self._configuration = configuration
        self._ttl_provider = ttl_provider

    def partday_forecast(self) -> tuple[List[Mapping], bool]:
        if self._ttl_provider:
            self._service.set_ttl(self._ttl_provider())
        config = self._configuration.load()
        coords = config.get("coordinates", {})
        lat = float(coords.get("latitude", 48.866667))
        lon = float(coords.get("longitude", 2.333333))
        return self._service.get_partday_forecast(lat, lon)

    def daily_forecast(self, target_date: date) -> tuple[Mapping, bool]:
        if self._ttl_provider:
            self._service.set_ttl(self._ttl_provider())
        config = self._configuration.load()
        coords = config.get("coordinates", {})
        lat = float(coords.get("latitude", 48.866667))
        lon = float(coords.get("longitude", 2.333333))
        return self._service.get_daily_minmax_precip(target_date, lat, lon)
