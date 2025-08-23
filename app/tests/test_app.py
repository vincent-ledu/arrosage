import pytest
import time

from app import app, load_config, save_config


@pytest.fixture
def client():
  with app.test_client() as client:
    yield client

def test_coordinates(client):
  response = client.get('/api/coordinates')
  assert response.status_code == 200
  data = response.get_json()
  assert 'latitude' in data
  assert 'longitude' in data
  assert isinstance(data['latitude'], float)
  assert isinstance(data['longitude'], float)

def test_temperature_max(client):
  response = client.get('/api/temperature-max')
  assert response.status_code == 200
  data = response.get_json()
  assert isinstance(data, float)  # Assuming the API returns a float for max temperature

def test_watering_type(client):
  response = client.get('/api/watering-type')
  assert response.status_code == 200
  data = response.get_data(as_text=True)
  assert data in ['low', 'moderate', 'standard', 'reinforced', 'high']  # Replace with actual watering types

def test_settings_page(client):
  response = client.get('/settings/')
  assert response.status_code == 200
  assert b'Latitude' in response.data
  assert b'Longitude' in response.data
def test_save_config():
  config = {
    "pump": 1,
    "valve": 2,
    "levels": [5, 6, 7, 8],
    "watering": {
      "low": {"threshold": 15, "morning-duration": 30, "evening-duration": 30},
      "moderate": {"threshold": 20, "morning-duration": 45, "evening-duration": 45},
      "standard": {"threshold": 25, "morning-duration": 60, "evening-duration": 60},
      "reinforced": {"threshold": 30, "morning-duration": 75, "evening-duration": 75},
      "high": {"threshold": 35, "morning-duration": 90, "evening-duration": 90}
    },
    "coordinates": {"latitude": 48.866667, "longitude": 2.333333}
  }
  
  save_config(config)
  
  loaded_config = load_config()
  
  assert loaded_config == config
def test_save_config_invalid():
  config = {
    "pump": "invalid",  # Invalid type
    "valve": 2,
    "levels": [5, 6, 7, 8],
    "watering": {
      "low": {"threshold": 15, "morning-duration": 30, "evening-duration": 30},
      "moderate": {"threshold": 20, "morning-duration": 45, "evening-duration": 45},
      "standard": {"threshold": 25, "morning-duration": 60, "evening-duration": 60},
      "reinforced": {"threshold": 30, "morning-duration": 75, "evening-duration": 75},
      "high": {"threshold": 35, "morning-duration": 90, "evening-duration": 90}
    },
    "coordinates": {"latitude": 48.866667, "longitude": 2.333333}
  }
  
  with pytest.raises(ValueError):
    save_config(config)
  # Assuming save_config raises ValueError for invalid types
  # Adjust the exception type based on your implementation
  loaded_config = load_config()
  assert loaded_config != config  # Ensure the invalid config was not saved
  assert loaded_config["pump"] != "invalid"  # Ensure the invalid value was not saved
  assert loaded_config["pump"] == 1  # Default value should be preserved
  assert loaded_config["valve"] == 2  # Default value should be preserved
  assert loaded_config["levels"] == [5, 6, 7, 8]  # Default levels should be preserved

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