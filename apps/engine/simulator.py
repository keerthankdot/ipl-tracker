from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from apps.engine.elo import compute_current_elo
from apps.engine.nrr import (
    ALL_TEAMS,
    calculate_all_standings,
    generate_scoreline,
    parse_overs,
)
from apps.engine.weights import calculate_match_probability, load_h2h

DATA_DIR = Path(__file__).parent / "data"


def load_schedule() -> dict:
    return json.loads((DATA_DIR / "ipl2026_schedule.json").read_text())


def get_completed_matches(schedule: dict) -> list[dict]:
    return [m for m in schedule["matches"] if m["status"] == "completed"]


def get_remaining_matches(schedule: dict) -> list[dict]:
    return [m for m in schedule["matches"] if m["status"] == "upcoming"]


def load_venues() -> dict:
    return json.loads((DATA_DIR / "venues.json").read_text())


def copy_standings(standings: list[dict]) -> list[dict]:
    return [dict(s) for s in standings]


def update_standings_for_match(
    standings_dict: dict,
    team1: str,
    team2: str,
    winner: str,
    bat_first: str,
    scoreline: dict,
) -> None:
    """Update standings in-place for one simulated match."""
    loser = team2 if winner == team1 else team1

    standings_dict[winner]["won"] += 1
    standings_dict[winner]["points"] += 2
    standings_dict[loser]["lost"] += 1
    standings_dict[winner]["played"] += 1
    standings_dict[loser]["played"] += 1

    # Map scoreline to team1/team2 based on who batted first
    if bat_first == team1:
        t1_runs = scoreline["bat_first_score"]
        t1_overs_str = scoreline["bat_first_overs"]
        t1_all_out = scoreline["bat_first_all_out"]
        t2_runs = scoreline["chase_score"]
        t2_overs_str = scoreline["chase_overs"]
        t2_all_out = scoreline["chase_all_out"]
    else:
        t2_runs = scoreline["bat_first_score"]
        t2_overs_str = scoreline["bat_first_overs"]
        t2_all_out = scoreline["bat_first_all_out"]
        t1_runs = scoreline["chase_score"]
        t1_overs_str = scoreline["chase_overs"]
        t1_all_out = scoreline["chase_all_out"]

    t1_overs = 20.0 if t1_all_out else parse_overs(t1_overs_str)
    t2_overs = 20.0 if t2_all_out else parse_overs(t2_overs_str)

    # Team1 NRR accumulators
    standings_dict[team1]["total_runs_scored"] += t1_runs
    standings_dict[team1]["total_overs_faced"] += t1_overs
    standings_dict[team1]["total_runs_conceded"] += t2_runs
    standings_dict[team1]["total_overs_bowled"] += t2_overs

    # Team2 NRR accumulators (mirror)
    standings_dict[team2]["total_runs_scored"] += t2_runs
    standings_dict[team2]["total_overs_faced"] += t2_overs
    standings_dict[team2]["total_runs_conceded"] += t1_runs
    standings_dict[team2]["total_overs_bowled"] += t1_overs


def rank_teams(standings_dict: dict) -> list[str]:
    """Rank teams by points DESC then NRR DESC. Returns list of team codes."""
    def sort_key(team: str):
        s = standings_dict[team]
        of = s["total_overs_faced"]
        ob = s["total_overs_bowled"]
        if of > 0 and ob > 0:
            nrr = (s["total_runs_scored"] / of) - (s["total_runs_conceded"] / ob)
        else:
            nrr = 0.0
        return (s["points"], nrr)

    return sorted(ALL_TEAMS, key=sort_key, reverse=True)


def play_match(
    team1: str, team2: str, rng: np.random.Generator, win_prob_team1: float = 0.5
) -> tuple[str, str]:
    """Returns (winner, loser) based on win probability for team1."""
    if rng.random() < win_prob_team1:
        return (team1, team2)
    return (team2, team1)


def simulate_playoffs(top4: list[str], rng: np.random.Generator) -> str:
    """Simulate IPL playoff bracket. Returns champion."""
    q1_winner, q1_loser = play_match(top4[0], top4[1], rng)
    elim_winner, _ = play_match(top4[2], top4[3], rng)
    q2_winner, _ = play_match(q1_loser, elim_winner, rng)
    champion, _ = play_match(q1_winner, q2_winner, rng)
    return champion


