from __future__ import annotations

import math


def float_to_cricket_overs(overs_float: float) -> str:
    """Convert float overs (e.g. 16.333) to cricket notation (e.g. '16.2')."""
    whole = int(overs_float)
    balls = round((overs_float - whole) * 6)
    if balls >= 6:
        whole += 1
        balls = 0
    return f"{whole}.{balls}"


def calculate_nrr_bat_first(
    rs: int, of: float, rc: int, ob: float,
    target_nrr: float, venue_avg: int,
) -> dict:
    """Calculate what team needs batting first to reach target_nrr.

    Assumes: team bats 20 overs, opponent scores venue_avg in 20 overs.
    Returns: min team score, margin needed, resulting NRR.
    """
    opp_score = venue_avg
    new_of = of + 20.0
    new_ob = ob + 20.0

    # target_nrr <= (rs + team_score) / new_of - (rc + opp_score) / new_ob
    # team_score >= target_nrr * new_of + (rc + opp_score) / new_ob * new_of - rs
    # Simplify: team_score >= target_nrr * new_of + (rc + opp_score) * new_of / new_ob - rs
    rhs = (rc + opp_score) / new_ob
    min_score = math.ceil(target_nrr * new_of + rhs * new_of - rs)
    min_score = max(min_score, opp_score + 1)  # must at least beat opponent

    margin = min_score - opp_score
    resulting_nrr = (rs + min_score) / new_of - (rc + opp_score) / new_ob

    return {
        "min_team_score": min_score,
        "opponent_score": opp_score,
        "min_margin_runs": margin,
        "resulting_nrr": round(resulting_nrr, 3),
    }


def calculate_nrr_chase(
    rs: int, of: float, rc: int, ob: float,
    target_nrr: float, venue_avg: int,
) -> dict:
    """Calculate max overs to chase in to reach target_nrr.

    Assumes: opponent scores venue_avg in 20 overs, team chases venue_avg+1.
    Returns: max overs allowed, resulting NRR.
    """
    opp_score = venue_avg
    chase_score = opp_score + 1
    new_ob = ob + 20.0
    rhs = (rc + opp_score) / new_ob

    # target_nrr <= (rs + chase_score) / (of + max_overs) - rhs
    # of + max_overs <= (rs + chase_score) / (target_nrr + rhs)
    denominator = target_nrr + rhs
    if denominator <= 0:
        return {
            "chase_score": chase_score,
            "opponent_score": opp_score,
            "max_overs": "20.0",
            "max_overs_float": 20.0,
            "resulting_nrr": round((rs + chase_score) / (of + 20.0) - rhs, 3),
        }

    max_of_total = (rs + chase_score) / denominator
    max_overs = max_of_total - of

    max_overs = max(0.1, min(20.0, max_overs))
    # Floor to nearest ball (team needs to finish within this)
    max_overs_balls = int(max_overs) * 6 + int((max_overs % 1) * 6)
    max_overs_clamped = max_overs_balls // 6 + (max_overs_balls % 6) / 6.0

    resulting_nrr = (rs + chase_score) / (of + max_overs_clamped) - rhs

    return {
        "chase_score": chase_score,
        "opponent_score": opp_score,
        "max_overs": float_to_cricket_overs(max_overs_clamped),
        "max_overs_float": round(max_overs_clamped, 4),
        "resulting_nrr": round(resulting_nrr, 3),
    }


def calculate_loss_impact(
    rs: int, of: float, rc: int, ob: float,
    venue_avg: int, loss_margin: int = 30,
) -> float:
    """Calculate NRR after a loss by given margin.

    Assumes: opponent scores venue_avg, team scores venue_avg - margin, both 20 overs.
    """
    team_score = max(50, venue_avg - loss_margin)
    new_rs = rs + team_score
    new_of = of + 20.0
    new_rc = rc + venue_avg
    new_ob = ob + 20.0
    return round(new_rs / new_of - new_rc / new_ob, 3)


def classify_feasibility(margin_runs: int, max_overs_float: float) -> str:
    """Classify how feasible a target is."""
    # Bat first: by margin
    if margin_runs <= 0:
        return "comfortable"
    if margin_runs <= 15:
        return "achievable"
    if margin_runs <= 35:
        return "difficult"
    return "unlikely"


def classify_chase_feasibility(max_overs_float: float) -> str:
    """Classify chase feasibility by overs available."""
    if max_overs_float >= 19.0:
        return "comfortable"
    if max_overs_float >= 17.0:
        return "achievable"
    if max_overs_float >= 14.0:
        return "difficult"
    return "unlikely"


