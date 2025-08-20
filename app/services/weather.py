from collections import Counter, defaultdict
from datetime import datetime
import requests
from flask_babel import lazy_gettext as _

WMO = {
    0:  ("🌞", _("Clear sky")),
    1:  ("☀️", _("Mainly clear")),
    2:  ("⛅", _("Partly cloudy")),
    3:  ("☁️", _("Overcast")),
    45: ("🌫️", _("Fog")),
    48: ("🌫️❄️", _("Freezing fog (rime)")),
    51: ("🌦️", _("Drizzle: light")),
    53: ("🌦️", _("Drizzle: moderate")),
    55: ("🌦️", _("Drizzle: dense/heavy")),
    56: ("🌧️❄️", _("Freezing drizzle: light")),
    57: ("🌧️❄️", _("Freezing drizzle: dense/heavy")),
    61: ("🌧️", _("Rain: light")),
    63: ("🌧️", _("Rain: moderate")),
    65: ("🌧️", _("Rain: heavy")),
    66: ("🌧️❄️", _("Freezing rain: light")),
    67: ("🌧️❄️", _("Freezing rain: heavy")),
    71: ("🌨️", _("Snowfall: light")),
    73: ("🌨️", _("Snowfall: moderate")),
    75: ("🌨️", _("Snowfall: heavy")),
    77: ("❄️", _("Snow grains")),
    80: ("🌦️", _("Rain showers: light")),
    81: ("🌦️", _("Rain showers: moderate")),
    82: ("🌧️", _("Rain showers: violent")),
    85: ("🌨️", _("Snow showers: light")),
    86: ("🌨️", _("Snow showers: heavy")),
    95: ("⛈️", _("Thunderstorm")),
    96: ("⛈️🧊", _("Thunderstorm with hail (slight/moderate)")),
    99: ("⛈️🧊", _("Thunderstorm with heavy hail")),
}

def wmo_icon_text(code: int):
    return WMO.get(code, ("❔", _("Unknown weather code")))

def fetch_open_meteo(lat, lon, days=7):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "weather_code,cloudcover,temperature_2m,precipitation,precipitation_probability",
        "forecast_days": days,
        "timezone": "Europe/Paris",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def slice_partday(dt: datetime) -> str:
    h = dt.hour
    if 0 <= h <= 5:  return "night"
    if 6 <= h <= 11:  return "morning"
    if 12 <= h <= 17: return "afternoon"
    if 18 <= h <= 23: return "evening"
    return "other"

def aggregate_by_partday(data):
    H = data["hourly"]
    times = [datetime.fromisoformat(t) for t in H["time"]]

    # Regroupe par date -> (morning/afternoon) -> liste d’indices horaires
    buckets = defaultdict(lambda: {"night": [], "morning": [], "afternoon": [], "evening": []})
    for i, dt in enumerate(times):
        half = slice_partday(dt)
        if half != "other":
            dkey = dt.date().isoformat()
            buckets[dkey][half].append(i)

    out = []
    for dkey, halves in sorted(buckets.items()):
        row = {"date": dkey}
        for half_name, idxs in halves.items():
            if not idxs:
                row[f"{half_name}_icon"] = "—"
                row[f"{half_name}_precip_mm"] = 0.0
                row[f"{half_name}_temp_avg"] = None
                continue

            # Dominant / sévère weather_code
            codes = [H["weather_code"][i] for i in idxs]
            # priorité “sévérité” : on prend le max du code si égalité de fréquence
            freq = Counter(codes).most_common()
            max_count = freq[0][1]
            candidates = [c for c, k in freq if k == max_count]
            dom_code = max(candidates)
            icon_text = wmo_icon_text(dom_code)
            # icon = icon_for_code(dom_code)

            precip = sum(H["precipitation"][i] or 0 for i in idxs)
            temps = [H["temperature_2m"][i] for i in idxs if H["temperature_2m"][i] is not None]
            tavg = round(sum(temps)/len(temps), 1) if temps else None

            row[f"{half_name}_icon"] = icon_text[0]
            row[f"{half_name}_text"] = icon_text[1]
            row[f"{half_name}_precip_mm"] = round(precip, 1)
            row[f"{half_name}_temp_avg"] = tavg

        out.append(row)
    return out
