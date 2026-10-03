"""
Side-by-side comparison of 2 to 6 players for a chosen season.

The comparison radar is intentionally relative to the selected players:
each metric is normalized to 0-100 across the current selection. The
table below always exposes the underlying values, so the visualization
never hides the real statistics.
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
page_header(
    "Player analysis",
    "Compare Players",
    "Put 2 to 6 players side-by-side and explore how their performance profiles differ.",
)

METRIC_GROUPS = {
    "Attacking": [
        "goals_p90", "xg", "assists_p90", "shots_p90",
        "shot_creating_actions_p90", "goal_creating_actions_p90",
    ],
    "Passing": [
        "progressive_passes_p90", "pass_completion_pct",
        "key_passes_p90", "progressive_passes",
    ],
    "Possession": [
        "progressive_carries_p90", "take_ons_successful_pct",
        "progressive_carries", "key_passes_p90",
    ],
    "Defense": [
        "tackles_won_p90", "interceptions_p90", "clearances_p90",
        "aerial_duels_won_pct", "shots_blocked", "passes_blocked",
    ],
    "Goalkeeping": [
        "save_pct", "goals_against_p90", "saves_p90",
        "clean_sheets_p90", "crosses_stopped_p90",
    ],
}

METRIC_LABELS = {
    "goals_p90": "Goals / 90",
    "xg": "xG",
    "assists_p90": "Assists / 90",
    "shots_p90": "Shots / 90",
    "shot_creating_actions_p90": "SCA / 90",
    "goal_creating_actions_p90": "GCA / 90",
    "progressive_passes_p90": "Progressive Passes / 90",
    "pass_completion_pct": "Pass Completion %",
    "key_passes_p90": "Key Passes / 90",
    "progressive_passes": "Progressive Passes",
    "progressive_carries_p90": "Progressive Carries / 90",
    "take_ons_successful_pct": "Take-On Success %",
    "progressive_carries": "Progressive Carries",
    "tackles_won_p90": "Tackles Won / 90",
    "interceptions_p90": "Interceptions / 90",
    "clearances_p90": "Clearances / 90",
    "aerial_duels_won_pct": "Aerial Duel Win %",
    "shots_blocked": "Shots Blocked",
    "passes_blocked": "Passes Blocked",
    "save_pct": "Save %",
    "goals_against_p90": "Goals Against / 90",
    "saves_p90": "Saves / 90",
    "clean_sheets_p90": "Clean Sheets / 90",
    "crosses_stopped_p90": "Crosses Stopped / 90",
}

if "compare_selection" not in st.session_state:
    st.session_state.compare_selection = {}

control_left, control_right = st.columns([1, 1])
with control_left:
    season = st.text_input(
        "Season",
        value="2023-2024",
        help="Use the YYYY-YYYY format, for example 2023-2024.",
    )
with control_right:
    st.caption("Comparison limit")
    st.markdown("**2–6 players**")

st.markdown("#### Add players")
name_query = st.text_input(
    "Search by player name",
    placeholder="e.g. Haaland, Mbappé, Bellingham",
    label_visibility="collapsed",
)

if name_query and len(name_query) >= 2:
    try:
        matches = search_players(name_query, limit=8)
    except APIError as e:
        st.error(str(e))
        matches = []

    if matches:
        for m in matches:
            pid = m["player_id"]
            label = f"{m['player_name']} · {m['nation']} · b. {m['born']}"
            added = pid in st.session_state.compare_selection
            cols = st.columns([6, 1])
            cols[0].write(label)
            if cols[1].button(
                "Added" if added else "Add",
                key=f"add_{pid}",
                disabled=added or len(st.session_state.compare_selection) >= 6,
                use_container_width=True,
            ):
                st.session_state.compare_selection[pid] = label
                st.rerun()
    else:
        st.info("No players found.")

selected = st.session_state.compare_selection
if selected:
    st.markdown("#### Selected players")
    selected_cols = st.columns(min(max(len(selected), 2), 3))
    for index, (pid, label) in enumerate(list(selected.items())):
        with selected_cols[index % len(selected_cols)]:
            with st.container(border=True):
                st.markdown(f"**{label.split(' · ')[0]}**")
                st.caption(label.split(" · ", 1)[1] if " · " in label else "")
                if st.button("Remove", key=f"remove_{pid}", use_container_width=True):
                    del selected[pid]
                    st.rerun()

player_ids = list(selected.keys())
if len(player_ids) < 2:
    st.info("Add at least 2 players to start the comparison.")
    st.stop()

try:
    rows = compare_players(player_ids, season)
except APIError as e:
    st.error(str(e))
    st.stop()

df = pd.DataFrame(rows).reset_index(drop=True)
if df.empty:
    st.warning("No comparison data is available.")
    st.stop()

# One aggregated row is returned per player-season, including players who
# changed clubs during the season.
positions = sorted(df["position"].dropna().unique().tolist())
if len(positions) > 1:
    st.info(
        "These players do not all share the same position. The comparison "
        "still shows their actual statistics; radar values are relative only "
        "to the selected players, not a position-adjusted league percentile."
    )

st.markdown("#### Season snapshot")
cards = st.columns(len(df))
for col, (_, row) in zip(cards, df.iterrows()):
    with col:
        st.markdown(
            f"**{row['player_name']}**  
"
            f"{row.get('position', '—')} · {int(row['minutes_played']):,} min"
        )
        st.metric("Goals", int(row.get("goals", 0)))
        st.metric("Assists", int(row.get("assists", 0)))
        xg = row.get("xg")
        st.metric("xG", f"{float(xg):.1f}" if pd.notna(xg) else "—")

st.divider()

group_choice = st.radio(
    "Performance area",
    list(METRIC_GROUPS.keys()),
    horizontal=True,
)
requested_metrics = METRIC_GROUPS[group_choice]

available_metrics = [
    metric
    for metric in requested_metrics
    if metric in df.columns and df[metric].notna().all()
]

if not available_metrics:
    st.warning(
        "This performance area does not have enough shared data for all "
        "selected players. Try another area or choose players with compatible positions."
    )
    st.stop()

if len(available_metrics) < len(requested_metrics):
    missing = [
        METRIC_LABELS.get(m, m)
        for m in requested_metrics
        if m not in available_metrics
    ]
    st.caption("Excluded from radar because at least one selected player has no value: " + ", ".join(missing))

def normalize_for_radar(frame: pd.DataFrame, cols: list[str]) -> dict[str, list[float]]:
    scaled = {}
    for metric in cols:
        values = pd.to_numeric(frame[metric], errors="coerce")
        vmin = values.min()
        vmax = values.max()
        if pd.isna(vmin) or pd.isna(vmax):
            continue
        if vmax == vmin:
            scaled[metric] = [50.0] * len(frame)
        else:
            scaled[metric] = list((values - vmin) / (vmax - vmin) * 100)
    return scaled

scaled = normalize_for_radar(df, available_metrics)

st.markdown(f"#### {group_choice} profile")
st.caption(
    "Radar scores are relative to the selected players for this comparison. "
    "They are not league percentiles. Hover over a point to see the normalized value."
)

fig = go.Figure()
for i, row in df.iterrows():
    values = [scaled[m][i] for m in available_metrics]
    labels = [METRIC_LABELS.get(m, m) for m in available_metrics]
    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name=row["player_name"],
            opacity=0.55,
            hovertemplate="%{theta}<br>Relative score: %{r:.0f}/100<extra></extra>",
        )
    )

fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100],
            ticksuffix="",
            gridcolor="rgba(156,163,175,0.22)",
        ),
        angularaxis=dict(gridcolor="rgba(156,163,175,0.16)"),
    ),
    height=520,
    margin=dict(l=40, r=40, t=25, b=25),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)
st.plotly_chart(fig, width="stretch")

st.markdown("#### Metric-by-metric comparison")
comparison_rows = []
for metric in available_metrics:
    row = {"Metric": METRIC_LABELS.get(metric, metric)}
    for _, player in df.iterrows():
        row[player["player_name"]] = player[metric]
    comparison_rows.append(row)

comparison_df = pd.DataFrame(comparison_rows)
st.dataframe(
    comparison_df,
    hide_index=True,
    width="stretch",
    column_config={
        player["player_name"]: st.column_config.NumberColumn(
            player["player_name"],
            format="%.2f",
        )
        for _, player in df.iterrows()
    },
)

st.divider()
st.markdown("#### Season statistics")
display_cols = [
    "player_name", "team_name", "league_name", "position",
    "age", "matches_played", "minutes_played", "goals", "assists", "xg", "npxg",
]
display_cols = [c for c in display_cols if c in df.columns]
detail_df = df[display_cols].copy()
detail_df = detail_df.rename(
    columns={
        "player_name": "Player",
        "team_name": "Primary club",
        "league_name": "League",
        "position": "Position",
        "age": "Age",
        "matches_played": "Apps",
        "minutes_played": "Minutes",
        "goals": "Goals",
        "assists": "Assists",
        "xg": "xG",
        "npxg": "npxG",
    }
)
st.dataframe(detail_df, hide_index=True, width="stretch")
