from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pytest

from apps.engine.elo import compute_current_elo
from apps.engine.nrr import ALL_TEAMS
from apps.engine.simulator import (
    get_completed_matches,
    get_remaining_matches,
    load_schedule,
    load_venues,
)
from apps.engine.weights import (
    calculate_form,
    calculate_match_probability,
    get_h2h_probability,
    load_h2h,
    venue_advantage,
)


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
def elo_ratings(completed_matches):
    return compute_current_elo(completed_matches)


@pytest.fixture
def h2h_data():
    return load_h2h()


# ===========================================================================
# GROUP 1: Form Calculation
# ===========================================================================

class TestForm:
    def test_no_matches(self, completed_matches):
        # Use a fake team that hasn't played
        form = calculate_form([], "RCB")
        assert form == 0.0

    def test_one_win(self, completed_matches):
        # RR has 1 win
        form = calculate_form(completed_matches, "RR")
        assert form == pytest.approx(0.02, abs=0.001)

    def test_two_losses(self, completed_matches):
        # KKR has 2 losses
        form = calculate_form(completed_matches, "KKR")
        assert form == pytest.approx(-0.04, abs=0.001)

    def test_form_clamped(self):
        # Simulate 10 wins in a row
        fake_matches = [
            {"team1": "RCB", "team2": f"T{i}", "winner": "RCB",
             "status": "completed", "date": f"2026-04-{i:02d}"}
            for i in range(1, 11)
        ]
        form = calculate_form(fake_matches, "RCB", window=10)
        assert form <= 0.15

    def test_win_streak_bonus(self):
        fake_matches = [
            {"team1": "RCB", "team2": f"T{i}", "winner": "RCB",
             "status": "completed", "date": f"2026-04-{i:02d}"}
            for i in range(1, 5)
        ]
        form = calculate_form(fake_matches, "RCB")
        # 4 wins = 4*0.02 = 0.08 + 0.03 streak bonus = 0.11
        assert form == pytest.approx(0.11, abs=0.001)

    def test_loss_streak_penalty(self):
        fake_matches = [
            {"team1": "KKR", "team2": f"T{i}", "winner": f"T{i}",
             "status": "completed", "date": f"2026-04-{i:02d}"}
            for i in range(1, 5)
        ]
        form = calculate_form(fake_matches, "KKR")
        # 4 losses = -0.08 - 0.03 penalty = -0.11
        assert form == pytest.approx(-0.11, abs=0.001)


# ===========================================================================
# GROUP 2: Venue Advantage
# ===========================================================================

class TestVenue:
    def test_home_advantage(self, venues):
        adj = venue_advantage("RCB", "CSK", venues["chinnaswamy"])
        assert adj == pytest.approx(0.05)

    def test_away_disadvantage(self, venues):
        # CSK is team1 at chinnaswamy (RCB home) -- no advantage
        adj = venue_advantage("CSK", "RCB", venues["chinnaswamy"])
        assert adj == pytest.approx(-0.05)

    def test_neutral_venue(self, venues):
        adj = venue_advantage("RCB", "CSK", venues["guwahati"])
        assert adj == pytest.approx(0.0)

    def test_secondary_home(self, venues):
        # PBKS at Dharamsala (secondary home)
        adj = venue_advantage("PBKS", "RCB", venues["dharamsala"])
        assert adj == pytest.approx(0.05)

    def test_rr_secondary_home(self, venues):
        adj = venue_advantage("RR", "CSK", venues["guwahati"])
        assert adj == pytest.approx(0.05)


# ===========================================================================
# GROUP 3: Head-to-Head
# ===========================================================================

class TestH2H:
    def test_h2h_csk_vs_rcb(self, h2h_data):
        # CSK has 7-5 vs RCB → CSK perspective = 7/12 ≈ 0.583
        prob = get_h2h_probability(h2h_data, "CSK", "RCB")
        assert 0.55 < prob < 0.62

    def test_h2h_rcb_vs_csk(self, h2h_data):
        # Reverse: RCB perspective = 5/12 ≈ 0.417
        prob = get_h2h_probability(h2h_data, "RCB", "CSK")
        assert 0.38 < prob < 0.45

    def test_h2h_even(self, h2h_data):
        # CSK vs RR: 5-5
        prob = get_h2h_probability(h2h_data, "CSK", "RR")
        assert prob == pytest.approx(0.5, abs=0.01)

    def test_h2h_no_data(self, h2h_data):
        prob = get_h2h_probability({}, "RCB", "CSK")
        assert prob == 0.5


# ===========================================================================
# GROUP 4: Combined Probability
# ===========================================================================

class TestCombinedProbability:
    def test_always_clamped(self, completed_matches, elo_ratings, venues, h2h_data, remaining_matches):
        for match in remaining_matches:
            prob = calculate_match_probability(
                match, completed_matches, elo_ratings, venues, h2h_data
            )
            assert 0.20 <= prob <= 0.80, f"Match {match['id']}: prob={prob}"

    def test_average_roughly_balanced(self, completed_matches, elo_ratings, venues, h2h_data, remaining_matches):
        probs = [
            calculate_match_probability(m, completed_matches, elo_ratings, venues, h2h_data)
            for m in remaining_matches
        ]
        avg = sum(probs) / len(probs)
        # Should be roughly 0.50 (system isn't biased)
        assert 0.42 < avg < 0.58, f"Average prob: {avg}"

    def test_toss_up(self, completed_matches, venues, h2h_data):
        # Equal elo, neutral venue
        equal_elo = {t: 1500.0 for t in ALL_TEAMS}
        match = {
            "team1": "RCB", "team2": "CSK", "venue": "guwahati",
        }
        prob = calculate_match_probability(
            match, [], equal_elo, venues, h2h_data
        )
        assert 0.45 < prob < 0.55


# ===========================================================================
# GROUP 5: Integration with Simulator
# ===========================================================================

class TestWeightedSimulation:
    def test_weighted_sim_sums_correctly(self):
        from apps.engine.simulator import simulate_season
        results = simulate_season(n_sims=5000, seed=42)
        total_t4 = sum(r["top4_pct"] for r in results)
        total_t2 = sum(r["top2_pct"] for r in results)
        total_ti = sum(r["title_pct"] for r in results)
        assert abs(total_t4 - 400.0) < 5.0
        assert abs(total_t2 - 200.0) < 5.0
        assert abs(total_ti - 100.0) < 5.0

    def test_weighted_sim_kkr_worse(self):
        from apps.engine.simulator import simulate_season
        results = simulate_season(n_sims=10000, seed=42)
        rr = next(r for r in results if r["team"] == "RR")
        kkr = next(r for r in results if r["team"] == "KKR")
        assert rr["top4_pct"] > kkr["top4_pct"]
        # KKR should be much worse than Phase 1's ~18%
        assert kkr["top4_pct"] < 25

    def test_weighted_sim_performance(self):
        from apps.engine.simulator import simulate_season
        start = time.time()
        simulate_season(n_sims=50000, seed=42)
        elapsed = time.time() - start
        print(f"\nWeighted 50K sims: {elapsed:.1f}s")
        assert elapsed < 30
