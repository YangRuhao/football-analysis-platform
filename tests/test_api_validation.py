import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.routers import compare, leaderboard, players, profile


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, *_args):
        return None

    def fetchall(self):
        return self.rows


def fake_cursor(rows=None):
    return FakeCursor(rows)


def test_compare_rejects_duplicate_player_ids(monkeypatch):
    monkeypatch.setattr(compare, "get_cursor", lambda: fake_cursor())
    response = TestClient(app).get(
        "/compare",
        params=[("player_ids", 1), ("player_ids", 1), ("season", "2023-2024")],
    )
    assert response.status_code == 400


def test_compare_rejects_bad_season(monkeypatch):
    monkeypatch.setattr(compare, "get_cursor", lambda: fake_cursor())
    response = TestClient(app).get(
        "/compare",
        params=[("player_ids", 1), ("player_ids", 2), ("season", "2023")],
    )
    assert response.status_code == 422


def test_leaderboard_rejects_bad_position(monkeypatch):
    monkeypatch.setattr(leaderboard, "get_cursor", lambda: fake_cursor())
    response = TestClient(app).get(
        "/leaderboard",
        params={"season": "2023-2024", "metric": "goals", "position": "XX"},
    )
    assert response.status_code == 422


def test_player_search_rejects_short_name(monkeypatch):
    monkeypatch.setattr(players, "get_cursor", lambda: fake_cursor())
    response = TestClient(app).get("/players/search", params={"name": "A"})
    assert response.status_code == 422


def test_profile_rejects_bad_season(monkeypatch):
    monkeypatch.setattr(profile, "get_cursor", lambda: fake_cursor())
    response = TestClient(app).get("/players/1/profile/2023")
    assert response.status_code == 422


def test_profile_rejects_non_positive_player_id(monkeypatch):
    monkeypatch.setattr(profile, "get_cursor", lambda: fake_cursor())
    response = TestClient(app).get("/players/0/profile/2023-2024")
    assert response.status_code == 422


def test_profile_rejects_invalid_min_minutes(monkeypatch):
    monkeypatch.setattr(profile, "get_cursor", lambda: fake_cursor())
    response = TestClient(app).get(
        "/players/1/profile/2023-2024",
        params={"min_minutes": -1},
    )
    assert response.status_code == 422


def test_compare_rejects_more_than_six_players(monkeypatch):
    monkeypatch.setattr(compare, "get_cursor", lambda: fake_cursor())
    params = [("player_ids", i) for i in range(1, 8)]
    params.append(("season", "2023-2024"))
    response = TestClient(app).get("/compare", params=params)
    assert response.status_code == 422
