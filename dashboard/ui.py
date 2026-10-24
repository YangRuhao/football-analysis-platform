"""Shared visual components and styling for the Streamlit dashboard."""

import streamlit as st


def apply_global_styles() -> None:
    """Apply the shared dark scouting-platform visual system."""
    st.markdown(
        """
        <style>
        :root {
            --fa-green: #39e58c;
            --fa-bg: #080d12;
            --fa-surface: #101820;
            --fa-border: #25323e;
            --fa-muted: #9aa8b5;
            --fa-text: #edf3f7;
        }
        .stApp {
            background: radial-gradient(ellipse at 78% 0%, rgba(57,229,140,.075), transparent 34%), var(--fa-bg);
            color: var(--fa-text);
        }
        [data-testid="stHeader"] { background: rgba(8,13,18,.88); }
        [data-testid="stSidebar"] { background: #0b1218; border-right: 1px solid var(--fa-border); }
        .block-container { max-width: 1480px; padding-top: 2rem; padding-bottom: 3.5rem; }
        h1, h2, h3 { letter-spacing: -.035em; }
        h1 { font-weight: 750 !important; }
        .fa-eyebrow {
            color: var(--fa-green); font-size: .76rem; font-weight: 800;
            letter-spacing: .15em; text-transform: uppercase; margin-bottom: .45rem;
        }
        .fa-subtitle { color: var(--fa-muted); font-size: 1rem; line-height: 1.65; max-width: 780px; margin-bottom: 1.35rem; }
        .fa-hero {
            background: radial-gradient(ellipse at 85% 12%, rgba(57,229,140,.13), transparent 38%),
                linear-gradient(135deg, #121d25 0%, #0e171e 62%, #10231d 100%);
            border: 1px solid #2a3c43; border-radius: 22px;
            padding: clamp(1.35rem, 3vw, 2.5rem); margin: .5rem 0 1.5rem;
        }
        .fa-hero-kicker { color: var(--fa-green); font-size: .76rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
        .fa-hero-title {
            color: #f4f8fa; font-size: clamp(2rem, 4.5vw, 3.6rem); font-weight: 800;
            line-height: 1.03; letter-spacing: -.055em; max-width: 720px; margin: .7rem 0 .85rem;
        }
        .fa-hero-copy { color: #b4c1ca; font-size: 1.02rem; line-height: 1.7; max-width: 690px; }
        .fa-section-label { color: #b3c0ca; font-size: .76rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin: 1.65rem 0 .8rem; }
        .fa-card {
            background: linear-gradient(155deg, rgba(20,31,41,.98), rgba(13,21,28,.98));
            border: 1px solid var(--fa-border); border-radius: 16px;
            padding: 1.15rem 1.2rem; min-height: 155px; height: 100%;
            transition: border-color 160ms ease, transform 160ms ease;
        }
        .fa-card:hover { border-color: rgba(57,229,140,.55); transform: translateY(-2px); }
        .fa-card h3 { color: var(--fa-text); margin: 0 0 .45rem; font-size: 1.02rem; font-weight: 750; }
        .fa-card p { color: var(--fa-muted); font-size: .91rem; line-height: 1.55; margin: 0; }
        .fa-card-icon { color: var(--fa-green); font-size: 1.4rem; margin-bottom: .7rem; }
        .fa-metric-card { background: var(--fa-surface); border: 1px solid var(--fa-border); border-radius: 14px; padding: .95rem 1rem; min-height: 94px; }
        .fa-metric-label { color: var(--fa-muted); font-size: .76rem; font-weight: 700; letter-spacing: .045em; text-transform: uppercase; }
        .fa-metric-value { color: var(--fa-text); font-size: 1.45rem; font-weight: 800; letter-spacing: -.04em; margin-top: .25rem; }
        div[data-testid="stMetric"] { background: var(--fa-surface); border: 1px solid var(--fa-border); border-radius: 12px; padding: .8rem 1rem; }
        div[data-testid="stDataFrame"] { border: 1px solid var(--fa-border); border-radius: 10px; overflow: hidden; }
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background-color: #101820; border-color: var(--fa-border); }
        button[kind="primary"] { font-weight: 750; border: 1px solid rgba(57,229,140,.4); }
        .fa-footnote { color: var(--fa-muted); font-size: .8rem; line-height: 1.55; }
        @media (max-width: 768px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.2rem; }
            .fa-subtitle { font-size: .94rem; }
            .fa-hero { border-radius: 16px; padding: 1.25rem; }
        }
        @media (prefers-reduced-motion: reduce) { .fa-card { transition: none; } .fa-card:hover { transform: none; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    """Render a consistent page header."""
    st.markdown(f'<div class="fa-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="fa-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def section_heading(title: str) -> None:
    """Render a small uppercase section label."""
    st.markdown(f'<div class="fa-section-label">{title}</div>', unsafe_allow_html=True)


def info_card(icon: str, title: str, body: str) -> None:
    """Render a compact dashboard feature card."""
    st.markdown(
        f"""
        <div class="fa-card">
            <div class="fa-card-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
