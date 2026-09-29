-- The Full schema for the football analytics platform.
-- Column set here matches exactly what load_historical.py inserts,
-- which in turn matches the actual columns confirmed present in the
-- 7 historical FBref/Kaggle CSVs (2017/18-2023/24). 
-- Notably: there is no xA/xAG column anywhere in that dataset, only xG and npxG.

-- ===================== Dimensions =====================

CREATE TABLE leagues (
    league_id     SERIAL PRIMARY KEY,
    league_name   VARCHAR(50) NOT NULL UNIQUE
    -- Premier League, La Liga, Bundesliga, Serie A, Ligue 1
);

CREATE TABLE seasons (
    season_id      SERIAL PRIMARY KEY,
    season_label   VARCHAR(9) NOT NULL UNIQUE,   -- '2017-2018'
    start_year     SMALLINT NOT NULL,
    -- Whether this season's source data includes expected-assist figures.
    -- FALSE for all 7 historical seasons in the current dataset, since
    -- xA/xAG isn't present anywhere in it. Kept as a flag (not hardcoded
    -- logic) so a future data source that does include xA doesn't require
    -- a schema change.
    has_xa_data    BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (start_year BETWEEN 1900 AND 2100)
);

CREATE TABLE teams (
    team_id     SERIAL PRIMARY KEY,
    team_name   VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE players (
    player_id     SERIAL PRIMARY KEY,
    player_name   VARCHAR(150) NOT NULL,
    nation        VARCHAR(50),
    born          SMALLINT,
    UNIQUE (player_name, born),   -- dedupe key across seasons/files
    CHECK (born IS NULL OR born BETWEEN 1900 AND 2100)
);

-- ===================== Core fact table =====================
-- One row per player-team-season stint. A mid-season transfer produces
-- two rows (one per team), which is expected and confirmed to occur in
-- the source data (114 such players in the 2023/24 file alone).

CREATE TABLE player_season_stats (
    stat_id          SERIAL PRIMARY KEY,
    player_id        INT NOT NULL REFERENCES players(player_id),
    team_id          INT NOT NULL REFERENCES teams(team_id),
    season_id        INT NOT NULL REFERENCES seasons(season_id),
    league_id        INT NOT NULL REFERENCES leagues(league_id),
    position         VARCHAR(5),      -- 'DF','MF','FW','GK'
    age              SMALLINT,
    matches_played   SMALLINT,
    minutes_played   INT,             -- renamed from the source's mislabeled 'Avg Mins per Match'
    nineties         NUMERIC(6,2) GENERATED ALWAYS AS (minutes_played / 90.0) STORED,
    UNIQUE (player_id, team_id, season_id),
    CHECK (minutes_played >= 0),
    CHECK (matches_played >= 0),
    CHECK (age IS NULL OR age BETWEEN 0 AND 100)
);

CREATE INDEX idx_pss_player   ON player_season_stats(player_id);
CREATE INDEX idx_pss_season   ON player_season_stats(season_id);
CREATE INDEX idx_pss_position ON player_season_stats(position);
CREATE INDEX idx_pss_league   ON player_season_stats(league_id);

-- ===================== Attacking =====================
-- No xA/xAG column exists in the source — only xg and npxg.

CREATE TABLE player_season_attacking (
    stat_id                    INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    goals                      SMALLINT,
    assists                    SMALLINT,
    goals_and_assists          SMALLINT,
    non_penalty_goals          SMALLINT,
    penalty_kicks_made         SMALLINT,
    xg                         NUMERIC(5,2),   -- 'Expected Goals'
    npxg                       NUMERIC(5,2),   -- 'Exp NPG'
    goals_p90                  NUMERIC(4,2),
    assists_p90                NUMERIC(4,2),
    total_shots                SMALLINT,
    shots_on_target_pct        NUMERIC(5,2),
    shots_p90                  NUMERIC(4,2),
    goals_per_shot             NUMERIC(4,2),
    goals_per_shot_on_target   NUMERIC(4,2),
    shot_creating_actions_p90  NUMERIC(4,2),
    goal_creating_actions_p90  NUMERIC(4,2)
,
    CHECK (shots_on_target_pct IS NULL OR shots_on_target_pct BETWEEN 0 AND 100)
);

-- ===================== Passing =====================

CREATE TABLE player_season_passing (
    stat_id                     INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    progressive_passes          SMALLINT,
    passes_completed            SMALLINT,
    passes_attempted            SMALLINT,
    pass_completion_pct         NUMERIC(5,2),
    progressive_pass_distance   INT,
    short_pass_completion_pct   NUMERIC(5,2),
    medium_pass_completion_pct  NUMERIC(5,2),
    long_pass_completion_pct    NUMERIC(5,2),
    key_passes                  SMALLINT,
    passes_into_final_third     SMALLINT,   -- source column '1/3'
    passes_into_penalty_area    SMALLINT
,
    CHECK (pass_completion_pct IS NULL OR pass_completion_pct BETWEEN 0 AND 100),
    CHECK (short_pass_completion_pct IS NULL OR short_pass_completion_pct BETWEEN 0 AND 100),
    CHECK (medium_pass_completion_pct IS NULL OR medium_pass_completion_pct BETWEEN 0 AND 100),
    CHECK (long_pass_completion_pct IS NULL OR long_pass_completion_pct BETWEEN 0 AND 100)
);

-- ===================== Possession / carrying =====================

CREATE TABLE player_season_possession (
    stat_id                     INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    progressive_carries         SMALLINT,   -- de-duped ('Progressive Carries' == 'carries_prgc')
    take_ons_attempted          SMALLINT,
    take_ons_successful_pct     NUMERIC(5,2),
    times_tackled_on_take_on    SMALLINT,
    carries_into_final_third    SMALLINT,
    carries_into_penalty_area   SMALLINT,
    possessions_lost            SMALLINT,
    touches_def_penalty_area    SMALLINT    -- only zone-specific touches available in source, no total touches
,
    CHECK (take_ons_successful_pct IS NULL OR take_ons_successful_pct BETWEEN 0 AND 100)
);

-- ===================== Defense =====================

CREATE TABLE player_season_defense (
    stat_id                INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    tackles_attempted      SMALLINT,
    tackles_won            SMALLINT,
    dribbles_tackled_pct   NUMERIC(5,2),
    shots_blocked          SMALLINT,
    passes_blocked         SMALLINT,
    interceptions          SMALLINT,
    clearances             SMALLINT,
    errors                 SMALLINT,
    aerial_duels_won_pct   NUMERIC(5,2)
,
    CHECK (dribbles_tackled_pct IS NULL OR dribbles_tackled_pct BETWEEN 0 AND 100),
    CHECK (aerial_duels_won_pct IS NULL OR aerial_duels_won_pct BETWEEN 0 AND 100)
);

-- ===================== Goalkeeping =====================
-- Present on every row but 0/blank for outfield players.

CREATE TABLE player_season_goalkeeping (
    stat_id            INT PRIMARY KEY REFERENCES player_season_stats(stat_id),
    goals_against       SMALLINT,
    goals_against_p90    NUMERIC(4,2),
    saves                SMALLINT,
    save_pct             NUMERIC(5,2),
    clean_sheets         SMALLINT,
    clean_sheet_pct      NUMERIC(5,2),
    penalty_save_pct     NUMERIC(5,2),
    crosses_stopped      SMALLINT
,
    CHECK (save_pct IS NULL OR save_pct BETWEEN 0 AND 100),
    CHECK (clean_sheet_pct IS NULL OR clean_sheet_pct BETWEEN 0 AND 100),
    CHECK (penalty_save_pct IS NULL OR penalty_save_pct BETWEEN 0 AND 100)
);

-- ===================== Supporting tables =====================

-- Caches the LLM-generated write-up so it isn't regenerated on every page view.
CREATE TABLE player_llm_summaries (
    summary_id      SERIAL PRIMARY KEY,
    player_id       INT NOT NULL REFERENCES players(player_id),
    season_id       INT REFERENCES seasons(season_id),   -- NULL = career-wide summary
    summary_text    TEXT NOT NULL,
    model_used      VARCHAR(50),
    stats_snapshot  JSONB,     -- exact numbers the LLM was given, for traceability
    generated_at    TIMESTAMP DEFAULT now()
);

-- Provenance record for the README's data-sources section and for debugging.
CREATE TABLE data_sources (
    source_id        SERIAL PRIMARY KEY,
    source_name      VARCHAR(100) NOT NULL,
    seasons_covered  VARCHAR(50),
    retrieved_date   DATE,
    notes            TEXT
);

INSERT INTO data_sources (source_name, seasons_covered, retrieved_date, notes) VALUES
    ('FBref via Kaggle (akshankrithick, MIT licensed)', '2017-2018 to 2023-2024',
     CURRENT_DATE,
     'No xA/xAG column present in this dataset. "Avg Mins per Match" column '
     'was mislabeled in the source; it is actually total minutes played.');

-- ===================== Wide view for dashboard queries =====================
-- Refresh after each data load: REFRESH MATERIALIZED VIEW mv_player_season_full;

CREATE MATERIALIZED VIEW mv_player_season_full AS
SELECT
    pss.stat_id, pss.player_id, pss.team_id, pss.season_id, pss.league_id,
    pss.position, pss.age, pss.matches_played, pss.minutes_played, pss.nineties,
    p.player_name, p.nation, p.born,
    t.team_name,
    l.league_name,
    s.season_label, s.has_xa_data,

    a.goals, a.assists, a.goals_and_assists, a.non_penalty_goals,
    a.penalty_kicks_made, a.xg, a.npxg, a.goals_p90, a.assists_p90,
    a.total_shots, a.shots_on_target_pct, a.shots_p90, a.goals_per_shot,
    a.goals_per_shot_on_target, a.shot_creating_actions_p90, a.goal_creating_actions_p90,

    ps.progressive_passes, ps.passes_completed, ps.passes_attempted,
    ps.pass_completion_pct, ps.progressive_pass_distance,
    ps.short_pass_completion_pct, ps.medium_pass_completion_pct,
    ps.long_pass_completion_pct, ps.key_passes, ps.passes_into_final_third,
    ps.passes_into_penalty_area,

    po.progressive_carries, po.take_ons_attempted, po.take_ons_successful_pct,
    po.times_tackled_on_take_on, po.carries_into_final_third,
    po.carries_into_penalty_area, po.possessions_lost, po.touches_def_penalty_area,

    d.tackles_attempted, d.tackles_won, d.dribbles_tackled_pct, d.shots_blocked,
    d.passes_blocked, d.interceptions, d.clearances, d.errors, d.aerial_duels_won_pct,

    gk.goals_against, gk.goals_against_p90, gk.saves, gk.save_pct,
    gk.clean_sheets, gk.clean_sheet_pct, gk.penalty_save_pct, gk.crosses_stopped

FROM player_season_stats pss
JOIN players p  ON p.player_id = pss.player_id
JOIN teams t    ON t.team_id = pss.team_id
JOIN leagues l  ON l.league_id = pss.league_id
JOIN seasons s  ON s.season_id = pss.season_id
LEFT JOIN player_season_attacking a   ON a.stat_id = pss.stat_id
LEFT JOIN player_season_passing ps    ON ps.stat_id = pss.stat_id
LEFT JOIN player_season_possession po ON po.stat_id = pss.stat_id
LEFT JOIN player_season_defense d     ON d.stat_id = pss.stat_id
LEFT JOIN player_season_goalkeeping gk ON gk.stat_id = pss.stat_id;

CREATE UNIQUE INDEX idx_mv_player_season_full_stat_id ON mv_player_season_full(stat_id);
