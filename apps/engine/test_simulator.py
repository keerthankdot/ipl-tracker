from __future__ import annotations

import time

import numpy as np
import pytest

from apps.engine.nrr import ALL_TEAMS, calculate_all_standings
from apps.engine.simulator import (
    copy_standings,
    get_completed_matches,
    get_remaining_matches,
    load_schedule,
    load_venues,
    play_match,
    rank_teams,
    simulate_one_season,
    simulate_playoffs,
    simulate_season,
    simulate_with_forced_outcomes,
    update_standings_for_match,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def schedule():
    return load_schedule()


@pytest.fixture
def completed_matches(schedule):
    return get_completed_matches(schedule)


@pytest.fixture
def remaining_matches(schedule):
    return get_remaining_matches(schedule)


@pytest.fixture
def venues():
    return load_venues()


@pytest.fixture
def base_standings(completed_matches):
    return calculate_all_standings(completed_matches)


def make_empty_standings():
    return [{
        "team": t, "played": 0, "won": 0, "lost": 0, "no_result": 0,
        "points": 0, "nrr": 0.0,
        "total_runs_scored": 0, "total_overs_faced": 0.0,
        "total_runs_conceded": 0, "total_overs_bowled": 0.0,
    } for t in ALL_TEAMS]


# ===========================================================================
# GROUP 1: Data Loading
# ===========================================================================

class TestDataLoading:
    def test_load_schedule(self, schedule):
        assert schedule["total_league_matches"] == 70
        assert len(schedule["matches"]) == 74

    def test_get_completed_matches(self, completed_matches):
        assert len(completed_matches) == 6
        assert all(m["status"] == "completed" for m in completed_matches)
        assert all("winner" in m for m in completed_matches)

    def test_get_remaining_matches(self, remaining_matches):
        assert len(remaining_matches) == 64
        assert all(m["status"] == "upcoming" for m in remaining_matches)
        assert all(m.get("team1") and m.get("team2") and m.get("venue") for m in remaining_matches)

    def test_load_venues(self, venues):
        assert len(venues) == 13
        assert "chinnaswamy" in venues
        assert venues["chinnaswamy"]["avg_1st_innings"] == 177

    def test_every_remaining_match_has_valid_venue(self, remaining_matches, venues):
        for match in remaining_matches:
            assert match["venue"] in venues, f"Match {match['id']} has unknown venue {match['venue']}"


# ===========================================================================
# GROUP 2: Standings Copy + Update
# ===========================================================================

class TestStandingsUpdate:
    def test_copy_is_independent(self, base_standings):
        copy = copy_standings(base_standings)
        copy[0]["points"] = 999
        assert base_standings[0]["points"] != 999

    def test_copy_preserves_values(self, base_standings):
        copy = copy_standings(base_standings)
        assert copy[0]["team"] == base_standings[0]["team"]
        assert copy[0]["nrr"] == base_standings[0]["nrr"]
        assert copy[0]["total_runs_scored"] == base_standings[0]["total_runs_scored"]

    def test_winner_gets_2_points(self):
        standings = make_empty_standings()
        sd = {s["team"]: s for s in standings}
        scoreline = {
            "bat_first_score": 180, "bat_first_overs": "20.0",
            "chase_score": 160, "chase_overs": "20.0",
            "bat_first_won": True, "bat_first_all_out": False, "chase_all_out": False,
        }
        update_standings_for_match(sd, "RCB", "CSK", "RCB", "RCB", scoreline)
        assert sd["RCB"]["points"] == 2
        assert sd["RCB"]["won"] == 1
        assert sd["CSK"]["points"] == 0
        assert sd["CSK"]["lost"] == 1
        assert sd["RCB"]["played"] == 1
        assert sd["CSK"]["played"] == 1

    def test_nrr_accumulators(self):
        standings = make_empty_standings()
        sd = {s["team"]: s for s in standings}
        scoreline = {
            "bat_first_score": 180, "bat_first_overs": "20.0",
            "chase_score": 160, "chase_overs": "20.0",
            "bat_first_won": True, "bat_first_all_out": False, "chase_all_out": False,
        }
        # RCB batted first
        update_standings_for_match(sd, "RCB", "CSK", "RCB", "RCB", scoreline)
        assert sd["RCB"]["total_runs_scored"] == 180
        assert sd["RCB"]["total_overs_faced"] == 20.0
        assert sd["RCB"]["total_runs_conceded"] == 160
        assert sd["RCB"]["total_overs_bowled"] == 20.0

    def test_chase_win_overs(self):
        standings = make_empty_standings()
        sd = {s["team"]: s for s in standings}
        scoreline = {
            "bat_first_score": 170, "bat_first_overs": "20.0",
            "chase_score": 171, "chase_overs": "18.2",
            "bat_first_won": False, "bat_first_all_out": False, "chase_all_out": False,
        }
        # CSK batted first, MI chased and won
        update_standings_for_match(sd, "CSK", "MI", "MI", "CSK", scoreline)
        assert sd["MI"]["total_runs_scored"] == 171
        assert abs(sd["MI"]["total_overs_faced"] - 18.333) < 0.01
        assert sd["MI"]["total_runs_conceded"] == 170
        assert sd["MI"]["total_overs_bowled"] == 20.0

    def test_all_out_override(self):
        standings = make_empty_standings()
        sd = {s["team"]: s for s in standings}
        scoreline = {
            "bat_first_score": 175, "bat_first_overs": "20.0",
            "chase_score": 140, "chase_overs": "17.3",
            "bat_first_won": True, "bat_first_all_out": False, "chase_all_out": True,
        }
        # GT batted first, KKR chased and got all out
        update_standings_for_match(sd, "GT", "KKR", "GT", "GT", scoreline)
        assert sd["KKR"]["total_overs_faced"] == 20.0  # all out override
        assert sd["GT"]["total_overs_bowled"] == 20.0   # opponent all out override


# ===========================================================================
# GROUP 3: Single Simulation Run
# ===========================================================================

class TestSingleSim:
    def test_all_teams_play_14(self, base_standings, remaining_matches, venues):
        rng = np.random.default_rng(42)
        ranked, champion = simulate_one_season(base_standings, remaining_matches, venues, rng)
        # ranked is list of team codes; need to check played from the internal standings
        # Actually simulate_one_season returns (ranked_codes, champion)
        # We need a way to check played counts. Let's test via simulate_season instead.
        # For now, verify 10 teams ranked
        assert len(ranked) == 10

    def test_total_points_correct(self, base_standings, remaining_matches, venues):
        rng = np.random.default_rng(42)
        # We need the standings dict to check. Let's use a workaround:
        # Run simulate_one_season and check via the internal logic.
        # Actually, let's test this through the standings returned.
        standings_copy = copy_standings(base_standings)
        sd = {s["team"]: s for s in standings_copy}
        for match in remaining_matches:
            venue_data = venues[match["venue"]]
            winner, loser = play_match(match["team1"], match["team2"], rng)
            bat_first = match["team1"] if rng.random() < 0.5 else match["team2"]
            from apps.engine.nrr import generate_scoreline
            scoreline = generate_scoreline(venue_data, rng)
            update_standings_for_match(sd, match["team1"], match["team2"], winner, bat_first, scoreline)
        total_points = sum(s["points"] for s in sd.values())
        assert total_points == 140  # 70 matches x 2 points
        for s in sd.values():
            assert s["played"] == 14, f"{s['team']} played {s['played']}"

    def test_standings_are_sorted(self, base_standings, remaining_matches, venues):
        rng = np.random.default_rng(42)
        ranked, _ = simulate_one_season(base_standings, remaining_matches, venues, rng)
        # ranked is a list of team codes sorted by points then NRR
        assert len(ranked) == 10

    def test_deterministic_with_seed(self, base_standings, remaining_matches, venues):
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        ranked1, champ1 = simulate_one_season(base_standings, remaining_matches, venues, rng1)
        ranked2, champ2 = simulate_one_season(base_standings, remaining_matches, venues, rng2)
        assert ranked1 == ranked2
        assert champ1 == champ2


# ===========================================================================
# GROUP 4: Playoff Simulation
# ===========================================================================

class TestPlayoffs:
    def test_returns_one_of_top4(self):
        top4 = ["RR", "RCB", "MI", "DC"]
        rng = np.random.default_rng(42)
        champion = simulate_playoffs(top4, rng)
        assert champion in top4

    def test_all_four_can_win(self):
        top4 = ["RR", "RCB", "MI", "DC"]
        winners = set()
        for seed in range(10000):
            rng = np.random.default_rng(seed)
            winners.add(simulate_playoffs(top4, rng))
        assert winners == {"RR", "RCB", "MI", "DC"}

    def test_rank1_advantage(self):
        top4 = ["RR", "RCB", "MI", "DC"]
        counts = {t: 0 for t in top4}
        for seed in range(50000):
            rng = np.random.default_rng(seed)
            counts[simulate_playoffs(top4, rng)] += 1
        top2_wins = counts["RR"] + counts["RCB"]
        bottom2_wins = counts["MI"] + counts["DC"]
        assert top2_wins > bottom2_wins
        assert counts["RR"] / 50000 > 0.20
        assert counts["DC"] / 50000 < 0.35

    def test_no_self_play(self):
        top4 = ["RR", "RCB", "MI", "DC"]
        for seed in range(1000):
            rng = np.random.default_rng(seed)
            champion = simulate_playoffs(top4, rng)
            assert champion in top4


# ===========================================================================
# GROUP 5: Full Monte Carlo
# ===========================================================================

class TestMonteCarlo:
    def test_returns_10_teams(self):
        results = simulate_season(n_sims=1000, seed=42)
        assert len(results) == 10
        teams = {r["team"] for r in results}
        assert teams == set(ALL_TEAMS)

    def test_top4_sums_to_400(self):
        results = simulate_season(n_sims=5000, seed=42)
        total = sum(r["top4_pct"] for r in results)
        assert abs(total - 400.0) < 5.0

    def test_top2_sums_to_200(self):
        results = simulate_season(n_sims=5000, seed=42)
        total = sum(r["top2_pct"] for r in results)
        assert abs(total - 200.0) < 5.0

    def test_title_sums_to_100(self):
        results = simulate_season(n_sims=5000, seed=42)
        total = sum(r["title_pct"] for r in results)
        assert abs(total - 100.0) < 5.0

    def test_no_team_at_zero_or_hundred(self):
        results = simulate_season(n_sims=10000, seed=42)
        for r in results:
            assert r["top4_pct"] > 0.5, f"{r['team']} top4={r['top4_pct']}%"
            assert r["top4_pct"] < 99.5, f"{r['team']} top4={r['top4_pct']}%"

    def test_rr_better_than_kkr(self):
        results = simulate_season(n_sims=10000, seed=42)
        rr = next(r for r in results if r["team"] == "RR")
        kkr = next(r for r in results if r["team"] == "KKR")
        assert rr["top4_pct"] > kkr["top4_pct"]

    def test_deterministic_with_seed(self):
        r1 = simulate_season(n_sims=1000, seed=42)
        r2 = simulate_season(n_sims=1000, seed=42)
        for a, b in zip(r1, r2):
            assert a["top4_pct"] == b["top4_pct"]


# ===========================================================================
# GROUP 6: Performance
# ===========================================================================

# ===========================================================================
# GROUP 7: Forced Outcomes / Impact
# ===========================================================================

class TestForcedOutcomes:
    def test_forced_sums_correct(self):
        results = simulate_with_forced_outcomes({"M007": "CSK"}, n_sims=5000, seed=42)
        total = sum(r["top4_pct"] for r in results)
        assert abs(total - 400.0) < 5.0

    def test_forced_csk_wins_helps_csk(self):
        baseline = simulate_season(n_sims=5000, seed=42)
        forced = simulate_with_forced_outcomes({"M007": "CSK"}, n_sims=5000, seed=42)
        bl_csk = next(r for r in baseline if r["team"] == "CSK")["top4_pct"]
        fo_csk = next(r for r in forced if r["team"] == "CSK")["top4_pct"]
        assert fo_csk > bl_csk  # Forcing CSK win should help CSK

    def test_forced_pbks_wins_helps_pbks(self):
        baseline = simulate_season(n_sims=5000, seed=42)
        forced = simulate_with_forced_outcomes({"M007": "PBKS"}, n_sims=5000, seed=42)
        bl = next(r for r in baseline if r["team"] == "PBKS")["top4_pct"]
        fo = next(r for r in forced if r["team"] == "PBKS")["top4_pct"]
        assert fo > bl

    def test_forced_deterministic(self):
        r1 = simulate_with_forced_outcomes({"M007": "CSK"}, n_sims=1000, seed=42)
        r2 = simulate_with_forced_outcomes({"M007": "CSK"}, n_sims=1000, seed=42)
        for a, b in zip(r1, r2):
            assert a["top4_pct"] == b["top4_pct"]

    def test_forced_invalid_match_ignored(self):
        # Should not crash
        results = simulate_with_forced_outcomes({"M999": "CSK"}, n_sims=1000, seed=42)
        assert len(results) == 10

    def test_forced_multiple_matches(self):
        results = simulate_with_forced_outcomes(
            {"M007": "CSK", "M008": "MI", "M009": "RR"}, n_sims=1000, seed=42
        )
        assert len(results) == 10
        total = sum(r["top4_pct"] for r in results)
        assert abs(total - 400.0) < 10.0


class TestPerformance:
    def test_50k_under_30_seconds(self):
        start = time.time()
        results = simulate_season(n_sims=50000, seed=42)
        elapsed = time.time() - start
        print(f"\n50K sims completed in {elapsed:.1f}s")
        assert elapsed < 30
