"""Landing page for the football analytics dashboard."""

import streamlit as st

from ui import apply_global_styles, info_card, page_header

st.set_page_config(page_title="Football Analytics Platform", page_icon="⚽", layout="wide")
apply_global_styles()

page_header(
    "Football intelligence",
    "Explore football performance.",
    "Search players, compare seasons and uncover league-wide patterns across Europe's top five leagues from 2017/18 to 2023/24.",
)

st.markdown('<div class="fa-section-label">Start exploring</div>', unsafe_allow_html=True)
cols = st.columns(3)
with cols[0]:
    info_card("🔎", "Player Profile", "Search a player and follow their season-by-season performance, club stints and career trends.")
with cols[1]:
    info_card("📊", "Compare Players", "Put players side-by-side and inspect how their attacking, passing, possession and defensive profiles differ.")
with cols[2]:
    info_card("🏆", "Leaderboards", "Filter a season, position and metric to explore the players at the top of the table.")

st.markdown('<div class="fa-section-label">Dataset at a glance</div>', unsafe_allow_html=True)
metric_cols = st.columns(4)
metric_cols[0].metric("Leagues", "5")
metric_cols[1].metric("Seasons", "7")
metric_cols[2].metric("Coverage", "2017/18–2023/24")
metric_cols[3].metric("Data focus", "Player performance")

st.info("**Data note:** the historical dataset contains xG and non-penalty xG (npxG), but no xA/xAG. Most values are season totals; metrics explicitly labelled p90 are per-90 figures.")

with st.expander("About the data"):
    st.markdown("""
The historical data was compiled from FBref/Sports Reference (via Opta) and redistributed through Kaggle by akshankrithick.

The platform treats mid-season transfers as separate club stints so the underlying data is not silently combined. On player profile career trends, the stint with the most minutes is used as the representative row for a season.

This is an educational portfolio project; source provenance and limitations are documented in DATA_SOURCES.md.
""")
