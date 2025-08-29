# app/routes/history_series.py

from flask import Blueprint, jsonify, request
from sqlalchemy import func, cast, Float, Integer
from datetime import date, datetime, timedelta, time

from db.db_tasks import get_session
from db.models import Task, WeatherData  # ForecastStats.date = Date, Task.created_at = DateTime

bp = Blueprint("history_series", __name__)

def _parse_date_ymd(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)  # "YYYY-MM-DD"
    except ValueError:
        return None

@bp.get("/api/history/series")
def history_series():
    # -------- paramètres --------
    try:
        days = int(request.args.get("days", 15))
    except ValueError:
        days = 15
    days = max(1, min(days, 365))

    today = date.today()
    end_date = _parse_date_ymd(request.args.get("end")) or today
    if end_date > today:
        end_date = today
    start_date = end_date - timedelta(days=days - 1)

    # bornes temporelles pour filtrer les DATETIME (intervalle semi-ouvert [start_dt, end_dt_next))
    start_dt = datetime.combine(start_date, time.min)  # 00:00:00
    end_dt_next = datetime.combine(end_date + timedelta(days=1), time.min)  # jour suivant 00:00:00

    with get_session() as s:
        # 1) Agrégation des tâches complétées par jour (DATE(Task.created_at))
        tasks_agg_sq = (
            s.query(
                func.date(Task.created_at).label("day"),
                cast(func.sum(Task.duration), Integer).label("duration_sec"),
                cast(func.count(), Integer).label("runs"),
            )
            .filter(Task.status == "completed")
            .filter(Task.created_at >= start_dt)
            .filter(Task.created_at < end_dt_next)
            .group_by(func.date(Task.created_at))
        ).subquery()

        # 2) Plage météo + LEFT JOIN sur la clé DATE
        rows = (
            s.query(
                WeatherData.date.label("day"),
                cast(WeatherData.min_temp, Float).label("min_temp"),
                cast(WeatherData.max_temp, Float).label("max_temp"),
                cast(WeatherData.precipitation, Float).label("precip_mm"),
                cast(func.coalesce(tasks_agg_sq.c.duration_sec, 0), Integer).label("duration_sec"),
                cast(func.coalesce(tasks_agg_sq.c.runs, 0), Integer).label("runs"),
            )
            .outerjoin(tasks_agg_sq, tasks_agg_sq.c.day == WeatherData.date)
            .filter(WeatherData.date >= start_date)
            .filter(WeatherData.date <= end_date)
            .order_by(WeatherData.date)
            .all()
        )

        # 3) Pour le bouton "-15j" : plus ancienne date météo disponible
        oldest_date = s.query(func.min(WeatherData.date)).scalar()
        has_prev = bool(oldest_date and oldest_date < start_date)

    data = [
        {
            "day": r.day.isoformat() if r.day else None,
            "min_temp": float(r.min_temp) if r.min_temp is not None else None,
            "max_temp": float(r.max_temp) if r.max_temp is not None else None,
            "precip_mm": float(r.precip_mm) if r.precip_mm is not None else 0.0,
            "duration_min": round((r.duration_sec or 0) / 60, 1),
            "runs": int(r.runs or 0),
        }
        for r in rows
    ]

    prev_end = (start_date - timedelta(days=1)) if has_prev else None

    return jsonify({
        "meta": {
            "days": days,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "has_prev": has_prev,
            "prev_end": prev_end.isoformat() if prev_end else None,
        },
        "data": data
    })
