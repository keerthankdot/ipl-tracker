from __future__ import annotations

import hashlib
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path as _Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(_Path(__file__).parent / ".env")

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from apps.engine.classifier import classify_match, estimate_impact
from apps.engine.nrr_strategy import generate_nrr_strategy
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
from apps.engine.weights import TEAM_HOME_CITIES, calculate_match_probability, load_h2h

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


class ScenarioOutcome(BaseModel):
    match_id: str
    winner: str


class ScenarioRequest(BaseModel):
    outcomes: list[ScenarioOutcome]
    n_simulations: int = 5000


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


@app.post("/api/scenario")
def scenario(req: ScenarioRequest):
    sched = load_schedule()
    completed = get_completed_matches(sched)
    remaining = get_remaining_matches(sched)

    remaining_ids = {m["id"] for m in remaining}
    for outcome in req.outcomes:
        if outcome.match_id not in remaining_ids:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={"error": f"Match {outcome.match_id} not found in upcoming matches"},
            )

    forced = {o.match_id: o.winner for o in req.outcomes}

    baseline = simulate_season(n_sims=req.n_simulations)

    if not forced:
        return {
            "results": baseline,
            "baseline": baseline,
            "deltas": [{"team": t, "top4_delta": 0.0, "top2_delta": 0.0, "title_delta": 0.0} for t in ALL_TEAMS],
            "forced_count": 0,
            "simulations_run": req.n_simulations,
            "generated_at": _now_ist(),
        }

    scenario_results = simulate_with_forced_outcomes(
        forced=forced, n_sims=req.n_simulations
    )

    baseline_map = {r["team"]: r for r in baseline}
    scenario_map = {r["team"]: r for r in scenario_results}

    deltas = []
    for team in ALL_TEAMS:
        deltas.append({
            "team": team,
            "top4_delta": round(scenario_map[team]["top4_pct"] - baseline_map[team]["top4_pct"], 1),
            "top2_delta": round(scenario_map[team]["top2_pct"] - baseline_map[team]["top2_pct"], 1),
            "title_delta": round(scenario_map[team]["title_pct"] - baseline_map[team]["title_pct"], 1),
        })
    deltas.sort(key=lambda d: abs(d["top4_delta"]), reverse=True)

    return {
        "results": scenario_results,
        "baseline": baseline,
        "deltas": deltas,
        "forced_count": len(forced),
        "simulations_run": req.n_simulations,
        "generated_at": _now_ist(),
    }


