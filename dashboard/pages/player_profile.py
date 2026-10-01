"""
Search for a player, pick a season, and see their full stat breakdown
plus a career trend chart.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from api_client import APIError, get_player_career, search_players  # noqa: E402
from ui import apply_global_styles, page_header  # noqa: E402

st.set_page_config(page_title="Player Profile", page_icon="🔍", layout="wide")
apply_global_styles()
page_header("Player analysis", "Player Profile", "Search a player and explore season-by-season performance, club stints and career trends.")

STAT_GROUPS = {
    "Attacking": [
        "goals", "assists", "goals_and_assists", "non_penalty_goals",
        "penalty_kicks_made", "xg", "npxg", "goals_p90", "assists_p90",
        "total_shots", "shots_on_target_pct", "shots_p90", "goals_per_shot",
        "goals_per_shot_on_target", "shot_creating_actions_p90",
        "goal_creating_actions_p90",
    ],
    "Passing": [
        "progressive_passes", "passes_completed", "passes_attempted",
        "pass_completion_pct", "progressive_pass_distance",
        "short_pass_completion_pct", "medium_pass_completion_pct",
        "long_pass_completion_pct", "key_passes", "passes_into_final_third",
        "passes_into_penalty_area",
    ],
    "Possession": [
        "progressive_carries", "take_ons_attempted", "take_ons_successful_pct",
        "times_tackled_on_take_on", "carries_into_final_third",
        "carries_into_penalty_area", "possessions_lost", "touches_def_penalty_area",
    ],
    "Defense": [
        "tackles_attempted", "tackles_won", "dribbles_tackled_pct", "shots_blocked",
        "passes_blocked", "interceptions", "clearances", "errors", "aerial_duels_won_pct",
    ],
    "Goalkeeping": [
        "goals_against", "goals_against_p90", "saves", "save_pct",
        "clean_sheets", "clean_sheet_pct", "penalty_save_pct", "crosses_stopped",
    ],
}

name = st.text_input("Search for a player", placeholder="e.g. Haaland, Bellingham, Yamal")

if not name or len(name) < 2:
    st.info("Type at least 2 characters to search.")
    st.stop()

try:
    matches = search_players(name)
except APIError as e:
    st.error(str(e))
    st.stop()

options = {f"{m['player_name']} ({m['nation']}, b. {m['born']})": m["player_id"] for m in matches}
choice = st.selectbox("Select a player", options.keys())
player_id = options[choice]
display_name = choice.split(" (")[0]

try:
    career = get_player_career(player_id)
except APIError as e:
    st.error(str(e))
    st.stop()

df = pd.DataFrame(career)

# A mid-season transfer produces two rows sharing one season_label.
# For the career trend chart, collapse to the stint with more minutes
# so each season contributes exactly one point.
df_primary = df.sort_values("minutes_played", ascending=False).drop_duplicates("season_label")

season_labels = sorted(df["season_label"].unique())
season = st.selectbox("Season", season_labels, index=len(season_labels) - 1)

season_rows = df[df["season_label"] == season]
if len(season_rows) > 1:
    st.caption(f"Played for multiple clubs in {season} - showing both stints below.")

st.subheader(f"{display_name} - {season}")

for _, row in season_rows.iterrows():
    with st.container(border=True):
        st.markdown(f"**{row['team_name']}** ({row['league_name']}) - {row['position']}, age {row['age']}")

        cols = st.columns(4)
        cols[0].metric("Minutes", int(row["minutes_played"]) if pd.notna(row["minutes_played"]) else "-")
        cols[1].metric("Goals", int(row["goals"]) if pd.notna(row["goals"]) else "-")
        cols[2].metric("Assists", int(row["assists"]) if pd.notna(row["assists"]) else "-")
        cols[3].metric("xG", f"{row['xg']:.1f}" if pd.notna(row["xg"]) else "-")

        with st.expander("Full stat breakdown"):
            tabs = st.tabs(list(STAT_GROUPS.keys()))
            for tab, (_, cols_list) in zip(tabs, STAT_GROUPS.items()):
                with tab:
                    values = {c: row[c] for c in cols_list if pd.notna(row.get(c))}
                    if values:
                        st.dataframe(pd.Series(values, name="value"), width='stretch')
                    else:
                        st.caption("No data in this category for this stint.")

st.divider()
st.subheader("Career trend")
trend_metric = st.selectbox(
    "Metric", ["goals", "assists", "xg", "npxg", "minutes_played"], key="trend_metric"
)
trend_df = df_primary.sort_values("season_label")
fig = px.line(
    trend_df, x="season_label", y=trend_metric, markers=True,
    title=f"{display_name} - {trend_metric} by season",
)
st.plotly_chart(fig, width='stretch')