import pytest
import time
from dotenv import load_dotenv

from app import app
from config import config as local_config
import db.db_weather_data as db_weather_data
from datetime import date, timedelta

def pytest_configure(config):
    # Charger le .env.test en priorité
    load_dotenv(dotenv_path=".env.test", override=True)

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
  assert isinstance(data, float)
  assert -50.0 < data < 60.0  # Température réaliste

def test_minmax_temperature_precip(client):
  response = client.get('/api/forecast-minmax-precip')
  assert response.status_code in [200, 201]
  data = response.get_json()
  assert 'temperature_2m_max' in data
  assert 'temperature_2m_min' in data
  assert 'precipitation_sum' in data
  assert isinstance(data['temperature_2m_max'], float)
  assert isinstance(data['temperature_2m_min'], float)
  assert isinstance(data['precipitation_sum'], float)

"""
Test de la mise en cache des données météo.
"""
def test_minmax_temperature_precip_cache(client):
  db_weather_data.delete_weather_data_by_date(date.today())  # Supprime les données si elles existent
  response1 = client.get('/api/forecast-minmax-precip')
  assert response1.status_code in [201]
  data1 = response1.get_json()
  time.sleep(2)  # Attendre un peu pour s'assurer que le cache est en place
  response2 = client.get('/api/forecast-minmax-precip')
  assert response2.status_code in [200]
  data2 = response2.get_json()
  assert data1 == data2  # Les données doivent être identiques si elles sont mises en cache

"""
Test du TTL, en mockant le TTL à 2 secondes.
"""
def test_minmax_temperature_precip_cache_ttl(client, monkeypatch):
  db_weather_data.delete_weather_data_by_date(date.today())  # Supprime les données si elles existent

  # Mock le TTL à 2 secondes
  monkeypatch.setattr('app.TTL', timedelta(seconds=1))

  response1 = client.get('/api/forecast-minmax-precip')
  assert response1.status_code in [201]
  data1 = response1.get_json()
  time.sleep(2)  # Attendre plus longtemps que le TTL
  response2 = client.get('/api/forecast-minmax-precip')
  assert response2.status_code in [201]  # Devrait être 201 car les données sont rafraîchies
  data2 = response2.get_json()
  assert data1 == data2  # Les données devraient être identiques même après le rafraîchissement

def test_forecast_data(client):
  response = client.get('/api/forecast')
  assert response.status_code == 200
  data = response.get_json()
  assert isinstance(data, list)
  if len(data) > 0:
    entry = data[0]
    assert 'afternoon_icon' in entry
    assert 'afternoon_temp_avg' in entry
    assert 'afternoon_text' in entry
    assert 'afternoon_precip_mm' in entry
    assert 'morning_icon' in entry
    assert 'morning_temp_avg' in entry
    assert 'morning_text' in entry
    assert 'morning_precip_mm' in entry
    assert isinstance(entry['date'], str)

def test_watering_type(client):
  response = client.get('/api/watering-type')
  assert response.status_code == 200
  data = response.get_data(as_text=True)
  assert data in ['low', 'moderate', 'standard', 'reinforced', 'high']  # Replace with actual watering types

def test_watering_type_paramter(client):
  response = client.get('/api/watering-type?temp=22')
  assert response.status_code == 200
  data = response.get_data(as_text=True)
  assert data in ['low', 'moderate', 'standard', 'reinforced', 'high']  # Replace with actual watering types

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
  local_config.save_config(config)
  loaded_config = local_config.load_config()
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
    local_config.save_config(config)
  # Assuming save_config raises ValueError for invalid types
  # Adjust the exception type based on your implementation
  loaded_config = local_config.load_config()
  assert loaded_config != config  # Ensure the invalid config was not saved
  assert loaded_config["pump"] != "invalid"  # Ensure the invalid value was not saved
  assert loaded_config["pump"] == 1  # Default value should be preserved
  assert loaded_config["valve"] == 2  # Default value should be preserved
  assert loaded_config["levels"] == [5, 6, 7, 8]  # Default levels should be preserved

def test_tasks_endpoint(client):
  response = client.get('/api/tasks')
  assert response.status_code == 200
  data = response.get_json()
  assert isinstance(data, list)
  for task in data:
    assert 'id' in task
    assert 'duration' in task
    assert 'status' in task
    assert 'created_at' in task
    assert 'updated_at' in task
    assert isinstance(task['id'], str)
    assert isinstance(task['duration'], int)
    assert isinstance(task['status'], str)
    assert isinstance(task['created_at'], str)

def test_task_current(client):
  response = client.get('/api/task')
  assert response.status_code in [200, 404]
  data = response.get_json()
  if response.status_code == 200:
    assert 'id' in data
    assert 'duration' in data
    assert 'status' in data
    assert 'created_at' in data
    assert 'updated_at' in data
    assert isinstance(data['id'], str)
    assert isinstance(data['duration'], int)
    assert isinstance(data['status'], str)
    assert isinstance(data['created_at'], str)
    assert isinstance(data['updated_at'], str)
  if response.status_code == 404:
    assert data is not None
    assert data['task_id'] is None