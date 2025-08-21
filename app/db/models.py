from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from db.database import Base

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(20)) 
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped = mapped_column(DateTime(timezone=True), onupdate=func.now())
    duration: Mapped[Integer] = mapped_column(Integer)  # in seconds
