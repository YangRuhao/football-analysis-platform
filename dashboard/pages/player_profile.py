"""
Position-aware player analytics profile.

Percentiles are calculated by the API against players in the same season,
same representative position, and minimum-minute cohort.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from api_client import APIError, get_player_career, get_player_profile, search_players  # noqa: E402
from ui import apply_global_styles, page_header  # noqa: E402

st.set_page_config(page_title="Player Profile", page_icon="🔍", layout="wide")
apply_global_styles()
page_header(
    "Player analysis",
    "Player Profile",
    "Search a player and explore position-specific performance, percentiles and career trends.",
)

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

options = {
    f"{m['player_name']} ({m['nation']}, b. {m['born']})": m["player_id"]
    for m in matches
}
choice = st.selectbox("Select a player", options.keys())
player_id = options[choice]
display_name = choice.split(" (")[0]

try:
    career = get_player_career(player_id)
except APIError as e:
    st.error(str(e))
    st.stop()

df = pd.DataFrame(career)
if df.empty:
    st.warning("No season data is available for this player.")
    st.stop()

season_labels = sorted(df["season_label"].dropna().unique())
season = st.selectbox("Season", season_labels, index=len(season_labels) - 1)

try:
    profile = get_player_profile(player_id, season, min_minutes=900)
except APIError as e:
    st.error(str(e))
    st.stop()

player = profile["player"]
season_data = profile["season"]
comparison = profile["comparison"]
metrics = pd.DataFrame(profile["metrics"])

st.markdown(
    f"### {player['player_name']}  ·  {player['position']}\n"
    f"**{season}** · {comparison['min_minutes']}+ minutes cohort"
)

summary = st.columns(5)
summary[0].metric("Minutes", f"{season_data['minutes_played']:,}")
summary[1].metric("Appearances", season_data["matches_played"])
summary[2].metric("Goals", season_data["goals"])
summary[3].metric("Assists", season_data["assists"])
summary[4].metric("xG", f"{season_data['xg']:.1f}" if season_data["xg"] is not None else "—")

st.caption(
    f"Percentiles compare {player['player_name']} with "
    f"{comparison['player_count']} {comparison['position']} players in {season} "
    f"with at least {comparison['min_minutes']} minutes. A transferred player is "
    "aggregated to one player-season observation."
)

left, right = st.columns([1.05, 1])

with left:
    st.markdown("#### Performance profile")
    if metrics.empty:
        st.info("No percentile metrics are available for this position.")
    else:
        labels = metrics["label"].tolist()
        values = metrics["percentile"].tolist()
        theta = labels + [labels[0]]
        radar_values = values + [values[0]]

        fig = go.Figure(
            go.Scatterpolar(
                r=radar_values,
                theta=theta,
                fill="toself",
                name=player["player_name"],
                hovertemplate="%{theta}<br>Percentile: %{r:.1f}<extra></extra>",
            )
        )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], ticksuffix="")),
            showlegend=False,
            height=470,
            margin=dict(l=30, r=30, t=30, b=30),
        )
        st.plotly_chart(fig, width="stretch")

with right:
    st.markdown("#### Percentile breakdown")
    st.caption("100 = higher within the position cohort; 50 = around the middle.")
    for _, row in metrics.iterrows():
        pct = float(row["percentile"])
        value = float(row["value"])
        st.markdown(f"**{row['label']}**  ·  {value:.2f}  ·  **{pct:.0f}th**")
        st.progress(max(0.0, min(1.0, pct / 100.0)))

st.divider()
st.subheader("Season history")

# For the historical chart, collapse transfers to the highest-minute stint so
# each season contributes one club/position row. The percentile section above
# uses the complete aggregated player-season instead.
df_primary = df.sort_values("minutes_played", ascending=False).drop_duplicates("season_label")
trend_metric = st.selectbox(
    "Metric",
    ["goals", "assists", "xg", "npxg", "minutes_played"],
    key="trend_metric",
)
trend_df = df_primary.sort_values("season_label")

import plotly.express as px
fig = px.line(
    trend_df,
    x="season_label",
    y=trend_metric,
    markers=True,
    title=f"{display_name} — {trend_metric.replace('_', ' ').title()} by season",
)
fig.update_layout(height=360, margin=dict(l=20, r=20, t=50, b=20))
st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Detailed season statistics")

season_rows = df[df["season_label"] == season]
if len(season_rows) > 1:
    st.caption(f"Played for {len(season_rows)} clubs in {season}; detailed tables retain each club stint.")

for _, row in season_rows.iterrows():
    with st.container(border=True):
        st.markdown(
            f"**{row['team_name']}** ({row['league_name']}) · "
            f"{row['position']} · age {row['age']}"
        )
        tabs = st.tabs(list(STAT_GROUPS.keys()))
        for tab, (_, cols_list) in zip(tabs, STAT_GROUPS.items()):
            with tab:
                values = {
                    c: row[c]
                    for c in cols_list
                    if c in row.index and pd.notna(row[c])
                }
                if values:
                    table = pd.DataFrame(
                        [{"Metric": k.replace("_", " ").title(), "Value": v} for k, v in values.items()]
                    )
                    st.dataframe(table, hide_index=True, use_container_width=True)
                else:
                    st.caption("No data in this category for this stint.")
