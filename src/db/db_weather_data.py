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

def add_weather_data(date: Union[DateType, str], min_temp: float, max_temp: float, precipitation: float) -> int:
    """Insère ou met à jour les données météo pour une date donnée. Renvoie l'id de la ligne."""
    logger.debug(f"insert weather data at {date}")
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()
    with get_session() as s:
        record = s.query(WeatherData).filter(WeatherData.date == date).first()
        if record:
            record.min_temp = min_temp
            record.max_temp = max_temp
            record.precipitation = precipitation
        else:
            record = WeatherData(
                date=date,
                min_temp=min_temp,
                max_temp=max_temp,
                precipitation=precipitation,
            )
            s.add(record)
        s.commit()
        s.refresh(record)
        return record.id

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
