from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from db.database import get_session
from db.models import DeviceCommandLog, DeviceSnapshot


DEFAULT_DEVICE_ID = "garden-pi"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_snapshot(device_id: str = DEFAULT_DEVICE_ID) -> DeviceSnapshot | None:
    with get_session() as s:
        return s.get(DeviceSnapshot, device_id)


def upsert_snapshot(
    *,
    device_id: str = DEFAULT_DEVICE_ID,
    status: str,
    last_seen_at: datetime | None,
    water_level_percent: int | None,
    watering: bool | None,
    remaining_sec: int | None,
    error: str | None,
) -> None:
    with get_session() as s:
        row = s.get(DeviceSnapshot, device_id)
        if row is None:
            row = DeviceSnapshot(
                device_id=device_id,
                status=status,
                last_seen_at=last_seen_at,
                water_level_percent=water_level_percent,
                watering=watering,
                remaining_sec=remaining_sec,
                error=error,
                updated_at=_now_utc(),
            )
            s.add(row)
        else:
            row.status = status
            row.last_seen_at = last_seen_at
            row.water_level_percent = water_level_percent
            row.watering = watering
            row.remaining_sec = remaining_sec
            row.error = error
            row.updated_at = _now_utc()
        s.commit()


def log_command(
    *,
    device_id: str = DEFAULT_DEVICE_ID,
    command: str,
    payload: dict[str, Any] | None,
    result: str,
    error: str | None = None,
) -> None:
    with get_session() as s:
        s.add(
            DeviceCommandLog(
                device_id=device_id,
                command=command,
                payload=json.dumps(payload) if payload is not None else None,
                result=result,
                error=error,
                created_at=_now_utc(),
            )
        )
        s.commit()


def list_commands(device_id: str = DEFAULT_DEVICE_ID, limit: int = 100) -> list[DeviceCommandLog]:
    with get_session() as s:
        stmt = (
            select(DeviceCommandLog)
            .where(DeviceCommandLog.device_id == device_id)
            .order_by(DeviceCommandLog.created_at.desc())
            .limit(int(limit))
        )
        return list(s.scalars(stmt).all())

