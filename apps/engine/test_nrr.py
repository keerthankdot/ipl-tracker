from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from apps.engine.nrr import (
    calculate_all_standings,
    calculate_nrr,
    extract_team_match_data,
    generate_scoreline,
    parse_overs,
    parse_score,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def completed_matches():
    schedule_path = Path(__file__).parent / "data" / "ipl2026_schedule.json"
    data = json.loads(schedule_path.read_text())
    return [m for m in data["matches"] if m["status"] == "completed"]


@pytest.fixture
def chinnaswamy_venue():
    venues_path = Path(__file__).parent / "data" / "venues.json"
    venues = json.loads(venues_path.read_text())
    return venues["chinnaswamy"]


@pytest.fixture
def chepauk_venue():
    venues_path = Path(__file__).parent / "data" / "venues.json"
    venues = json.loads(venues_path.read_text())
    return venues["chepauk"]


# ===========================================================================
# GROUP 1: Score Parsing
# ===========================================================================

class TestParseScore:
    def test_with_wickets(self):
        assert parse_score("203/4") == (203, False)

    def test_all_out_no_slash(self):
        assert parse_score("127") == (127, True)

    def test_high_total(self):
        assert parse_score("226/8") == (226, False)

    def test_all_out_higher(self):
        assert parse_score("161") == (161, True)

    def test_explicit_10_wickets(self):
        assert parse_score("141/10") == (141, True)


# ===========================================================================
# GROUP 2: Overs Parsing
# ===========================================================================

class TestParseOvers:
    def test_full_20(self):
        assert parse_overs("20.0") == 20.0

    def test_18_2(self):
        assert abs(parse_overs("18.2") - 18.333333) < 0.001

    def test_19_5(self):
        assert abs(parse_overs("19.5") - 19.833333) < 0.001

    def test_0_1(self):
        assert abs(parse_overs("0.1") - 0.166666) < 0.001

    def test_15_4(self):
        assert abs(parse_overs("15.4") - 15.666666) < 0.001

    def test_16_0(self):
        assert parse_overs("16.0") == 16.0

    def test_12_1(self):
        assert abs(parse_overs("12.1") - 12.166666) < 0.001

    def test_19_1(self):
        assert abs(parse_overs("19.1") - 19.166666) < 0.001

    def test_17_1(self):
        assert abs(parse_overs("17.1") - 17.166666) < 0.001

    def test_19_4(self):
        assert abs(parse_overs("19.4") - 19.666666) < 0.001


# ===========================================================================
# GROUP 3: Team Match Data Extraction
# ===========================================================================

class TestExtractTeamMatchData:
    def test_rcb_from_match1(self, completed_matches):
        m = completed_matches[0]  # M001: RCB vs SRH
        data = extract_team_match_data(m, "RCB")
        assert data["runs_scored"] == 203
        assert abs(data["overs_faced"] - 15.6667) < 0.01
        assert data["runs_conceded"] == 201
        assert data["overs_bowled"] == 20.0
        assert data["is_all_out"] is False

    def test_srh_from_match1(self, completed_matches):
        m = completed_matches[0]  # M001: RCB vs SRH
        data = extract_team_match_data(m, "SRH")
        assert data["runs_scored"] == 201
        assert data["overs_faced"] == 20.0
        assert data["runs_conceded"] == 203
        assert abs(data["overs_bowled"] - 15.6667) < 0.01
        assert data["is_all_out"] is False

    def test_kkr_from_match6_all_out_override(self, completed_matches):
        m = completed_matches[5]  # M006: KKR vs SRH
        data = extract_team_match_data(m, "KKR")
        assert data["runs_scored"] == 161
        assert data["overs_faced"] == 20.0  # ALL OUT OVERRIDE
        assert data["runs_conceded"] == 226
        assert data["overs_bowled"] == 20.0
        assert data["is_all_out"] is True

    def test_csk_from_match3_all_out_override(self, completed_matches):
        m = completed_matches[2]  # M003: RR vs CSK
        data = extract_team_match_data(m, "CSK")
        assert data["runs_scored"] == 127
        assert data["overs_faced"] == 20.0  # ALL OUT OVERRIDE
        assert data["runs_conceded"] == 128
        assert abs(data["overs_bowled"] - 12.1667) < 0.01
        assert data["is_all_out"] is True


# ===========================================================================
# GROUP 4: Cumulative NRR -- THE ACID TEST
# ===========================================================================

class TestNRR:
    def test_nrr_rr(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "RR") - 4.171) < 0.01

    def test_nrr_rcb(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "RCB") - 2.907) < 0.01

    def test_nrr_dc(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "DC") - 1.397) < 0.01

    def test_nrr_mi(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "MI") - 0.687) < 0.01

    def test_nrr_pbks(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "PBKS") - 0.509) < 0.01

    def test_nrr_srh(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "SRH") - 0.469) < 0.01

    def test_nrr_gt(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "GT") - (-0.509)) < 0.01

    def test_nrr_lsg(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "LSG") - (-1.397)) < 0.01

    def test_nrr_kkr(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "KKR") - (-1.964)) < 0.01

    def test_nrr_csk(self, completed_matches):
        assert abs(calculate_nrr(completed_matches, "CSK") - (-4.171)) < 0.01


