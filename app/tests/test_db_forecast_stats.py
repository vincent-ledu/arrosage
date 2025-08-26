import pytest
from sqlalchemy.sql import text
from datetime import datetime, date
from dotenv import load_dotenv

from db.database import engine, get_session, Base
from db.db_weather_data import init_db, get_connection, get_weather_data, add_weather_data

def pytest_configure(config):
    # Charger le .env.test en priorité
    load_dotenv(dotenv_path=".env.test", override=True)

@pytest.fixture
def db():
  init_db()
  yield
  # Cleanup if necessary

@pytest.fixture(autouse=True)
def db(monkeypatch):
    init_db()  # crée la base et les tables
    yield

    # Nettoyage : supprime les données de toutes les tables
    with get_connection() as s:
      tables = ["tasks"]
      for table in tables:
          s.execute(text(f"DELETE FROM {table}"))
      s.commit()

def test_add_forecast_data(db):
  dt = datetime.now()
  data_id = add_weather_data("2025-01-01", 18.2, 25.3, 12.3)
  assert data_id is not None
  data = get_weather_data(data_id)
  assert data is not None
  assert data.id == data_id
  assert data.min_temp == 18.2
  assert data.max_temp == 25.3
  assert data.precipitation == 12.3
  assert data.created_at is not None
  assert data.updated_at is not None
  assert data.created_at == data.updated_at

def test_get_forecast_data_by_date(db):
  dt = date(2025, 1, 2)
  data_id = add_weather_data(dt, 15.0, 22.0, 5.0)
  assert data_id is not None
  data = get_weather_data(data_id)
  assert data is not None
  assert data.id == data_id
  assert data.min_temp == 15.0
  assert data.max_temp == 22.0
  assert data.precipitation == 5.0
  assert data.created_at is not None
  assert data.updated_at is not None
  assert data.created_at == data.updated_at

def test_get_forecast_data(db):
  dt = date(2025, 1, 3)
  data_id = add_weather_data(dt, 10.0, 20.0, 0.0)
  assert data_id is not None
  data = get_weather_data(data_id)
  assert data is not None
  assert data.id == data_id
  assert data.min_temp == 10.0
  assert data.max_temp == 20.0
  assert data.precipitation == 0.0
  assert data.created_at is not None
  assert data.updated_at is not None
  assert data.created_at == data.updated_at