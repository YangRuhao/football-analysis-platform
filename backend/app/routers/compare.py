from typing import List
import re

from fastapi import APIRouter, HTTPException, Query

from app.db import get_cursor
from app.schemas import PlayerSeasonStats

router = APIRouter(prefix="/compare", tags=["compare"])
SEASON_PATTERN = re.compile(r"^\d{4}-\d{4}$")


@router.get("", response_model=List[PlayerSeasonStats])
def compare_players(
    player_ids: List[int] = Query(..., min_length=2, max_length=10),
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
            SELECT *
            FROM mv_player_season_full
            WHERE player_id = ANY(%s) AND season_label = %s
            ORDER BY player_name, team_name
            """,
            (unique_ids, season),
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
