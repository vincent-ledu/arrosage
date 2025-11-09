from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.db import db_tasks
from interfaces.http.flask.container import ServiceContainer

bp = Blueprint("system", __name__)


def container() -> ServiceContainer:
    return current_app.config["container"]


@bp.route("/health")
@bp.route("/healthz")
@bp.route("/healthcheck")
@bp.route("/api/healthcheck")
def health():
    try:
        container().device_controller.get_level()
        conn = db_tasks.get_connection()
        conn.close()
        return jsonify({"status": "healthy"}), 200
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"status": "unhealthy", "error": str(exc)}), 500
