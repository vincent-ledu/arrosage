from __future__ import annotations

from datetime import date
from typing import List, Mapping, Sequence

from domain.weather.ports import ForecastCache

from app.db import db_forecast_data, db_weather_data


class SqlForecastCache(ForecastCache):
    def get_partday_forecast(self) -> List[Mapping]:
        return db_forecast_data.get_forecast()

    def store_partday_forecast(self, entries: Sequence[Mapping]) -> None:
        db_forecast_data.add_forecast_data(list(entries))

    def get_daily_forecast(self, target_date: date) -> Mapping | None:
        record = db_weather_data.get_weather_data_by_date(target_date)
        if not record:
            return None
        return {
            "temperature_2m_min": record.min_temp,
            "temperature_2m_max": record.max_temp,
            "precipitation_sum": record.precipitation,
            "updated_at": record.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def store_daily_forecast(
        self,
        target_date: date,
        min_temp: float,
        max_temp: float,
        precipitation: float,
    ) -> None:
        db_weather_data.add_weather_data(target_date, min_temp, max_temp, precipitation)