def simulate_one_season(
    base_standings: list[dict],
    remaining: list[dict],
    venues: dict,
    rng: np.random.Generator,
    match_probs: Optional[list[float]] = None,
    forced_outcomes: Optional[dict[int, str]] = None,
) -> tuple[list[str], str]:
    """Run one simulation of the remaining season. Returns (ranked_team_codes, champion).

    forced_outcomes: optional dict mapping match index to forced winner team code.
    """
    standings_copy = copy_standings(base_standings)
    sd = {s["team"]: s for s in standings_copy}

    for i, match in enumerate(remaining):
        venue_data = venues[match["venue"]]
        if forced_outcomes and i in forced_outcomes:
            forced_winner = forced_outcomes[i]
            winner = forced_winner
        else:
            prob = match_probs[i] if match_probs else 0.5
            winner, _ = play_match(match["team1"], match["team2"], rng, prob)
        bat_first = match["team1"] if rng.random() < 0.5 else match["team2"]
        scoreline = generate_scoreline(venue_data, rng)
        update_standings_for_match(sd, match["team1"], match["team2"], winner, bat_first, scoreline)

    ranked = rank_teams(sd)
    top4 = ranked[:4]
    champion = simulate_playoffs(top4, rng)
    return (ranked, champion)


def simulate_season(n_sims: int = 50000, seed: Optional[int] = None) -> list[dict]:
    """Top-level Monte Carlo simulation. Returns per-team probabilities."""
    schedule = load_schedule()
    completed = get_completed_matches(schedule)
    remaining = get_remaining_matches(schedule)
    venues = load_venues()

    base_standings = calculate_all_standings(completed)

    # Pre-compute weighted match probabilities (once, not per sim)
    elo_ratings = compute_current_elo(completed)
    h2h_data = load_h2h()
    match_probs = [
        calculate_match_probability(m, completed, elo_ratings, venues, h2h_data)
        for m in remaining
    ]

    counts = {team: {"top4": 0, "top2": 0, "title": 0} for team in ALL_TEAMS}
    rng = np.random.default_rng(seed)

    for _ in range(n_sims):
        ranked, champion = simulate_one_season(
            base_standings, remaining, venues, rng, match_probs
        )

        for team in ranked[:4]:
            counts[team]["top4"] += 1
        for team in ranked[:2]:
            counts[team]["top2"] += 1
        counts[champion]["title"] += 1

    results = []
    for team in ALL_TEAMS:
        results.append({
            "team": team,
            "top4_pct": round(counts[team]["top4"] / n_sims * 100, 1),
            "top2_pct": round(counts[team]["top2"] / n_sims * 100, 1),
            "title_pct": round(counts[team]["title"] / n_sims * 100, 1),
        })

    results.sort(key=lambda r: r["top4_pct"], reverse=True)
    return results


def simulate_with_forced_outcomes(
    forced: dict[str, str],
    n_sims: int = 10000,
    seed: Optional[int] = None,
) -> list[dict]:
    """Run simulation with specific match outcomes forced.

    Args:
        forced: {match_id: winner_team_code}, e.g. {"M007": "CSK"}
        n_sims: simulations to run (default 10K for interactive speed)
        seed: optional random seed
    """
    schedule = load_schedule()
    completed = get_completed_matches(schedule)
    remaining = get_remaining_matches(schedule)
    venues = load_venues()

    base_standings = calculate_all_standings(completed)
    elo_ratings = compute_current_elo(completed)
    h2h_data = load_h2h()
    match_probs = [
        calculate_match_probability(m, completed, elo_ratings, venues, h2h_data)
        for m in remaining
    ]

    # Map match_id to index
    forced_indices: dict[int, str] = {}
    for i, match in enumerate(remaining):
        if match["id"] in forced:
            forced_indices[i] = forced[match["id"]]

    counts = {team: {"top4": 0, "top2": 0, "title": 0} for team in ALL_TEAMS}
    rng = np.random.default_rng(seed)

    for _ in range(n_sims):
        ranked, champion = simulate_one_season(
            base_standings, remaining, venues, rng, match_probs, forced_indices
        )
        for team in ranked[:4]:
            counts[team]["top4"] += 1
        for team in ranked[:2]:
            counts[team]["top2"] += 1
        counts[champion]["title"] += 1

    results = []
    for team in ALL_TEAMS:
        results.append({
            "team": team,
            "top4_pct": round(counts[team]["top4"] / n_sims * 100, 1),
            "top2_pct": round(counts[team]["top2"] / n_sims * 100, 1),
            "title_pct": round(counts[team]["title"] / n_sims * 100, 1),
        })
    results.sort(key=lambda r: r["top4_pct"], reverse=True)
    return results
