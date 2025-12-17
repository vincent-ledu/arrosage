from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, jsonify, request
from flask_babel import gettext as _
import requests

from application.watering.commands import (
    StartManualWateringCommand,
    StopWateringCommand,
)
from domain.shared.exceptions import DomainError
from interfaces.http.flask.container import ServiceContainer
from services.pi_client import PiServiceClient, load_pi_service_config
from utils.serializer import task_to_dict
from db import db_device, db_tasks

bp = Blueprint("watering", __name__)


def container() -> ServiceContainer:
    return current_app.config["container"]


@bp.route("/api/water-level")
def water_level():
    pi_config = load_pi_service_config()
    if not pi_config:
        level = container().device_controller.get_level()
        return {"level": int(level * 25)}

    snapshot = db_device.get_snapshot()
    if snapshot and snapshot.water_level_percent is not None:
        return {
            "level": int(snapshot.water_level_percent),
            "available": True,
            "stale": snapshot.status != "online",
            "last_seen_at": snapshot.last_seen_at.isoformat()
            if snapshot.last_seen_at
            else None,
        }

    # No cache yet -> expose a safe value without breaking the UI.
    return {"level": 0, "available": False, "stale": True, "last_seen_at": None}


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
        jsonify(
            {
                "error": message,
                "flash": {"message": message, "category": category},
            }
        ),
        status_code,
    )


@bp.route("/api/command/open-water", methods=["GET"])
def open_water():
    duration = request.args.get("duration", type=int)
    if duration is None:
        return _error_response("Duration parameter is required", "error", 400)

    pi_config = load_pi_service_config()
    if pi_config:
        client = PiServiceClient(pi_config)
        idempotency_key = request.headers.get("Idempotency-Key")
        try:
            db_device.log_command(
                command="start",
                payload={"duration_sec": duration},
                result="requested",
            )
            result = client.start_watering(
                duration_sec=duration,
                idempotency_key=idempotency_key,
            )
            task_id = result.get("job_id")
            if task_id:
                db_tasks.add_task_with_id(task_id, duration, "in progress")
            db_device.log_command(
                command="start",
                payload={"duration_sec": duration, "job_id": task_id},
                result="accepted",
            )
            return (
                jsonify(
                    {
                        "task_id": task_id,
                        "flash": {
                            "message": _("Watering task started."),
                            "category": "success",
                        },
                    }
                ),
                202,
            )
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", 500)
            message = "Pi error"
            if status_code == 409:
                message = "Watering is already in progress."
            db_device.log_command(
                command="start",
                payload={"duration_sec": duration},
                result="failed",
                error=str(exc),
            )
            return _error_response(message, "error", status_code)
        except requests.RequestException as exc:
            db_device.log_command(
                command="start",
                payload={"duration_sec": duration},
                result="failed",
                error=str(exc),
            )
            return _error_response("Pi unreachable", "error", 503)
        except Exception as exc:  # pragma: no cover - defensive
            db_device.log_command(
                command="start",
                payload={"duration_sec": duration},
                result="failed",
                error=str(exc),
            )
            return _error_response(str(exc), "error", 500)

    command = StartManualWateringCommand(duration_seconds=duration)
    try:
        result = container().start_watering_handler.handle(command)
        return jsonify(result), 202
    except DomainError as exc:
        message = str(exc)
        mapping = {
            "Watering is already in progress.": (
                409,
                "error",
                "Watering is already in progress.",
            ),
            "Not enough water.": (507, "error", "Not enough water."),
            "Temperature is too low to water.": (
                400,
                "warning",
                "Temperature is too low to water.",
            ),
            "Watering is disabled for the current month.": (
                400,
                "warning",
                "Watering is disabled for the current month.",
            ),
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
    pi_config = load_pi_service_config()
    if pi_config:
        client = PiServiceClient(pi_config)
        try:
            db_device.log_command(command="stop", payload=None, result="requested")
            client.stop_watering()
            active = container().watering_repository.get_active_task()
            if active:
                db_tasks.update_status(active.id, "canceled")
            db_device.log_command(command="stop", payload=None, result="accepted")
            return (
                jsonify(
                    {
                        "message": "stopped",
                        "flash": {
                            "message": _("Watering task terminated."),
                            "category": "success",
                        },
                    }
                ),
                200,
            )
        except requests.RequestException as exc:
            db_device.log_command(
                command="stop", payload=None, result="failed", error=str(exc)
            )
            return _error_response("Pi unreachable", "error", 503)
        except Exception as exc:  # pragma: no cover - defensive
            db_device.log_command(
                command="stop", payload=None, result="failed", error=str(exc)
            )
            return _error_response(str(exc), "error", 500)

    result = container().stop_watering_handler.handle(StopWateringCommand())
    if "error" in result:
        return _error_response(_(result["error"]), "warning", 404)
    return (
        jsonify(
            {
                "message": result["message"],
                "flash": {
                    "message": _("Watering task terminated."),
                    "category": "success",
                },
            }
        ),
        200,
    )
