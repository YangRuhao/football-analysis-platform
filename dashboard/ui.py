"""Shared visual components and styling for the Streamlit dashboard."""

import streamlit as st


def apply_global_styles() -> None:
    """Apply the shared visual system used across dashboard pages."""
    st.markdown(
        """
        <style>
        :root {
            --fa-green: #22c55e;
            --fa-bg: #0b0f14;
            --fa-surface: #111820;
            --fa-border: #24303b;
            --fa-muted: #9ca3af;
        }

        .block-container {
            max-width: 1400px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.02em;
        }

        .fa-eyebrow {
            color: var(--fa-green);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .fa-subtitle {
            color: var(--fa-muted);
            font-size: 1rem;
            line-height: 1.6;
            max-width: 760px;
            margin-bottom: 1.5rem;
        }

        .fa-card {
            background: linear-gradient(180deg, rgba(17,24,32,0.98), rgba(13,19,26,0.98));
            border: 1px solid var(--fa-border);
            border-radius: 14px;
            padding: 1.25rem;
            height: 100%;
        }

        .fa-card h3 {
            margin: 0 0 0.45rem 0;
            font-size: 1.05rem;
        }

        .fa-card p {
            color: var(--fa-muted);
            line-height: 1.55;
            margin: 0;
        }

        .fa-card-icon {
            font-size: 1.45rem;
            margin-bottom: 0.55rem;
        }

        .fa-section-label {
            color: var(--fa-muted);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 1.5rem 0 0.75rem;
        }

        div[data-testid="stMetric"] {
            background: var(--fa-surface);
            border: 1px solid var(--fa-border);
            border-radius: 12px;
            padding: 0.8rem 1rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--fa-border);
            border-radius: 10px;
            overflow: hidden;
        }

        button[kind="primary"] {
            font-weight: 700;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.25rem;
            }

            .fa-subtitle {
                font-size: 0.95rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    """Render a consistent page header."""
    st.markdown(f'<div class="fa-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="fa-subtitle">{subtitle}</div>', unsafe_allow_html=True)


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
