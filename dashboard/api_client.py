"""
Thin wrapper around the FastAPI backend's endpoints, shared by every
page in the dashboard. Keeping all HTTP calls in one place means the
pages themselves never construct a URL or handle a requests.Response
directly.

Environment variable:
    API_BASE_URL (default: http://localhost:8000)
"""

import os
from typing import List, Optional

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Kept in sync by hand with backend/app/routers/leaderboard.py's
# ALLOWED_TABLES_BY_METRIC. If you add a metric on the backend, add it
# here too or it simply won't appear as a choice in the dashboard.
LEADERBOARD_METRICS = [
    "goals", "assists", "goals_and_assists", "xg", "npxg", "goals_p90",
    "assists_p90", "total_shots", "shots_p90", "shot_creating_actions_p90",
    "goal_creating_actions_p90", "progressive_passes", "pass_completion_pct",
    "key_passes", "progressive_carries", "take_ons_successful_pct",
    "tackles_won", "interceptions", "clearances", "aerial_duels_won_pct",
    "save_pct", "clean_sheets",
]

POSITIONS = ["DF", "MF", "FW", "GK"]


class APIError(Exception):
    """Raised when the backend returns a non-2xx response. Carries the
    backend's own detail message so pages can show it directly rather
    than a generic 'something went wrong'."""
    pass


def _get(path: str, params: dict) -> list | dict:
    try:
        resp = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
    except requests.exceptions.ConnectionError as exc:
        raise APIError(
            f"Could not reach the API at {API_BASE_URL}. Is the backend running?"
        ) from exc

    if resp.status_code == 404:
        raise APIError(resp.json().get("detail", "Not found"))
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=300)
def search_players(name: str, limit: int = 20) -> list[dict]:
    return _get("/players/search", {"name": name, "limit": limit})


@st.cache_data(ttl=300)
def get_player_career(player_id: int) -> list[dict]:
    return _get(f"/players/{player_id}", {})


@st.cache_data(ttl=300)
def get_player_season(player_id: int, season_label: str) -> list[dict]:
    return _get(f"/players/{player_id}/seasons/{season_label}", {})


@st.cache_data(ttl=300)
def compare_players(player_ids: List[int], season: str) -> list[dict]:
    # `requests` serializes a list value as repeated query params
    # (player_ids=1&player_ids=2&...), which is exactly the format
    # FastAPI's List[int] Query parameter expects on the other end.
    return _get("/compare", {"player_ids": player_ids, "season": season})


@st.cache_data(ttl=300)
def get_leaderboard(
    season: str,
    metric: str,
    position: Optional[str] = None,
    min_minutes: int = 900,
    limit: int = 50,
) -> list[dict]:
    params = {"season": season, "metric": metric, "min_minutes": min_minutes, "limit": limit}
    if position:
        params["position"] = position
    return _get("/leaderboard", params)