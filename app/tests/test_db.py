import pytest
import time
import os
from sqlalchemy.sql import text

from db.db import get_connection, init_db, add_task, get_all_tasks, update_status, get_task, get_tasks_by_status, get_tasks_summary_by_day


@pytest.fixture
def db():
  init_db()
  yield
  # Cleanup if necessary

@pytest.fixture(autouse=True)
def db(monkeypatch):
    init_db()  # crée la base et les tables
    yield

    # Nettoyage : supprime les données de toutes les tables
    with get_connection() as s:
      tables = ["tasks"]
      for table in tables:
          s.execute(text(f"DELETE FROM {table}"))
      s.commit()

def test_add_task(db):
  task_id = add_task(10, "in progress", min_temp=15.5, max_temp=25.3, precipitation=2.0)
  assert task_id is not None
  task = get_task(task_id)
  assert task is not None
  assert task.id == task_id
  assert task.status == "in progress"
  assert task.duration == 10
  assert task.min_temp == 15.5
  assert task.max_temp == 25.3
  assert task.precipitation == 2.0
  assert task.created_at is not None
  assert task.updated_at is not None
  # assert task.created_at == task.updated_at
  update_status(task_id, "completed")

def test_get_all_tasks(db):
  task_id1 = add_task(10, "in progress", min_temp=15.5, max_temp=25.3, precipitation=2.0)
  task_id2 = add_task(10, "in progress", min_temp=16.0, max_temp=26.0, precipitation=1.5)
  tasks = get_all_tasks()
  assert len(tasks) >= 2

def test_update_status(db):
  task_id = add_task(10, "in progress", min_temp=15.5, max_temp=25.3, precipitation=2.0)
  update_status(task_id, "completed")
  task = get_task(task_id)
  assert task.status == "completed"
  assert task.updated_at > task.created_at

def test_get_tasks_by_status(db):
  task_id1 = add_task(10, "in progress", min_temp=15.5, max_temp=25.3, precipitation=2.0)
  task_id2 = add_task(10, "in progress", min_temp=16.0, max_temp=26.0, precipitation=1.5)
  update_status(task_id1, "completed")
  
  completed_tasks = get_tasks_by_status("completed")
  assert len(completed_tasks) == 1
  assert completed_tasks[0].id == task_id1

  pending_tasks = get_tasks_by_status("in progress")
  assert len(pending_tasks) == 1
  assert pending_tasks[0].id == task_id2

