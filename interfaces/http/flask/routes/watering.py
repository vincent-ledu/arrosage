from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, jsonify, request
from flask_babel import gettext as _

from application.watering.commands import (
    StartManualWateringCommand,
    StopWateringCommand,
)
from domain.shared.exceptions import DomainError
from interfaces.http.flask.container import ServiceContainer
from app.utils.serializer import task_to_dict

bp = Blueprint("watering", __name__)


def container() -> ServiceContainer:
    return current_app.config["container"]


@bp.route("/api/water-level")
def water_level():
    level = container().device_controller.get_level()
    return {"level": int(level * 25)}


@bp.route("/api/water-levels")
def water_levels():
    return jsonify(container().device_controller.debug_water_levels()), 200


@bp.route("/api/watering-type")
def classify_watering():
    temp = request.args.get("temp", type=float)
    if temp is None:
        forecast, _ = container().weather_queries.daily_forecast(date.today())
        temp = forecast.get("temperature_2m_max")
        if temp is None:
            return (
                jsonify({"error": _("Failed to fetch temperature")}),
                500,
            )
    watering_type = container().watering_queries.classify_watering(temp)
    return watering_type, 200


@bp.route("/api/tasks")
def task_list():
    return jsonify(container().watering_queries.list_tasks()), 200


@bp.route("/api/tasks/<task_id>")
def task_detail(task_id: str):
    task = container().watering_repository.get(task_id)
    if not task:
        return jsonify({"error": _("Task %(task_id)s not found", task_id=task_id)}), 404
    return jsonify(task_to_dict(task)), 200


@bp.route("/api/task")
def current_task():
    task = container().watering_queries.current_task()
    if not task:
        return jsonify({"task_id": None}), 404
    return jsonify(task), 200


def _error_response(message: str, category: str, status_code: int):
    return (
        jsonify({
            "error": message,
            "flash": {"message": message, "category": category},
        }),
        status_code,
    )


@bp.route("/api/command/open-water", methods=["GET"])
def open_water():
    duration = request.args.get("duration", type=int)
    if duration is None:
        return _error_response("Duration parameter is required", "error", 400)

    command = StartManualWateringCommand(duration_seconds=duration)
    try:
        result = container().start_watering_handler.handle(command)
        return jsonify(result), 202
    except DomainError as exc:
        message = str(exc)
        mapping = {
            "Watering is already in progress.": (409, "error", "Watering is already in progress."),
            "Not enough water.": (507, "error", "Not enough water."),
            "Temperature is too low to water.": (400, "warning", "Temperature is too low to water."),
            "Watering is disabled for the current month.": (400, "warning", "Watering is disabled for the current month."),
            "Invalid duration": (400, "error", "Invalid duration"),
        }
        status_code, category, response_message = mapping.get(
            message, (400, "error", message)
        )
        return _error_response(response_message, category, status_code)
    except Exception as exc:  # pragma: no cover - defensive
        return _error_response(str(exc), "error", 500)


@bp.route("/api/command/close-water")
def close_water():
    result = container().stop_watering_handler.handle(StopWateringCommand())
    if "error" in result:
        return _error_response(_(result["error"]), "warning", 404)
    return (
        jsonify({
            "message": result["message"],
            "flash": {"message": _("Watering task terminated."), "category": "success"},
        }),
        200,
    )
