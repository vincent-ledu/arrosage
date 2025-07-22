import pytest
from db import get_connection, init_db, add_task, get_all_tasks, update_status, get_task, get_tasks_by_status, get_tasks_summary_by_day
import time

@pytest.fixture
def db():
  init_db()
  yield
  # Cleanup if necessary

@pytest.fixture(autouse=True)
def db(monkeypatch):
    # Utilise une base temporaire différente pour chaque session de test
    monkeypatch.setenv("DB_PATH", ":memoy")
    
    init_db()  # crée la base et les tables
    yield

    # Nettoyage : supprime les données de toutes les tables
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        for (table,) in cursor.fetchall():
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()

def test_add_task(db):
  task_id = add_task(time.time(), 10, "in progress")
  assert task_id is not None
  task = get_task(task_id)
  assert task is not None
  assert task['id'] == task_id
  assert task['status'] == "in progress"
  update_status(task_id, "completed")

def test_get_all_tasks(db):
  task_id1 = add_task(time.time(), 10, "in progress")
  task_id2 = add_task(time.time(), 10, "in progress")
  tasks = get_all_tasks()
  assert len(tasks) >= 2

def test_update_status(db):
  task_id = add_task(time.time(), 10, "in progress")
  update_status(task_id, "completed")
  task = get_task(task_id)
  assert task['status'] == "completed"

def test_get_tasks_by_status(db):
  task_id1 = add_task(time.time(), 10, "in progress")
  task_id2 = add_task(time.time(), 10, "in progress")
  update_status(task_id1, "completed")
  
  completed_tasks = get_tasks_by_status("completed")
  assert len(completed_tasks) == 1
  assert completed_tasks[0]['id'] == task_id1

  pending_tasks = get_tasks_by_status("in progress")
  assert len(pending_tasks) == 1
  assert pending_tasks[0]['id'] == task_id2

