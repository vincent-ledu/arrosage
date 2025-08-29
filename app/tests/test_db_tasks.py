import pytest
from sqlalchemy.sql import text
from dotenv import load_dotenv
from db.db_tasks import get_connection, add_task, get_all_tasks, update_status, get_task, get_tasks_by_status

def pytest_configure(config):
    # Charger le .env.test en priorité
    load_dotenv(dotenv_path=".env.test", override=True)

@pytest.fixture(autouse=True)
def db(monkeypatch):
    # Nettoyage : supprime les données de toutes les tables
    with get_connection() as s:
      tables = ["tasks"]
      for table in tables:
          s.execute(text(f"DELETE FROM {table}"))
      s.commit()

def test_add_task(db):
  task_id = add_task(10, "in progress")
  assert task_id is not None
  task = get_task(task_id)
  assert task is not None
  assert task.id == task_id
  assert task.status == "in progress"
  assert task.duration == 10
  assert task.created_at is not None
  assert task.updated_at is not None
  assert task.created_at == task.updated_at
  update_status(task_id, "completed")

def test_get_all_tasks(db):
  task_id1 = add_task(10, "in progress")
  task_id2 = add_task(10, "in progress")
  tasks = get_all_tasks()
  assert len(tasks) >= 2

def test_update_status(db):
  task_id = add_task(10, "in progress")
  update_status(task_id, "completed")
  task = get_task(task_id)
  assert task.status == "completed"
  assert task.updated_at >= task.created_at

def test_get_tasks_by_status(db):
  task_id1 = add_task(10, "in progress")
  task_id2 = add_task(10, "in progress")
  update_status(task_id1, "completed")
  
  completed_tasks = get_tasks_by_status("completed")
  assert len(completed_tasks) == 1
  assert completed_tasks[0].id == task_id1

  pending_tasks = get_tasks_by_status("in progress")
  assert len(pending_tasks) == 1
  assert pending_tasks[0].id == task_id2

def test_get_task(db):
  task_id = add_task(10, "in progress")
  task = get_task(task_id)
  assert task is not None
  assert task.id == task_id
  assert task.status == "in progress"
  assert task.duration == 10
  assert task.created_at is not None
  assert task.updated_at is not None
  assert task.created_at == task.updated_at
  update_status(task_id, "completed")
  task = get_task(task_id)
  assert task.status == "completed"
  assert task.updated_at >= task.created_at
  assert task.duration == 10
  assert task.id == task_id
  assert task.created_at is not None
  assert task.updated_at is not None
