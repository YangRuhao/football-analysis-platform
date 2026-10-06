import os

import psycopg2
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def db_connection():
    config = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "dbname": os.environ.get("DB_NAME", "football_analytics"),
        "user": os.environ.get("DB_USER", "football_app"),
        "password": os.environ.get("DB_PASSWORD"),
    }
    try:
        conn = psycopg2.connect(**config)
    except psycopg2.OperationalError:
        if os.environ.get("REQUIRE_DB_TESTS") == "1":
            raise
        pytest.skip("PostgreSQL is not available; set REQUIRE_DB_TESTS=1 to require it")
    yield conn
    conn.close()


@pytest.fixture()
def seeded_db(db_connection):
    conn = db_connection
    with conn.cursor() as cur:
        cur.execute(
            """
            TRUNCATE
                player_llm_summaries,
                player_season_goalkeeping,
                player_season_defense,
                player_season_possession,
                player_season_passing,
                player_season_attacking,
                player_season_stats,
                players,
                teams,
                leagues,
                seasons
            RESTART IDENTITY CASCADE
            """
        )
        cur.execute(
            "INSERT INTO leagues (league_name) VALUES ('Premier League') RETURNING league_id"
        )
        league_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO seasons (season_label, start_year) VALUES ('2023-2024', 2023) RETURNING season_id"
        )
        season_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO teams (team_name) VALUES ('Test FC') RETURNING team_id"
        )
        team_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO players (player_name, nation, born)
            VALUES ('Test Player', 'IE', 2000)
            RETURNING player_id
            """
        )
        player_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO player_season_stats
                (player_id, team_id, season_id, league_id, position, age,
                 matches_played, minutes_played)
            VALUES (%s, %s, %s, %s, 'FW', 23, 30, 2400)
            RETURNING stat_id
            """,
            (player_id, team_id, season_id, league_id),
        )
        stat_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO player_season_attacking
                (stat_id, goals, assists, goals_and_assists, xg, npxg, total_shots)
            VALUES (%s, 20, 5, 25, 18.5, 15.0, 70)
            """,
            (stat_id,),
        )
        cur.execute("REFRESH MATERIALIZED VIEW mv_player_season_full")
    conn.commit()
    yield {"player_id": player_id, "stat_id": stat_id}
    with conn.cursor() as cur:
        cur.execute("TRUNCATE players, teams, leagues, seasons CASCADE")
        cur.execute("REFRESH MATERIALIZED VIEW mv_player_season_full")
    conn.commit()


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_database_schema_is_loaded(db_connection):
    with db_connection.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('players', 'player_season_stats', 'player_season_attacking')
            """
        )
        assert cur.fetchone()[0] == 3


def test_health_checks_real_database(client, db_connection):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_player_search_reads_postgres(client, seeded_db):
    response = client.get("/players/search", params={"name": "Test"})
    assert response.status_code == 200
    assert response.json()[0]["player_id"] == seeded_db["player_id"]


def test_player_season_reads_materialized_view(client, seeded_db):
    response = client.get(f"/players/{seeded_db['player_id']}/seasons/2023-2024")
    assert response.status_code == 200
    assert response.json()[0]["goals"] == 20
    assert response.json()[0]["minutes_played"] == 2400


def test_compare_reads_postgres(client, seeded_db):
    response = client.get(
        "/compare",
        params=[
            ("player_ids", seeded_db["player_id"]),
            ("player_ids", 999999),
            ("season", "2023-2024"),
        ],
    )
    assert response.status_code == 404

def test_compare_aggregates_normalized_stat_tables(client, seeded_db, db_connection):
    conn = db_connection
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO teams (team_name) VALUES ('Second Test FC') RETURNING team_id"
        )
        second_team_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO players (player_name, nation, born)
            VALUES ('Second Test Player', 'IE', 2001)
            RETURNING player_id
            """
        )
        second_player_id = cur.fetchone()[0]
        cur.execute(
            "SELECT season_id, league_id FROM seasons WHERE season_label = '2023-2024'"
        )
        season_id, league_id = cur.fetchone()
        cur.execute(
            """
            INSERT INTO player_season_stats
                (player_id, team_id, season_id, league_id, position, age,
                 matches_played, minutes_played)
            VALUES (%s, %s, %s, %s, 'FW', 22, 20, 1800)
            RETURNING stat_id
            """,
            (second_player_id, second_team_id, season_id, league_id),
        )
        second_stat_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO player_season_passing
                (stat_id, progressive_passes, passes_completed, passes_attempted, key_passes)
            VALUES (%s, 60, 600, 800, 30)
            """,
            (second_stat_id,),
        )
        cur.execute(
            """
            INSERT INTO player_season_possession
                (stat_id, progressive_carries, take_ons_attempted, take_ons_successful_pct)
            VALUES (%s, 45, 40, 50)
            """,
            (second_stat_id,),
        )
        cur.execute(
            """
            INSERT INTO player_season_passing
                (stat_id, progressive_passes, passes_completed, passes_attempted, key_passes)
            SELECT stat_id, 80, 700, 1000, 40
            FROM player_season_stats
            WHERE player_id = %s
            """,
            (seeded_db["player_id"],),
        )
        cur.execute(
            """
            INSERT INTO player_season_possession
                (stat_id, progressive_carries, take_ons_attempted, take_ons_successful_pct)
            SELECT stat_id, 30, 20, 75
            FROM player_season_stats
            WHERE player_id = %s
            """,
            (seeded_db["player_id"],),
        )
    conn.commit()

    response = client.get(
        "/compare",
        params=[
            ("player_ids", seeded_db["player_id"]),
            ("player_ids", second_player_id),
            ("season", "2023-2024"),
        ],
    )
    assert response.status_code == 200

    rows = {row["player_id"]: row for row in response.json()}
    first = rows[seeded_db["player_id"]]
    second = rows[second_player_id]

    assert first["progressive_passes"] == 80
    assert first["passes_completed"] == 700
    assert first["passes_attempted"] == 1000
    assert first["key_passes"] == 40
    assert first["progressive_passes_p90"] == pytest.approx(3.0)
    assert first["pass_completion_pct"] == pytest.approx(70.0)

    assert second["progressive_passes"] == 60
    assert second["passes_completed"] == 600
    assert second["passes_attempted"] == 800
    assert second["key_passes"] == 30
    assert second["progressive_passes_p90"] == pytest.approx(3.0)
    assert second["pass_completion_pct"] == pytest.approx(75.0)


def test_leaderboard_reads_postgres(client, seeded_db):
    response = client.get(
        "/leaderboard",
        params={"season": "2023-2024", "metric": "goals", "min_minutes": 0},
    )
    assert response.status_code == 200
    assert response.json()[0]["value"] == 20
    assert response.json()[0]["metric"] == "goals"


def test_database_constraints_reject_invalid_minutes(db_connection, seeded_db):
    with db_connection.cursor() as cur:
        with pytest.raises(psycopg2.errors.CheckViolation):
            cur.execute(
                """
                INSERT INTO player_season_stats
                    (player_id, team_id, season_id, league_id, position, age,
                     matches_played, minutes_played)
                SELECT player_id, team_id, season_id, league_id, 'FW', 23, 1, -1
                FROM player_season_stats
                LIMIT 1
                """
            )
        db_connection.rollback()
    # The fixture remains usable after the failed transaction.
