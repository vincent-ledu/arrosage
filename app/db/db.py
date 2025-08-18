import os
import uuid
from typing import Optional, Dict, List

from sqlalchemy import select, update, func
from sqlalchemy.orm import Session

from db.database import engine, get_session, Base
from db.models import Task

def get_connection() -> Session:
  """Compatibilité ascendante : renvoie une session SQLAlchemy utilisable via 'with'."""
  return get_session()


def init_db():
  """Crée la table si absente (idempotent), comme avant."""
  Base.metadata.create_all(bind=engine)


def add_task(start_time, duration, status) -> str:
  """Insère une tâche et renvoie son id (UUID str)."""
  task_id = str(uuid.uuid4())
  with get_session() as s:
    t = Task(id=task_id, start_time=int(start_time), duration=int(duration), status=str(status))
    s.add(t)
    s.commit()
  return task_id

def get_tasks_by_status(status):
  """Récupère les tâches par statut, triées par start_time décroissant."""
  with get_session() as s:
    stmt = select(Task).where(Task.status == status).order_by(Task.start_time.desc())
    rows = list(s.scalars(stmt))
    return [
      {
        "id": r.id,
        "start_time": int(r.start_time),
        "duration": int(r.duration),
        "status": r.status,
      }
      for r in rows
    ]
def update_status(task_id, new_status) -> None:
  with get_session() as s:
    s.execute(
      update(Task)
      .where(Task.id == str(task_id))
      .values(status=str(new_status))
    )
    s.commit()


def get_task(task_id) -> Optional[Dict]:
  with get_session() as s:
    obj = s.get(Task, str(task_id))
    if not obj:
      return None
    return {
      "id": obj.id,
      "start_time": int(obj.start_time),
      "duration": int(obj.duration),
      "status": obj.status,
    }


def get_all_tasks() -> List[Dict]:
  with get_session() as s:
    stmt = select(Task).order_by(Task.start_time.desc())
    rows = list(s.scalars(stmt))
    return [
      {
        "id": r.id,
        "start_time": int(r.start_time),
        "duration": int(r.duration),
        "status": r.status,
      }
      for r in rows
    ]


def get_tasks_summary_by_day() -> Dict[int, int]:
  """
  Retourne {epoch_day: total_duration} pour les tâches status='terminated'.
  epoch_day = (start_time // 86400) * 86400 (en secondes, minuit UTC à la louche — identique à l’implémentation précédente).
  """
  with get_session() as s:
    # ((start_time / 86400) * 86400) en SQL. En SQLite, la division d'entiers reste entière.
    day_expr = (Task.start_time / 86400) * 86400
    stmt = (
      select(day_expr.label("day"), func.sum(Task.duration).label("sum_dur"))
      .where(Task.status == "terminated")
      .group_by("day")
    )
    result = {}
    for row in s.execute(stmt):
      # row.day peut être float selon le dialecte → on cast en int pour respecter le format d'avant
      result[int(row.day)] = int(row.sum_dur or 0)
    return result