def generate_nrr_strategy(
    team: str,
    standings: list[dict],
    next_match: dict,
    venue_avg: int,
) -> dict:
    """Generate full NRR strategy for a team's next match."""
    my = next((s for s in standings if s["team"] == team), None)
    if not my:
        return {"scenarios": []}

    rs = my["total_runs_scored"]
    of = my["total_overs_faced"]
    rc = my["total_runs_conceded"]
    ob = my["total_overs_bowled"]

    # Sort by NRR for ranking
    by_nrr = sorted(standings, key=lambda s: s["nrr"], reverse=True)
    nrr_rank = next(i + 1 for i, s in enumerate(by_nrr) if s["team"] == team)

    scenarios = []

    # 1. Overtake team above
    if nrr_rank > 1:
        above = by_nrr[nrr_rank - 2]
        bat = calculate_nrr_bat_first(rs, of, rc, ob, above["nrr"], venue_avg)
        chase = calculate_nrr_chase(rs, of, rc, ob, above["nrr"], venue_avg)
        feasibility = classify_feasibility(bat["min_margin_runs"], 0)
        chase_feas = classify_chase_feasibility(chase["max_overs_float"])
        # Use the easier of the two
        feas_order = ["comfortable", "achievable", "difficult", "unlikely"]
        overall = feas_order[min(feas_order.index(feasibility), feas_order.index(chase_feas))]

        scenarios.append({
            "target": "overtake_above",
            "target_team": above["team"],
            "target_nrr": above["nrr"],
            "bat_first": {
                "description": f"Bat first: score {bat['min_team_score']}+, restrict opponent to under {bat['opponent_score']}",
                "min_margin_runs": bat["min_margin_runs"],
                "resulting_nrr": bat["resulting_nrr"],
            },
            "chase": {
                "description": f"Chase: finish in under {chase['max_overs']} overs",
                "max_overs": chase["max_overs"],
                "resulting_nrr": chase["resulting_nrr"],
            },
            "feasibility": overall,
        })

    # 2. Maintain position (stay above team below)
    if nrr_rank < len(by_nrr):
        below = by_nrr[nrr_rank]
        bat = calculate_nrr_bat_first(rs, of, rc, ob, below["nrr"], venue_avg)
        chase = calculate_nrr_chase(rs, of, rc, ob, below["nrr"], venue_avg)
        feasibility = classify_feasibility(bat["min_margin_runs"], 0)
        chase_feas = classify_chase_feasibility(chase["max_overs_float"])
        feas_order = ["comfortable", "achievable", "difficult", "unlikely"]
        overall = feas_order[min(feas_order.index(feasibility), feas_order.index(chase_feas))]

        scenarios.append({
            "target": "maintain_position",
            "target_team": below["team"],
            "target_nrr": below["nrr"],
            "bat_first": {
                "description": f"Bat first: any win of {bat['min_margin_runs']}+ runs keeps you above {below['team']}" if bat["min_margin_runs"] > 0 else f"Bat first: any win keeps you above {below['team']}",
                "min_margin_runs": bat["min_margin_runs"],
                "resulting_nrr": bat["resulting_nrr"],
            },
            "chase": {
                "description": f"Chase: finish in under {chase['max_overs']} overs to stay above {below['team']}",
                "max_overs": chase["max_overs"],
                "resulting_nrr": chase["resulting_nrr"],
            },
            "feasibility": overall,
        })

    # 3. Loss scenario
    loss_nrr = calculate_loss_impact(rs, of, rc, ob, venue_avg, 30)
    loss_rank = sum(1 for s in by_nrr if s["nrr"] > loss_nrr and s["team"] != team) + 1

    scenarios.append({
        "target": "loss_scenario",
        "description": f"If you lose by 30+ runs, your NRR drops to {loss_nrr:+.3f}",
        "worst_case_nrr": loss_nrr,
        "resulting_rank": loss_rank,
    })

    opponent = next_match["team2"] if next_match["team1"] == team else next_match["team1"]

    return {
        "team": team,
        "current_nrr": my["nrr"],
        "nrr_rank": nrr_rank,
        "next_match": {
            "id": next_match["id"],
            "opponent": opponent,
            "venue": next_match["venue"],
            "venue_avg_1st": venue_avg,
        },
        "scenarios": scenarios,
    }
