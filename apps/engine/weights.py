from __future__ import annotations

import json
from pathlib import Path

from apps.engine.elo import expected_score

DATA_DIR = Path(__file__).parent / "data"

TEAM_HOME_CITIES: dict[str, list[str]] = {
    "RCB": ["Bengaluru"],
    "CSK": ["Chennai"],
    "MI": ["Mumbai"],
    "KKR": ["Kolkata"],
    "SRH": ["Hyderabad"],
    "RR": ["Jaipur", "Guwahati"],
    "DC": ["Delhi"],
    "PBKS": ["Mullanpur (New Chandigarh)", "Dharamsala"],
    "GT": ["Ahmedabad"],
    "LSG": ["Lucknow"],
}


def load_h2h() -> dict:
    """Load head-to-head records."""
    return json.loads((DATA_DIR / "h2h.json").read_text())


def venue_advantage(team1: str, team2: str, venue_data: dict) -> float:
    """Returns adjustment for team1 based on home advantage.
    +0.05 if team1 is home, -0.05 if team2 is home, 0.0 neutral.
    """
    city = venue_data["city"]
    t1_home = city in TEAM_HOME_CITIES.get(team1, [])
    t2_home = city in TEAM_HOME_CITIES.get(team2, [])
    if t1_home:
        return 0.05
    elif t2_home:
        return -0.05
    return 0.0


def calculate_form(completed_matches: list[dict], team: str, window: int = 5) -> float:
    """Calculate form score from last N matches. Returns float in [-0.15, +0.15]."""
    team_matches = [
        m for m in completed_matches
        if (m["team1"] == team or m["team2"] == team) and m["status"] == "completed"
    ]
    recent = sorted(team_matches, key=lambda m: m["date"], reverse=True)[:window]
    if not recent:
        return 0.0

    form_score = 0.0
    for match in recent:
        if match["winner"] == team:
            form_score += 0.02
        else:
            form_score -= 0.02

    # Win streak bonus
    streak = 0
    for match in recent:
        if match["winner"] == team:
            streak += 1
        else:
            break
    if streak >= 3:
        form_score += 0.03

    # Loss streak penalty
    loss_streak = 0
    for match in recent:
        if match["winner"] != team:
            loss_streak += 1
        else:
            break
    if loss_streak >= 3:
        form_score -= 0.03

    return max(-0.15, min(0.15, form_score))


def get_h2h_probability(h2h_data: dict, team1: str, team2: str) -> float:
    """Get H2H win probability for team1 vs team2."""
    # Keys are alphabetical
    teams_sorted = sorted([team1, team2])
    key = f"{teams_sorted[0]}_vs_{teams_sorted[1]}"
    record = h2h_data.get(key)
    if not record or record["total"] == 0:
        return 0.5

    if teams_sorted[0] == team1:
        return record["team1_wins"] / record["total"]
    else:
        return record["team2_wins"] / record["total"]


def calculate_match_probability(
    match: dict,
    completed_matches: list[dict],
    elo_ratings: dict,
    venues: dict,
    h2h_data: dict,
) -> float:
    """Calculate win probability for team1. Returns float in [0.20, 0.80]."""
    team1 = match["team1"]
    team2 = match["team2"]

    # 1. Elo component (40%)
    elo_prob = expected_score(elo_ratings[team1], elo_ratings[team2])

    # 2. Venue component (20%)
    venue_data = venues.get(match["venue"], {})
    home_adj = venue_advantage(team1, team2, venue_data) if venue_data else 0.0
    venue_prob = 0.5 + home_adj

    # 3. Form component (25%)
    form1 = calculate_form(completed_matches, team1)
    form2 = calculate_form(completed_matches, team2)
    form_prob = 0.5 + (form1 - form2)
    form_prob = max(0.3, min(0.7, form_prob))

    # 4. H2H component (5%)
    h2h_prob = get_h2h_probability(h2h_data, team1, team2)

    # 5. Combine
    combined = (
        0.40 * elo_prob
        + 0.20 * venue_prob
        + 0.25 * form_prob
        + 0.05 * h2h_prob
        + 0.10 * 0.5
    )

    # 6. Clamp
    return max(0.20, min(0.80, combined))
