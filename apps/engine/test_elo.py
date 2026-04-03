from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.engine.elo import (
    compute_current_elo,
    expected_score,
    load_initial_elo,
    update_elo,
)
from apps.engine.nrr import ALL_TEAMS
from apps.engine.simulator import get_completed_matches, load_schedule


@pytest.fixture
def completed_matches():
    schedule = load_schedule()
    return get_completed_matches(schedule)


class TestEloSystem:
    def test_initial_ratings_load(self):
        ratings = load_initial_elo()
        assert len(ratings) == 10
        for team in ALL_TEAMS:
            assert team in ratings
            assert ratings[team] > 0

    def test_expected_score_equal(self):
        assert abs(expected_score(1500, 1500) - 0.5) < 0.001

    def test_expected_score_100_diff(self):
        exp = expected_score(1600, 1500)
        assert 0.63 < exp < 0.65  # ~64%

    def test_update_close_match(self):
        new_w, new_l = update_elo(1500, 1500, margin_mult=1.0)
        # Winner gains ~16 (K=32, expected=0.5, 32*1.0*0.5=16)
        assert abs(new_w - 1516) < 1
        assert abs(new_l - 1484) < 1

    def test_update_blowout(self):
        new_w, new_l = update_elo(1500, 1500, margin_mult=1.5)
        # 32 * 1.5 * 0.5 = 24
        assert abs(new_w - 1524) < 1
        assert abs(new_l - 1476) < 1

    def test_update_upset(self):
        new_w, new_l = update_elo(1400, 1600)
        # Underdog wins: expected ~0.24, change = 32*(1-0.24) = ~24.3
        change = new_w - 1400
        assert change > 20  # Big swing for upset

    def test_elo_conservation(self, completed_matches):
        initial = load_initial_elo()
        initial_total = sum(initial.values())
        current = compute_current_elo(completed_matches)
        current_total = sum(current.values())
        assert abs(initial_total - current_total) < 0.01  # Zero-sum

    def test_elo_after_6_matches(self, completed_matches):
        ratings = compute_current_elo(completed_matches)
        # KKR lost 2, RR won big: RR should be above KKR
        assert ratings["KKR"] < ratings["RR"]
        # Winners should have gained, losers should have dropped
        # GT started lowest (1480) and lost 1: should still be near bottom
        assert ratings["GT"] < ratings["RR"]
