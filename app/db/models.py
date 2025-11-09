# app/models.py
from __future__ import annotations

from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Date, DateTime, func
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.db.database import Base

class WeatherData(Base):
    __tablename__ = "weather_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # date UTC
    min_temp: Mapped[float] = mapped_column(Float, nullable=False)  # en °C
    max_temp: Mapped[float] = mapped_column(Float, nullable=False)  # en °C
    precipitation: Mapped[float] = mapped_column(Float, nullable=False)  # en mm
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),          # initialisé à la création
        onupdate=func.now(),         # mis à jour à chaque UPDATE
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<WeatherData(date={self.date}, min={self.min_temp}, max={self.max_temp}, created_at={self.created_at}, updated_at={self.updated_at})>"

class ForecastData(Base):
    __tablename__ = "forecast_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Jour de prévision
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)

    # Températures min/max du jour
    temp_min: Mapped[float] = mapped_column(Float, nullable=False)
    temp_max: Mapped[float] = mapped_column(Float, nullable=False)

    # ---- Prévisions par tranche de journée ----
    # Nuit
    night_icon: Mapped[str | None] = mapped_column(String(10))
    night_text: Mapped[str | None] = mapped_column(String(100))
    night_precip_mm: Mapped[float | None] = mapped_column(Float, default=0.0)
    night_temp_avg: Mapped[float | None] = mapped_column(Float)

    # Matin
    morning_icon: Mapped[str | None] = mapped_column(String(10))
    morning_text: Mapped[str | None] = mapped_column(String(100))
    morning_precip_mm: Mapped[float | None] = mapped_column(Float, default=0.0)
    morning_temp_avg: Mapped[float | None] = mapped_column(Float)

    # Après-midi
    afternoon_icon: Mapped[str | None] = mapped_column(String(10))
    afternoon_text: Mapped[str | None] = mapped_column(String(100))
    afternoon_precip_mm: Mapped[float | None] = mapped_column(Float, default=0.0)
    afternoon_temp_avg: Mapped[float | None] = mapped_column(Float)

    # Soir
    evening_icon: Mapped[str | None] = mapped_column(String(10))
    evening_text: Mapped[str | None] = mapped_column(String(100))
    evening_precip_mm: Mapped[float | None] = mapped_column(Float, default=0.0)
    evening_temp_avg: Mapped[float | None] = mapped_column(Float)

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<ForecastData(date={self.date}, min={self.temp_min}, max={self.temp_max})>"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)  # UUID4 hex
    status: Mapped[str] = mapped_column(String(20), index=True)
    duration: Mapped[int] = mapped_column(Integer)  # en secondes

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),          # défini côté app : aware UTC
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
