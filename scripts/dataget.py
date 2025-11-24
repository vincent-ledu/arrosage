#!/usr/bin/env python3
import os
import requests
import mysql.connector
from datetime import date, timedelta
from typing import Dict, List, Set
from urllib.parse import urlparse, parse_qs

# -----------------------
# Configuration
# -----------------------
# Les variables ci-dessous sont alimentées par l'environnement (/etc/default/arrosage en prod)

def _load_db_config():
    """Récupère la configuration DB depuis DATABASE_URL ou les variables DB* individuelles."""
    url = os.getenv("DATABASE_URL")
    if url:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip("/") or None,
            "charset": query.get("charset", [None])[0],
        }

    # Fallback sur les variables individuelles
    return {
        "host": os.getenv("DBHOST", "localhost"),
        "port": int(os.getenv("DBPORT", 3306)),
        "user": os.getenv("DBUSER"),
        "password": os.getenv("DBPASSWORD"),
        "database": os.getenv("DBNAME"),
        "charset": os.getenv("DBOPTIONS", "charset=utf8mb4").replace("charset=", ""),
    }


DB_CONFIG = _load_db_config()

WEATHER_TABLE = os.getenv("WEATHER_TABLE", "weather_data")

LATITUDE = float(os.getenv("LATITUDE", 48.862725))
LONGITUDE = float(os.getenv("LONGITUDE", 2.287592))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Paris")

# Date à partir de laquelle tu veux être sûr que toutes les données sont complètes
START_DATE = date.fromisoformat(os.getenv("START_DATE", "2025-07-11"))


# -----------------------
# Helpers dates
# -----------------------

def daterange(start: date, end: date):
    """Generate dates from start to end inclusive."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


# -----------------------
# MySQL helpers
# -----------------------

def get_connection():
    """Create and return a new MySQL connection."""
    connect_kwargs = {
        "host": DB_CONFIG["host"],
        "port": DB_CONFIG["port"],
        "user": DB_CONFIG["user"],
        "password": DB_CONFIG["password"],
        "database": DB_CONFIG["database"],
    }
    if DB_CONFIG.get("charset"):
        connect_kwargs["charset"] = DB_CONFIG["charset"]
    return mysql.connector.connect(**connect_kwargs)


def get_existing_dates(conn, start_date: date, end_date: date) -> Set[date]:
    """Return a set of dates that already exist in weather_data between start_date and end_date."""
    query = f"""
        SELECT date
        FROM {WEATHER_TABLE}
        WHERE date BETWEEN %s AND %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (start_date, end_date))
        rows = cur.fetchall()
    return {row[0] for row in rows}


def upsert_weather_data(
    conn,
    daily_data: Dict[date, Dict[str, float]],
    target_dates: List[date],
):
    """
    Insert data for target_dates into weather_data using ON DUPLICATE KEY UPDATE.

    daily_data: mapping date -> {"min_temp": float, "max_temp": float, "precipitation": float}
    target_dates: only those dates will be written
    """
    query = f"""
        INSERT INTO {WEATHER_TABLE} (
            date,
            min_temp,
            max_temp,
            precipitation,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, NOW(), NOW()
        )
        ON DUPLICATE KEY UPDATE
            min_temp      = VALUES(min_temp),
            max_temp      = VALUES(max_temp),
            precipitation = VALUES(precipitation),
            updated_at    = NOW()
    """

    with conn.cursor() as cur:
        for d in target_dates:
            if d not in daily_data:
                print(f"[WARN] No data from Open-Meteo for {d}, skipping.")
                continue
            record = daily_data[d]
            cur.execute(
                query,
                (
                    d,
                    record["min_temp"],
                    record["max_temp"],
                    record["precipitation"],
                ),
            )
    conn.commit()


# -----------------------
# Open-Meteo API helper
# -----------------------

def fetch_open_meteo_daily(start_date: date, end_date: date) -> Dict[date, Dict[str, float]]:
    """
    Call Open-Meteo archive API and return mapping:
    date -> {"min_temp": float, "max_temp": float, "precipitation": float}
    """
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum",
        "timezone": TIMEZONE,
    }

    print(f"[INFO] Calling Open-Meteo from {start_date} to {end_date}...")
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "daily" not in data:
        raise RuntimeError(f"Unexpected response from Open-Meteo: {data}")

    daily = data["daily"]
    dates = daily["time"]
    tmin_list = daily["temperature_2m_min"]
    tmax_list = daily["temperature_2m_max"]
    precip_list = daily["precipitation_sum"]

    result: Dict[date, Dict[str, float]] = {}
    for i, d_str in enumerate(dates):
        d = date.fromisoformat(d_str)
        result[d] = {
            "min_temp": float(tmin_list[i]) if tmin_list[i] is not None else 0.0,
            "max_temp": float(tmax_list[i]) if tmax_list[i] is not None else 0.0,
            "precipitation": float(precip_list[i]) if precip_list[i] is not None else 0.0,
        }

    print(f"[INFO] Received {len(result)} daily records from Open-Meteo.")
    return result


# -----------------------
# Main logic
# -----------------------

def main():
    # End date = today (tu peux mettre - 1 jour si tu veux éviter le jour courant)
    today = date.today()
    end_date = today

    print(f"[INFO] Completing weather data from {START_DATE} to {end_date}.")

    conn = get_connection()
    try:
        # 1. Find missing dates in DB
        existing = get_existing_dates(conn, START_DATE, end_date)
        all_days = list(daterange(START_DATE, end_date))
        missing = [d for d in all_days if d not in existing]

        if not missing:
            print("[INFO] No missing dates in this range, nothing to do.")
            return

        print(f"[INFO] Found {len(missing)} missing dates.")

        # 2. Call Open-Meteo for the minimal continuous range that covers missing dates
        first_missing = min(missing)
        last_missing = max(missing)

        daily_data = fetch_open_meteo_daily(first_missing, last_missing)

        # 3. Insert only missing dates
        upsert_weather_data(conn, daily_data, missing)

        print("[INFO] Weather data completion done.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