@app.get("/api/winpath/{team}")
def winpath(team: str):
    team_upper = team.upper()
    if team_upper not in ALL_TEAMS:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": f"Unknown team: {team}"})

    sched = load_schedule()
    completed = get_completed_matches(sched)
    remaining = get_remaining_matches(sched)
    venues = load_venues()

    sim_results = simulate_season(n_sims=50000)
    team_result = next(r for r in sim_results if r["team"] == team_upper)
    team_top4 = team_result["top4_pct"]

    elo_ratings = compute_current_elo(completed)
    h2h_data = load_h2h()
    standings = calculate_all_standings(completed)
    standings_dict = {s["team"]: s for s in standings}

    all_team_matches = [
        m for m in sched["matches"]
        if m.get("team1") == team_upper or m.get("team2") == team_upper
    ]
    team_remaining = [m for m in all_team_matches if m["status"] == "upcoming"]

    match_list = []
    for m in all_team_matches:
        opponent = m["team2"] if m["team1"] == team_upper else m["team1"]
        venue_data = venues.get(m["venue"], {})
        is_home = venue_data.get("city", "") in TEAM_HOME_CITIES.get(team_upper, [])

        if m["status"] == "completed":
            won = m.get("winner") == team_upper
            score = f"{m.get('score_team1', '?')} ({m.get('overs_team1', '?')}) vs {m.get('score_team2', '?')} ({m.get('overs_team2', '?')})"
            match_list.append({
                "id": m["id"], "match_number": m["match_number"],
                "date": m["date"], "time": m["time"],
                "opponent": opponent, "venue": m["venue"],
                "venue_name": venue_data.get("name", m["venue"]),
                "venue_city": venue_data.get("city", ""),
                "is_home": is_home, "status": "completed",
                "result": "won" if won else "lost", "score": score,
                "win_prob": None, "impact": None, "classification": None,
            })
        else:
            win_prob = calculate_match_probability(m, completed, elo_ratings, venues, h2h_data)
            if m["team1"] != team_upper:
                win_prob = 1.0 - win_prob
            impact_val = estimate_impact(team_upper, m, standings_dict, len(team_remaining))
            classification = classify_match(win_prob, impact_val, team_top4)
            match_list.append({
                "id": m["id"], "match_number": m["match_number"],
                "date": m["date"], "time": m["time"],
                "opponent": opponent, "venue": m["venue"],
                "venue_name": venue_data.get("name", m["venue"]),
                "venue_city": venue_data.get("city", ""),
                "is_home": is_home, "status": "upcoming",
                "result": None, "score": None,
                "win_prob": round(win_prob, 3),
                "impact": impact_val,
                "classification": classification,
            })

    match_list.sort(key=lambda m: m["date"])
    upcoming = [m for m in match_list if m["status"] == "upcoming"]
    completed_team = [m for m in match_list if m["status"] == "completed"]

    return {
        "team": team_upper,
        "team_top4_pct": team_top4,
        "matches": match_list,
        "summary": {
            "matches_played": len(completed_team),
            "matches_remaining": len(upcoming),
            "wins": sum(1 for m in completed_team if m["result"] == "won"),
            "losses": sum(1 for m in completed_team if m["result"] == "lost"),
            "must_wins": sum(1 for m in upcoming if m["classification"] == "MUST_WIN"),
            "favored": sum(1 for m in upcoming if m["classification"] == "FAVORED"),
            "toss_ups": sum(1 for m in upcoming if m["classification"] == "TOSS_UP"),
            "tough": sum(1 for m in upcoming if m["classification"] == "TOUGH"),
            "upset_needed": sum(1 for m in upcoming if m["classification"] == "UPSET_NEEDED"),
        },
        "generated_at": _now_ist(),
    }


@app.get("/api/nrr-strategy/{team}")
def nrr_strategy(team: str):
    team_upper = team.upper()
    if team_upper not in ALL_TEAMS:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": f"Unknown team: {team}"})

    sched = load_schedule()
    completed = get_completed_matches(sched)
    remaining = get_remaining_matches(sched)
    venues = load_venues()

    standings = calculate_all_standings(completed)

    team_remaining = [
        m for m in remaining
        if m["team1"] == team_upper or m["team2"] == team_upper
    ]
    if not team_remaining:
        return {"team": team_upper, "scenarios": [], "generated_at": _now_ist()}

    next_match = team_remaining[0]
    venue_data = venues.get(next_match["venue"], {})
    venue_avg = venue_data.get("avg_1st_innings", 165)

    result = generate_nrr_strategy(team_upper, standings, next_match, venue_avg)
    result["generated_at"] = _now_ist()
    return result


