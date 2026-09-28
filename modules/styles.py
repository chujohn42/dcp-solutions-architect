"""Custom CSS and small HTML components layered on top of the theme in
.streamlit/config.toml."""

from html import escape

import streamlit as st

_CSS = """
<style>
/* Layout */
.block-container { padding-top: 1.75rem; padding-bottom: 2rem; max-width: 1200px; }
footer { visibility: hidden; }

/* Hero */
.hero .eyebrow {
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; color: #2a78d6; margin-bottom: 0.2rem;
}
.hero h1 { font-size: 1.7rem; font-weight: 700; line-height: 1.2; margin: 0; padding: 0; }
.hero p { color: #5b6573; margin: 0.3rem 0 0; font-size: 0.98rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; border-bottom: 1px solid #e3e7ee; }
.stTabs [data-baseweb="tab"] { padding: 0.6rem 1rem; }
.stTabs [data-baseweb="tab"] p { font-size: 1rem; font-weight: 500; }
.stTabs [aria-selected="true"] p { font-weight: 650; }

/* Metric cards */
[data-testid="stMetric"] {
  background: #ffffff; border: 1px solid #e3e7ee; border-radius: 0.6rem;
  padding: 0.75rem 1rem;
}
[data-testid="stMetricLabel"] p { color: #5b6573; font-weight: 500; }

/* Big result cards (Stack Fit score, Growth headline) */
.result-card {
  background: #ffffff; border: 1px solid #e3e7ee; border-radius: 0.75rem;
  padding: 1.1rem 1.3rem; margin-bottom: 1rem;
}
.result-card .label { color: #5b6573; font-size: 0.9rem; font-weight: 500; }
.result-card .value { font-size: 2.4rem; font-weight: 700; line-height: 1.25; }
.result-card .value .suffix { font-size: 1.3rem; font-weight: 600; color: #1e8a4c; }
.result-card .reason { color: #3d4654; font-size: 1rem; margin-top: 0.2rem; }
.level-low .value { color: #1e8a4c; }
.level-medium .value { color: #b8620b; }
.level-high .value { color: #c63b32; }
.level-none .value { color: #6b7280; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{eyebrow}</div>'
        f"<h1>{title}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def result_card(label: str, value: str, reason: str = "", level: str = "", suffix: str = "") -> None:
    """Large single-result card. level: low | medium | high | none | '' (neutral)."""
    suffix_html = f' <span class="suffix">{escape(suffix)}</span>' if suffix else ""
    reason_html = f'<div class="reason">{escape(reason)}</div>' if reason else ""
    st.markdown(
        f'<div class="result-card level-{level}"><div class="label">{escape(label)}</div>'
        f'<div class="value">{escape(value)}{suffix_html}</div>{reason_html}</div>',
        unsafe_allow_html=True,
    )
