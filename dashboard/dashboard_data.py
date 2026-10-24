"""Small, pure helpers for dashboard defaults and chart preparation."""

import math
from typing import Any

SUPPORTED_SEASONS = [f"{start}-{start + 1}" for start in range(2017, 2024)]
DEFAULT_SEASON = "2023-2024"

HOME_METRICS = [
    "goals",
    "assists",
    "xg",
    "npxg",
    "goals_p90",
    "assists_p90",
    "total_shots",
    "progressive_passes",
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
        "progressive_passes": "Progressive passes",
        "key_passes": "Key passes",
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
