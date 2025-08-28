from sqlalchemy.orm import Session

from datetime import date as DateType, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from db.database import engine, get_session, Base
from db.models import ForecastData
from sqlalchemy import text
from typing import List

def get_connection() -> Session:
  """Compatibilité ascendante : renvoie une session SQLAlchemy utilisable via 'with'."""
  return get_session()

def to_dict_list(objs: List[ForecastData]) -> list[dict]:
    """
    Transforme une liste d'objets ForecastData en liste de dictionnaires.
    """
    results: list[dict] = []
    for obj in objs:
        results.append({
            "date": obj.date.isoformat() if obj.date else None,
            "temp_min": obj.temp_min,
            "temp_max": obj.temp_max,

            "night_icon": obj.night_icon,
            "night_text": obj.night_text,
            "night_precip_mm": obj.night_precip_mm,
            "night_temp_avg": obj.night_temp_avg,

            "morning_icon": obj.morning_icon,
            "morning_text": obj.morning_text,
            "morning_precip_mm": obj.morning_precip_mm,
            "morning_temp_avg": obj.morning_temp_avg,

            "afternoon_icon": obj.afternoon_icon,
            "afternoon_text": obj.afternoon_text,
            "afternoon_precip_mm": obj.afternoon_precip_mm,
            "afternoon_temp_avg": obj.afternoon_temp_avg,

            "evening_icon": obj.evening_icon,
            "evening_text": obj.evening_text,
            "evening_precip_mm": obj.evening_precip_mm,
            "evening_temp_avg": obj.evening_temp_avg,
            "created_at": DateType.strftime(obj.created_at, "%Y-%m-%d %H:%M:%S"),
            "updated_at": DateType.strftime(obj.updated_at, "%Y-%m-%d %H:%M:%S"),
        })
    return results

def from_dict_list(data: list[dict]) -> List[ForecastData]:
    """Convertit une liste de dictionnaires météo en objets ForecastData"""
    objects: List[ForecastData] = []
    for entry in data:
        # conversion de la date string -> date
        day = datetime.strptime(entry["date"], "%Y-%m-%d").date()

        obj = ForecastData(
            date=day,
            temp_min=entry.get("temp_min"),
            temp_max=entry.get("temp_max"),

            night_icon=entry.get("night_icon"),
            night_text=entry.get("night_text"),
            night_precip_mm=entry.get("night_precip_mm"),
            night_temp_avg=entry.get("night_temp_avg"),

            morning_icon=entry.get("morning_icon"),
            morning_text=entry.get("morning_text"),
            morning_precip_mm=entry.get("morning_precip_mm"),
            morning_temp_avg=entry.get("morning_temp_avg"),

            afternoon_icon=entry.get("afternoon_icon"),
            afternoon_text=entry.get("afternoon_text"),
            afternoon_precip_mm=entry.get("afternoon_precip_mm"),
            afternoon_temp_avg=entry.get("afternoon_temp_avg"),

            evening_icon=entry.get("evening_icon"),
            evening_text=entry.get("evening_text"),
            evening_precip_mm=entry.get("evening_precip_mm"),
            evening_temp_avg=entry.get("evening_temp_avg"),
        )
        objects.append(obj)
    
    return objects

def add_forecast_data(data: list[dict]) -> None:
    objects = from_dict_list(data)
    
    with get_session() as s:
      s.execute(text(f"TRUNCATE TABLE {ForecastData.__tablename__}"))

      s.add_all(objects)
      s.commit()

def get_forecast():
  """Récupère les données des 5 prochains jours"""
  with get_session() as s:
    return to_dict_list(s.query(ForecastData).filter(ForecastData.date >= DateType.today()).all()) 

def get_forecast_data_by_date(date: DateType) -> Optional[ForecastData]:
  """Récupère les données météo par date."""
  with get_session() as s:
    return s.query(ForecastData).filter(ForecastData.date == date).first()
