"""
Top-N players in the top 5 leagues by a chosen stat, for a given
season. Defaults to the top 50 with a 900-minute qualification floor
so small-sample outliers don't dominate the ranking.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from api_client import APIError, LEADERBOARD_METRICS, POSITIONS, get_leaderboard  # noqa: E402
from ui import apply_global_styles, page_header  # noqa: E402

st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")
apply_global_styles()
page_header("League analysis", "Leaderboard", "Explore top performers by season, position and metric, with a minutes threshold to reduce small-sample noise.")

col1, col2, col3 = st.columns(3)
season = col1.text_input("Season", value="2023-2024")
metric = col2.selectbox("Metric", LEADERBOARD_METRICS, index=LEADERBOARD_METRICS.index("goals"))
position = col3.selectbox("Position", ["Any"] + POSITIONS)

col4, col5 = st.columns(2)
min_minutes = col4.slider("Minimum minutes played", 0, 3000, 900, step=90)
limit = col5.slider("Show top", 10, 100, 50, step=10)

try:
    rows = get_leaderboard(
        season=season,
        metric=metric,
        position=None if position == "Any" else position,
        min_minutes=min_minutes,
        limit=limit,
    )
except APIError as e:
    st.error(str(e))
    st.stop()

df = pd.DataFrame(rows)

st.subheader(
    f"Top {len(df)} by {metric} - {season}" + (f" ({position})" if position != "Any" else "")
)

fig = px.bar(
    df.sort_values("value"), x="value", y="player_name", orientation="h",
    hover_data=["team_name", "league_name", "minutes_played"],
    labels={"value": metric, "player_name": ""},
    height=max(400, 20 * len(df)),
)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    df[["player_name", "team_name", "league_name", "position", "minutes_played", "value"]]
    .rename(columns={"value": metric}),
    use_container_width=True,
    hide_index=True,
)