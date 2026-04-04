from __future__ import annotations

import pytest

from apps.engine.classifier import classify_match, estimate_impact


class TestClassification:
    def test_must_win_high_impact(self):
        assert classify_match(0.55, 9.0, 45.0) == "MUST_WIN"

    def test_must_win_danger_zone(self):
        assert classify_match(0.50, 6.0, 40.0) == "MUST_WIN"

    def test_favored(self):
        assert classify_match(0.65, 3.0, 60.0) == "FAVORED"

    def test_toss_up(self):
        assert classify_match(0.50, 3.0, 60.0) == "TOSS_UP"

    def test_tough(self):
        assert classify_match(0.35, 3.0, 60.0) == "TOUGH"

    def test_upset_needed(self):
        assert classify_match(0.22, 3.0, 60.0) == "UPSET_NEEDED"

    def test_favored_but_must_win(self):
        # Impact overrides probability
        assert classify_match(0.70, 10.0, 50.0) == "MUST_WIN"


class TestImpactEstimation:
    def test_early_season(self):
        sd = {"RCB": {"points": 2}}
        impact = estimate_impact("RCB", {}, sd, 13)
        assert 5.0 < impact < 15.0

    def test_late_season(self):
        sd = {"RCB": {"points": 10}}
        impact = estimate_impact("RCB", {}, sd, 3)
        assert impact > 15.0

    def test_safe_team(self):
        sd = {"RCB": {"points": 20}}
        impact = estimate_impact("RCB", {}, sd, 5)
        # Well above 16 threshold, lower urgency
        safe = impact
        sd2 = {"RCB": {"points": 6}}
        endangered = estimate_impact("RCB", {}, sd2, 5)
        assert endangered > safe

    def test_no_remaining(self):
        sd = {"RCB": {"points": 14}}
        assert estimate_impact("RCB", {}, sd, 0) == 0.0

    def test_capped_at_25(self):
        sd = {"RCB": {"points": 0}}
        impact = estimate_impact("RCB", {}, sd, 1)
        assert impact <= 25.0


class TestWinPathEndpoint:
    def test_winpath_returns_all_matches(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        r = client.get("/api/winpath/rcb")
        assert r.status_code == 200
        d = r.json()
        assert d["team"] == "RCB"
        assert len(d["matches"]) == 14

    def test_winpath_completed_has_result(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        d = client.get("/api/winpath/rcb").json()
        completed = [m for m in d["matches"] if m["status"] == "completed"]
        assert len(completed) >= 1
        for m in completed:
            assert m["result"] in ("won", "lost")
            assert m["score"] is not None

    def test_winpath_upcoming_has_classification(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        d = client.get("/api/winpath/rcb").json()
        upcoming = [m for m in d["matches"] if m["status"] == "upcoming"]
        for m in upcoming:
            assert m["classification"] in ("MUST_WIN", "FAVORED", "TOSS_UP", "TOUGH", "UPSET_NEEDED")
            assert m["win_prob"] is not None
            assert 0.2 <= m["win_prob"] <= 0.8
            assert m["impact"] is not None

    def test_winpath_summary_counts(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        d = client.get("/api/winpath/rcb").json()
        s = d["summary"]
        assert s["matches_played"] + s["matches_remaining"] == 14
        upcoming = [m for m in d["matches"] if m["status"] == "upcoming"]
        assert s["must_wins"] + s["favored"] + s["toss_ups"] + s["tough"] + s["upset_needed"] == len(upcoming)

    def test_winpath_invalid_team(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        r = client.get("/api/winpath/xyz")
        assert r.status_code == 404

    def test_winpath_sorted_by_date(self):
        from fastapi.testclient import TestClient
        from apps.engine.main import app
        client = TestClient(app)
        d = client.get("/api/winpath/rcb").json()
        dates = [m["date"] for m in d["matches"]]
        assert dates == sorted(dates)
