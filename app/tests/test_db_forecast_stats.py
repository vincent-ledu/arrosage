import pytest
from sqlalchemy.sql import text
from datetime import datetime, date

from db.database import engine, get_session, Base
from db.db_forecast_stats import init_db, get_connection, get_forecast_data, add_forecast_data


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
      tables = ["forecast_stats"]
      for table in tables:
          s.execute(text(f"DELETE FROM {table}"))
      s.commit()

def test_add_forecast_data(db):
  dt = datetime.now()
  data_id = add_forecast_data("2025-01-01", 18.2, 25.3, 12.3)
  assert data_id is not None
  data = get_forecast_data(data_id)
  assert data is not None
  assert data.id == data_id
  assert data.min_temp == 18.2
  assert data.max_temp == 25.3
  assert data.precipitation == 12.3
  assert data.created_at is not None
  assert data.updated_at is not None
  assert data.created_at == data.updated_at
