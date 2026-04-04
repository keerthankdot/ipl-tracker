from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"


def load_players() -> dict:
    """Load player stats from players.json."""
    path = DATA_DIR / "players.json"
    if not path.exists():
        return {"players": {}, "team_squads": {}}
    return json.loads(path.read_text())


def compute_player_summary(player: dict) -> dict:
    """Compute summary stats from recent matches."""
    role = player.get("role", "batter")
    matches = player.get("recent_matches", [])

    if not matches:
        return {"batting": None, "bowling": None}

    batting_summary = None
    bowling_summary = None

    if role in ("batter", "allrounder"):
        total_runs = 0
        total_balls = 0
        innings = 0
        for m in matches:
            batting = m if "runs" in m else m.get("batting", {})
            if batting and batting.get("runs") is not None:
                total_runs += batting["runs"]
                total_balls += batting.get("balls", 0)
                innings += 1
        if innings > 0:
            batting_summary = {
                "innings": innings,
                "total_runs": total_runs,
                "avg": round(total_runs / innings, 1),
                "strike_rate": round(total_runs / max(total_balls, 1) * 100, 1) if total_balls > 0 else 0,
            }

    if role in ("bowler", "allrounder"):
        total_wickets = 0
        total_rc = 0
        total_overs = 0.0
        bowling_innings = 0
        for m in matches:
            bowling = m if "wickets" in m else m.get("bowling", {})
            if bowling and bowling.get("wickets") is not None:
                total_wickets += bowling["wickets"]
                total_rc += bowling.get("runs_conceded", 0)
                overs_str = str(bowling.get("overs", "0"))
                parts = overs_str.split(".")
                total_overs += int(parts[0]) + (int(parts[1]) / 6 if len(parts) > 1 else 0)
                bowling_innings += 1
        if bowling_innings > 0:
            bowling_summary = {
                "innings": bowling_innings,
                "wickets": total_wickets,
                "economy": round(total_rc / max(total_overs, 0.1), 2),
                "avg": round(total_rc / total_wickets, 1) if total_wickets > 0 else None,
            }

    return {"batting": batting_summary, "bowling": bowling_summary}


def get_team_players(team: str) -> list[dict]:
    """Get key players and their recent form for a team."""
    data = load_players()
    squad_keys = data.get("team_squads", {}).get(team, [])
    players = []
    for key in squad_keys:
        player = data.get("players", {}).get(key)
        if player:
            summary = compute_player_summary(player)
            players.append({
                "id": key,
                "name": player["name"],
                "team": player["team"],
                "role": player["role"],
                "matches_played": len(player.get("recent_matches", [])),
                "summary": summary,
            })
    return players


def get_match_players(team1: str, team2: str) -> dict:
    """Get key players for both teams in a match."""
    return {
        "team1_players": get_team_players(team1),
        "team2_players": get_team_players(team2),
    }
