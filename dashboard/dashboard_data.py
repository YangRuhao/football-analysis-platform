"""Small, pure helpers for dashboard defaults and chart preparation."""

import math
from typing import Any

SUPPORTED_SEASONS = [f"{start}-{start + 1}" for start in range(2017, 2024)]
DEFAULT_SEASON = "2023-2024"

HOME_METRICS = [
    "goals", "assists", "goals_and_assists", "xg", "npxg", "goals_p90",
    "assists_p90", "total_shots", "shots_p90",
    "shot_creating_actions_p90", "goal_creating_actions_p90",
    "progressive_passes", "pass_completion_pct", "key_passes",
    "progressive_carries", "take_ons_successful_pct", "tackles_won",
    "interceptions", "clearances", "aerial_duels_won_pct", "save_pct", "clean_sheets",
]


def metric_label(metric: str) -> str:
    """Return a readable label for an API metric identifier."""
    labels = {
        "goals": "Goals",
        "assists": "Assists",
        "goals_and_assists": "Goals + assists",
        "xg": "Expected goals (xG)",
        "npxg": "Non-penalty xG",
        "goals_p90": "Goals per 90",
        "assists_p90": "Assists per 90",
        "total_shots": "Total shots",
        "shots_p90": "Shots per 90",
        "shot_creating_actions_p90": "Shot-creating actions per 90",
        "goal_creating_actions_p90": "Goal-creating actions per 90",
        "progressive_passes": "Progressive passes",
        "pass_completion_pct": "Pass completion %",
        "key_passes": "Key passes",
        "progressive_carries": "Progressive carries",
        "take_ons_successful_pct": "Successful take-ons %",
        "tackles_won": "Tackles won",
        "interceptions": "Interceptions",
        "clearances": "Clearances",
        "aerial_duels_won_pct": "Aerial duels won %",
        "save_pct": "Save %",
        "clean_sheets": "Clean sheets",
    }
    return labels.get(metric, metric.replace("_", " ").title())


def prepare_leaderboard_rows(
    rows: list[dict[str, Any]], limit: int = 10
) -> list[dict[str, Any]]:
    """Filter invalid values and return the strongest rows first.

    The returned copy includes a numeric chart value used by Plotly,
    avoiding mixed Decimal/string dtypes from the API response.
    """
    if limit < 1:
        return []

    prepared: list[dict[str, Any]] = []
    for row in rows:
        try:
            value = float(row.get("value"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value):
            continue
        item = dict(row)
        item["_chart_value"] = value
        prepared.append(item)

    prepared.sort(key=lambda item: item["_chart_value"], reverse=True)
    return prepared[:limit]
