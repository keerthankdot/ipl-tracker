from __future__ import annotations

import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from apps.engine.nrr import ALL_TEAMS, calculate_all_standings
from apps.engine.simulator import (
    get_completed_matches,
    get_remaining_matches,
    load_schedule,
    load_venues,
    simulate_season,
)

app = FastAPI(
    title="Win Path Engine",
    description="IPL qualification path simulation engine by Ascnd Technologies",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://winpath.ascnd.in",
        "https://ipl-tracker-mu.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IST = timezone(timedelta(hours=5, minutes=30))

_sim_cache: dict = {
    "key": None,
    "results": None,
    "generated_at": None,
    "elapsed": None,
}


def _now_ist() -> str:
    return datetime.now(IST).isoformat()


def _cache_key(completed: list[dict]) -> str:
    ids = sorted(m["id"] for m in completed)
    return hashlib.md5(",".join(ids).encode()).hexdigest()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/standings")
def standings():
    schedule = load_schedule()
    completed = get_completed_matches(schedule)
    all_standings = calculate_all_standings(completed)

    return {
        "standings": [
            {
                "rank": i + 1,
                "team": s["team"],
                "played": s["played"],
                "won": s["won"],
                "lost": s["lost"],
                "no_result": s["no_result"],
                "points": s["points"],
                "nrr": s["nrr"],
            }
            for i, s in enumerate(all_standings)
        ],
        "last_updated": _now_ist(),
        "matches_completed": len(completed),
        "matches_remaining": 70 - len(completed),
    }


@app.get("/api/schedule")
def schedule(
    team: Optional[str] = Query(None, description="Filter by team code (e.g., RCB)"),
    status: Optional[str] = Query(None, description="Filter by status: completed, upcoming"),
):
    data = load_schedule()
    matches = data["matches"]

    if team:
        team_upper = team.upper()
        matches = [
            m for m in matches
            if m.get("team1") == team_upper or m.get("team2") == team_upper
        ]

    if status:
        matches = [m for m in matches if m["status"] == status]

    return {
        "matches": matches,
        "total": len(data["matches"]),
        "filtered": len(matches),
    }


@app.post("/api/simulate")
def simulate(n_simulations: int = 50000):
    sched = load_schedule()
    completed = get_completed_matches(sched)

    key = _cache_key(completed)
    if _sim_cache["key"] == key and _sim_cache["results"] is not None:
        return {
            "results": _sim_cache["results"],
            "simulations_run": n_simulations,
            "elapsed_seconds": _sim_cache["elapsed"],
            "based_on_matches": len(completed),
            "generated_at": _sim_cache["generated_at"],
            "cached": True,
        }

    start = time.time()
    results = simulate_season(n_sims=n_simulations)
    elapsed = round(time.time() - start, 1)

    _sim_cache["key"] = key
    _sim_cache["results"] = results
    _sim_cache["elapsed"] = elapsed
    _sim_cache["generated_at"] = _now_ist()

    return {
        "results": results,
        "simulations_run": n_simulations,
        "elapsed_seconds": elapsed,
        "based_on_matches": len(completed),
        "generated_at": _sim_cache["generated_at"],
        "cached": False,
    }
