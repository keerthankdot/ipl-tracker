from __future__ import annotations

import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from apps.engine.elo import compute_current_elo
from apps.engine.nrr import ALL_TEAMS, calculate_all_standings
from apps.engine.simulator import (
    get_completed_matches,
    get_remaining_matches,
    load_schedule,
    load_venues,
    simulate_season,
    simulate_with_forced_outcomes,
)
from apps.engine.weights import calculate_match_probability, load_h2h

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

_impact_cache: dict = {}


class ImpactRequest(BaseModel):
    match_id: str
    n_simulations: int = 10000


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


@app.post("/api/impact")
def impact(req: ImpactRequest):
    sched = load_schedule()
    completed = get_completed_matches(sched)
    remaining = get_remaining_matches(sched)

    target = next((m for m in remaining if m["id"] == req.match_id), None)
    if not target:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"error": f"Match {req.match_id} not found or already completed"},
        )

    # Check cache
    key = _cache_key(completed)
    impact_key = (key, req.match_id)
    if impact_key in _impact_cache:
        return _impact_cache[impact_key]

    # Baseline
    baseline = simulate_season(n_sims=req.n_simulations)

    # Scenario A: team1 wins
    scenario_a = simulate_with_forced_outcomes(
        forced={req.match_id: target["team1"]}, n_sims=req.n_simulations
    )

    # Scenario B: team2 wins
    scenario_b = simulate_with_forced_outcomes(
        forced={req.match_id: target["team2"]}, n_sims=req.n_simulations
    )

    baseline_map = {r["team"]: r["top4_pct"] for r in baseline}
    scenario_a_map = {r["team"]: r["top4_pct"] for r in scenario_a}
    scenario_b_map = {r["team"]: r["top4_pct"] for r in scenario_b}

    impact_list = []
    for team in ALL_TEAMS:
        delta_a = round(scenario_a_map[team] - baseline_map[team], 1)
        delta_b = round(scenario_b_map[team] - baseline_map[team], 1)
        impact_list.append({
            "team": team,
            "if_team1_wins": delta_a,
            "if_team2_wins": delta_b,
            "most_affected": abs(delta_a) > 3 or abs(delta_b) > 3,
        })
    impact_list.sort(
        key=lambda x: max(abs(x["if_team1_wins"]), abs(x["if_team2_wins"])),
        reverse=True,
    )

    # Match win probability
    elo_ratings = compute_current_elo(completed)
    h2h_data = load_h2h()
    venues = load_venues()
    win_prob = calculate_match_probability(target, completed, elo_ratings, venues, h2h_data)

    result = {
        "match": {
            "id": target["id"],
            "team1": target["team1"],
            "team2": target["team2"],
            "date": target["date"],
            "venue": target["venue"],
            "team1_win_pct": round(win_prob * 100, 1),
            "team2_win_pct": round((1 - win_prob) * 100, 1),
        },
        "baseline": baseline,
        "if_team1_wins": scenario_a,
        "if_team2_wins": scenario_b,
        "impact": impact_list,
        "simulations_run": req.n_simulations,
        "generated_at": _now_ist(),
    }

    _impact_cache[impact_key] = result
    return result
