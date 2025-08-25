import pytest
import time
from dotenv import load_dotenv

from app import app
from config import config as local_config

def pytest_configure(config):
    # Charger le .env.test en priorité
    load_dotenv(dotenv_path=".env.test", override=True)

@pytest.fixture
def client():
  with app.test_client() as client:
    yield client


def test_checkWaterLevels(client):
  response = client.get('/api/water-level')
  assert response.status_code == 200
  data = response.get_json()
  assert isinstance(data, dict)
  assert 'level' in data
  assert isinstance(data['level'], int)
  
def test_open_water_command(client):
  response = client.get('/api/command/open-water?duration=1')
  assert response.status_code == 202
  data = response.get_json()
  assert 'task_id' in data
  assert 'status' in data
  assert data['status'] == "in progress"
  time.sleep(3)
  task = client.get('/api/tasks/' + str(data['task_id']))
  assert task.status_code == 200
  task_data = task.get_json()
  assert task_data['status'] == "completed"

def test_open_water_command_invalid_duration(client):
  response = client.get('/api/command/open-water?duration=-10')
  assert response.status_code == 400  # Assuming the API returns a 400 for invalid duration
  data = response.get_json()
  assert 'error' in data
  assert data['error'] == 'Invalid duration'  # Adjust based on your actual error message
  # Ensure the error message matches your API's response for invalid duration
  response = client.get('/api/command/open-water?duration=0')
  assert response.status_code == 400  # Assuming the API returns a 400 for zero duration
  data = response.get_json()
  assert 'error' in data
  assert data['error'] == 'Invalid duration'  # Adjust based on your actual error message
  # Ensure the error message matches your API's response for zero duration


def test_open_water_command_missing_duration(client):
  response = client.get('/api/command/open-water')
  assert response.status_code == 400  # Assuming the API returns a 400 for missing duration
  data = response.get_json()
  assert 'error' in data
  assert data['error'] == 'Duration parameter is required'  # Adjust based on your actual error message
  # Ensure the error message matches your API's response for missing duration
def test_open_water_command_invalid_method(client):
  response = client.post('/api/command/open-water?duration=60')
  assert response.status_code == 405  # Assuming the API returns a 405 for invalid method
  
def test_close_water_command(client):
  response = client.get('/api/command/open-water?duration=5')
  assert response.status_code == 202
  response = client.get('/api/command/close-water')
  assert response.status_code == 200
  data = response.get_json()
  assert 'message' in data

def test_close_water_command_no_open(client):
  response = client.get('/api/command/close-water')
  assert response.status_code == 404  # Assuming the API returns a 404 for no open water command
  data = response.get_json()
  assert 'error' in data
  assert data['error'] == 'Water is already closed'  # Adjust based on your actual error message
  # Ensure the error message matches your API's response for no open water command