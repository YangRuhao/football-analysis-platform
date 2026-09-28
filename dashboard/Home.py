"""
Landing page for the football analytics dashboard. Player lookup,
comparison, and leaderboard each live in the pages/ folder (Streamlit's
multipage convention) - this page is just the entry point.

Run with:
    streamlit run Home.py
"""

import streamlit as st

st.set_page_config(page_title="Football Analytics Platform", page_icon="⚽", layout="wide")

st.title("⚽ Football Analytics Platform")

st.markdown(
    """
Player stats, comparisons, and leaderboards for Europe's top 5 leagues
(Premier League, La Liga, Bundesliga, Serie A, Ligue 1), 2017/18-2023/24.

**Use the pages in the sidebar:**
- **Player Profile** - look up a player and see their season-by-season stats
- **Compare Players** - put 2 to 6 players side-by-side for a chosen season
- **Leaderboard** - see the top players in the top 5 leagues by any stat

---

**Worth knowing about the data:**
- There's no expected-assists figure (xA/xAG) in this dataset - only xG and non-penalty xG (npxG).
- Most stats here are season totals, not per-90 figures, except where a column is explicitly labelled `p90`.

Data compiled from FBref/Sports Reference (via Opta), redistributed under MIT by
[akshankrithick on Kaggle](https://www.kaggle.com/datasets/akshankrithick/fbref-2017-2024-for-europes-top-5-leagues).
"""
)