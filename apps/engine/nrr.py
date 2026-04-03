from __future__ import annotations

from typing import Optional

import numpy as np

ALL_TEAMS = ["RCB", "CSK", "MI", "KKR", "SRH", "RR", "DC", "PBKS", "GT", "LSG"]


def parse_score(score_str: str) -> tuple[int, bool]:
    """Parse score string like '203/4' or '127' (all out).
    Returns (runs, is_all_out).
    """
    if "/" in score_str:
        parts = score_str.split("/")
        runs = int(parts[0])
        wickets = int(parts[1])
        return (runs, wickets == 10)
    else:
        return (int(score_str), True)


def parse_overs(overs_str: str) -> float:
    """Parse overs string like '18.2' (18 overs 2 balls) to float.
    In cricket, 1 ball = 1/6 of an over.
    """
    parts = overs_str.split(".")
    whole = int(parts[0])
    balls = int(parts[1]) if len(parts) > 1 else 0
    return whole + balls / 6.0


def extract_team_match_data(match: dict, team: str) -> dict:
    """Extract a team's NRR perspective from a completed match.
    Returns runs_scored, overs_faced, runs_conceded, overs_bowled, is_all_out.
    """
    if match["team1"] == team:
        my_score_str = match["score_team1"]
        my_overs_str = match["overs_team1"]
        opp_score_str = match["score_team2"]
        opp_overs_str = match["overs_team2"]
    elif match["team2"] == team:
        my_score_str = match["score_team2"]
        my_overs_str = match["overs_team2"]
        opp_score_str = match["score_team1"]
        opp_overs_str = match["overs_team1"]
    else:
        raise ValueError(f"{team} not in match {match['id']}")

    my_runs, my_all_out = parse_score(my_score_str)
    opp_runs, opp_all_out = parse_score(opp_score_str)

    my_overs_raw = parse_overs(my_overs_str)
    opp_overs_raw = parse_overs(opp_overs_str)

    # All-out override: team bowled out gets full 20 overs charged
    overs_faced = 20.0 if my_all_out else my_overs_raw
    overs_bowled = 20.0 if opp_all_out else opp_overs_raw

    return {
        "runs_scored": my_runs,
        "overs_faced": overs_faced,
        "runs_conceded": opp_runs,
        "overs_bowled": overs_bowled,
        "is_all_out": my_all_out,
    }


def calculate_nrr(completed_matches: list[dict], team: str) -> float:
    """Calculate cumulative NRR for a team across all completed matches."""
    team_matches = [
        m for m in completed_matches
        if m["team1"] == team or m["team2"] == team
    ]
    if not team_matches:
        return 0.0

    total_rs = 0
    total_of = 0.0
    total_rc = 0
    total_ob = 0.0

    for m in team_matches:
        data = extract_team_match_data(m, team)
        total_rs += data["runs_scored"]
        total_of += data["overs_faced"]
        total_rc += data["runs_conceded"]
        total_ob += data["overs_bowled"]

    nrr = (total_rs / total_of) - (total_rc / total_ob)
    return round(nrr, 3)


def calculate_all_standings(completed_matches: list[dict]) -> list[dict]:
    """Build full standings table from completed matches, sorted by points then NRR."""
    standings = {}
    for team in ALL_TEAMS:
        standings[team] = {
            "team": team,
            "played": 0,
            "won": 0,
            "lost": 0,
            "no_result": 0,
            "points": 0,
            "nrr": 0.0,
            "total_runs_scored": 0,
            "total_overs_faced": 0.0,
            "total_runs_conceded": 0,
            "total_overs_bowled": 0.0,
        }

    for m in completed_matches:
        t1, t2 = m["team1"], m["team2"]
        winner = m["winner"]
        loser = t2 if winner == t1 else t1

        standings[winner]["played"] += 1
        standings[winner]["won"] += 1
        standings[winner]["points"] += 2

        standings[loser]["played"] += 1
        standings[loser]["lost"] += 1

    for team in ALL_TEAMS:
        team_matches = [
            m for m in completed_matches
            if m["team1"] == team or m["team2"] == team
        ]
        total_rs = 0
        total_of = 0.0
        total_rc = 0
        total_ob = 0.0
        for m in team_matches:
            data = extract_team_match_data(m, team)
            total_rs += data["runs_scored"]
            total_of += data["overs_faced"]
            total_rc += data["runs_conceded"]
            total_ob += data["overs_bowled"]

        standings[team]["total_runs_scored"] = total_rs
        standings[team]["total_overs_faced"] = total_of
        standings[team]["total_runs_conceded"] = total_rc
        standings[team]["total_overs_bowled"] = total_ob
        standings[team]["nrr"] = calculate_nrr(completed_matches, team)

    sorted_standings = sorted(
        standings.values(),
        key=lambda s: (s["points"], s["nrr"]),
        reverse=True,
    )
    return sorted_standings


def generate_scoreline(venue_data: dict, rng: np.random.Generator) -> dict:
    """Generate a plausible T20 match scoreline based on venue stats."""
    first_innings = int(rng.normal(venue_data["avg_1st_innings"], 20))
    first_innings = max(80, min(280, first_innings))

    margin = abs(int(rng.normal(15, 20)))
    margin = max(1, min(100, margin))

    bat_first_wins = rng.random() < (venue_data["bat_first_win_pct"] / 100.0)

    if bat_first_wins:
        bat_first_score = first_innings
        chase_score = first_innings - margin
        chase_score = max(80, chase_score)
        bat_first_overs = "20.0"
        chase_all_out = bool(rng.random() < 0.25)
        chase_overs = "20.0"
        bat_first_all_out = bool(rng.random() < 0.15)
    else:
        bat_first_score = first_innings
        bat_first_overs = "20.0"
        chase_score = first_innings + 1
        # How quickly they chased
        chase_run_rate = chase_score / 20.0
        surplus_balls = int(margin / max(chase_run_rate / 6.0, 0.01))
        surplus_balls = max(1, min(60, surplus_balls))
        balls_used = 120 - surplus_balls + int(rng.normal(0, 10))
        balls_used = max(6, min(120, balls_used))
        chase_overs_int = balls_used // 6
        chase_balls = balls_used % 6
        chase_overs = f"{chase_overs_int}.{chase_balls}"
        chase_all_out = False
        bat_first_all_out = bool(rng.random() < 0.15)

    return {
        "bat_first_score": bat_first_score,
        "bat_first_overs": bat_first_overs,
        "chase_score": chase_score,
        "chase_overs": chase_overs,
        "bat_first_won": bool(bat_first_wins),
        "bat_first_all_out": bat_first_all_out,
        "chase_all_out": chase_all_out,
    }
