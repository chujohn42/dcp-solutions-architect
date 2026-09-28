"""2. Growth tab — UI only. All model logic lives in growth_model.py."""

from dataclasses import replace

import altair as alt
import pandas as pd
import streamlit as st

from modules.growth_model import (
    DEFAULT_LEVERS,
    LEVER_INFO,
    Baseline,
    Driver,
    Lever,
    baseline_projection,
    display_name,
    isolated_impact,
    prioritize,
    project,
    sss_growth_pct,
)
from modules.styles import result_card

BAR_COLOR = "#2a78d6"
DRIVER_PLAIN = {
    Driver.TRAFFIC: "more visitors",
    Driver.CONVERSION: "more visitors ordering",
    Driver.AOV: "bigger orders",
}


def _baseline_inputs() -> Baseline:
    c1, c2, c3 = st.columns(3)
    orders = c1.number_input(
        "Monthly online orders", min_value=1, step=1_000, key="growth_orders"
    )
    aov = c2.number_input(
        "Average order value ($)", min_value=0.01, step=1.00, format="%.2f",
        key="growth_aov",
    )
    conv = c3.number_input(
        "Conversion rate (%)", min_value=0.1, max_value=100.0, step=0.1, format="%.1f",
        key="growth_conv", help="Share of site visitors who place an order.",
    )
    return Baseline(monthly_orders=orders, aov=aov, conversion_rate=conv / 100)


def _lever_toggles() -> list[Lever]:
    ss = st.session_state
    st.markdown("**Growth levers**")
    cols = st.columns(2)
    for i, lever in enumerate(DEFAULT_LEVERS):
        label, desc = LEVER_INFO[lever.name]
        with cols[i % 2]:
            st.toggle(f"{label} (+{ss[f'lift_{i}']:g}%)", key=f"lever_on_{i}")
            st.caption(desc)

    with st.expander("Adjust assumptions"):
        st.caption("Assumed lift for each lever. These are placeholders, not benchmarks.")
        acols = st.columns(2)
        for i, lever in enumerate(DEFAULT_LEVERS):
            acols[i % 2].number_input(
                f"{display_name(lever)}: % {DRIVER_PLAIN[lever.driver]}",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f", key=f"lift_{i}",
            )

    return [
        replace(lever, lift_pct=float(ss[f"lift_{i}"]), enabled=bool(ss[f"lever_on_{i}"]))
        for i, lever in enumerate(DEFAULT_LEVERS)
    ]


def _impact_chart(df: pd.DataFrame) -> alt.Chart:
    base = alt.Chart(df).encode(
        x=alt.X(
            "Per year:Q", title="Extra sales per year (each lever on its own)",
            axis=alt.Axis(format="$~s", tickCount=4),
        ),
        y=alt.Y("Lever:N", sort="-x", title=None, axis=alt.Axis(labelLimit=200)),
        tooltip=[
            alt.Tooltip("Lever:N"),
            alt.Tooltip("Per year:Q", title="Extra sales / year", format="$,.0f"),
        ],
    )
    bars = base.mark_bar(color=BAR_COLOR, cornerRadiusEnd=4, size=22)
    labels = base.mark_text(align="left", dx=6).encode(
        text=alt.Text("Per year:Q", format="$,.0f")
    )
    return (bars + labels).properties(height=48 * len(df) + 40)


def render() -> None:
    st.caption("Estimate how much more the merchant could sell online with DCP growth features.")

    left, right = st.columns([1, 1.1], gap="large")
    with left:
        baseline = _baseline_inputs()
        levers = _lever_toggles()

    before = baseline_projection(baseline)
    after = project(baseline, levers)
    extra_per_year = (after.sales - before.sales) * 12
    growth_pct = sss_growth_pct(before, after)

    # Shared with the Rollout Plan tab (rendered after this one).
    ss = st.session_state
    ss["growth_ranked"] = prioritize(baseline, levers)
    ss["growth_sss_pct"] = growth_pct
    ss["growth_extra_per_year"] = extra_per_year

    with right:
        result_card(
            "Estimated extra sales per year",
            f"${extra_per_year:,.0f}",
            suffix=f"(+{growth_pct:.1f}%)",
        )
        enabled = [l for l in levers if l.enabled]
        if not enabled:
            st.info("Turn on at least one growth lever to see its impact.")
            return
        df = pd.DataFrame(
            [
                {"Lever": display_name(l), "Per year": isolated_impact(baseline, l) * 12}
                for l in enabled
            ]
        )
        st.altair_chart(_impact_chart(df), width="stretch")
        if len(enabled) > 1:
            st.caption(
                "Together the levers add slightly more than the bars summed, because "
                "they boost each other."
            )
