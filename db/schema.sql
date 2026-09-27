-- ===== Dimensions =====
CREATE TABLE leagues (
    league_id     SERIAL PRIMARY KEY,
    league_name   VARCHAR(50) NOT NULL UNIQUE   -- Premier League, La Liga, Bundesliga, Serie A, Ligue 1
);

CREATE TABLE seasons (
    season_id          SERIAL PRIMARY KEY,
    season_label        VARCHAR(9) NOT NULL UNIQUE,  -- '2017-2018'
    start_year           SMALLINT NOT NULL,
    has_xa_data           BOOLEAN NOT NULL DEFAULT FALSE  -- FALSE for all 7 historical seasons; only relevant if you later add a source that has xA
);

CREATE TABLE teams (
    team_id       SERIAL PRIMARY KEY,
    team_name     VARCHAR(100) NOT NULL UNIQUE   -- 'squad' column
);

CREATE TABLE players (
    player_id      SERIAL PRIMARY KEY,
    player_name    VARCHAR(150) NOT NULL,
    nation         VARCHAR(50),
    born           SMALLINT,
    UNIQUE (player_name, born)          -- dedupe key across seasons/files
);

-- ===== Core fact table (one row per player-team-season stint) =====
CREATE TABLE player_season_stats (
    stat_id           SERIAL PRIMARY KEY,
    player_id         INT NOT NULL REFERENCES players(player_id),
    team_id           INT NOT NULL REFERENCES teams(team_id),
    season_id         INT NOT NULL REFERENCES seasons(season_id),
    league_id         INT NOT NULL REFERENCES leagues(league_id),
    position          VARCHAR(5),        -- 'DF','MF','FW','GK' — single value in this dataset
    age               SMALLINT,
    matches_played    SMALLINT,
    minutes_played    INT,               -- renamed from the mislabeled 'Avg Mins per Match'
    nineties          NUMERIC(6,2) GENERATED ALWAYS AS (minutes_played / 90.0) STORED,
    UNIQUE (player_id, team_id, season_id)
);
CREATE INDEX idx_pss_player   ON player_season_stats(player_id);
CREATE INDEX idx_pss_season   ON player_season_stats(season_id);
CREATE INDEX idx_pss_position ON player_season_stats(position);

-- ===== Attacking (no xA — only xG/npxG exist) =====
CREATE TABLE player_season_attacking (
    stat_id             INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    goals               SMALLINT,
    assists             SMALLINT,
    goals_and_assists   SMALLINT,
    non_penalty_goals   SMALLINT,
    penalty_kicks_made  SMALLINT,
    xg                  NUMERIC(5,2),    -- 'Expected Goals'
    npxg                NUMERIC(5,2),    -- 'Exp NPG'
    goals_p90           NUMERIC(4,2),
    assists_p90         NUMERIC(4,2),
    total_shots         SMALLINT,
    shots_on_target_pct NUMERIC(5,2),
    shots_p90           NUMERIC(4,2),
    goals_per_shot      NUMERIC(4,2),
    goals_per_shot_on_target NUMERIC(4,2),
    shot_creating_actions_p90 NUMERIC(4,2),
    goal_creating_actions_p90 NUMERIC(4,2)
);

-- ===== Passing =====
CREATE TABLE player_season_passing (
    stat_id                  INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    progressive_passes       SMALLINT,
    passes_completed         SMALLINT,
    passes_attempted         SMALLINT,
    pass_completion_pct      NUMERIC(5,2),
    progressive_pass_distance INT,
    short_pass_completion_pct NUMERIC(5,2),
    medium_pass_completion_pct NUMERIC(5,2),
    long_pass_completion_pct  NUMERIC(5,2),
    key_passes                SMALLINT,
    passes_into_final_third   SMALLINT,   -- source column '1/3'
    passes_into_penalty_area  SMALLINT
);

-- ===== Possession / carrying =====
CREATE TABLE player_season_possession (
    stat_id                  INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    progressive_carries      SMALLINT,   -- de-duped ('Progressive Carries' == 'carries_prgc')
    take_ons_attempted       SMALLINT,
    take_ons_successful_pct  NUMERIC(5,2),
    times_tackled_on_take_on SMALLINT,
    carries_into_final_third SMALLINT,
    carries_into_penalty_area SMALLINT,
    possessions_lost         SMALLINT,
    touches_def_penalty_area SMALLINT     -- only zone-specific touches available, no total touches
);

-- ===== Defense =====
CREATE TABLE player_season_defense (
    stat_id             INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    tackles_attempted   SMALLINT,
    tackles_won         SMALLINT,
    dribbles_tackled_pct NUMERIC(5,2),
    shots_blocked       SMALLINT,
    passes_blocked      SMALLINT,
    interceptions       SMALLINT,
    clearances          SMALLINT,
    errors              SMALLINT,
    aerial_duels_won_pct NUMERIC(5,2)
);

-- ===== Goalkeeping (separate — mostly null/zero for outfield players) =====
CREATE TABLE player_season_goalkeeping (
    stat_id           INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    goals_against      SMALLINT,
    goals_against_p90   NUMERIC(4,2),
    saves               SMALLINT,
    save_pct            NUMERIC(5,2),
    clean_sheets        SMALLINT,
    clean_sheet_pct     NUMERIC(5,2),
    penalty_save_pct    NUMERIC(5,2),
    crosses_stopped     SMALLINT
);

-- ===== Supporting tables (unchanged from before) =====
CREATE TABLE player_llm_summaries (
    summary_id       SERIAL PRIMARY KEY,
    player_id        INT NOT NULL REFERENCES players(player_id),
    season_id        INT REFERENCES seasons(season_id),
    summary_text     TEXT NOT NULL,
    model_used       VARCHAR(50),
    stats_snapshot   JSONB,
    generated_at     TIMESTAMP DEFAULT now()
);

CREATE TABLE data_sources (
    source_id        SERIAL PRIMARY KEY,
    source_name      VARCHAR(100) NOT NULL,
    seasons_covered  VARCHAR(50),
    retrieved_date   DATE,
    notes            TEXT
);
