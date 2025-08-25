# app/db/db.py (ou où se trouve get_forecast_data)

from sqlalchemy.orm import Session

from datetime import date as DateType, datetime
from typing import Optional, Union
from zoneinfo import ZoneInfo

from db.database import engine, get_session, Base
from db.models import ForecastStats
from sqlalchemy import text


def get_connection() -> Session:
  """Compatibilité ascendante : renvoie une session SQLAlchemy utilisable via 'with'."""
  return get_session()


def init_db():
  """Crée la table si absente (idempotent), comme avant."""
  Base.metadata.create_all(bind=engine)

def add_forecast_data(date: DateType, min_temp: float, max_temp: float, precipitation: float) -> int:
    """Insère ou met à jour les données météo pour une date donnée. Renvoie l'id de la ligne."""

    with get_session() as s:
        # Utilisation de INSERT ... ON DUPLICATE KEY UPDATE pour MariaDB/MySQL
        stmt = text("""
            INSERT INTO forecast_stats (date, min_temp, max_temp, precipitation, created_at, updated_at)
            VALUES (:date, :min_temp, :max_temp, :precipitation, :created_at, :updated_at)
            ON DUPLICATE KEY UPDATE
                min_temp = VALUES(min_temp),
                max_temp = VALUES(max_temp),
                precipitation = VALUES(precipitation),
                updated_at = VALUES(updated_at)
        """)
        now = datetime.now(ZoneInfo("UTC"))
        params = {
            "date": date,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "precipitation": precipitation,
            "created_at": now,
            "updated_at": now,
        }
        s.execute(stmt, params)
        s.commit()
        # Récupère l'id (suppose que la colonne 'date' est unique)
        result = s.execute(
            text("SELECT id FROM forecast_stats WHERE date = :date"),
            {"date": date}
        )
        row = result.first()
        return row.id if row else None
  
def get_forecast_data(data_id: int) -> Optional[ForecastStats]:
  """Récupère les données météo par id."""
  with get_session() as s:
    return s.get(ForecastStats, data_id)

def get_forecast_data_by_date(date: DateType) -> Optional[ForecastStats]:
  """Récupère les données météo par date."""
  with get_session() as s:
    return s.query(ForecastStats).filter(ForecastStats.date == date).first()