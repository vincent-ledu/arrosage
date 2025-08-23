# app/routes/history_series.py

from flask import Blueprint, jsonify, request
from sqlalchemy import func
from datetime import datetime, timedelta, timezone, time as dtime
from db.db import get_session
from db.models import Task  # adapte si besoin

bp = Blueprint("history_series", __name__)

def _parse_date_ymd(s: str):
    try:
        # date naive -> on attachera UTC plus bas
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return None

@bp.get("/api/history/series")
def history_series():
    # --- Params ---
    try:
        days = int(request.args.get("days", 15))
    except ValueError:
        days = 15
    days = max(1, min(days, 365))

    end_param = request.args.get("end")

    # toujours travailler en UTC
    now_utc = datetime.now(timezone.utc)
    today_utc_date = now_utc.date()

    end_naive = _parse_date_ymd(end_param) if end_param else None
    # borne de fin en date (locale naïve) => convertie en UTC-date (on considère que ce sont des dates civiles)
    end_date = (end_naive.date() if end_naive else today_utc_date)
    if end_date > today_utc_date:
        end_date = today_utc_date

    start_date = end_date - timedelta(days=days - 1)

    # >>> BORNES AWARE EN UTC <<<
    start_dt = datetime.combine(start_date, dtime.min, tzinfo=timezone.utc)
    end_dt_excl = datetime.combine(end_date + timedelta(days=1), dtime.min, tzinfo=timezone.utc)

    # précipitations : gère l'ancienne faute de frappe
    precip_col = getattr(Task, "precipitation", None) or getattr(Task, "precipitaiton")

    with get_session() as s:
        rows = (
            s.query(
                func.date(Task.created_at).label("day"),
                func.avg(Task.min_temp).label("min_temp"),
                func.avg(Task.max_temp).label("max_temp"),
                func.avg(precip_col).label("precip_mm"),
                func.sum(Task.duration).label("duration_sec"),
                func.count().label("runs"),
            )
            .filter(Task.status == "completed")
            .filter(Task.created_at >= start_dt)   # AWARE
            .filter(Task.created_at < end_dt_excl) # AWARE
            .group_by(func.date(Task.created_at))
            .order_by(func.date(Task.created_at))
            .all()
        )

        # y a-t-il des données avant start_date ?
        oldest_row = (
            s.query(func.min(func.date(Task.created_at)))
             .filter(Task.status == "completed")
             .first()
        )
        oldest_day = oldest_row[0] if oldest_row and oldest_row[0] else None
        has_prev = False
        if oldest_day:
            try:
                oldest_day_dt = datetime.strptime(str(oldest_day), "%Y-%m-%d").date()
                has_prev = oldest_day_dt < start_date
            except Exception:
                has_prev = False

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
