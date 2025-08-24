# app/routes/history_series.py

from flask import Blueprint, jsonify, request
from sqlalchemy import func, literal, bindparam, String
from datetime import date, datetime, timedelta
from db.db_tasks import get_session
from db.models import Task, ForecastStats  # ForecastStats.date est un DATE (ou TEXT 'YYYY-MM-DD')

bp = Blueprint("history_series", __name__)

def _parse_date_ymd(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def _as_iso_date_str(x) -> str | None:
    if x is None:
        return None
    if hasattr(x, "isoformat"):
        try:
            return x.isoformat()
        except Exception:
            pass
    s = str(x)
    # tronque "YYYY-MM-DD HH:MM:SS" -> "YYYY-MM-DD"
    return s[:10] if len(s) >= 10 else s

@bp.get("/api/history/series")
def history_series():
    # -------- paramètres --------
    try:
        days = int(request.args.get("days", 15))
    except ValueError:
        days = 15
    days = max(1, min(days, 365))

    end_param = request.args.get("end")
    today = date.today()
    end_date = _parse_date_ymd(end_param) or today
    if end_date > today:
        end_date = today
    start_date = end_date - timedelta(days=days - 1)

    start_iso = start_date.isoformat()  # "YYYY-MM-DD"
    end_iso   = end_date.isoformat()

    # Bind params en STRING (clé jour ISO)
    bp_start_iso = bindparam("bp_start_iso", start_iso, type_=String())
    bp_end_iso   = bindparam("bp_end_iso",   end_iso,   type_=String())

    with get_session() as s:
        # clé jour ISO côté tasks et forecast_stats
        day_str_tasks = func.strftime("%Y-%m-%d", Task.created_at)
        day_str_fs    = func.strftime("%Y-%m-%d", ForecastStats.date)

        # Agrégation des tâches "completed" par jour ISO
        tasks_agg_sq = (
            s.query(
                day_str_tasks.label("day_str"),
                func.sum(Task.duration).label("duration_sec"),
                func.count().label("runs"),
            )
            .filter(Task.status == "completed")
            .filter(day_str_tasks >= bp_start_iso)
            .filter(day_str_tasks <= bp_end_iso)
            .group_by(day_str_tasks)
        ).subquery()

        # Météo + LEFT JOIN sur la clé string
        rows = (
            s.query(
                ForecastStats.date.label("day"),
                ForecastStats.min_temp.label("min_temp"),
                ForecastStats.max_temp.label("max_temp"),
                ForecastStats.precipitation.label("precip_mm"),
                func.coalesce(tasks_agg_sq.c.duration_sec, literal(0)).label("duration_sec"),
                func.coalesce(tasks_agg_sq.c.runs,        literal(0)).label("runs"),
            )
            .outerjoin(tasks_agg_sq, tasks_agg_sq.c.day_str == day_str_fs)
            .filter(day_str_fs >= bp_start_iso)
            .filter(day_str_fs <= bp_end_iso)
            .order_by(ForecastStats.date)
            .all()
        )

        # pour le bouton "-15j"
        oldest_row = s.query(func.min(ForecastStats.date)).first()
        oldest_iso = _as_iso_date_str(oldest_row[0] if oldest_row else None)
        has_prev = bool(oldest_iso and oldest_iso < start_iso)

    data = [
        {
            "day": r.day.isoformat().split('T')[0] if r.day else None,
            "min_temp": float(r.min_temp) if r.min_temp is not None else None,
            "max_temp": float(r.max_temp) if r.max_temp is not None else None,
            "precip_mm": float(r.precip_mm) if r.precip_mm is not None else 0.0,
            "duration_min": round((r.duration_sec or 0) / 60.0, 1),
            "runs": int(r.runs or 0),
        }
        for r in rows
    ]

    prev_end = (start_date - timedelta(days=1)) if has_prev else None

    return jsonify({
        "meta": {
            "days": days,
            "start": start_iso,
            "end": end_iso,
            "has_prev": has_prev,
            "prev_end": prev_end.isoformat() if prev_end else None,
        },
        "data": data
    })
