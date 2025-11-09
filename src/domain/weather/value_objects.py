from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass(slots=True)
class DailyForecast:
    date: datetime
    min_temp: float
    max_temp: float
    precipitation_sum: float


@dataclass(slots=True)
class PartDayForecast:
    period: str
    temperature: float
    precipitation_probability: float


def serialize_daily_forecast(forecasts: List[DailyForecast]) -> List[Dict[str, float]]:
    return [
        {
            "date": forecast.date.strftime("%Y-%m-%d"),
            "temperature_2m_min": forecast.min_temp,
            "temperature_2m_max": forecast.max_temp,
            "precipitation_sum": forecast.precipitation_sum,
        }
        for forecast in forecasts
    ]
