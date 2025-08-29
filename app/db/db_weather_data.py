from sqlalchemy.orm import Session

from datetime import date as DateType, datetime
from typing import Optional, Union
from zoneinfo import ZoneInfo

from db.database import engine, get_session, Base
from db.models import WeatherData
from sqlalchemy import text
import logging


logger = logging.getLogger(__name__)

def get_connection() -> Session:
  """Compatibilité ascendante : renvoie une session SQLAlchemy utilisable via 'with'."""
  return get_session()

def add_weather_data(date: DateType, min_temp: float, max_temp: float, precipitation: float) -> int:
    """Insère ou met à jour les données météo pour une date donnée. Renvoie l'id de la ligne."""
    logger.debug(f'insert weather data at {date}')
    with get_session() as s:
        # Utilisation de INSERT ... ON DUPLICATE KEY UPDATE pour MariaDB/MySQL
        stmt = text("""
            INSERT INTO weather_data (date, min_temp, max_temp, precipitation)
            VALUES (:date, :min_temp, :max_temp, :precipitation)
            ON DUPLICATE KEY UPDATE
                min_temp = VALUES(min_temp),
                max_temp = VALUES(max_temp),
                precipitation = VALUES(precipitation)
        """)
        now = datetime.now(ZoneInfo("UTC"))
        params = {
            "date": date,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "precipitation": precipitation,
        }
        s.execute(stmt, params)
        s.commit()
        # Récupère l'id (suppose que la colonne 'date' est unique)
        result = s.execute(
            text("SELECT id FROM weather_data WHERE date = :date"),
            {"date": date}
        )
        row = result.first()
        return row.id if row else None

def delete_weather_data_by_date(date: DateType) -> None:
  with get_session() as s:
    s.execute(text("DELETE FROM weather_data WHERE date = :date"), {"date": date})
    s.commit()

def get_weather_data(data_id: int) -> Optional[WeatherData]:
  """Récupère les données météo par id."""
  with get_session() as s:
    return s.get(WeatherData, data_id)

def get_weather_data_by_date(date: DateType) -> Optional[WeatherData]:
  """Récupère les données météo par date."""
  with get_session() as s:
    return s.query(WeatherData).filter(WeatherData.date == date).first()