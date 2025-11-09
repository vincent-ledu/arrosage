from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import requests

from domain.weather.ports import ForecastProvider

os.makedirs("/var/log/gunicorn", exist_ok=True)

from services import weather

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_timestamp() -> str:
    return _utc_now().strftime("%Y-%m-%d %H:%M:%S")


_FALLBACK_DAILY = {
    "temperature_2m_min": 10.0,
    "temperature_2m_max": 20.0,
    "precipitation_sum": 0.0,
    "updated_at": _utc_timestamp(),
}


def _fallback_partday() -> list[dict]:
    now = _utc_now()
    entries = []
    for i in range(5):
        day = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        entries.append(
            {
                "date": day,
                "temp_min": 10.0,
                "temp_max": 20.0,
                "night_icon": "—",
                "night_text": "Clear",
                "night_precip_mm": 0.0,
                "night_temp_avg": 12.0,
                "morning_icon": "—",
                "morning_text": "Clear",
                "morning_precip_mm": 0.0,
                "morning_temp_avg": 14.0,
                "afternoon_icon": "—",
                "afternoon_text": "Clear",
                "afternoon_precip_mm": 0.0,
                "afternoon_temp_avg": 18.0,
                "evening_icon": "—",
                "evening_text": "Clear",
                "evening_precip_mm": 0.0,
                "evening_temp_avg": 16.0,
                "updated_at": _utc_timestamp(),
            }
        )
    return entries


class OpenMeteoClient(ForecastProvider):
    def fetch_daily_forecast(self, latitude: float, longitude: float) -> dict:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            "&forecast_days=1&timezone=Europe%2FParis"
        )
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()["daily"]
            return {
                "temperature_2m_min": float(data["temperature_2m_min"][0]),
                "temperature_2m_max": float(data["temperature_2m_max"][0]),
                "precipitation_sum": float(data["precipitation_sum"][0]),
                "updated_at": _utc_timestamp(),
            }
        except (requests.RequestException, KeyError, IndexError, ValueError):
            return dict(_FALLBACK_DAILY)

    def fetch_partday_forecast(self, latitude: float, longitude: float):
        try:
            raw = weather.fetch_open_meteo(latitude, longitude)
            aggregated = weather.aggregate_by_partday(raw)
            timestamp = _utc_timestamp()
            for entry in aggregated:
                entry["updated_at"] = timestamp
            return aggregated
        except (requests.RequestException, KeyError, ValueError):
            return _fallback_partday()
