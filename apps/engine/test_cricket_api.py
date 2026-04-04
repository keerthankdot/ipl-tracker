from __future__ import annotations

import pytest

from apps.engine.cricket_api import (
    compute_player_summary,
    get_match_players,
    get_team_players,
    load_players,
)


class TestPlayerData:
    def test_load_players(self):
        data = load_players()
        assert len(data["players"]) >= 40
        assert len(data["team_squads"]) == 10
        for key, player in data["players"].items():
            assert "name" in player
            assert "team" in player
            assert "role" in player

    def test_get_team_players_rcb(self):
        players = get_team_players("RCB")
        assert len(players) >= 4
        assert all(p["team"] == "RCB" for p in players)

    def test_get_team_players_unknown(self):
        players = get_team_players("XYZ")
        assert players == []

    def test_compute_batter_summary(self):
        player = {
            "role": "batter",
            "recent_matches": [
                {"runs": 45, "balls": 30, "strike_rate": 150.0},
                {"runs": 82, "balls": 48, "strike_rate": 170.8},
                {"runs": 12, "balls": 10, "strike_rate": 120.0},
            ],
        }
        summary = compute_player_summary(player)
        assert summary["batting"]["total_runs"] == 139
        assert summary["batting"]["innings"] == 3
        assert abs(summary["batting"]["avg"] - 46.3) < 0.1

    def test_compute_bowler_summary(self):
        player = {
            "role": "bowler",
            "recent_matches": [
                {"overs": "4.0", "runs_conceded": 28, "wickets": 2, "economy": 7.0},
                {"overs": "3.2", "runs_conceded": 35, "wickets": 1, "economy": 10.5},
            ],
        }
        summary = compute_player_summary(player)
        assert summary["bowling"]["wickets"] == 3
        assert summary["bowling"]["innings"] == 2
        assert summary["bowling"]["economy"] > 0

    def test_compute_allrounder_summary(self):
        player = {
            "role": "allrounder",
            "recent_matches": [
                {
                    "batting": {"runs": 45, "balls": 30, "strike_rate": 150.0},
                    "bowling": {"overs": "4.0", "runs_conceded": 28, "wickets": 2, "economy": 7.0},
                }
            ],
        }
        summary = compute_player_summary(player)
        assert summary["batting"] is not None
        assert summary["bowling"] is not None

    def test_get_match_players(self):
        result = get_match_players("RCB", "CSK")
        assert len(result["team1_players"]) >= 4
        assert len(result["team2_players"]) >= 4
        assert all(p["team"] == "RCB" for p in result["team1_players"])
        assert all(p["team"] == "CSK" for p in result["team2_players"])

    def test_match_detail_includes_players(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        r = client.get("/api/match-detail/M011/rcb")
        d = r.json()
        assert "players" in d
        assert len(d["players"]["team1_players"]) >= 4
        assert len(d["players"]["team2_players"]) >= 4
