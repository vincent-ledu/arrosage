# utils/serializers.py
from datetime import timezone
import logging

logger = logging.getLogger(__name__)


def to_iso_utc(dt):
    if dt is None:
        return None
    # Assure UTC et format ISO-8601 avec 'Z'
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def task_to_dict(t):
    status = getattr(t, "status", None)
    if hasattr(status, "value"):
        status_value = status.value
    else:
        status_value = status
    return {
        "id": t.id,
        "status": status_value,
        "duration": t.duration,  # secondes
        "created_at": to_iso_utc(t.created_at),
        "updated_at": to_iso_utc(t.updated_at),
    }
