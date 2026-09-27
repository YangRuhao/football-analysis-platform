from typing import List
from fastapi import APIRouter, HTTPException, Query
  
from app.db import get_cursor
from app.schemas import PlayerSearchResult, PlayerSeasonStats
   
router = APIRouter(prefix="/players", tags=["players"])
    
@router.get("/search", response_model=List[PlayerSearchResult])
def search_players(
    name: str = Query(..., min_length=2, description="Partial or full player name"),
    limit: int = Query(20, ge=1, le=100),
):
             
    """Case-insensitive partial-name search — this is what powers the dashboard's player lookup box."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT player_id, player_name, nation, born
            FROM players
            WHERE player_name ILIKE %s
            ORDER BY player_name
            LIMIT %s
            """,
            (f"%{name}%", limit),
        )
        rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No players found matching '{name}'")
    return rows                                                 

@router.get("/{player_id}", response_model=List[PlayerSeasonStats])
def get_player_career(player_id: int):
    """Every season-stint row for this player, oldest first. A list
    because a mid-season transfer produces two rows for one season."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM mv_player_season_full WHERE player_id = %s ORDER BY season_label",
            (player_id,),
        )
        rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for player_id {player_id}")
    return rows

@router.get("/{player_id}/seasons/{season_label}", response_model=List[PlayerSeasonStats])
def get_player_season(player_id: int, season_label: str):
    """One season's stat line(s) for this player."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM mv_player_season_full WHERE player_id = %s AND season_label = %s",
            (player_id, season_label),
        )
        rows = cur.fetchall()
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No data for player_id {player_id} in season {season_label}",
        )
    return rows

