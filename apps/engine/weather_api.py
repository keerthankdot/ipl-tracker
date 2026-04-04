from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

IST = timezone(timedelta(hours=5, minutes=30))

VENUE_COORDS = {
    "chinnaswamy":    {"lat": 12.9788, "lon": 77.5996},
    "wankhede":       {"lat": 18.9388, "lon": 72.8258},
    "eden_gardens":   {"lat": 22.5646, "lon": 88.3433},
    "chepauk":        {"lat": 13.0627, "lon": 80.2792},
    "rajiv_gandhi":   {"lat": 17.4065, "lon": 78.5507},
    "sawai_mansingh": {"lat": 26.8929, "lon": 75.8069},
    "arun_jaitley":   {"lat": 28.6377, "lon": 77.2433},
    "narendra_modi":  {"lat": 23.0920, "lon": 72.5967},
    "ekana":          {"lat": 26.8470, "lon": 80.9953},
    "mullanpur":      {"lat": 30.7810, "lon": 76.7174},
    "dharamsala":     {"lat": 32.2190, "lon": 76.3234},
    "guwahati":       {"lat": 26.1445, "lon": 91.7362},
    "nava_raipur":    {"lat": 21.1610, "lon": 81.7870},
}

_weather_cache: dict = {}
CACHE_TTL = 6 * 3600  # 6 hours


def predict_dew(temperature_c: float, humidity_pct: int, match_time_ist: str) -> dict:
    """Predict dew conditions based on CLAUDE.md model."""
    hour = int(match_time_ist.split(":")[0])

    # Afternoon matches: no dew
    if hour < 17:
        return {
            "level": "none",
            "impact": "Afternoon match. No dew expected. Conditions should be even for both innings.",
            "is_evening_match": False,
        }

    is_evening = hour >= 19

    if is_evening and humidity_pct > 70 and temperature_c < 25:
        level = "heavy"
        impact = "Heavy dew expected. Bowling second will be extremely difficult. Ball skids on, making grip nearly impossible for spinners."
    elif is_evening and humidity_pct > 60 and temperature_c < 28:
        level = "moderate"
        impact = "Moderate dew likely after 8:30 PM. Teams bowling second will face some grip issues, especially spinners."
    elif is_evening and humidity_pct > 50:
        level = "light"
        impact = "Light dew possible in the second innings. Minimal impact on bowling."
    else:
        level = "none"
        impact = "No significant dew expected. Conditions should be even for both innings."

    return {"level": level, "impact": impact, "is_evening_match": is_evening}


def fetch_forecast(venue_key: str) -> Optional[dict]:
    """Fetch 5-day forecast from OpenWeatherMap. Caches for 6 hours."""
    cached = _weather_cache.get(venue_key)
    if cached and (time.time() - cached["fetched_at"]) < CACHE_TTL:
        return cached["data"]

    coords = VENUE_COORDS.get(venue_key)
    if not coords:
        return None

    api_key = os.environ.get("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = httpx.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": api_key,
                "units": "metric",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        _weather_cache[venue_key] = {"data": data, "fetched_at": time.time()}
        return data
    except Exception:
        return None


def get_weather_for_match(
    venue_key: str, match_date: str, match_time: str
) -> Optional[dict]:
    """Get weather forecast for a specific match. Returns None on failure."""
    forecast = fetch_forecast(venue_key)
    if not forecast or "list" not in forecast:
        return None

    match_dt_ist = datetime.fromisoformat(f"{match_date}T{match_time}:00+05:30")
    match_dt_utc = match_dt_ist.astimezone(timezone.utc)

    closest = None
    min_diff = float("inf")
    for entry in forecast["list"]:
        entry_dt = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
        diff = abs((entry_dt - match_dt_utc).total_seconds())
        if diff < min_diff:
            min_diff = diff
            closest = entry

    if not closest:
        return None

    temp_c = closest["main"]["temp"]
    humidity = closest["main"]["humidity"]
    wind_speed = closest["wind"]["speed"]
    wind_deg = closest["wind"].get("deg", 0)
    rain_prob = closest.get("pop", 0) * 100
    rain_mm = closest.get("rain", {}).get("3h", 0)
    clouds = closest.get("clouds", {}).get("all", 0)
    weather_desc = closest["weather"][0]["description"] if closest.get("weather") else "unknown"

    dew = predict_dew(temp_c, humidity, match_time)

    return {
        "temperature_c": round(temp_c, 1),
        "humidity_pct": humidity,
        "wind_speed_kmh": round(wind_speed * 3.6, 1),
        "wind_direction_deg": wind_deg,
        "rain_probability_pct": round(rain_prob, 0),
        "rain_mm": round(rain_mm, 1),
        "cloud_cover_pct": clouds,
        "description": weather_desc,
        "dew": dew,
        "forecast_for": match_dt_ist.isoformat(),
    }
