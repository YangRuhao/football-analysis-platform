import os
from pathlib import Path

import psycopg2
import pytest

from etl.load_historical import load_and_clean_csv, run_etl


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
def isolated_db(db_connection):
    with db_connection.cursor() as cur:
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
        cur.execute("REFRESH MATERIALIZED VIEW mv_player_season_full")
    db_connection.commit()
    yield db_connection
    with db_connection.cursor() as cur:
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
        cur.execute("REFRESH MATERIALIZED VIEW mv_player_season_full")
    db_connection.commit()


def test_season_filename_is_normalized(tmp_path):
    source = Path("data/raw/historical/cleaned_2023-24.csv")
    df = load_and_clean_csv(str(source))
    assert df["season_label"].iloc[0] == "2023-2024"
    assert "carries_prgc" not in df.columns
    assert "Goals Scored" not in df.columns


def test_etl_idempotency(isolated_db):
    data_dir = str(Path("data/raw/historical"))
    first_inserted, first_skipped = run_etl(data_dir)
    isolated_db.commit()

    with isolated_db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM player_season_stats")
        first_count = cur.fetchone()[0]

    second_inserted, second_skipped = run_etl(data_dir)
    isolated_db.commit()

    with isolated_db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM player_season_stats")
        second_count = cur.fetchone()[0]

    assert first_inserted > 0
    assert first_skipped == 0
    assert second_inserted == 0
    assert second_skipped == first_inserted
    assert second_count == first_count


def test_etl_dry_run_does_not_persist(isolated_db):
    data_dir = str(Path("data/raw/historical"))
    dry_inserted, dry_skipped = run_etl(data_dir, dry_run=True)

    with isolated_db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM player_season_stats")
        stat_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM players")
        player_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM teams")
        team_count = cur.fetchone()[0]

    assert dry_inserted > 0
    assert dry_skipped == 0
    assert stat_count == 0
    assert player_count == 0
    assert team_count == 0
