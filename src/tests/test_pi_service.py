import importlib

import pytest


@pytest.fixture
def client(monkeypatch, tmp_path):
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
    response = client.get("/healthz")
    assert response.status_code == 200


def test_auth_required(client):
    response = client.get("/v1/status")
    assert response.status_code == 401


def test_water_level(client):
    response = client.get("/v1/water-level", headers=_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert "level_percent" in data
    assert data["level_percent"] in {0, 25, 50, 75, 100}


def test_start_stop_and_status(client):
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
    monkeypatch.setenv("PI_MAX_WATERING_DURATION_SEC", "10")
    response = client.post(
        "/v1/watering/start",
        json={"duration_sec": 11},
        headers=_auth_headers(),
    )
    assert response.status_code == 400


def test_idempotency_key_returns_same_job(client):
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
    response = client.get("/v1/gpio?verbose=1", headers=_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert "pump" in data
    assert "valve" in data
    assert "levels" in data
    assert "levels_state" in data
    assert "outputs" in data

