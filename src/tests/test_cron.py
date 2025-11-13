"""Tests pour le module cron.py"""
from dotenv import load_dotenv
import cron


def pytest_configure(config):
    """ Charger le .env.test en priorité """
    load_dotenv(dotenv_path=".env.test", override=True)


def test_watering(monkeypatch):
    """ Mock requests.get """

    mock_get = lambda url, headers=None: None
    calls = []

    class MockResponse:
        def __init__(self, text, status_code=200):
            self.text = text
            self.status_code = status_code

    def fake_get(url, headers=None, **kwargs):
        calls.append((url, headers))
        if url == "http://localhost/api/watering-type":
            return MockResponse("standard")
        return MockResponse("")

    monkeypatch.setattr(cron.requests, "get", fake_get)

    # Mock load_config to return a specific configuration
    monkeypatch.setattr(
        cron.local_config,
        "load_config",
        lambda: {
            "watering": {
                "low": {"morning-duration": 10, "evening-duration": 20},
                "moderate": {"morning-duration": 30, "evening-duration": 40},
                "standard": {"morning-duration": 50, "evening-duration": 60},
                "reinforced": {"morning-duration": 70, "evening-duration": 80},
                "high": {"morning-duration": 90, "evening-duration": 100},
            }
        },
    )

    # Call the watering function for morning
    cron.watering("morning")

    # Check that the correct URL was called with the expected duration
    assert (
        "http://localhost/api/watering-type",
        {"X-Real-IP": "192.168.0.105"},
    ) in calls
    assert (
        "http://localhost/api/command/open-water?duration=50",
        {"X-Real-IP": "192.168.0.105"},
    ) in calls
    assert len(calls) == 2
