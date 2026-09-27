from typing import List
from fastapi import APIRouter, HTTPException, Query
  
from app.db import get_cursor
from app.schemas import PlayerSeasonStats
   
router = APIRouter(prefix="/compare", tags=["compare"])
    
@router.get("", response_model=List[PlayerSeasonStats])
def compare_players(
    player_ids: List[int] = Query(..., description="2 to 10 player IDs to compare"),
    season: str = Query(..., description="Season label, e.g. '2023-2024'"),
):
    if not (2 <= len(player_ids) <= 10):
        raise HTTPException(status_code=400, detail="Provide between 2 and 10 player_ids")
                      
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM mv_player_season_full
            WHERE player_id = ANY(%s) AND season_label = %s
            """,
            (player_ids, season),
        )
        rows = cur.fetchall()
                                              
    found_ids = {row["player_id"] for row in rows}
    missing = set(player_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"No data for season {season} for player_id(s): {sorted(missing)}",
        )
    return rows
                                                                       

