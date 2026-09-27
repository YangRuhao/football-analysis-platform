# Data Sources & Attribution

This project is a non-commercial, educational portfolio project. It does not claim
ownership of any underlying football statistics — all stats ultimately originate from
the providers credited below. This file documents where the data comes from, what
license applies, and the known quirks/limitations you should be aware of before
building on top of it.

## Historical data (2017/18 – 2023/24)

- **Original stats provider:** Opta, via [FBref](https://fbref.com) / Sports Reference.
- **Compiled dataset:** [FBref 2017-2024 for Europe's Top 5 Leagues](https://www.kaggle.com/datasets/akshankrithick/fbref-2017-2024-for-europes-top-5-leagues)
  by Akshan Krithick, on Kaggle.
- **License:** MIT (as stated by the Kaggle uploader for the compiled dataset).
- **Coverage:** Player-season statistics for Europe's top 5 leagues — Premier League,
  La Liga, Bundesliga, Serie A, Ligue 1 — across 7 seasons, 2017/18 through 2023/24.
- **Files used:** `cleaned_2017-18.csv` through `cleaned_2023-24.csv` (one file per
  season, 65 columns each, identical structure across all 7 files).
- **Retrieved:** September 2026.

FBref's advanced statistics (xG, per-90 breakdowns, progressive actions, etc.) were
pulled from the live FBref site in January 2026 following a data-provider dispute
with Opta. Because this dataset was scraped and published before that shutdown, it
still contains the full advanced-stat columns for all 7 seasons it covers.

### Known data quality notes

These are things we found while inspecting the raw files — noted here so nobody
downstream is caught off guard:

- **No expected assists (xA / xAG).** The dataset includes `Expected Goals` (xG) and
  `Exp NPG` (non-penalty xG), but **no expected-assists column exists anywhere in any
  of the 7 files.** This is a gap in the source data itself, not a processing choice
  on our end.
- **Per-90 coverage is limited.** Only goals, assists, shots, goals-against, and
  shot/goal-creating actions are provided as per-90 figures in the raw data.
  Everything else (progressive carries/passes, tackles, interceptions, key passes,
  etc.) is a **season total** — per-90 versions of those are computed by this
  project's pipeline, not sourced directly.
- **`Avg Mins per Match` is mislabeled.** Despite the column name, this is the
  player's **total minutes played** for that season/team, not an average per match
  (verified against known real-world totals). This project's schema stores it as
  `minutes_played` to avoid perpetuating the confusion.
- **Two exact duplicate columns** exist in the raw files: `Progressive Carries` /
  `carries_prgc`, and `Goals` / `Goals Scored`. Each pair is 100% identical; the
  duplicate is dropped during loading.
- **Goalkeeping stats share the same row structure as outfield stats** in the raw
  data (`Goals Against`, `Saves`, `Clean Sheets`, etc. are 0/blank for non-goalkeepers).
  This project separates them into their own table rather than mixing them with
  attacking/passing/possession stats.
- **Player identity** is resolved by `(player name, birth year)` — there is no player
  ID in the source data, and mid-season transfers appear as two separate rows for the
  same player (one per team) within a season's file.

## Current-season data (2024/25 onward)

- **Basic stats** (appearances, goals, assists, cards, minutes): [FBref](https://fbref.com),
  which still publishes these live even after losing its advanced-stats feed.
- **xG / npxG:** [Understat](https://understat.com), scraped periodically — no
  official API is used.
- Current-season rows do **not** include the fuller advanced-stat set (progressive
  actions, shot/goal-creating actions, etc.) that the 2017/18–2023/24 historical
  dataset has, since FBref no longer exposes these. See the `has_xa_data` /
  data-completeness handling in `db/schema.sql` for how this is flagged in the
  database.

## Disclaimer

This is a personal, non-commercial portfolio project built for educational and
demonstration purposes. It is not affiliated with, endorsed by, or an official
product of FBref, Sports Reference, Opta, Understat, or Kaggle. All statistics
remain the property of their original providers. If you are a rights holder and
have concerns about this project, please open an issue on the repository.
