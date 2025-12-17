from __future__ import annotations

import os
from datetime import datetime, timezone

import requests
from flask import Blueprint, jsonify, request

from db import db_device
from services.pi_client import PiServiceClient, load_pi_service_config


bp = Blueprint("device", __name__)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@bp.get("/api/device/snapshot")
def snapshot():
    snapshot = db_device.get_snapshot()
    if not snapshot:
        return jsonify({"available": False, "status": "unknown"}), 200

    max_age_sec = int(os.environ.get("PI_SNAPSHOT_MAX_AGE_SEC", "120"))
    now = _now_utc()
    last_seen_at = snapshot.last_seen_at
    age_sec = None
    stale = True
    if last_seen_at:
        age_sec = int((now - last_seen_at).total_seconds())
        stale = age_sec > max_age_sec or snapshot.status != "online"

    return (
        jsonify(
            {
                "available": True,
                "device_id": snapshot.device_id,
                "status": snapshot.status,
                "stale": stale,
                "age_sec": age_sec,
                "last_seen_at": last_seen_at.isoformat() if last_seen_at else None,
                "water_level_percent": snapshot.water_level_percent,
                "watering": snapshot.watering,
                "remaining_sec": snapshot.remaining_sec,
                "error": snapshot.error,
                "updated_at": snapshot.updated_at.isoformat()
                if snapshot.updated_at
                else None,
            }
        ),
        200,
    )


@bp.get("/api/device/gpio")
def gpio():
    pi_config = load_pi_service_config()
    if not pi_config:
        return jsonify({"error": "PI_SERVICE_URL not configured"}), 400

    verbose = request.args.get("verbose", "0") in {"1", "true", "yes", "on"}
    client = PiServiceClient(pi_config)
    try:
        return jsonify(client.get_gpio(verbose=verbose)), 200
    except requests.RequestException as exc:
        return jsonify({"error": "Pi unreachable", "detail": str(exc)}), 503

