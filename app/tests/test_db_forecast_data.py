import pytest
from sqlalchemy.sql import text
from datetime import datetime, date
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

forecast_data = [{'date': '2025-08-28', 'temp_min': 17.5, 'temp_max': 23.8, 'night_icon': '☁️', 'night_text': 'Couvert', 'night_precip_mm': 0.1, 'night_temp_avg': 20.7, 'morning_icon': '☁️', 'morning_text': 'Couvert', 'morning_precip_mm': 0.8, 'morning_temp_avg': 18.5, 'afternoon_icon': '☁️', 'afternoon_text': 'Couvert', 'afternoon_precip_mm': 0.0, 'afternoon_temp_avg': 22.2, 'evening_icon': '⛅', 'evening_text': 'Partiellement nuageux', 'evening_precip_mm': 0.0, 'evening_temp_avg': 21.9, 'created_at': '2025-08-28 23:23:46', 'updated_at': '2025-08-28 23:23:46'}, {'date': '2025-08-29', 'temp_min': 15.6, 'temp_max': 22.5, 'night_icon': '☁️', 'night_text': 'Couvert', 'night_precip_mm': 0.0, 'night_temp_avg': 17.3, 'morning_icon': '🌧️', 'morning_text': 'Pluie : faible', 'morning_precip_mm': 4.6, 'morning_temp_avg': 15.9, 'afternoon_icon': '🌦️', 'afternoon_text': 'Averses de pluie : faibles', 'afternoon_precip_mm': 0.2, 'afternoon_temp_avg': 20.4, 'evening_icon': '⛅', 'evening_text': 'Partiellement nuageux', 'evening_precip_mm': 0.2, 'evening_temp_avg': 20.2, 'created_at': '2025-08-28 23:23:46', 'updated_at': '2025-08-28 23:23:46'}, {'date': '2025-08-30', 'temp_min': 14.9, 'temp_max': 22.7, 'night_icon': '☀️', 'night_text': 'Peu nuageux', 'night_precip_mm': 0.0, 'night_temp_avg': 16.3, 'morning_icon': '⛅', 'morning_text': 'Partiellement nuageux', 'morning_precip_mm': 0.0, 'morning_temp_avg': 15.9, 'afternoon_icon': '☁️', 'afternoon_text': 'Couvert', 'afternoon_precip_mm': 0.0, 'afternoon_temp_avg': 21.5, 'evening_icon': '🌧️', 'evening_text': 'Pluie : faible', 'evening_precip_mm': 1.2, 'evening_temp_avg': 19.8, 'created_at': '2025-08-28 23:23:46', 'updated_at': '2025-08-28 23:23:46'}, {'date': '2025-08-31', 'temp_min': 18.3, 'temp_max': 22.6, 'night_icon': '🌧️', 'night_text': 'Pluie : faible', 'night_precip_mm': 1.9, 'night_temp_avg': 19.0, 'morning_icon': '☁️', 'morning_text': 'Couvert', 'morning_precip_mm': 0.0, 'morning_temp_avg': 19.0, 'afternoon_icon': '☁️', 'afternoon_text': 'Couvert', 'afternoon_precip_mm': 0.0, 'afternoon_temp_avg': 22.1, 'evening_icon': '☁️', 'evening_text': 'Couvert', 'evening_precip_mm': 0.0, 'evening_temp_avg': 20.5, 'created_at': '2025-08-28 23:23:46', 'updated_at': '2025-08-28 23:23:46'}, {'date': '2025-09-01', 'temp_min': 15.1, 'temp_max': 23.5, 'night_icon': '☁️', 'night_text': 'Couvert', 'night_precip_mm': 0.0, 'night_temp_avg': 16.7, 'morning_icon': '⛅', 'morning_text': 'Partiellement nuageux', 'morning_precip_mm': 0.0, 'morning_temp_avg': 16.1, 'afternoon_icon': '☁️', 'afternoon_text': 'Couvert', 'afternoon_precip_mm': 0.0, 'afternoon_temp_avg': 22.2, 'evening_icon': '☁️', 'evening_text': 'Couvert', 'evening_precip_mm': 0.6, 'evening_temp_avg': 19.4, 'created_at': '2025-08-28 23:23:46', 'updated_at': '2025-08-28 23:23:46'}, {'date': '2025-09-02', 'temp_min': 13.0, 'temp_max': 22.7, 'night_icon': '⛅', 'night_text': 'Partiellement nuageux', 'night_precip_mm': 0.3, 'night_temp_avg': 15.0, 'morning_icon': '⛅', 'morning_text': 'Partiellement nuageux', 'morning_precip_mm': 0.0, 'morning_temp_avg': 14.6, 'afternoon_icon': '☁️', 'afternoon_text': 'Couvert', 'afternoon_precip_mm': 0.0, 'afternoon_temp_avg': 21.3, 'evening_icon': '🌦️', 'evening_text': 'Averses de pluie : faibles', 'evening_precip_mm': 3.9, 'evening_temp_avg': 19.6, 'created_at': '2025-08-28 23:23:46', 'updated_at': '2025-08-28 23:23:46'}, {'date': '2025-09-03', 'temp_min': 16.9, 'temp_max': 23.8, 'night_icon': '🌦️', 'night_text': 'Averses de pluie : faibles', 'night_precip_mm': 0.9, 'night_temp_avg': 17.2, 'morning_icon': '☁️', 'morning_text': 'Couvert', 'morning_precip_mm': 1.2, 'morning_temp_avg': 17.8, 'afternoon_icon': '⛅', 'afternoon_text': 'Partiellement nuageux', 'afternoon_precip_mm': 0.0, 'afternoon_temp_avg': 22.5, 'evening_icon': '⛅', 'evening_text': 'Partiellement nuageux', 'evening_precip_mm': 0.0, 'evening_temp_avg': 21.5, 'created_at': '2025-08-28 23:23:46', 'updated_at': '2025-08-28 23:23:46'}]

def test_add_forecast_data(db):
  db_forecast_data.add_forecast_data(forecast_data)
  data = db_forecast_data.get_forecast()
  assert data is not None
  assert len(data) >= 5
  assert data[0]["created_at"] is not None
  assert data[0]["updated_at"] is not None
  assert data[0]["created_at"] == data[0]["updated_at"]