# ===========================================================================
# GROUP 5: Full Standings Table
# ===========================================================================

class TestStandings:
    def test_standings_order(self, completed_matches):
        standings = calculate_all_standings(completed_matches)
        teams_in_order = [s["team"] for s in standings]
        expected = ["RR", "RCB", "DC", "MI", "PBKS", "SRH", "GT", "LSG", "KKR", "CSK"]
        assert teams_in_order == expected

    def test_standings_points(self, completed_matches):
        standings = calculate_all_standings(completed_matches)
        two_pointers = [s for s in standings if s["points"] == 2]
        zero_pointers = [s for s in standings if s["points"] == 0]
        assert len(two_pointers) == 6
        assert len(zero_pointers) == 4
        total_played = sum(s["played"] for s in standings)
        assert total_played == 12  # 6 matches x 2 teams

    def test_standings_nrr_tiebreak(self, completed_matches):
        standings = calculate_all_standings(completed_matches)
        two_point_teams = [s for s in standings if s["points"] == 2]
        nrrs = [s["nrr"] for s in two_point_teams]
        # Must be sorted descending
        assert nrrs == sorted(nrrs, reverse=True)


# ===========================================================================
# GROUP 6: Scoreline Generation
# ===========================================================================

class TestScorelineGeneration:
    def test_runs_in_range(self, chinnaswamy_venue):
        rng = np.random.default_rng(42)
        for _ in range(1000):
            sl = generate_scoreline(chinnaswamy_venue, rng)
            assert 80 <= sl["bat_first_score"] <= 280
            assert 80 <= sl["chase_score"] <= 280

    def test_winner_scores_more(self, chinnaswamy_venue):
        rng = np.random.default_rng(42)
        for _ in range(1000):
            sl = generate_scoreline(chinnaswamy_venue, rng)
            if sl["bat_first_won"]:
                assert sl["bat_first_score"] > sl["chase_score"]
            else:
                assert sl["chase_score"] >= sl["bat_first_score"]

    def test_overs_format(self, chinnaswamy_venue):
        rng = np.random.default_rng(42)
        for _ in range(1000):
            sl = generate_scoreline(chinnaswamy_venue, rng)
            for overs_str in [sl["bat_first_overs"], sl["chase_overs"]]:
                parts = overs_str.split(".")
                assert len(parts) == 2
                balls = int(parts[1])
                assert 0 <= balls <= 5
            assert sl["bat_first_overs"] == "20.0"

    def test_chase_overs_when_chasing_wins(self, chinnaswamy_venue):
        rng = np.random.default_rng(42)
        chase_wins = []
        for _ in range(1000):
            sl = generate_scoreline(chinnaswamy_venue, rng)
            if not sl["bat_first_won"]:
                chase_wins.append(sl)
        assert len(chase_wins) > 0
        some_under_20 = any(sl["chase_overs"] != "20.0" for sl in chase_wins)
        assert some_under_20, "Some chase wins should finish before 20 overs"

    def test_venue_influence(self, chinnaswamy_venue, chepauk_venue):
        rng = np.random.default_rng(42)
        chinnaswamy_scores = []
        chepauk_scores = []
        for _ in range(5000):
            sl = generate_scoreline(chinnaswamy_venue, rng)
            chinnaswamy_scores.append(sl["bat_first_score"])
        rng2 = np.random.default_rng(99)
        for _ in range(5000):
            sl = generate_scoreline(chepauk_venue, rng2)
            chepauk_scores.append(sl["bat_first_score"])
        chin_avg = sum(chinnaswamy_scores) / len(chinnaswamy_scores)
        chep_avg = sum(chepauk_scores) / len(chepauk_scores)
        assert chin_avg > chep_avg
        assert abs(chin_avg - 177) < 5
        assert abs(chep_avg - 160) < 5

    def test_bat_first_win_pct(self, chepauk_venue):
        rng = np.random.default_rng(42)
        bat_first_wins = sum(
            1 for _ in range(10000)
            if generate_scoreline(chepauk_venue, rng)["bat_first_won"]
        )
        pct = bat_first_wins / 10000
        assert 0.50 <= pct <= 0.66
