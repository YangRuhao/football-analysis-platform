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
                -- Comparison reads the normalized source tables directly rather
                -- than the materialized dashboard view. This guarantees that a
                -- comparison sees the latest committed player statistics even
                -- if the materialized view has not been refreshed yet.
                SELECT
                    pss.player_id,
                    pss.team_id,
                    pss.season_id,
                    pss.league_id,
                    pss.position,
                    pss.age,
                    pss.matches_played,
                    pss.minutes_played,
                    p.player_name,
                    p.nation,
                    p.born,
                    t.team_name,
                    l.league_name,
                    s.season_label,
                    a.goals,
                    a.assists,
                    a.goals_and_assists,
                    a.non_penalty_goals,
                    a.penalty_kicks_made,
                    a.xg,
                    a.npxg,
                    a.total_shots,
                    a.shot_creating_actions_p90,
                    a.goal_creating_actions_p90,
                    ps.progressive_passes,
                    ps.passes_completed,
                    ps.passes_attempted,
                    ps.key_passes,
                    po.progressive_carries,
                    po.take_ons_attempted,
                    po.take_ons_successful_pct,
                    d.tackles_attempted,
                    d.tackles_won,
                    d.interceptions,
                    d.clearances,
                    d.shots_blocked,
                    d.passes_blocked,
                    d.aerial_duels_won_pct,
                    gk.saves,
                    gk.goals_against,
                    gk.clean_sheets,
                    gk.crosses_stopped
                FROM player_season_stats pss
                JOIN players p ON p.player_id = pss.player_id
                JOIN teams t ON t.team_id = pss.team_id
                JOIN leagues l ON l.league_id = pss.league_id
                JOIN seasons s ON s.season_id = pss.season_id
                LEFT JOIN player_season_attacking a ON a.stat_id = pss.stat_id
                LEFT JOIN player_season_passing ps ON ps.stat_id = pss.stat_id
                LEFT JOIN player_season_possession po ON po.stat_id = pss.stat_id
                LEFT JOIN player_season_defense d ON d.stat_id = pss.stat_id
                LEFT JOIN player_season_goalkeeping gk ON gk.stat_id = pss.stat_id
                WHERE pss.player_id = ANY(%s) AND s.season_label = %s
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
                    COALESCE(SUM(s.matches_played), 0)::int AS matches_played,
                    COALESCE(SUM(s.minutes_played), 0)::int AS minutes_played,
                    COALESCE(SUM(s.goals), 0)::int AS goals,
                    COALESCE(SUM(s.assists), 0)::int AS assists,
                    COALESCE(SUM(s.goals_and_assists), 0)::int AS goals_and_assists,
                    COALESCE(SUM(s.non_penalty_goals), 0)::int AS non_penalty_goals,
                    COALESCE(SUM(s.penalty_kicks_made), 0)::int AS penalty_kicks_made,
                    COALESCE(SUM(s.xg), 0)::numeric AS xg,
                    COALESCE(SUM(s.npxg), 0)::numeric AS npxg,
                    COALESCE(SUM(s.total_shots), 0)::int AS total_shots,
                    COALESCE(SUM(s.progressive_passes), 0)::int AS progressive_passes,
                    COALESCE(SUM(s.key_passes), 0)::int AS key_passes,
                    COALESCE(SUM(s.passes_completed), 0)::int AS passes_completed,
                    COALESCE(SUM(s.passes_attempted), 0)::int AS passes_attempted,
                    COALESCE(SUM(s.progressive_carries), 0)::int AS progressive_carries,
                    COALESCE(SUM(s.take_ons_attempted), 0)::int AS take_ons_attempted,
                    COALESCE(SUM(s.tackles_attempted), 0)::int AS tackles_attempted,
                    COALESCE(SUM(s.tackles_won), 0)::int AS tackles_won,
                    COALESCE(SUM(s.interceptions), 0)::int AS interceptions,
                    COALESCE(SUM(s.clearances), 0)::int AS clearances,
                    COALESCE(SUM(s.shots_blocked), 0)::int AS shots_blocked,
                    COALESCE(SUM(s.passes_blocked), 0)::int AS passes_blocked,
                    COALESCE(SUM(s.saves), 0)::int AS saves,
                    COALESCE(SUM(s.goals_against), 0)::int AS goals_against,
                    COALESCE(SUM(s.clean_sheets), 0)::int AS clean_sheets,
                    COALESCE(SUM(s.crosses_stopped), 0)::int AS crosses_stopped,
                    SUM(CASE WHEN s.take_ons_successful_pct IS NOT NULL THEN COALESCE(s.take_ons_attempted, 0) * s.take_ons_successful_pct / 100.0 ELSE 0 END)::numeric AS successful_take_ons,
                    SUM(COALESCE(s.shot_creating_actions_p90, 0) * (COALESCE(s.minutes_played, 0) / 90.0))::numeric AS sca_total,
                    SUM(COALESCE(s.goal_creating_actions_p90, 0) * (COALESCE(s.minutes_played, 0) / 90.0))::numeric AS gca_total,
                    SUM(CASE WHEN s.aerial_duels_won_pct IS NOT NULL THEN s.aerial_duels_won_pct * COALESCE(s.minutes_played, 0) ELSE 0 END)::numeric AS aerial_pct_minutes_weighted,
                    SUM(CASE WHEN s.aerial_duels_won_pct IS NOT NULL THEN COALESCE(s.minutes_played, 0) ELSE 0 END)::int AS aerial_pct_minutes
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
                CASE WHEN a.passes_attempted > 0 THEN a.passes_completed * 100.0 / a.passes_attempted END AS pass_completion_pct,
                CASE WHEN a.take_ons_attempted > 0 THEN a.successful_take_ons * 100.0 / a.take_ons_attempted END AS take_ons_successful_pct,
                CASE WHEN a.saves + a.goals_against > 0 THEN a.saves * 100.0 / (a.saves + a.goals_against) END AS save_pct,
                CASE WHEN a.aerial_pct_minutes > 0 THEN a.aerial_pct_minutes_weighted / a.aerial_pct_minutes END AS aerial_duels_won_pct
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
