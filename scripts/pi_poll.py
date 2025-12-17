"""Periodic poller (VM side) to update cached Pi snapshot in DB.

Intended to run on the VM (cron/systemd timer). It calls the Raspberry Pi
pi-service (REST) and stores the last known state in the database so the UI
stays available even when the Pi is unreachable.
"""

from __future__ import annotations

import os
import sys
import logging
from datetime import datetime, timezone
from datetime import timedelta
from pathlib import Path

# Ensure project root (and src/ when present) are on the Python path so imports
# work no matter where the script is executed from (cron, deployment symlink, etc.).
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
for path in (ROOT_DIR, SRC_DIR):
    path_str = str(path)
    if path_str not in sys.path and path.exists():
        sys.path.insert(0, path_str)

import requests

from db import db_device, db_tasks
from services.pi_client import PiServiceClient, load_pi_service_config


logger = logging.getLogger(__name__)

_handlers = [logging.StreamHandler()]
if os.getenv("TESTING") != "1":
    os.makedirs("/var/log/gunicorn", exist_ok=True)
    _handlers.insert(0, logging.FileHandler("/var/log/gunicorn/pi-poll.log"))

logging.basicConfig(
    level=logging.DEBUG if os.getenv("PI_POLL_DEBUG", "0") == "1" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_handlers,
    force=True,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _reconcile_tasks(*, watering: bool, now: datetime) -> None:
    if watering:
        return
    active = db_tasks.get_tasks_by_status("in progress")
    if not active:
        return
    task = active[0]
    created_at = getattr(task, "created_at", None)
    duration = int(getattr(task, "duration", 0) or 0)
    if created_at is None:
        db_tasks.update_status(task.id, "completed")
        return

    end_at = created_at + timedelta(seconds=duration)

    if now >= end_at:
        db_tasks.update_status(task.id, "completed")
    else:
        db_tasks.update_status(task.id, "canceled")


def poll_once() -> int:
    config = load_pi_service_config()
    if not config:
        logger.info("PI_SERVICE_URL not set: skipping poll.")
        return 0

    client = PiServiceClient(config)
    now = _now_utc()

    try:
        status = client.get_status()
        water_level = status.get("water_level_percent")
        watering = bool(status.get("watering"))
        remaining_sec = status.get("remaining_sec")
        db_device.upsert_snapshot(
            status="online",
            last_seen_at=now,
            water_level_percent=int(water_level) if water_level is not None else None,
            watering=watering,
            remaining_sec=int(remaining_sec) if remaining_sec is not None else None,
            error=None,
        )
        _reconcile_tasks(watering=watering, now=now)
        logger.info("Pi online: level=%s watering=%s", water_level, watering)
        return 0
    except requests.RequestException as exc:
        existing = db_device.get_snapshot()
        db_device.upsert_snapshot(
            status="offline",
            last_seen_at=getattr(existing, "last_seen_at", None),
            water_level_percent=getattr(existing, "water_level_percent", None),
            watering=getattr(existing, "watering", None),
            remaining_sec=getattr(existing, "remaining_sec", None),
            error=str(exc),
        )
        logger.warning("Pi unreachable: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(poll_once())
