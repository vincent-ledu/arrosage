# app/models.py
from __future__ import annotations

from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Date, DateTime, func
from sqlalchemy.sql.sqltypes import TIMESTAMP

from db.database import Base

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

class ForecastData(Base):
    __tablename__ = "forecast_data"

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
