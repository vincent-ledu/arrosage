# app/routes/history_series.py  (ou directement dans app.py)

from flask import Blueprint, jsonify
from sqlalchemy import func
import logging

from db.db import get_session
from db.models import Task  # adapte l'import si besoin

logger = logging.getLogger(__name__)

bp = Blueprint("history_series", __name__)

@bp.get("/api/history/series")
def history_series():
    """
    Renvoie une série agrégée par jour, pour les tâches 'completed'.
    - min/max moyen du jour (si plusieurs runs)
    - cumul des précipitations (mm)
    - cumul du temps d'arrosage (secondes -> minutes côté front)
    """
    with get_session() as s:
        rows = (
            s.query(
                func.date(Task.created_at).label("day"),
                func.avg(Task.min_temp).label("min_temp"),
                func.avg(Task.max_temp).label("max_temp"),
                func.avg(Task.precipitation).label("precip_mm"),
                func.sum(Task.duration).label("duration_sec"),
                func.count().label("runs"),
            )
            .filter(Task.status == "completed")
            .group_by(func.date(Task.created_at))
            .order_by(func.date(Task.created_at))
            .all()
        )

    data = [
        {
            "day": str(r.day),
            "min_temp": float(r.min_temp) if r.min_temp is not None else None,
            "max_temp": float(r.max_temp) if r.max_temp is not None else None,
            "precip_mm": float(r.precip_mm) if r.precip_mm is not None else 0.0,
            "duration_min": round((r.duration_sec or 0) / 60.0, 1),
            "runs": int(r.runs),
        }
        for r in rows
    ]
    logger.debug(f"history_series: {data}")
    return jsonify(data)
