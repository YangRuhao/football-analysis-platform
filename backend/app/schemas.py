from typing import List, Optional
from pydantic import BaseModel, ConfigDict
    
class PlayerSearchResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    player_id: int
    player_name: str
    nation: Optional[str] = None
    born: Optional[int] = None

class PlayerSeasonStats(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    player_id: int
    player_name: str
    season_label: Optional[str] = None
    stat_id: Optional[int] = None
    nation: Optional[str] = None
    born: Optional[int] = None
    team_name: Optional[str] = None
    league_name: Optional[str] = None
    has_xa_data: Optional[bool] = None
    position: Optional[str] = None
    age: Optional[int] = None
    matches_played: Optional[int] = None
    minutes_played: Optional[int] = None
    nineties: Optional[float] = None
                                                                                      
    # Attacking
    goals: Optional[int] = None
    assists: Optional[int] = None
    goals_and_assists: Optional[int] = None
    non_penalty_goals: Optional[int] = None
    penalty_kicks_made: Optional[int] = None
    xg: Optional[float] = None
    npxg: Optional[float] = None
    goals_p90: Optional[float] = None
    assists_p90: Optional[float] = None
    total_shots: Optional[int] = None
    shots_on_target_pct: Optional[float] = None
    shots_p90: Optional[float] = None
    goals_per_shot: Optional[float] = None
    goals_per_shot_on_target: Optional[float] = None
    shot_creating_actions_p90: Optional[float] = None
    goal_creating_actions_p90: Optional[float] = None                                                                                                                                              
    # Passing
    progressive_passes: Optional[int] = None
    passes_completed: Optional[int] = None
    passes_attempted: Optional[int] = None
    pass_completion_pct: Optional[float] = None
    progressive_pass_distance: Optional[int] = None
    short_pass_completion_pct: Optional[float] = None
    medium_pass_completion_pct: Optional[float] = None
    long_pass_completion_pct: Optional[float] = None
    key_passes: Optional[int] = None
    passes_into_final_third: Optional[int] = None
    passes_into_penalty_area: Optional[int] = None                                                                                                                                                 
    # Possession
    progressive_carries: Optional[int] = None
    take_ons_attempted: Optional[int] = None
    take_ons_successful_pct: Optional[float] = None
    times_tackled_on_take_on: Optional[int] = None
    carries_into_final_third: Optional[int] = None
    carries_into_penalty_area: Optional[int] = None
    possessions_lost: Optional[int] = None
    touches_def_penalty_area: Optional[int] = None                                                                                                                                                 
    # Defense
    tackles_attempted: Optional[int] = None
    tackles_won: Optional[int] = None
    dribbles_tackled_pct: Optional[float] = None
    shots_blocked: Optional[int] = None
    passes_blocked: Optional[int] = None
    interceptions: Optional[int] = None
    clearances: Optional[int] = None
    errors: Optional[int] = None
    aerial_duels_won_pct: Optional[float] = None
                                                                                                                   
    # Goalkeeping
    goals_against: Optional[int] = None
    goals_against_p90: Optional[float] = None
    saves: Optional[int] = None
    save_pct: Optional[float] = None
    clean_sheets: Optional[int] = None
    clean_sheet_pct: Optional[float] = None
    penalty_save_pct: Optional[float] = None
    crosses_stopped: Optional[int] = None                                                                                                                                                  

class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    player_id: int
    player_name: str
    value: Optional[float] = None
    team_name: Optional[str] = None
    league_name: Optional[str] = None
    season_label: Optional[str] = None
    position: Optional[str] = None
    minutes_played: Optional[int] = None
    metric: Optional[str] = None


class ProfilePlayer(BaseModel):
    model_config = ConfigDict(extra="allow")
    player_id: int
    player_name: str
    nation: Optional[str] = None
    born: Optional[int] = None
    age: Optional[int] = None
    position: Optional[str] = None

class ProfileSeason(BaseModel):
    model_config = ConfigDict(extra="allow")
    season_label: str
    minutes_played: int
    matches_played: int
    goals: int
    assists: int
    xg: Optional[float] = None
    npxg: Optional[float] = None

class ProfileComparison(BaseModel):
    position: str
    min_minutes: int
    player_count: int

class ProfileMetric(BaseModel):
    key: str
    label: str
    value: float
    percentile: float
    direction: str
    comparison_count: int

class PlayerProfileResponse(BaseModel):
    player: ProfilePlayer
    season: ProfileSeason
    comparison: ProfileComparison
    metrics: List[ProfileMetric]
