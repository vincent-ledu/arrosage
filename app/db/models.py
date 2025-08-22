# app/models.py
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float

from db.database import Base
from utils.types import UTCDateTime, utcnow

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    duration: Mapped[int] = mapped_column(Integer)  # en secondes
    min_temp: Mapped[float] = mapped_column(Float)  # en °C
    max_temp: Mapped[float] = mapped_column(Float)  # en °C
    precipitation: Mapped[float] = mapped_column(Float)  # en mm

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=utcnow,          # défini côté app : aware UTC
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=utcnow,          # initialisé à la création
        onupdate=utcnow,         # mis à jour à chaque UPDATE
        nullable=False,
        index=True,
    )
