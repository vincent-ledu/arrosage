import pytest
import unittest.mock

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
    response = client.get("/api/water-level")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert "level" in data
    assert isinstance(data["level"], int)


def test_open_water_command(client):
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        response = client.get("/api/command/open-water?duration=1")
        assert response.status_code == 202
        data = response.get_json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "in progress"
        time.sleep(3)
        task = client.get("/api/tasks/" + str(data["task_id"]))
        assert task.status_code == 200
        task_data = task.get_json()
        assert task_data["status"] == "completed"


def test_open_water_command_invalid_duration(client):
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        response = client.get("/api/command/open-water?duration=-10")
        assert (
            response.status_code == 400
        )  # Assuming the API returns a 400 for invalid duration
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"] == "Invalid duration"
        )  # Adjust based on your actual error message
        # Ensure the error message matches your API's response for invalid duration
        response = client.get("/api/command/open-water?duration=0")
        assert (
            response.status_code == 400
        )  # Assuming the API returns a 400 for zero duration
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"] == "Invalid duration"
        )  # Adjust based on your actual error message
        # Ensure the error message matches your API's response for zero duration


def test_open_water_command_missing_duration(client):
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        response = client.get("/api/command/open-water")
        assert (
            response.status_code == 400
        )  # Assuming the API returns a 400 for missing duration
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"] == "Duration parameter is required"
        )  # Adjust based on your actual error message
        # Ensure the error message matches your API's response for missing duration


def test_open_water_command_invalid_method(client):
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        response = client.post("/api/command/open-water?duration=60")
        assert (
            response.status_code == 405
        )  # Assuming the API returns a 405 for invalid method


def test_open_water_command_already_in_progress(client):
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        response = client.get("/api/command/open-water?duration=5")
        assert response.status_code == 202
        response = client.get("/api/command/open-water?duration=5")
        assert (
            response.status_code == 409
        )  # Assuming the API returns a 409 for already in progress
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"] == "Watering is already in progress."
        )  # Adjust based on your actual error message
        # Ensure the error message matches your API's response for already in progress
        time.sleep(6)  # Wait for the first watering to complete


def test_open_water_command_not_enough_water(client):
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        # Mock getLevel to return a low value (simulate not enough water)
        with unittest.mock.patch("app.ctlInst.getLevel", return_value=0):
            response = client.get("/api/command/open-water?duration=300")
            assert (
                response.status_code == 507
            )  # Assuming the API returns a 507 for not enough water
            data = response.get_json()
            assert "error" in data
            assert (
                data["error"] == "Not enough water."
            )  # Adjust based on your actual error message
            # Ensure the error message matches your API's response for not enough water


def test_open_water_command_too_long_duration(client):
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        response = client.get("/api/command/open-water?duration=1000")
        assert (
            response.status_code == 400
        )  # Assuming the API returns a 400 for too long duration
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"] == "Invalid duration"
        )  # Adjust based on your actual error message
        # Ensure the error message matches your API's response for too long duration


def test_open_water_command_temp_too_low(client):
    # Mock get_minmax_temperature_precip to simulate temperature too low
    class MockResponse:
        def get_json(self):
            return {
                "temperature_2m_min": 2.1,
                "temperature_2m_max": 5.5,
                "precipitation_sum": 0,
            }

    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        with unittest.mock.patch(
            "app.get_minmax_temperature_precip", return_value=(MockResponse(), 200)
        ):
            response = client.get("/api/command/open-water?duration=5")
            assert (
                response.status_code == 400
            )  # Assuming the API returns a 400 for temp too low
            data = response.get_json()
            assert "error" in data
            assert (
                data["error"] == "Temperature is too low to water."
            )  # Adjust based on your actual error message
            # Ensure the error message matches your API's response for temp too low


def test_open_water_command_month_not_enabled(client):
    # Mock the config to disable current month
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [m for m in range(1, 13) if m != current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        response = client.get("/api/command/open-water?duration=5")
        assert (
            response.status_code == 400
        )  # Assuming the API returns a 400 for month not enabled
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"] == "Watering is disabled for the current month."
        )  # Adjust based on your actual error message
        # Ensure the error message matches your API's response for month not enabled


def test_close_water_command(client):
    original_load_config = local_config.load_config

    def mock_load_config():
        config = original_load_config()
        current_month = time.localtime().tm_mon
        config["enabled_months"] = [current_month]
        return config

    with unittest.mock.patch.object(
        local_config, "load_config", side_effect=mock_load_config
    ):
        response = client.get("/api/command/open-water?duration=5")
        assert response.status_code == 202
        response = client.get("/api/command/close-water")
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data


def test_close_water_command_no_open(client):
    response = client.get("/api/command/close-water")
    assert (
        response.status_code == 404
    )  # Assuming the API returns a 404 for no open water command
    data = response.get_json()
    assert "error" in data
    assert (
        data["error"] == "Water is already closed"
    )  # Adjust based on your actual error message
    # Ensure the error message matches your API's response for no open water command