@app.get("/api/match-detail/{match_id}/{team}")
def match_detail(match_id: str, team: str):
    from fastapi.responses import JSONResponse

    team_upper = team.upper()
    if team_upper not in ALL_TEAMS:
        return JSONResponse(status_code=404, content={"error": f"Unknown team: {team}"})

    sched = load_schedule()
    completed = get_completed_matches(sched)
    remaining = get_remaining_matches(sched)
    venues = load_venues()

    # Find the match
    all_matches = sched["matches"]
    match = next((m for m in all_matches if m["id"] == match_id), None)
    if not match:
        return JSONResponse(status_code=404, content={"error": f"Match {match_id} not found"})

    if match.get("team1") != team_upper and match.get("team2") != team_upper:
        return JSONResponse(status_code=400, content={"error": f"{team_upper} is not playing in {match_id}"})

    opponent = match["team2"] if match["team1"] == team_upper else match["team1"]
    venue_key = match["venue"]
    venue_data = venues.get(venue_key, {})
    is_home = venue_data.get("city", "") in TEAM_HOME_CITIES.get(team_upper, [])

    # Venue intelligence
    venue_intel = {
        "name": venue_data.get("name", venue_key),
        "city": venue_data.get("city", ""),
        "capacity": venue_data.get("capacity"),
        "avg_1st_innings": venue_data.get("avg_1st_innings", 165),
        "avg_2nd_innings": venue_data.get("avg_2nd_innings", 155),
        "bat_first_win_pct": venue_data.get("bat_first_win_pct", 50),
        "chase_win_pct": venue_data.get("chase_win_pct", 50),
        "pace_wicket_pct": venue_data.get("pace_wicket_pct", 50),
        "spin_wicket_pct": venue_data.get("spin_wicket_pct", 50),
        "dew_factor": venue_data.get("dew_factor", "moderate"),
        "altitude_m": venue_data.get("altitude_m"),
        "boundary_avg_m": venue_data.get("boundary_avg_m"),
        "notes": venue_data.get("notes", ""),
    }

    # Toss analysis: derive from venue bat-first/chase stats
    toss_analysis = {
        "bat_first_win_pct": venue_data.get("bat_first_win_pct", 50),
        "chase_win_pct": venue_data.get("chase_win_pct", 50),
        "recommendation": "Bowl first" if venue_data.get("chase_win_pct", 50) > 52 else "Bat first" if venue_data.get("bat_first_win_pct", 50) > 52 else "No clear advantage",
        "dew_factor": venue_data.get("dew_factor", "moderate"),
    }

    # H2H
    h2h_data = load_h2h()
    teams_sorted = sorted([team_upper, opponent])
    h2h_key = f"{teams_sorted[0]}_vs_{teams_sorted[1]}"
    h2h_record = h2h_data.get(h2h_key, {"team1_wins": 0, "team2_wins": 0, "total": 0})
    if teams_sorted[0] == team_upper:
        my_wins = h2h_record["team1_wins"]
        opp_wins = h2h_record["team2_wins"]
    else:
        my_wins = h2h_record["team2_wins"]
        opp_wins = h2h_record["team1_wins"]

    h2h = {
        "my_wins": my_wins,
        "opponent_wins": opp_wins,
        "total": h2h_record["total"],
        "my_win_pct": round(my_wins / h2h_record["total"] * 100, 1) if h2h_record["total"] > 0 else 50.0,
    }

    # Win probability
    win_prob = None
    impact_data = None
    classification = None
    if match["status"] == "upcoming":
        elo_ratings = compute_current_elo(completed)
        wp = calculate_match_probability(match, completed, elo_ratings, venues, h2h_data)
        if match["team1"] != team_upper:
            wp = 1.0 - wp
        win_prob = round(wp, 3)

        # Impact (lightweight: use the estimate, not full sim)
        standings = calculate_all_standings(completed)
        standings_dict = {s["team"]: s for s in standings}
        team_remaining_count = sum(
            1 for m in remaining
            if m["team1"] == team_upper or m["team2"] == team_upper
        )
        from apps.engine.classifier import classify_match, estimate_impact
        impact_val = estimate_impact(team_upper, match, standings_dict, team_remaining_count)

        sim_results = simulate_season(n_sims=50000)
        team_top4 = next(r for r in sim_results if r["team"] == team_upper)["top4_pct"]
        classification = classify_match(wp, impact_val, team_top4)
        impact_data = {"impact_pct": impact_val, "team_top4_pct": team_top4}

    # Completed match result
    result_data = None
    if match["status"] == "completed":
        won = match.get("winner") == team_upper
        result_data = {
            "result": "won" if won else "lost",
            "score_team1": match.get("score_team1"),
            "overs_team1": match.get("overs_team1"),
            "score_team2": match.get("score_team2"),
            "overs_team2": match.get("overs_team2"),
            "winner": match.get("winner"),
        }

    # Weather forecast (upcoming matches only)
    weather_data = None
    if match["status"] == "upcoming":
        from apps.engine.weather_api import get_weather_for_match
        weather_data = get_weather_for_match(venue_key, match["date"], match["time"])

    # Player form
    from apps.engine.cricket_api import get_match_players
    players = get_match_players(team_upper, opponent)

    return {
        "match_id": match_id,
        "team": team_upper,
        "opponent": opponent,
        "date": match["date"],
        "time": match["time"],
        "status": match["status"],
        "is_home": is_home,
        "win_prob": win_prob,
        "classification": classification,
        "impact": impact_data,
        "result": result_data,
        "venue": venue_intel,
        "toss": toss_analysis,
        "h2h": h2h,
        "weather": weather_data,
        "players": players,
        "generated_at": _now_ist(),
    }
