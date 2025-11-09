from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, jsonify
from flask_babel import gettext as _

from interfaces.http.flask.container import ServiceContainer

bp = Blueprint("weather", __name__)


def container() -> ServiceContainer:
    return current_app.config["container"]


@bp.route("/api/forecast")
def forecast():
    try:
        data, from_cache = container().weather_queries.partday_forecast()
        status_code = 200 if from_cache else 201
        return jsonify(data[:5]), status_code
    except Exception as exc:  # pragma: no cover - defensive
        return (
            jsonify(
                {
                    "error": str(exc),
                    "flash": {
                        "message": _("Error fetching weather data. Please try again later."),
                        "category": "warning",
                    },
                }
            ),
            500,
        )


@bp.route("/api/forecast-minmax-precip")
def forecast_minmax_precip():
    try:
        data, from_cache = container().weather_queries.daily_forecast(date.today())
        status_code = 200 if from_cache else 201
        return jsonify(data), status_code
    except Exception as exc:  # pragma: no cover - defensive
        return (
            jsonify(
                {
                    "error": str(exc),
                    "flash": {
                        "message": _("Error fetching weather data. Please try again later."),
                        "category": "warning",
                    },
                }
            ),
            500,
        )


@bp.route("/api/temperature-max")
def temperature_max():
    try:
        response, _ = container().weather_queries.daily_forecast(date.today())
        max_temp = response.get("temperature_2m_max")
        if max_temp is None:
            raise ValueError("Max temperature not found in forecast data")
        return jsonify(max_temp), 200
    except Exception as exc:  # pragma: no cover - defensive
        return (
            jsonify(
                {
                    "error": str(exc),
                    "flash": {
                        "message": _("Error fetching weather data. Please try again later."),
                        "category": "warning",
                    },
                }
            ),
            500,
        )


@bp.route("/api/coordinates")
def coordinates():
    config = container().configuration_service.load().get("coordinates", {})
    latitude = float(config.get("latitude", 48.866667))
    longitude = float(config.get("longitude", 2.333333))
    return jsonify({"latitude": latitude, "longitude": longitude})
