import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.routers import compare, leaderboard, players


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
