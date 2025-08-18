from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from db.database import Base

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(20)) 
    start_time: Mapped[Integer] = mapped_column(Integer)  # epoch
    duration: Mapped[Integer] = mapped_column(Integer)  # in seconds
