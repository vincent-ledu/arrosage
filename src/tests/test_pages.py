import pytest
from dotenv import load_dotenv

from app import app


def pytest_configure(config):
    # Charger le .env.test en priorité
    load_dotenv(dotenv_path=".env.test", override=True)


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_index_page(client):
    response = client.get("/?lang=fr")
    assert response.status_code == 200
    assert b"Arrosage" in response.data
    assert b"Historique" in response.data
    assert "Paramètres" in response.data.decode("utf-8")
    assert b"Arrosage automatique" in response.data


def test_index_page_en(client):
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    response = client.get("/")
    assert response.status_code == 200
    assert b"Watering" in response.data
    assert b"History" in response.data
    assert b"Settings" in response.data
    assert b"Auto watering" in response.data


def test_settings_page(client):
    response = client.get("/settings/")
    assert response.status_code == 200
    assert b"Latitude" in response.data
    assert b"Longitude" in response.data


def test_settings_page_post(client):
    response = client.post(
        "/settings/",
        data={
            "pump": "1",
            "valve": "2",
            "levels": "5,6,7,8",
            "latitude": "48.8566",
            "longitude": "2.3522",
            "low_threshold": "15",
            "low_morning_duration": "30",
            "low_evening_duration": "30",
            "moderate_threshold": "20",
            "moderate_morning_duration": "45",
            "moderate_evening_duration": "45",
            "standard_threshold": "25",
            "standard_morning_duration": "60",
            "standard_evening_duration": "60",
            "reinforced_threshold": "30",
            "reinforced_morning_duration": "75",
            "reinforced_evening_duration": "75",
            "high_threshold": "35",
            "high_morning_duration": "90",
            "high_evening_duration": "90",
            "enabled_months": ["4", "5", "6", "7", "8", "9"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert (
        b"Settings saved successfully" in response.data
        or "Paramètres sauvés avec succès" in response.data.decode("utf-8")
    )


def test_history_page(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert b"Historique" in response.data
    assert "Période" in response.data.decode("utf-8")
