"""Tests for the pure dashboard data helpers."""

import math

from dashboard.dashboard_data import (
    DEFAULT_SEASON,
    HOME_METRICS,
    SUPPORTED_SEASONS,
    metric_label,
    prepare_leaderboard_rows,
)


def test_supported_seasons_cover_seven_historical_seasons():
    assert len(SUPPORTED_SEASONS) == 7
    assert SUPPORTED_SEASONS[0] == "2017-2018"
    assert SUPPORTED_SEASONS[-1] == DEFAULT_SEASON


def test_home_metrics_have_readable_labels():
    assert "goals" in HOME_METRICS
    assert metric_label("goals_p90") == "Goals per 90"
    assert metric_label("new_metric") == "New Metric"


def test_prepare_leaderboard_rows_sorts_and_limits_values():
    rows = [
        {"player_name": "Player A", "value": "4"},
        {"player_name": "Player B", "value": 12},
        {"player_name": "Player C", "value": 8},
    ]
    result = prepare_leaderboard_rows(rows, limit=2)
    assert [row["player_name"] for row in result] == ["Player B", "Player C"]
    assert [row["_chart_value"] for row in result] == [12.0, 8.0]
    assert rows[0]["value"] == "4"


def test_prepare_leaderboard_rows_skips_invalid_and_non_finite_values():
    rows = [
        {"player_name": "Missing", "value": None},
        {"player_name": "Bad", "value": "not-a-number"},
        {"player_name": "Infinite", "value": math.inf},
        {"player_name": "Valid", "value": "2.5"},
    ]
    result = prepare_leaderboard_rows(rows)
    assert len(result) == 1
    assert result[0]["player_name"] == "Valid"
    assert result[0]["_chart_value"] == 2.5


def test_prepare_leaderboard_rows_handles_empty_data_and_invalid_limit():
    assert prepare_leaderboard_rows([]) == []
    assert prepare_leaderboard_rows([{"value": 1}], limit=0) == []
