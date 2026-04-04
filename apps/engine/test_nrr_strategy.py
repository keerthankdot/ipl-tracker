from __future__ import annotations

import pytest

from apps.engine.nrr_strategy import (
    calculate_loss_impact,
    calculate_nrr_bat_first,
    calculate_nrr_chase,
    float_to_cricket_overs,
    generate_nrr_strategy,
)


class TestNRRTargetBatFirst:
    def test_basic(self):
        # Team at NRR ~+1.0, target +2.0, venue avg 170
        result = calculate_nrr_bat_first(
            rs=200, of=20.0, rc=180, ob=20.0,
            target_nrr=2.0, venue_avg=170,
        )
        assert result["min_team_score"] > 170  # Must outscore opponent
        assert result["min_margin_runs"] > 0
        assert result["resulting_nrr"] >= 1.99

    def test_maintain_easy(self):
        # Team at NRR ~+3.0, target +1.0 (easy to maintain)
        result = calculate_nrr_bat_first(
            rs=300, of=20.0, rc=240, ob=20.0,
            target_nrr=1.0, venue_avg=170,
        )
        # Any win should be enough
        assert result["min_margin_runs"] <= 15

    def test_impossible_gap(self):
        # Team at NRR -2.0, target +4.0 (huge gap)
        result = calculate_nrr_bat_first(
            rs=160, of=20.0, rc=200, ob=20.0,
            target_nrr=4.0, venue_avg=170,
        )
        assert result["min_margin_runs"] > 40  # Very large margin needed


class TestNRRTargetChase:
    def test_basic(self):
        result = calculate_nrr_chase(
            rs=200, of=20.0, rc=180, ob=20.0,
            target_nrr=2.0, venue_avg=170,
        )
        assert result["max_overs_float"] < 20.0
        assert result["max_overs_float"] > 0
        assert result["resulting_nrr"] >= 1.99

    def test_overs_format(self):
        result = calculate_nrr_chase(
            rs=200, of=20.0, rc=180, ob=20.0,
            target_nrr=2.0, venue_avg=170,
        )
        overs = result["max_overs"]
        parts = overs.split(".")
        assert len(parts) == 2
        balls = int(parts[1])
        assert 0 <= balls <= 5  # Valid cricket notation

    def test_easy_target(self):
        result = calculate_nrr_chase(
            rs=300, of=20.0, rc=240, ob=20.0,
            target_nrr=1.0, venue_avg=170,
        )
        assert result["max_overs_float"] >= 17.0  # Lots of room


class TestLossImpact:
    def test_loss_drops_nrr(self):
        current_nrr_approx = 200 / 20.0 - 180 / 20.0  # +1.0
        loss_nrr = calculate_loss_impact(
            rs=200, of=20.0, rc=180, ob=20.0,
            venue_avg=170, loss_margin=30,
        )
        assert loss_nrr < current_nrr_approx


class TestCricketOversFormat:
    def test_full_overs(self):
        assert float_to_cricket_overs(16.0) == "16.0"

    def test_partial(self):
        assert float_to_cricket_overs(16.333333) == "16.2"

    def test_five_balls(self):
        assert float_to_cricket_overs(18.833333) == "18.5"


class TestNRRStrategyEndpoint:
    def test_endpoint_returns_scenarios(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        r = client.get("/api/nrr-strategy/rcb")
        assert r.status_code == 200
        d = r.json()
        assert d["team"] == "RCB"
        assert d["nrr_rank"] >= 1
        assert len(d["scenarios"]) >= 2  # at least overtake + loss
        # Check scenario structure
        for s in d["scenarios"]:
            assert "target" in s
            if s["target"] in ("overtake_above", "maintain_position"):
                assert "bat_first" in s
                assert "chase" in s
                assert s["feasibility"] in ("comfortable", "achievable", "difficult", "unlikely")

    def test_endpoint_invalid_team(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        r = client.get("/api/nrr-strategy/xyz")
        assert r.status_code == 404
