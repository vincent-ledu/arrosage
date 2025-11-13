import pytest
from sqlalchemy.sql import text
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

from db import db_forecast_data


def pytest_configure(config):
    # Charger le .env.test en priorité
    load_dotenv(dotenv_path=".env.test", override=True)


@pytest.fixture(autouse=True)
def db(monkeypatch):
    # Nettoyage : supprime les données de toutes les tables
    with db_forecast_data.get_connection() as s:
        tables = ["tasks"]
        for table in tables:
            s.execute(text(f"DELETE FROM {table}"))
        s.commit()


_now_str = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

forecast_data = []
for offset in range(10):
    forecast_date = (date.today() + timedelta(days=offset)).isoformat()
    base_temp = 15 + offset * 0.3
    forecast_data.append(
        {
            "date": forecast_date,
            "temp_min": round(base_temp, 1),
            "temp_max": round(base_temp + 5.0, 1),
            "night_icon": "☁️",
            "night_text": "Couvert",
            "night_precip_mm": 0.1 * offset,
            "night_temp_avg": round(base_temp + 2.5, 1),
            "morning_icon": "⛅",
            "morning_text": "Partiellement nuageux",
            "morning_precip_mm": 0.2 * offset,
            "morning_temp_avg": round(base_temp + 1.0, 1),
            "afternoon_icon": "☀️",
            "afternoon_text": "Ensoleillé",
            "afternoon_precip_mm": 0.0,
            "afternoon_temp_avg": round(base_temp + 4.0, 1),
            "evening_icon": "🌙",
            "evening_text": "Ciel dégagé",
            "evening_precip_mm": 0.05 * offset,
            "evening_temp_avg": round(base_temp + 3.0, 1),
            "created_at": _now_str,
            "updated_at": _now_str,
        }
    )


def test_add_forecast_data(db):
    db_forecast_data.add_forecast_data(forecast_data)
    data = db_forecast_data.get_forecast()
    assert data is not None
    assert len(data) >= 5
    assert data[0]["created_at"] is not None
    assert data[0]["updated_at"] is not None
    assert data[0]["created_at"] == data[0]["updated_at"]
