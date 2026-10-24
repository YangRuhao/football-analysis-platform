"""Interactive landing page for the Football Analytics Platform."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))
from api_client import APIError, LEADERBOARD_METRICS, get_leaderboard, search_players  # noqa: E402
from dashboard_data import (  # noqa: E402
    DEFAULT_SEASON,
    HOME_METRICS,
    SUPPORTED_SEASONS,
    metric_label,
    prepare_leaderboard_rows,
)
from ui import apply_global_styles, info_card, section_heading  # noqa: E402

st.set_page_config(
    page_title="Football Analytics | Player Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_global_styles()

st.markdown(
    """
    <section class="fa-hero">
      <div class="fa-hero-kicker">Football intelligence · Historical performance</div>
      <div class="fa-hero-title">Find the story behind the stats.</div>
      <div class="fa-hero-copy">
        Explore player performance across Europe's top five leagues. Discover
        standout seasons, compare players and put individual numbers into context.
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

section_heading("Start with a player")
search_col, help_col = st.columns([2.2, 1], vertical_alignment="bottom")
with search_col:
    player_query = st.text_input(
        "Player search",
        placeholder="Search by name — e.g. Haaland, Bellingham, Yamal",
        key="home_player_query",
        label_visibility="collapsed",
    )
with help_col:
    st.caption("Search the player database and jump straight to their profile.")

if player_query and len(player_query.strip()) >= 2:
    try:
        matches = search_players(player_query.strip(), limit=8)
    except APIError as exc:
        st.warning("Player search is temporarily unavailable. Check the backend and try again.")
        with st.expander("Technical details"):
            st.code(str(exc))
        matches = []
    if matches:
        player_options = {
            f"{item['player_name']} · {item.get('nation') or 'Nation unavailable'} · born {item.get('born') or '—'}": item
            for item in matches
        }
        selected_label = st.selectbox("Matching players", options=list(player_options), key="home_player_match")
        selected_player = player_options[selected_label]
        if st.button("Open player profile", type="primary"):
            st.session_state["profile_player_search"] = selected_player["player_name"]
            st.switch_page("pages/player_profile.py")
    elif not st.session_state.get("home_search_failed", False):
        st.caption("No matching players found. Try a shorter name or check the spelling.")

section_heading("Explore the platform")
feature_cols = st.columns(3, gap="medium")
with feature_cols[0]:
    info_card("◉", "Player profiles", "Follow season-by-season output, positional percentiles, club stints and career trends.")
with feature_cols[1]:
    info_card("⇄", "Compare players", "Compare two to six players with actual statistics and visual performance profiles.")
with feature_cols[2]:
    info_card("↗", "Leaderboards", "Find top performers by season, position and metric, with a minutes threshold.")

section_heading("League leaders")
filter_cols = st.columns([1, 1, 1.3, 1], gap="medium")
season = filter_cols[0].selectbox(
    "Season", options=SUPPORTED_SEASONS, index=SUPPORTED_SEASONS.index(DEFAULT_SEASON),
    format_func=lambda value: value.replace("-", "–"),
)
metric_options = [item for item in HOME_METRICS if item in LEADERBOARD_METRICS]
metric = filter_cols[1].selectbox("Metric", options=metric_options, format_func=metric_label)
position = filter_cols[2].selectbox(
    "Position group", options=["Any", "FW", "MF", "DF", "GK"],
    format_func=lambda value: {"Any": "All positions", "FW": "Forwards", "MF": "Midfielders", "DF": "Defenders", "GK": "Goalkeepers"}[value],
)
min_minutes = filter_cols[3].selectbox(
    "Minimum minutes", options=[0, 450, 900, 1350, 1800], index=2,
    format_func=lambda value: f"{value:,}+" if value else "No minimum",
)

try:
    leaderboard_rows = get_leaderboard(
        season=season, metric=metric, position=None if position == "Any" else position,
        min_minutes=min_minutes, limit=10,
    )
    chart_rows = prepare_leaderboard_rows(leaderboard_rows, limit=10)
except APIError as exc:
    chart_rows = []
    st.warning("The leaderboard could not be loaded. Check that FastAPI and PostgreSQL are running, then refresh.")
    with st.expander("Technical details"):
        st.code(str(exc))

if chart_rows:
    chart_df = pd.DataFrame(chart_rows).sort_values("_chart_value", ascending=True)
    top_player = max(chart_rows, key=lambda row: row["_chart_value"])
    summary_cols = st.columns(3, gap="medium")
    summary_cols[0].metric("Season", season.replace("-", "–"))
    summary_cols[1].metric("Metric", metric_label(metric))
    summary_cols[2].metric(
        f"Top {metric_label(metric).lower()} value",
        f"{top_player['_chart_value']:,.2f}".rstrip("0").rstrip("."),
    )
    fig = px.bar(
        chart_df, x="_chart_value", y="player_name", orientation="h",
        custom_data=["team_name", "league_name", "minutes_played"],
        labels={"_chart_value": metric_label(metric), "player_name": ""},
        color_discrete_sequence=["#39e58c"], height=max(340, 38 * len(chart_df)),
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>" + metric_label(metric) + ": %{x:.2f}<br>"
            + "Team: %{customdata[0]}<br>League: %{customdata[1]}<br>"
            + "Minutes: %{customdata[2]:,.0f}<extra></extra>"
        ),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce5eb", family="Inter, sans-serif"),
        margin=dict(l=8, r=16, t=12, b=8),
        xaxis=dict(showgrid=True, gridcolor="rgba(154,168,181,0.15)", zeroline=False),
        yaxis=dict(showgrid=False, automargin=True), showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with st.expander("View leaderboard data"):
        table_df = pd.DataFrame(chart_rows).rename(columns={
            "player_name": "Player", "team_name": "Team", "league_name": "League",
            "position": "Position", "minutes_played": "Minutes", "_chart_value": metric_label(metric),
        })
        display_columns = [
            col for col in ["Player", "Team", "League", "Position", "Minutes", metric_label(metric)]
            if col in table_df.columns
        ]
        st.dataframe(table_df[display_columns], hide_index=True, use_container_width=True)
else:
    st.info(
        f"No leaderboard results are available for {season.replace('-', '–')} with these filters. "
        "Try another season, metric or minutes threshold."
    )

section_heading("Dataset coverage")
coverage_cols = st.columns(4, gap="medium")
coverage_values = [
    ("Leagues", "5", "Europe's top five leagues"),
    ("Seasons", "7", "2017/18–2023/24"),
    ("Analysis", "Player-level", "Season totals and per-90 metrics"),
    ("Benchmarks", "Position-aware", "Percentiles against positional peers"),
]
for col, (label, value, detail) in zip(coverage_cols, coverage_values):
    with col:
        st.markdown(
            f'<div class="fa-metric-card"><div class="fa-metric-label">{label}</div>'
            f'<div class="fa-metric-value">{value}</div><div class="fa-footnote">{detail}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <p class="fa-footnote" style="margin-top:1rem">
      Data coverage ends in 2023/24. Most statistics are season totals; only
      metrics explicitly labelled per 90 are rate-adjusted. xA/xAG is not
      available in the current historical dataset. Data provenance and
      limitations are documented in <code>DATA_SOURCES.md</code>.
    </p>
    """,
    unsafe_allow_html=True,
)
