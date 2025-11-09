from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Iterable, List, Mapping, Sequence


class ForecastProvider(ABC):
    @abstractmethod
    def fetch_daily_forecast(self, latitude: float, longitude: float) -> Mapping:
        ...

    @abstractmethod
    def fetch_partday_forecast(self, latitude: float, longitude: float) -> Mapping:
        ...


class ForecastCache(ABC):
    @abstractmethod
    def get_partday_forecast(self) -> List[Mapping]:
        ...

    @abstractmethod
    def store_partday_forecast(self, entries: Sequence[Mapping]) -> None:
        ...

    @abstractmethod
    def get_daily_forecast(self, target_date: date) -> Mapping | None:
        ...

    @abstractmethod
    def store_daily_forecast(
        self,
        target_date: date,
        min_temp: float,
        max_temp: float,
        precipitation: float,
    ) -> None:
        ...
