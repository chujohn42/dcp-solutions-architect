"""Custom CSS and small HTML components layered on top of the theme in
.streamlit/config.toml."""

import streamlit as st

_CSS = """
<style>
/* Layout */
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px; }
footer { visibility: hidden; }

/* Hero */
.hero { padding: 0.25rem 0 0.5rem; }
.hero .eyebrow {
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; color: #2a78d6; margin-bottom: 0.25rem;
}
.hero h1 { font-size: 1.9rem; font-weight: 700; line-height: 1.2; margin: 0; padding: 0; }
.hero p { color: #5b6573; margin: 0.35rem 0 0; font-size: 0.98rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; border-bottom: 1px solid #e3e7ee; }
.stTabs [data-baseweb="tab"] { padding: 0.6rem 1rem; font-weight: 500; }
.stTabs [data-baseweb="tab"] p { font-size: 0.98rem; }
.stTabs [aria-selected="true"] p { font-weight: 650; }

/* Metric cards */
[data-testid="stMetric"] {
  background: #ffffff; border: 1px solid #e3e7ee; border-radius: 0.6rem;
  padding: 0.85rem 1rem;
}
[data-testid="stMetricLabel"] p { color: #5b6573; font-weight: 500; }

/* Complexity score card */
.score-card {
  background: #ffffff; border: 1px solid #e3e7ee; border-radius: 0.6rem;
  padding: 0.85rem 1rem; height: 100%;
}
.score-card .label { color: #5b6573; font-size: 0.875rem; font-weight: 500; }
.score-card .value { font-size: 2rem; font-weight: 700; line-height: 1.3; }
.score-card .sub { color: #5b6573; font-size: 0.8rem; }
.score-low .value { color: #1e8a4c; }
.score-medium .value { color: #b8620b; }
.score-high .value { color: #c63b32; }
.score-none .value { color: #6b7280; }

/* Role-mapping section */
.role-card {
  background: #ffffff; border: 1px solid #e3e7ee; border-radius: 0.6rem;
  padding: 1rem 1.1rem; height: 100%;
}
.role-card .step { color: #2a78d6; font-size: 0.75rem; font-weight: 600;
  letter-spacing: 0.06em; text-transform: uppercase; }
.role-card h4 { margin: 0.2rem 0 0.4rem; padding: 0; font-size: 1.05rem; }
.role-card p { color: #3d4654; font-size: 0.92rem; margin: 0; }
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


def score_card(label: str, value: str, level: str, sub: str = "") -> None:
    """level: low | medium | high | none"""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="score-card score-{level}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def role_card(step: str, title: str, body: str) -> None:
    st.markdown(
        f'<div class="role-card"><div class="step">{step}</div>'
        f"<h4>{title}</h4><p>{body}</p></div>",
        unsafe_allow_html=True,
    )
