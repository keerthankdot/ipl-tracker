from __future__ import annotations


def classify_match(win_prob: float, impact_pct: float, team_top4_pct: float) -> str:
    """Classify a match from a team's perspective.

    Returns one of: MUST_WIN, FAVORED, TOSS_UP, TOUGH, UPSET_NEEDED
    """
    # MUST_WIN overrides probability-based classification
    if impact_pct > 8.0:
        return "MUST_WIN"
    if impact_pct > 5.0 and team_top4_pct < 55.0:
        return "MUST_WIN"

    # Probability-based
    if win_prob >= 0.60:
        return "FAVORED"
    if win_prob >= 0.45:
        return "TOSS_UP"
    if win_prob >= 0.30:
        return "TOUGH"
    return "UPSET_NEEDED"


def estimate_impact(
    team: str,
    match: dict,
    standings_dict: dict,
    remaining_count: int,
) -> float:
    """Estimate how much this match impacts the team's Top 4 qualification.

    Heuristic based on urgency, scarcity, and current position.
    Returns estimated impact as a percentage (0.0 to 25.0).
    """
    if remaining_count == 0:
        return 0.0

    current_points = standings_dict.get(team, {}).get("points", 0)
    target_points = 16  # Historical safe qualification threshold
    points_needed = max(0, target_points - current_points)

    # Base impact: each match worth ~100/matches_left percentage points
    base_impact = 100.0 / max(remaining_count, 1)

    # Urgency: team far from target = each match more critical
    urgency = points_needed / max(remaining_count * 2, 1)
    urgency_factor = min(2.0, 0.5 + urgency)

    # Scarcity: fewer matches left = higher impact each
    scarcity_factor = 1.0 + (14 - remaining_count) * 0.1

    impact = base_impact * urgency_factor * scarcity_factor
    return round(min(25.0, impact), 1)
