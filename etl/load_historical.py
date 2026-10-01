"""
load_historical.py

ETL script: loads the 7 historical FBref/Kaggle season CSVs
(cleaned_2017-18.csv ... cleaned_2023-24.csv) into the PostgreSQL
schema defined in db/schema.sql.

Data quirks handled here (confirmed by inspecting the actual files):
  - 'Avg Mins per Match' is mislabeled in the source; it is actually
    TOTAL minutes played, not an average. Renamed to `minutes_played`.
  - 'carries_prgc' is an exact duplicate of 'Progressive Carries', and
    'Goals Scored' is an exact duplicate of 'Goals'. Both duplicates
    are dropped rather than loaded twice.
  - There is no xA / xAG column anywhere in this dataset - only xG
    ('Expected Goals') and npxG ('Exp NPG') exist.
  - Goalkeeping columns (Saves, Clean Sheets, etc.) are present on
    every row but are 0/blank for outfield players; they're written
    to their own table (player_season_goalkeeping) regardless.
  - A player can appear twice in the same season file (mid-season
    transfer) - each row is a separate (player, team, season) stint,
    which is exactly what the UNIQUE constraint on
    player_season_stats is designed for.

Usage:
    python etl/load_historical.py [--data-dir PATH] [--dry-run]

Environment variables (defaults are for local Docker Compose):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import argparse
import glob
import logging
import os

import pandas as pd
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "historical"
)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "football_analytics"),
    "user": os.environ.get("DB_USER", "football_app"),
    "password": os.environ.get("DB_PASSWORD"),
}

# Raw source column name -> our schema's column name.
COLUMN_RENAME = {
    "player": "player_name",
    "nation": "nation",
    "pos": "position",
    "squad": "team_name",
    "comp": "league_name",
    "age": "age",
    "born": "born",
    "Matches Played": "matches_played",
    "Avg Mins per Match": "minutes_played",  # mislabeled in source; this is TOTAL minutes
    "Goals": "goals",
    "Assists": "assists",
    "Goals & Assists": "goals_and_assists",
    "Non Penalty Goals": "non_penalty_goals",
    "Penalty Kicks Made": "penalty_kicks_made",
    "Expected Goals": "xg",
    "Exp NPG": "npxg",
    "Progressive Carries": "progressive_carries",
    "Progressive Passes": "progressive_passes",
    "Goals p 90": "goals_p90",
    "Assists p 90": "assists_p90",
    "Tackles attempted": "tackles_attempted",
    "Tackles Won": "tackles_won",
    "% Dribbles tackled": "dribbles_tackled_pct",
    "Shots blocked": "shots_blocked",
    "Passes blocked": "passes_blocked",
    "Interceptions": "interceptions",
    "Clearances": "clearances",
    "Errors made": "errors",
    "Goals Against": "goals_against",
    "Goals against p 90": "goals_against_p90",
    "Saves": "saves",
    "Saves %": "save_pct",
    "Clean Sheets": "clean_sheets",
    "% Clean sheets": "clean_sheet_pct",
    "% Penalty saves": "penalty_save_pct",
    "Passes Completed": "passes_completed",
    "Passes Attempted": "passes_attempted",
    "Pass completion %": "pass_completion_pct",
    "Progressive passes distance": "progressive_pass_distance",
    "% Short pass completed": "short_pass_completion_pct",
    "% Medium passes completed": "medium_pass_completion_pct",
    "% Long passes completed": "long_pass_completion_pct",
    "Key passes": "key_passes",
    "1/3": "passes_into_final_third",
    "Passes into penalty area": "passes_into_penalty_area",
    "touches_def_pen": "touches_def_penalty_area",
    "Take ons attempted": "take_ons_attempted",
    "% Successful take-ons": "take_ons_successful_pct",
    "Times tackled during take-on": "times_tackled_on_take_on",
    "carries final 3rd": "carries_into_final_third",
    "carries penalty area": "carries_into_penalty_area",
    "Possessions lost": "possessions_lost",
    "Total Shots": "total_shots",
    "% Shots on target": "shots_on_target_pct",
    "Shots p 90": "shots_p90",
    "Goals per shot": "goals_per_shot",
    "Goals per shot on target": "goals_per_shot_on_target",
    "% Aerial Duels won": "aerial_duels_won_pct",
    "Shot creating actions p 90": "shot_creating_actions_p90",
    "Goal creating actions p 90": "goal_creating_actions_p90",
    "Crosses Stopped": "crosses_stopped",
    "season": "season_label_raw",  # not used for the DB season_id; filename is authoritative
}

# 'rk' is a meaningless per-file row index. 'carries_prgc' and 'Goals Scored'
# are confirmed exact duplicates of columns already in COLUMN_RENAME.
DROP_COLUMNS = ["rk", "carries_prgc", "Goals Scored"]

# These are the columns required to construct the player-season base row.
# Duplicate and optional statistic columns are validated only when present,
# then dropped or loaded into their statistic group tables as applicable.
REQUIRED_COLUMNS = {
    "player",
    "nation",
    "pos",
    "squad",
    "comp",
    "age",
    "born",
    "Matches Played",
    "Avg Mins per Match",
}

ATTACKING_COLS = [
    "goals", "assists", "goals_and_assists", "non_penalty_goals",
    "penalty_kicks_made", "xg", "npxg", "goals_p90", "assists_p90",
    "total_shots", "shots_on_target_pct", "shots_p90", "goals_per_shot",
    "goals_per_shot_on_target", "shot_creating_actions_p90",
    "goal_creating_actions_p90",
]
PASSING_COLS = [
    "progressive_passes", "passes_completed", "passes_attempted",
    "pass_completion_pct", "progressive_pass_distance",
    "short_pass_completion_pct", "medium_pass_completion_pct",
    "long_pass_completion_pct", "key_passes",
    "passes_into_final_third", "passes_into_penalty_area",
]
POSSESSION_COLS = [
    "progressive_carries", "take_ons_attempted", "take_ons_successful_pct",
    "times_tackled_on_take_on", "carries_into_final_third",
    "carries_into_penalty_area", "possessions_lost",
    "touches_def_penalty_area",
]
DEFENSE_COLS = [
    "tackles_attempted", "tackles_won", "dribbles_tackled_pct",
    "shots_blocked", "passes_blocked", "interceptions", "clearances",
    "errors", "aerial_duels_won_pct",
]
GOALKEEPING_COLS = [
    "goals_against", "goals_against_p90", "saves", "save_pct",
    "clean_sheets", "clean_sheet_pct", "penalty_save_pct", "crosses_stopped",
]

STAT_GROUP_TABLES = {
    "player_season_attacking": ATTACKING_COLS,
    "player_season_passing": PASSING_COLS,
    "player_season_possession": POSSESSION_COLS,
    "player_season_defense": DEFENSE_COLS,
    "player_season_goalkeeping": GOALKEEPING_COLS,
}


def season_label_from_filename(path: str) -> str:
    """'cleaned_2023-24.csv' -> '2023-2024'"""
    base = os.path.basename(path)
    yy = base.replace("cleaned_", "").replace(".csv", "")  # '2023-24'
    start, end_short = yy.split("-")
    end = str(int(start[:2] + end_short)) if len(end_short) == 2 else end_short
    return f"{start}-{end}"


def load_and_clean_csv(path: str) -> pd.DataFrame:
    # encoding="utf-8" is explicit and required here - without it, pandas
    # falls back to the OS locale's default encoding, which is cp1252 on
    # Windows rather than UTF-8. That silently mangles any accented name
    # (e.g. 'Loïs' -> 'LoÃ¯s') without raising an error, so this isn't
    # optional or just documentation.
    df = pd.read_csv(path, encoding="utf-8")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")

    df = df.drop(columns=[c for c in DROP_COLUMNS if c in df.columns])
    df = df.rename(columns=COLUMN_RENAME)
    df["season_label"] = season_label_from_filename(path)
    return df


def get_or_create_id(cur, table, id_col, unique_cols, row_values, cache):
    """Look up (or insert) a dimension row and return its surrogate id.
    Caches results in-process so a 2000+ row CSV doesn't issue a
    round trip to Postgres for every single lookup of the same team/player.
    """
    key = tuple(row_values[c] for c in unique_cols)
    if key in cache:
        return cache[key]

    # Use INSERT ... ON CONFLICT so concurrent ETL workers cannot race
    # between SELECT and INSERT and create duplicate dimension rows.
    cols = list(row_values.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    conflict_cols = ", ".join(unique_cols)
    cur.execute(
        f"""
        INSERT INTO {table} ({", ".join(cols)})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_cols}) DO UPDATE
            SET {unique_cols[0]} = EXCLUDED.{unique_cols[0]}
        RETURNING {id_col}
        """,
        [row_values[c] for c in cols],
    )
    new_id = cur.fetchone()[0]
    cache[key] = new_id
    return new_id

def clean_value(v):
    """NaN -> None so psycopg2 writes a real SQL NULL instead of the
    string 'nan'."""
    return None if pd.isna(v) else v


def insert_stat_group(cur, table, stat_id, row, columns):
    values = [clean_value(row[c]) for c in columns]
    placeholders = ", ".join(["%s"] * len(columns))
    cur.execute(
        f"INSERT INTO {table} (stat_id, {', '.join(columns)}) VALUES (%s, {placeholders})",
        [stat_id] + values,
    )


def load_season_file(cur, path, caches, dry_run=False):
    df = load_and_clean_csv(path)
    season_label = df["season_label"].iloc[0]
    start_year = int(season_label[:4])

    season_id = get_or_create_id(
        cur, "seasons", "season_id", ["season_label"],
        {"season_label": season_label, "start_year": start_year, "has_xa_data": False},
        caches["seasons"],
    )

    inserted, skipped = 0, 0
    for row_number, (_, row) in enumerate(df.iterrows(), start=1):
        savepoint = f"row_{row_number}"
        cur.execute(f"SAVEPOINT {savepoint}")

        try:
            league_id = get_or_create_id(
                cur,
                "leagues",
                "league_id",
                ["league_name"],
                {"league_name": row["league_name"]},
                caches["leagues"],
            )
            team_id = get_or_create_id(
                cur,
                "teams",
                "team_id",
                ["team_name"],
                {"team_name": row["team_name"]},
                caches["teams"],
            )
            player_id = get_or_create_id(
                cur,
                "players",
                "player_id",
                ["player_name", "born"],
                {
                    "player_name": row["player_name"],
                    "nation": row["nation"],
                    "born": int(row["born"]),
                },
                caches["players"],
            )

            cur.execute(
                """
                INSERT INTO player_season_stats
                    (player_id, team_id, season_id, league_id, position,
                    age, matches_played, minutes_played)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_id, team_id, season_id) DO NOTHING
                RETURNING stat_id
                """,
                (
                    player_id,
                    team_id,
                    season_id,
                    league_id,
                    row["position"],
                    int(row["age"]),
                    int(row["matches_played"]),
                    int(row["minutes_played"]),
                ),
            )
            result = cur.fetchone()

            if result is None:
                skipped += 1
                cur.execute(f"RELEASE SAVEPOINT {savepoint}")
                continue

            stat_id = result[0]
            for table, columns in STAT_GROUP_TABLES.items():
                insert_stat_group(cur, table, stat_id, row, columns)

            cur.execute(f"RELEASE SAVEPOINT {savepoint}")
            inserted += 1

        except Exception:
            logger.exception(
                "Failed on row %d for player=%s season=%s; rolling back row",
                row_number,
                row.get("player_name"),
                season_label,
            )
            cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            cur.execute(f"RELEASE SAVEPOINT {savepoint}")
            skipped += 1

    verb = "would insert" if dry_run else "inserted"
    logger.info(
        "%s: %s=%d skipped=%d (season=%s)",
        os.path.basename(path), verb, inserted, skipped, season_label,
    )
    return inserted, skipped


def run_etl(data_dir, dry_run=False):
    """Run the historical ETL and return inserted/skipped row counts.

    Dry-run executes the same parsing, validation, and database transaction
    path as a real load, then rolls the transaction back instead of committing.
    """
    csv_files = sorted(glob.glob(os.path.join(data_dir, "cleaned_*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "DB_PASSWORD must be set; refusing to use an insecure default password"
        )

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    caches = {"seasons": {}, "leagues": {}, "teams": {}, "players": {}}
    total_inserted, total_skipped = 0, 0

    try:
        with conn.cursor() as cur:
            for path in csv_files:
                ins, skip = load_season_file(cur, path, caches, dry_run=dry_run)
                total_inserted += ins
                total_skipped += skip

        if dry_run:
            conn.rollback()
            logger.info(
                "DRY RUN complete - transaction rolled back. "
                "Would have inserted %d rows, skipped %d.",
                total_inserted, total_skipped,
            )
        else:
            conn.commit()
            logger.info(
                "ETL complete - inserted %d rows, skipped %d, across %d seasons.",
                total_inserted, total_skipped, len(csv_files),
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                logger.info("Refreshing mv_player_season_full...")
                cur.execute("REFRESH MATERIALIZED VIEW mv_player_season_full")
            logger.info("Materialized view refreshed.")
        return total_inserted, total_skipped
    except Exception:
        conn.rollback()
        logger.exception("ETL failed, transaction rolled back.")
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                        help="Directory containing the cleaned_*.csv files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and validate everything but roll back instead of committing")
    args = parser.parse_args()

    logger.info(
        "Found %d season files in %s",
        len(glob.glob(os.path.join(args.data_dir, "cleaned_*.csv"))),
        args.data_dir,
    )
    run_etl(args.data_dir, dry_run=args.dry_run)

if __name__ == "__main__":
    main()