from __future__ import annotations

import json
from pathlib import Path

from apps.engine.nrr import ALL_TEAMS, parse_score

DATA_DIR = Path(__file__).parent / "data"

K_FACTOR = 32


def load_initial_elo() -> dict[str, float]:
    """Load seed Elo ratings from team_ratings.json."""
    data = json.loads((DATA_DIR / "team_ratings.json").read_text())
    return {team: data[team]["elo"] for team in ALL_TEAMS}


def expected_score(rating_a: float, rating_b: float) -> float:
    """Standard Elo expected score for player A."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def margin_multiplier(match: dict) -> float:
    """Calculate margin multiplier from match scorelines."""
    if not match.get("score_team1") or not match.get("score_team2"):
        return 1.0
    runs1, _ = parse_score(match["score_team1"])
    runs2, _ = parse_score(match["score_team2"])
    margin = abs(runs1 - runs2)
    if margin > 50:
        return 1.5
    elif margin > 30:
        return 1.3
    elif margin > 15:
        return 1.1
    return 1.0


def update_elo(
    winner_elo: float, loser_elo: float, margin_mult: float = 1.0
) -> tuple[float, float]:
    """Update Elo ratings after a match. Returns (new_winner_elo, new_loser_elo)."""
    exp = expected_score(winner_elo, loser_elo)
    change = K_FACTOR * margin_mult * (1.0 - exp)
    return (winner_elo + change, loser_elo - change)


def compute_current_elo(completed_matches: list[dict]) -> dict[str, float]:
    """Process all completed matches in order and return current Elo ratings."""
    ratings = load_initial_elo()
    sorted_matches = sorted(completed_matches, key=lambda m: m["date"])
    for match in sorted_matches:
        winner = match["winner"]
        loser = match["team2"] if winner == match["team1"] else match["team1"]
        mm = margin_multiplier(match)
        new_w, new_l = update_elo(ratings[winner], ratings[loser], mm)
        ratings[winner] = new_w
        ratings[loser] = new_l
    return ratings
