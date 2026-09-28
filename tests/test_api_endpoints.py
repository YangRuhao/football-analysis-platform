import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.routers import compare, leaderboard, players


class FakeCursor:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, *_args):
        if self.error:
            raise self.error

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return {"?column?": 1}


def cursor(rows=None, error=None):
    return FakeCursor(rows, error)


def client_without_startup():
    return TestClient(app, raise_server_exceptions=False)


def test_health_returns_503_when_database_fails(monkeypatch):
    from app import main
    monkeypatch.setattr(main, "check_database", lambda: (_ for _ in ()).throw(RuntimeError("db down")))
    response = client_without_startup().get("/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "database unavailable"


def test_player_search_returns_rows(monkeypatch):
    rows = [{"player_id": 1, "player_name": "Erling Haaland", "nation": "NO", "born": 2000}]
    monkeypatch.setattr(players, "get_cursor", lambda: cursor(rows))
    response = client_without_startup().get("/players/search?name=Haaland")
    assert response.status_code == 200
    assert response.json()[0]["player_name"] == "Erling Haaland"


def test_player_search_404(monkeypatch):
    monkeypatch.setattr(players, "get_cursor", lambda: cursor())
    response = client_without_startup().get("/players/search?name=Nobody")
    assert response.status_code == 404


def test_player_lookup_returns_rows(monkeypatch):
    row = {"player_id": 1, "player_name": "Example", "season_label": "2023-2024"}
    monkeypatch.setattr(players, "get_cursor", lambda: cursor([row]))
    response = client_without_startup().get("/players/1")
    assert response.status_code == 200


def test_player_lookup_rejects_invalid_id():
    response = client_without_startup().get("/players/0")
    assert response.status_code == 422


def test_season_lookup_rejects_invalid_season():
    response = client_without_startup().get("/players/1/seasons/2023")
    assert response.status_code == 422


def test_season_lookup_returns_rows(monkeypatch):
    row = {"player_id": 1, "player_name": "Example", "season_label": "2023-2024"}
    monkeypatch.setattr(players, "get_cursor", lambda: cursor([row]))
    response = client_without_startup().get("/players/1/seasons/2023-2024")
    assert response.status_code == 200


def test_compare_returns_rows(monkeypatch):
    rows = [
        {"player_id": 1, "player_name": "A"},
        {"player_id": 2, "player_name": "B"},
    ]
    monkeypatch.setattr(compare, "get_cursor", lambda: cursor(rows))
    response = client_without_startup().get(
        "/compare?player_ids=1&player_ids=2&season=2023-2024"
    )
    assert response.status_code == 200


@pytest.mark.parametrize("params", [
    "player_ids=1&player_ids=1&season=2023-2024",
    "player_ids=1&season=2023-2024",
    "player_ids=1&player_ids=2&season=2023",
])
def test_compare_rejects_invalid_inputs(monkeypatch, params):
    monkeypatch.setattr(compare, "get_cursor", lambda: cursor())
    response = client_without_startup().get("/compare?" + params)
    assert response.status_code in (400, 422)


def test_leaderboard_returns_rows(monkeypatch):
    rows = [{"player_id": 1, "player_name": "A", "value": 10}]
    monkeypatch.setattr(leaderboard, "get_cursor", lambda: cursor(rows))
    response = client_without_startup().get(
        "/leaderboard?season=2023-2024&metric=goals"
    )
    assert response.status_code == 200


@pytest.mark.parametrize("params", [
    {"season": "2023", "metric": "goals"},
    {"season": "2023-2024", "metric": "not_a_metric"},
    {"season": "2023-2024", "metric": "goals", "position": "XX"},
    {"season": "2023-2024", "metric": "goals", "limit": "0"},
    {"season": "2023-2024", "metric": "goals", "limit": "101"},
    {"season": "2023-2024", "metric": "goals", "min_minutes": "-1"},
])
def test_leaderboard_rejects_invalid_inputs(monkeypatch, params):
    monkeypatch.setattr(leaderboard, "get_cursor", lambda: cursor())
    response = client_without_startup().get("/leaderboard", params=params)
    assert response.status_code in (400, 422)


@pytest.mark.parametrize("position", ["DF", "MF", "FW", "GK"])
def test_leaderboard_accepts_valid_position(monkeypatch, position):
    monkeypatch.setattr(
        leaderboard,
        "get_cursor",
        lambda: cursor([{"player_id": 1, "player_name": "A", "value": 1}]),
    )
    response = client_without_startup().get(
        "/leaderboard",
        params={"season": "2023-2024", "metric": "goals", "position": position},
    )
    assert response.status_code == 200
