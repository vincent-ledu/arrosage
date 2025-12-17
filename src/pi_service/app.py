from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure top-level package is importable when running `python -m pi_service.app`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request

from pi_service.container import PiServiceContainer, build_pi_container

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    log_level = logging.DEBUG if os.environ.get("PI_SERVICE_DEBUG", "0") == "1" else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


def create_app() -> Flask:
    _configure_logging()

    app = Flask(__name__)
    app.config["container"] = build_pi_container()

    _register_hooks(app)
    _register_routes(app)

    return app


def container() -> PiServiceContainer:
    return app.config["container"]


def _token_from_request() -> str | None:
    bearer = request.headers.get("Authorization", "")
    if bearer.lower().startswith("bearer "):
        return bearer.split(" ", 1)[1].strip() or None
    return request.headers.get("X-API-Token") or None


def _register_hooks(app: Flask) -> None:
    @app.before_request
    def enforce_auth():
        token = os.environ.get("PI_SERVICE_TOKEN")
        if not token:
            return None

        if request.path in {"/healthz", "/healthcheck", "/"}:
            return None

        provided = _token_from_request()
        if not provided or provided != token:
            return jsonify({"error": "unauthorized"}), 401


def _register_routes(app: Flask) -> None:
    @app.get("/")
    def index():
        return jsonify({"service": "arrosage-pi", "status": "ok"}), 200

    @app.get("/healthz")
    @app.get("/healthcheck")
    def healthz():
        try:
            level_raw = container().device_controller.get_level()
            return (
                jsonify(
                    {
                        "status": "healthy",
                        "water_level_percent": int(level_raw * 25),
                    }
                ),
                200,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return jsonify({"status": "unhealthy", "error": str(exc)}), 500

    @app.get("/v1/water-level")
    def water_level():
        level_raw = container().device_controller.get_level()
        return (
            jsonify(
                {
                    "level_percent": int(level_raw * 25),
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    @app.get("/v1/status")
    def status():
        payload = container().watering_runtime.status()
        level_raw = container().device_controller.get_level()
        payload["water_level_percent"] = int(level_raw * 25)
        payload["ts"] = datetime.now(timezone.utc).isoformat()
        return jsonify(payload), 200

    @app.post("/v1/watering/start")
    def start_watering():
        max_duration = int(os.environ.get("PI_MAX_WATERING_DURATION_SEC", "900"))
        body = request.get_json(silent=True) or {}
        duration = body.get("duration_sec", request.args.get("duration_sec", type=int))
        if duration is None:
            return jsonify({"error": "duration_sec is required"}), 400
        if not isinstance(duration, int):
            return jsonify({"error": "duration_sec must be an integer"}), 400
        if duration <= 0:
            return jsonify({"error": "duration_sec must be > 0"}), 400
        if duration > max_duration:
            return (
                jsonify({"error": f"duration_sec must be <= {max_duration}"}),
                400,
            )

        idempotency_key = request.headers.get("Idempotency-Key")
        try:
            job = container().watering_runtime.start(
                duration, idempotency_key=idempotency_key
            )
            return (
                jsonify(
                    {
                        "job_id": job.job_id,
                        "duration_sec": job.duration_sec,
                        "started_at": job.started_at.isoformat(),
                        "scheduled_stop_at": job.scheduled_stop_at.isoformat(),
                    }
                ),
                202,
            )
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 409
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to start watering")
            return jsonify({"error": str(exc)}), 500

    @app.post("/v1/watering/stop")
    def stop_watering():
        stopped = container().watering_runtime.stop()
        return jsonify({"stopped": bool(stopped)}), 200

    @app.get("/v1/gpio")
    def gpio_state():
        verbose = request.args.get("verbose", "0") in {"1", "true", "yes", "on"}
        config = container().configuration_service.load()
        payload: dict = {
            "pump": {"pin": config.get("pump")},
            "valve": {"pin": config.get("valve")},
            "levels": [{"index": i, "pin": pin} for i, pin in enumerate(config.get("levels", []))],
        }

        if verbose:
            watering_status = container().watering_runtime.status()
            payload["watering"] = watering_status
            payload["outputs"] = {
                "pump": {"pin": config.get("pump"), "value": 1 if watering_status["watering"] else 0},
                "valve": {"pin": config.get("valve"), "value": 1 if watering_status["watering"] else 0},
            }
            payload["levels_state"] = container().device_controller.debug_water_levels()
        return jsonify(payload), 200


app = create_app()


def main() -> None:
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 8081)),
        debug=os.environ.get("PI_SERVICE_DEBUG", "0") == "1",
    )


if __name__ == "__main__":
    main()
