import os
import uuid
from typing import Optional, Dict, List

from sqlalchemy import select, update, func, Integer, cast
from sqlalchemy.orm import Session


from db.database import engine, get_session, Base
from db.models import Task

def get_connection() -> Session:
  """Compatibilité ascendante : renvoie une session SQLAlchemy utilisable via 'with'."""
  return get_session()


def init_db():
  """Crée la table si absente (idempotent), comme avant."""
  Base.metadata.create_all(bind=engine)


def add_task(duration, status, min_temp=None, max_temp=None, precipitation=None) -> str:
  """Insère une tâche et renvoie son id (UUID str)."""
  task_id = str(uuid.uuid4())
  with get_session() as s:
    t = Task(id=task_id, 
             duration=int(duration), 
             status=str(status), 
             min_temp=None if min_temp == None else float(min_temp), 
             max_temp=None if max_temp == None else float(max_temp), 
             precipitation=None if precipitation == None else float(precipitation))
    s.add(t)
    s.commit()
  return task_id

def get_tasks_by_status(status):
  """Récupère les tâches par statut, triées par created_at décroissant."""
  with get_session() as s:
    stmt = select(Task).where(Task.status == status).order_by(Task.created_at.desc())
    return s.scalars(stmt).all()

def get_daily_durations_for_done():
    """
    Somme des durées par jour (UTC), pour les statuts 'completed' ou 'cancelled'.
    Retourne une liste de dicts: [{"day": "YYYY-MM-DD", "sum_dur": 123}, ...]
    """
    with get_session() as s:
        dur_expr = (
            cast(func.strftime('%s', Task.updated_at), Integer) -
            cast(func.strftime('%s', Task.created_at), Integer)
        )
        day_expr = func.date(Task.created_at)  # UTC par défaut sous SQLite

        stmt = (
            select(
                day_expr.label("date"),
                func.coalesce(func.sum(dur_expr), 0).label("duration"),
            )
            .where(Task.status.in_(["completed", "cancelled"]))
            .group_by(day_expr)
            .order_by(day_expr)
        )

        rows = s.execute(stmt).all()
        return [{"date": r.date, "duration": round(r.duration / 60, 1)} for r in rows]

def update_status(task_id, new_status) -> None:
  with get_session() as s:
    s.execute(
      update(Task)
      .where(Task.id == str(task_id))
      .values(status=str(new_status))
    )
    s.commit()


def get_task(task_id) -> Optional[Dict]:
  with get_session() as s:  # type: Session
    return s.get(Task, str(task_id))


def get_all_tasks() -> List[Dict]:
  with get_session() as s:
    return s.scalars(select(Task).order_by(Task.created_at.desc())).all()
  
def get_tasks_summary_by_day():
    """
    Retourne { 'YYYY-MM-DD': total_duration_seconds } pour les tâches terminées.
    """
    with get_session() as s:
        dur_expr = (
            cast(func.strftime('%s', Task.updated_at), Integer)
            - cast(func.strftime('%s', Task.created_at), Integer)
        )
        day_expr = func.date(Task.created_at)  # 'YYYY-MM-DD' (UTC par défaut)

        stmt = (
            select(day_expr.label("day"), func.sum(dur_expr).label("sum_dur"))
            .where(Task.status == "completed" or Task.status == "cancelled")
            .group_by(day_expr)
            .order_by(day_expr)
        )

        rows = s.execute(stmt).all()
        return {day: int(sum_dur or 0) for day, sum_dur in rows}
