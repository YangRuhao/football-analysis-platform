from typing import List
import re

from fastapi import APIRouter, HTTPException, Query

from app.db import get_cursor
from app.schemas import PlayerSeasonStats

router = APIRouter(prefix="/compare", tags=["compare"])
SEASON_PATTERN = re.compile(r"^\d{4}-\d{4}$")


@router.get("", response_model=List[PlayerSeasonStats])
def compare_players(
    player_ids: List[int] = Query(..., min_length=2, max_length=6),
    season: str = Query(..., pattern=r"^\d{4}-\d{4}$"),
):
    unique_ids = list(dict.fromkeys(player_ids))
    if len(unique_ids) != len(player_ids):
        raise HTTPException(status_code=400, detail="player_ids must be unique")
    if not SEASON_PATTERN.fullmatch(season):
        raise HTTPException(status_code=422, detail="season must use YYYY-YYYY format")

    with get_cursor() as cur:
        cur.execute(
            """
            WITH stints AS (
                SELECT *
                FROM mv_player_season_full
                WHERE player_id = ANY(%s) AND season_label = %s
            ),
            primary_stint AS (
                SELECT DISTINCT ON (player_id)
                    player_id,
                    team_name,
                    league_name,
                    position,
                    age
                FROM stints
                ORDER BY player_id, minutes_played DESC NULLS LAST, team_name
            ),
            aggregated AS (
                SELECT
                    s.player_id,
                    MAX(s.player_name) AS player_name,
                    MAX(s.nation) AS nation,
                    MAX(s.born) AS born,
                    MAX(s.season_label) AS season_label,
                    SUM(COALESCE(s.matches_played, 0))::int AS matches_played,
                    SUM(COALESCE(s.minutes_played, 0))::int AS minutes_played,
                    SUM(COALESCE(s.goals, 0))::int AS goals,
                    SUM(COALESCE(s.assists, 0))::int AS assists,
                    SUM(COALESCE(s.goals_and_assists, 0))::int AS goals_and_assists,
                    SUM(COALESCE(s.non_penalty_goals, 0))::int AS non_penalty_goals,
                    SUM(COALESCE(s.penalty_kicks_made, 0))::int AS penalty_kicks_made,
                    SUM(COALESCE(s.xg, 0))::numeric AS xg,
                    SUM(COALESCE(s.npxg, 0))::numeric AS npxg,
                    SUM(COALESCE(s.total_shots, 0))::int AS total_shots,
                    SUM(COALESCE(s.progressive_passes, 0))::int AS progressive_passes,
                    SUM(COALESCE(s.key_passes, 0))::int AS key_passes,
                    SUM(COALESCE(s.passes_completed, 0))::int AS passes_completed,
                    SUM(COALESCE(s.passes_attempted, 0))::int AS passes_attempted,
                    SUM(COALESCE(s.progressive_carries, 0))::int AS progressive_carries,
                    SUM(COALESCE(s.take_ons_attempted, 0))::int AS take_ons_attempted,
                    SUM(COALESCE(s.tackles_attempted, 0))::int AS tackles_attempted,
                    SUM(COALESCE(s.tackles_won, 0))::int AS tackles_won,
                    SUM(COALESCE(s.interceptions, 0))::int AS interceptions,
                    SUM(COALESCE(s.clearances, 0))::int AS clearances,
                    SUM(COALESCE(s.shots_blocked, 0))::int AS shots_blocked,
                    SUM(COALESCE(s.passes_blocked, 0))::int AS passes_blocked,
                    SUM(COALESCE(s.saves, 0))::int AS saves,
                    SUM(COALESCE(s.goals_against, 0))::int AS goals_against,
                    SUM(COALESCE(s.clean_sheets, 0))::int AS clean_sheets,
                    SUM(COALESCE(s.crosses_stopped, 0))::int AS crosses_stopped,
                    SUM(COALESCE(s.shot_creating_actions_p90, 0) * COALESCE(s.nineties, 0))::numeric AS sca_total,
                    SUM(COALESCE(s.goal_creating_actions_p90, 0) * COALESCE(s.nineties, 0))::numeric AS gca_total,
                    MAX(s.pass_completion_pct) AS pass_completion_pct,
                    MAX(s.take_ons_successful_pct) AS take_ons_successful_pct,
                    MAX(s.aerial_duels_won_pct) AS aerial_duels_won_pct,
                    MAX(s.save_pct) AS save_pct
                FROM stints s
                GROUP BY s.player_id
            )
            SELECT
                a.*,
                p.team_name,
                p.league_name,
                p.position,
                p.age,
                CASE WHEN a.minutes_played > 0 THEN a.goals * 90.0 / a.minutes_played END AS goals_p90,
                CASE WHEN a.minutes_played > 0 THEN a.assists * 90.0 / a.minutes_played END AS assists_p90,
                CASE WHEN a.minutes_played > 0 THEN a.total_shots * 90.0 / a.minutes_played END AS shots_p90,
                CASE WHEN a.minutes_played > 0 THEN a.progressive_passes * 90.0 / a.minutes_played END AS progressive_passes_p90,
                CASE WHEN a.minutes_played > 0 THEN a.progressive_carries * 90.0 / a.minutes_played END AS progressive_carries_p90,
                CASE WHEN a.minutes_played > 0 THEN a.key_passes * 90.0 / a.minutes_played END AS key_passes_p90,
                CASE WHEN a.minutes_played > 0 THEN a.sca_total * 90.0 / a.minutes_played END AS shot_creating_actions_p90,
                CASE WHEN a.minutes_played > 0 THEN a.gca_total * 90.0 / a.minutes_played END AS goal_creating_actions_p90,
                CASE WHEN a.minutes_played > 0 THEN a.tackles_won * 90.0 / a.minutes_played END AS tackles_won_p90,
                CASE WHEN a.minutes_played > 0 THEN a.interceptions * 90.0 / a.minutes_played END AS interceptions_p90,
                CASE WHEN a.minutes_played > 0 THEN a.clearances * 90.0 / a.minutes_played END AS clearances_p90,
                CASE WHEN a.minutes_played > 0 THEN a.saves * 90.0 / a.minutes_played END AS saves_p90,
                CASE WHEN a.minutes_played > 0 THEN a.goals_against * 90.0 / a.minutes_played END AS goals_against_p90,
                CASE WHEN a.minutes_played > 0 THEN a.clean_sheets * 90.0 / a.minutes_played END AS clean_sheets_p90,
                CASE WHEN a.minutes_played > 0 THEN a.crosses_stopped * 90.0 / a.minutes_played END AS crosses_stopped_p90,
                CASE WHEN a.passes_attempted > 0 THEN a.passes_completed * 100.0 / a.passes_attempted END AS aggregated_pass_completion_pct
            FROM aggregated a
            JOIN primary_stint p ON p.player_id = a.player_id
            ORDER BY array_position(%s, a.player_id)
            """,
            (unique_ids, season, unique_ids),
        )
        rows = cur.fetchall()

    found_ids = {row["player_id"] for row in rows}
    missing = set(unique_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"No data for season {season} for player_id(s): {sorted(missing)}",
        )
    return rows
