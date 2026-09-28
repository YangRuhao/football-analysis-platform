from typing import List, Optional
import re

from fastapi import APIRouter, HTTPException, Query

from app.db import get_cursor
from app.schemas import LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])
SEASON_PATTERN = re.compile(r"^\d{4}-\d{4}$")

ALLOWED_TABLES_BY_METRIC = {
    "goals": "player_season_attacking",
    "assists": "player_season_attacking",
    "goals_and_assists": "player_season_attacking",
    "xg": "player_season_attacking",
    "npxg": "player_season_attacking",
    "goals_p90": "player_season_attacking",
    "assists_p90": "player_season_attacking",
    "total_shots": "player_season_attacking",
    "shots_p90": "player_season_attacking",
    "shot_creating_actions_p90": "player_season_attacking",
    "goal_creating_actions_p90": "player_season_attacking",
    "progressive_passes": "player_season_passing",
    "pass_completion_pct": "player_season_passing",
    "key_passes": "player_season_passing",
    "progressive_carries": "player_season_possession",
    "take_ons_successful_pct": "player_season_possession",
    "tackles_won": "player_season_defense",
    "interceptions": "player_season_defense",
    "clearances": "player_season_defense",
    "aerial_duels_won_pct": "player_season_defense",
    "save_pct": "player_season_goalkeeping",
    "clean_sheets": "player_season_goalkeeping",
}


@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(
    season: str = Query(..., pattern=r"^\d{4}-\d{4}$"),
    metric: str = Query(...),
    position: Optional[str] = Query(None, min_length=2, max_length=2, pattern=r"^(DF|MF|FW|GK)$"),
    min_minutes: int = Query(900, ge=0, le=50000),
    limit: int = Query(50, ge=1, le=100),
):
    if metric not in ALLOWED_TABLES_BY_METRIC:
        raise HTTPException(status_code=400, detail=f"Unknown metric '{metric}'")

    stat_table = ALLOWED_TABLES_BY_METRIC[metric]
    query = f"""
        SELECT pss.player_id, p.player_name, t.team_name, l.league_name,
               s.season_label, pss.position, pss.minutes_played,
               %s AS metric, st.{metric} AS value
        FROM player_season_stats pss
        JOIN players p ON p.player_id = pss.player_id
        JOIN teams t ON t.team_id = pss.team_id
        JOIN leagues l ON l.league_id = pss.league_id
        JOIN seasons s ON s.season_id = pss.season_id
        JOIN {stat_table} st ON st.stat_id = pss.stat_id
        WHERE s.season_label = %s
          AND pss.minutes_played >= %s
          AND st.{metric} IS NOT NULL
    """
    params = [metric, season, min_minutes]
    if position:
        params.append(position.upper())
        query += " AND pss.position = %s"
    query += f" ORDER BY st.{metric} DESC LIMIT %s"
    params.append(limit)

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No leaderboard data for season={season}, metric={metric}")
    return rows
