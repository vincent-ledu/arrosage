# utils/serializers.py
from datetime import timezone
import logging

logger = logging.getLogger(__name__)

def to_iso_utc(dt):
    if dt is None:
        return None
    # Assure UTC et format ISO-8601 avec 'Z'
    return dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

def task_to_dict(t):
    return {
        "id": t.id,
        "status": t.status,
        "duration": t.duration,  # secondes
        "created_at": to_iso_utc(t.created_at),
        "updated_at": to_iso_utc(t.updated_at),
    }
