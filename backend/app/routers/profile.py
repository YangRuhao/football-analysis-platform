from typing import List
import re

from fastapi import APIRouter, HTTPException, Query

from app.db import get_cursor
from app.schemas import PlayerProfileResponse

router = APIRouter(prefix="/players", tags=["players"])
SEASON_PATTERN = re.compile(r"^\d{4}-\d{4}$")

# These are the first profile radar templates. They deliberately use metrics
# that can be aggregated safely from the player-team-season rows. Percentiles
# are always calculated within the selected season + representative position
# + minimum-minutes cohort.
RADAR_METRICS = {
    "FW": [
        ("goals_p90", "Goals / 90", "higher"),
        ("xg_p90", "xG / 90", "higher"),
        ("assists_p90", "Assists / 90", "higher"),
        ("shots_p90", "Shots / 90", "higher"),
        ("shot_creating_actions_p90", "Shot-Creating Actions / 90", "higher"),
        ("goal_creating_actions_p90", "Goal-Creating Actions / 90", "higher"),
        ("progressive_carries_p90", "Progressive Carries / 90", "higher"),
    ],
    "MF": [
        ("goals_p90", "Goals / 90", "higher"),
        ("xg_p90", "xG / 90", "higher"),
        ("assists_p90", "Assists / 90", "higher"),
        ("progressive_passes_p90", "Progressive Passes / 90", "higher"),
        ("progressive_carries_p90", "Progressive Carries / 90", "higher"),
        ("key_passes_p90", "Key Passes / 90", "higher"),
        ("shot_creating_actions_p90", "Shot-Creating Actions / 90", "higher"),
    ],
    "DF": [
        ("progressive_passes_p90", "Progressive Passes / 90", "higher"),
        ("progressive_carries_p90", "Progressive Carries / 90", "higher"),
        ("tackles_won_p90", "Tackles Won / 90", "higher"),
        ("interceptions_p90", "Interceptions / 90", "higher"),
        ("clearances_p90", "Clearances / 90", "higher"),
        ("shots_blocked_p90", "Shots Blocked / 90", "higher"),
        ("passes_blocked_p90", "Passes Blocked / 90", "higher"),
    ],
    "GK": [
        ("saves_p90", "Saves / 90", "higher"),
        ("goals_against_p90", "Goals Against / 90", "lower"),
        ("clean_sheets_p90", "Clean Sheets / 90", "higher"),
        ("crosses_stopped_p90", "Crosses Stopped / 90", "higher"),
    ],
}


