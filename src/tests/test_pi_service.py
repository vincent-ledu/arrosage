""" Test cases for the pi_service Flask application. """
import importlib

import pytest

@pytest.fixture
def client(monkeypatch, tmp_path):
    """ Flask application test client fixture. """
    monkeypatch.setenv("ARROSAGE_CONFIG_FILE", str(tmp_path / "config.json"))
    monkeypatch.setenv("PI_SERVICE_TOKEN", "test-token")
    monkeypatch.setenv("PI_MAX_WATERING_DURATION_SEC", "900")

    from pi_service import app as pi_app_module

    importlib.reload(pi_app_module)
    app = pi_app_module.create_app()

    with app.test_client() as client:
        yield client


def _auth_headers():
    return {"X-API-Token": "test-token"}


def test_healthz_requires_no_auth(client):
    """ Test that the healthz endpoint does not require authentication. """
    response = client.get("/healthz")
    assert response.status_code == 200


def test_auth_required(client):
    """ Test that endpoints require authentication. """
    response = client.get("/v1/status")
    assert response.status_code == 401


def test_water_level(client):
    """ Test water level endpoint. """
    response = client.get("/v1/water-level", headers=_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert "level_percent" in data
    assert data["level_percent"] in {0, 25, 50, 75, 100}


def test_start_stop_and_status(client):
    """ Test starting, stopping watering and checking status. """
    response = client.post(
        "/v1/watering/start",
        json={"duration_sec": 5},
        headers=_auth_headers(),
    )
    assert response.status_code == 202
    payload = response.get_json()
    assert "job_id" in payload

    status = client.get("/v1/status", headers=_auth_headers()).get_json()
    assert status["watering"] is True
    assert status["remaining_sec"] >= 0

    stopped = client.post("/v1/watering/stop", headers=_auth_headers()).get_json()
    assert stopped["stopped"] in {True, False}


def test_start_rejects_too_long_duration(client, monkeypatch):
    """ Test that starting watering with too long duration is rejected. """
    monkeypatch.setenv("PI_MAX_WATERING_DURATION_SEC", "10")
    response = client.post(
        "/v1/watering/start",
        json={"duration_sec": 11},
        headers=_auth_headers(),
    )
    assert response.status_code == 400


def test_idempotency_key_returns_same_job(client):
    """ Test that using the same idempotency key returns the same job. """
    headers = dict(_auth_headers())
    headers["Idempotency-Key"] = "same-key"

    response1 = client.post("/v1/watering/start", json={"duration_sec": 5}, headers=headers)
    assert response1.status_code == 202
    job1 = response1.get_json()["job_id"]

    response2 = client.post("/v1/watering/start", json={"duration_sec": 5}, headers=headers)
    assert response2.status_code == 202
    job2 = response2.get_json()["job_id"]

    assert job1 == job2


def test_gpio_endpoint_verbose(client):
    """ Test GPIO endpoint with verbose output. """
    response = client.get("/v1/gpio?verbose=1", headers=_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert "pump" in data
    assert "valve" in data
    assert "levels" in data
    assert "levels_state" in data
    assert "outputs" in data

def test_gpio_endpoint_non_verbose(client):
    """ Test GPIO endpoint without verbose output. """
    response = client.get("/v1/gpio", headers=_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert "pump" in data
    assert "valve" in data
    assert "levels" in data
    assert "levels_state" not in data
    assert "outputs" not in data

def test_start_watering_invalid_duration(client):
    """ Test starting watering with invalid duration values. """
    # Missing duration
    response = client.post("/v1/watering/start", headers=_auth_headers())
    assert response.status_code == 400

    # Non-integer duration
    response = client.post(
        "/v1/watering/start",
        json={"duration_sec": "five"},
        headers=_auth_headers(),
    )
    assert response.status_code == 400

    # Negative duration
    response = client.post(
        "/v1/watering/start",
        json={"duration_sec": -10},
        headers=_auth_headers(),
    )
    assert response.status_code == 400

def test_start_watering_not_enough_water(client, monkeypatch):
    """ Test starting watering when there is not enough water. """
    class LowWaterController:
        def setup(self):
            pass

        def open_water(self):
            pass

        def close_water(self):
            pass

        def get_level(self):
            return 0

        def debug_water_levels(self):
            return {}

    monkeypatch.setattr("pi_service.container.create_device_controller", lambda: LowWaterController())
    from pi_service import app as pi_app_module
    importlib.reload(pi_app_module)
    app = pi_app_module.create_app()

    with app.test_client() as test_client:
        response = test_client.post(
            "/v1/watering/start",
            json={"duration_sec": 5},
            headers=_auth_headers(),
        )
        assert response.status_code == 507

def test_start_watering_runtime_error(client, monkeypatch):
    """ Test starting watering that raises a RuntimeError. """
    class RaisingRuntime:
        def start(self, duration_sec, idempotency_key=None):
            raise RuntimeError("Simulated runtime failure")

    class DummyController:
        def get_level(self):
            return 1

    def fake_build_pi_container():
        from pi_service.container import PiServiceContainer
        return PiServiceContainer(
            configuration_service=None,
            device_controller=DummyController(),
            watering_runtime=RaisingRuntime(),
        )

    monkeypatch.setattr("pi_service.container.build_pi_container", fake_build_pi_container)
    from pi_service import app as pi_app_module
    importlib.reload(pi_app_module)
    app = pi_app_module.create_app()

    with app.test_client() as test_client:
        response = test_client.post(
            "/v1/watering/start",
            json={"duration_sec": 5},
            headers=_auth_headers(),
        )
        assert response.status_code == 409

def test_start_watering_unexpected_error(client, monkeypatch):
    """ Test starting watering that raises an unexpected Exception. """
    class RaisingRuntime:
        def start(self, duration_sec, idempotency_key=None):
            raise Exception("Simulated Exception")

    class DummyController:
        def get_level(self):
            return 1

    def fake_build_pi_container():
        from pi_service.container import PiServiceContainer
        return PiServiceContainer(
            configuration_service=None,
            device_controller=DummyController(),
            watering_runtime=RaisingRuntime(),
        )

    monkeypatch.setattr("pi_service.container.build_pi_container", fake_build_pi_container)
    from pi_service import app as pi_app_module
    importlib.reload(pi_app_module)
    app = pi_app_module.create_app()

    with app.test_client() as test_client:
        response = test_client.post(
            "/v1/watering/start",
            json={"duration_sec": 5},
            headers=_auth_headers(),
        )
        assert response.status_code == 500
