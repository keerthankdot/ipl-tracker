from __future__ import annotations

import os

import pytest

from apps.engine.weather_api import get_weather_for_match, predict_dew


class TestDewModel:
    def test_heavy(self):
        r = predict_dew(23.0, 75, "19:30")
        assert r["level"] == "heavy"

    def test_moderate(self):
        r = predict_dew(26.0, 65, "19:30")
        assert r["level"] == "moderate"

    def test_light(self):
        r = predict_dew(27.0, 55, "19:30")
        assert r["level"] == "light"

    def test_none_low_humidity(self):
        r = predict_dew(30.0, 40, "19:30")
        assert r["level"] == "none"

    def test_afternoon_always_none(self):
        r = predict_dew(23.0, 75, "15:30")
        assert r["level"] == "none"
        assert r["is_evening_match"] is False

    def test_evening_boundary(self):
        # temp=25 is NOT < 25, so not heavy
        r = predict_dew(25.0, 70, "19:30")
        assert r["level"] == "moderate"

    def test_impact_string_nonempty(self):
        r = predict_dew(23.0, 75, "19:30")
        assert len(r["impact"]) > 20


class TestWeatherAPI:
    def test_unknown_venue_returns_none(self):
        r = get_weather_for_match("unknown_stadium", "2026-04-05", "19:30")
        assert r is None

    @pytest.mark.skipif(
        not os.environ.get("OPENWEATHERMAP_API_KEY"),
        reason="API key not set",
    )
    def test_real_api_response_structure(self):
        r = get_weather_for_match("chinnaswamy", "2026-04-05", "19:30")
        if r is not None:
            assert "temperature_c" in r
            assert "humidity_pct" in r
            assert "dew" in r
            assert r["dew"]["level"] in ("heavy", "moderate", "light", "none")
