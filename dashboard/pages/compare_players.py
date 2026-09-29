"""
Side-by-side comparison of 2 to 6 players for a chosen season: a
radar chart on a selected stat group, plus a full stats table.

The radar chart scales each metric to 0-100 *within the players
selected here* (min-max), not against the whole league - this is
what makes stats on very different scales (e.g. goals vs. pass
completion %) plot sensibly on the same chart. The table underneath
always shows the real, unscaled numbers.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from api_client import APIError, compare_players, search_players  # noqa: E402
from ui import apply_global_styles, page_header  # noqa: E402

st.set_page_config(page_title="Compare Players", page_icon="📊", layout="wide")
apply_global_styles()
page_header("Player analysis", "Compare Players", "Build a side-by-side view of 2 to 6 players for a selected season.")

METRIC_GROUPS = {
    "Attacking": ["goals", "assists", "xg", "npxg", "shots_p90", "shot_creating_actions_p90"],
    "Passing": ["progressive_passes", "pass_completion_pct", "key_passes", "passes_into_penalty_area"],
    "Possession": ["progressive_carries", "take_ons_successful_pct", "carries_into_final_third"],
    "Defense": ["tackles_won", "interceptions", "clearances", "aerial_duels_won_pct"],
}

if "compare_selection" not in st.session_state:
    st.session_state.compare_selection = {}  # player_id -> display label

season = st.text_input("Season", value="2023-2024", help="Format: YYYY-YYYY, e.g. 2023-2024")

st.caption("Search and add 2 to 6 players to compare.")
name_query = st.text_input("Search for a player to add")

if name_query and len(name_query) >= 2:
    try:
        matches = search_players(name_query)
    except APIError as e:
        st.error(str(e))
        matches = []

    for m in matches:
        label = f"{m['player_name']} ({m['nation']}, b. {m['born']})"
        already_added = m["player_id"] in st.session_state.compare_selection
        if st.button(
            f"{'Added' if already_added else 'Add'} {label}",
            key=f"add_{m['player_id']}",
            disabled=already_added,
        ):
            st.session_state.compare_selection[m["player_id"]] = label
            st.rerun()

if st.session_state.compare_selection:
    st.write("**Selected players:**")
    for pid, label in list(st.session_state.compare_selection.items()):
        col1, col2 = st.columns([5, 1])
        col1.write(label)
        if col2.button("Remove", key=f"remove_{pid}"):
            del st.session_state.compare_selection[pid]
            st.rerun()

player_ids = list(st.session_state.compare_selection.keys())

if len(player_ids) < 2:
    st.info("Add at least 2 players to compare.")
    st.stop()
if len(player_ids) > 6:
    st.warning("More than 6 players gets hard to read on a radar chart - using the first 6 added.")
    player_ids = player_ids[:6]

try:
    rows = compare_players(player_ids, season)
except APIError as e:
    st.error(str(e))
    st.stop()

df = pd.DataFrame(rows).reset_index(drop=True)

group_choice = st.radio("Compare on", list(METRIC_GROUPS.keys()), horizontal=True)
metrics = METRIC_GROUPS[group_choice]


def normalize_for_radar(frame: pd.DataFrame, cols: list) -> dict:
    """Min-max scale each column to 0-100 across just these rows, so
    metrics on very different scales (goals vs. a percentage) sit on
    a comparable radar axis. All-equal columns map to the midpoint."""
    scaled = {}
    for c in cols:
        vals = frame[c].astype(float).fillna(0)
        vmin, vmax = vals.min(), vals.max()
        scaled[c] = [50.0] * len(vals) if vmax == vmin else list((vals - vmin) / (vmax - vmin) * 100)
    return scaled


scaled = normalize_for_radar(df, metrics)

fig = go.Figure()
for i, row in df.iterrows():
    values = [scaled[m][i] for m in metrics]
    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]], theta=metrics + [metrics[0]],
            fill="toself", name=row["player_name"],
        )
    )
fig.update_layout(
    title=f"{group_choice} - {season} (scaled 0-100 within this comparison, not the full league)",
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Full stats table (actual values)")
display_cols = ["player_name", "team_name", "position", "minutes_played"] + metrics
st.dataframe(df[display_cols].set_index("player_name"), use_container_width=True)