@router.get(
    "/{player_id}/profile/{season_label}",
    response_model=PlayerProfileResponse,
)
def get_player_profile(
    player_id: int,
    season_label: str,
    min_minutes: int = Query(900, ge=0, le=50000),
):
    if player_id < 1:
        raise HTTPException(status_code=422, detail="player_id must be positive")
    if not SEASON_PATTERN.fullmatch(season_label):
        raise HTTPException(status_code=422, detail="season must use YYYY-YYYY format")

    with get_cursor() as cur:
        cur.execute(
            """
            WITH player_seasons AS (
                SELECT
                    player_id,
                    MAX(player_name) AS player_name,
                    MAX(nation) AS nation,
                    MAX(born) AS born,
                    season_label,
                    (ARRAY_AGG(position ORDER BY minutes_played DESC NULLS LAST))[1] AS position,
                    (ARRAY_AGG(age ORDER BY minutes_played DESC NULLS LAST))[1] AS age,
                    SUM(COALESCE(minutes_played, 0))::int AS minutes_played,
                    SUM(COALESCE(matches_played, 0))::int AS matches_played,
                    SUM(COALESCE(goals, 0))::int AS goals,
                    SUM(COALESCE(assists, 0))::int AS assists,
                    SUM(COALESCE(xg, 0))::numeric AS xg,
                    SUM(COALESCE(npxg, 0))::numeric AS npxg,
                    SUM(COALESCE(total_shots, 0))::int AS total_shots,
                    SUM(COALESCE(progressive_passes, 0))::int AS progressive_passes,
                    SUM(COALESCE(progressive_carries, 0))::int AS progressive_carries,
                    SUM(COALESCE(key_passes, 0))::int AS key_passes,
                    SUM(COALESCE(shot_creating_actions_p90, 0) * COALESCE(nineties, 0))::numeric AS sca_total,
                    SUM(COALESCE(goal_creating_actions_p90, 0) * COALESCE(nineties, 0))::numeric AS gca_total,
                    SUM(COALESCE(tackles_won, 0))::int AS tackles_won,
                    SUM(COALESCE(interceptions, 0))::int AS interceptions,
                    SUM(COALESCE(clearances, 0))::int AS clearances,
                    SUM(COALESCE(shots_blocked, 0))::int AS shots_blocked,
                    SUM(COALESCE(passes_blocked, 0))::int AS passes_blocked,
                    SUM(COALESCE(saves, 0))::int AS saves,
                    SUM(COALESCE(goals_against, 0))::int AS goals_against,
                    SUM(COALESCE(clean_sheets, 0))::int AS clean_sheets,
                    SUM(COALESCE(crosses_stopped, 0))::int AS crosses_stopped
                FROM mv_player_season_full
                GROUP BY player_id, season_label
            ),
            metrics AS (
                SELECT
                    ps.*,
                    m.metric_key,
                    m.metric_label,
                    m.direction,
                    m.value
                FROM player_seasons ps
                CROSS JOIN LATERAL (
                    SELECT * FROM (VALUES
                        ('goals_p90', 'Goals / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.goals * 90.0 / ps.minutes_played END),
                        ('xg_p90', 'xG / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.xg * 90.0 / ps.minutes_played END),
                        ('assists_p90', 'Assists / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.assists * 90.0 / ps.minutes_played END),
                        ('shots_p90', 'Shots / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.total_shots * 90.0 / ps.minutes_played END),
                        ('progressive_passes_p90', 'Progressive Passes / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.progressive_passes * 90.0 / ps.minutes_played END),
                        ('progressive_carries_p90', 'Progressive Carries / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.progressive_carries * 90.0 / ps.minutes_played END),
                        ('key_passes_p90', 'Key Passes / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.key_passes * 90.0 / ps.minutes_played END),
                        ('shot_creating_actions_p90', 'Shot-Creating Actions / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.sca_total * 90.0 / ps.minutes_played END),
                        ('goal_creating_actions_p90', 'Goal-Creating Actions / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.gca_total * 90.0 / ps.minutes_played END),
                        ('tackles_won_p90', 'Tackles Won / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.tackles_won * 90.0 / ps.minutes_played END),
                        ('interceptions_p90', 'Interceptions / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.interceptions * 90.0 / ps.minutes_played END),
                        ('clearances_p90', 'Clearances / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.clearances * 90.0 / ps.minutes_played END),
                        ('shots_blocked_p90', 'Shots Blocked / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.shots_blocked * 90.0 / ps.minutes_played END),
                        ('passes_blocked_p90', 'Passes Blocked / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.passes_blocked * 90.0 / ps.minutes_played END),
                        ('saves_p90', 'Saves / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.saves * 90.0 / ps.minutes_played END),
                        ('goals_against_p90', 'Goals Against / 90', 'lower', CASE WHEN ps.minutes_played > 0 THEN ps.goals_against * 90.0 / ps.minutes_played END),
                        ('clean_sheets_p90', 'Clean Sheets / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.clean_sheets * 90.0 / ps.minutes_played END),
                        ('crosses_stopped_p90', 'Crosses Stopped / 90', 'higher', CASE WHEN ps.minutes_played > 0 THEN ps.crosses_stopped * 90.0 / ps.minutes_played END)
                    ) AS x(metric_key, metric_label, direction, value)
                ) m
            ),
            eligible AS (
                SELECT *
                FROM metrics
                WHERE season_label = %s
                  AND minutes_played >= %s
                  AND position IS NOT NULL
                  AND value IS NOT NULL
                  AND metric_key = ANY(%s)
            ),
            ranked AS (
                SELECT
                    e.*,
                    COUNT(*) OVER (PARTITION BY e.position, e.metric_key) AS comparison_count,
                    CASE
                        WHEN COUNT(*) OVER (PARTITION BY e.position, e.metric_key) = 1 THEN 1.0
                        WHEN e.direction = 'lower' THEN 1.0 - PERCENT_RANK() OVER (PARTITION BY e.position, e.metric_key ORDER BY e.value ASC)
                        ELSE PERCENT_RANK() OVER (PARTITION BY e.position, e.metric_key ORDER BY e.value ASC)
                    END AS percentile
                FROM eligible e
            )
            SELECT
                r.player_id, r.player_name, r.nation, r.born, r.season_label,
                r.position, r.age, r.minutes_played, r.matches_played,
                r.goals, r.assists, r.xg, r.npxg,
                r.metric_key, r.metric_label, r.direction, r.value,
                ROUND((r.percentile * 100)::numeric, 1) AS percentile,
                r.comparison_count
            FROM ranked r
            WHERE r.player_id = %s
            ORDER BY array_position(%s, r.metric_key)
            """,
            (
                season_label,
                min_minutes,
                [key for key, _, _ in RADAR_METRICS["FW"] + RADAR_METRICS["MF"] + RADAR_METRICS["DF"] + RADAR_METRICS["GK"]],
                player_id,
                [key for key, _, _ in RADAR_METRICS["FW"] + RADAR_METRICS["MF"] + RADAR_METRICS["DF"] + RADAR_METRICS["GK"]],
            ),
        )
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No profile data for player_id {player_id} in season {season_label} with min_minutes={min_minutes}",
        )

    position = rows[0]["position"]
    allowed = {key for key, _, _ in RADAR_METRICS.get(position, [])}
    rows = [row for row in rows if row["metric_key"] in allowed]
    if not rows:
        raise HTTPException(status_code=404, detail=f"No profile metrics available for position {position}")

    first = rows[0]
    return {
        "player": {
            "player_id": first["player_id"],
            "player_name": first["player_name"],
            "nation": first["nation"],
            "born": first["born"],
            "age": first["age"],
            "position": position,
        },
        "season": {
            "season_label": first["season_label"],
            "minutes_played": first["minutes_played"],
            "matches_played": first["matches_played"],
            "goals": first["goals"],
            "assists": first["assists"],
            "xg": float(first["xg"]) if first["xg"] is not None else None,
            "npxg": float(first["npxg"]) if first["npxg"] is not None else None,
        },
        "comparison": {
            "position": position,
            "min_minutes": min_minutes,
            "player_count": first["comparison_count"],
        },
        "metrics": [
            {
                "key": row["metric_key"],
                "label": row["metric_label"],
                "value": float(row["value"]),
                "percentile": float(row["percentile"]),
                "direction": row["direction"],
                "comparison_count": row["comparison_count"],
            }
            for row in rows
        ],
    }
