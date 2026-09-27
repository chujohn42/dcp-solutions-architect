"""Growth Simulator tab — UI only. All model logic lives in growth_model.py."""

import altair as alt
import pandas as pd
import streamlit as st

from modules.growth_model import (
    LOW_EFFORT_MAX,
    Baseline,
    Driver,
    Lever,
    Projection,
    baseline_projection,
    prioritize,
    project,
    sss_growth_pct,
)

BAR_COLOR = "#2a78d6"


def _baseline_inputs() -> Baseline:
    st.markdown("#### Current state")
    c1, c2, c3 = st.columns(3)
    orders = c1.number_input(
        "Monthly digital orders", min_value=1, step=1_000, key="growth_orders"
    )
    aov = c2.number_input(
        "AOV ($)", min_value=0.01, step=1.00, format="%.2f", key="growth_aov"
    )
    conv = c3.number_input(
        "Conversion rate (%)", min_value=0.1, max_value=100.0, step=0.1,
        format="%.1f", key="growth_conv",
    )
    return Baseline(monthly_orders=orders, aov=aov, conversion_rate=conv / 100)


def _lever_editor() -> list[Lever]:
    st.markdown("#### Growth levers")
    st.caption(
        "Every value below is an editable assumption. The defaults are placeholders, "
        f"not benchmarks. Effort: 1 = easy, 5 = hard (≤ {LOW_EFFORT_MAX} counts as low effort)."
    )
    defaults = pd.DataFrame(
        [
            {
                "Enabled": l.enabled,
                "Lever": l.name,
                "Applies to": l.driver.value,
                "Lift %": l.lift_pct,
                "Effort (1–5)": l.effort,
            }
            for l in st.session_state["lever_rows"]
        ]
    )
    edited = st.data_editor(
        defaults,
        # Versioned key: Load Example / Reset bump it so new rows replace old edits.
        key=f"lever_editor_{st.session_state['lever_editor_version']}",
        hide_index=True,
        num_rows="fixed",
        width="stretch",
        column_config={
            "Enabled": st.column_config.CheckboxColumn(),
            "Lever": st.column_config.TextColumn(disabled=True),
            "Applies to": st.column_config.SelectboxColumn(
                options=[d.value for d in Driver], required=True
            ),
            "Lift %": st.column_config.NumberColumn(
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f%%", required=True
            ),
            "Effort (1–5)": st.column_config.NumberColumn(
                min_value=1, max_value=5, step=1, required=True
            ),
        },
    )
    return [
        Lever(
            name=row["Lever"],
            driver=Driver(row["Applies to"]),
            lift_pct=float(row["Lift %"]),
            effort=int(row["Effort (1–5)"]),
            enabled=bool(row["Enabled"]),
        )
        for _, row in edited.iterrows()
    ]


def _projection_table(before: Projection, after: Projection) -> pd.DataFrame:
    def fmt(p: Projection) -> dict[str, str]:
        return {
            "Sessions": f"{p.sessions:,.0f}",
            "Conversion": f"{p.conversion_rate:.2%}",
            "AOV": f"${p.aov:,.2f}",
            "Orders": f"{p.orders:,.0f}",
            "Digital sales": f"${p.sales:,.0f}",
        }

    return pd.DataFrame({"Before": fmt(before), "After": fmt(after)})


def _impact_chart(ranked_df: pd.DataFrame) -> alt.Chart:
    base = alt.Chart(ranked_df).encode(
        x=alt.X(
            "Incremental:Q",
            title="Incremental monthly sales (lever applied alone)",
            axis=alt.Axis(format="$,.0f", tickCount=5),
        ),
        y=alt.Y("Lever:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("Lever:N"),
            alt.Tooltip("Applies to:N"),
            alt.Tooltip("Lift %:Q", format=".1f"),
            alt.Tooltip("Incremental:Q", title="Incremental / month", format="$,.0f"),
            alt.Tooltip("Effort:Q"),
        ],
    )
    bars = base.mark_bar(color=BAR_COLOR, cornerRadiusEnd=4, size=20)
    labels = base.mark_text(align="left", dx=6).encode(
        text=alt.Text("Incremental:Q", format="$,.0f")
    )
    return (bars + labels).properties(height=46 * len(ranked_df) + 30)


def render() -> None:
    st.subheader("Same-Store Sales Growth Simulator")
    st.caption(
        "Model: sales = sessions × conversion × AOV, for the digital channel at existing "
        "stores. Each lever lifts one driver; lifts compound."
    )

    baseline = _baseline_inputs()
    levers = _lever_editor()

    before = baseline_projection(baseline)
    after = project(baseline, levers)
    ranked = prioritize(baseline, levers)

    # Shared with the Onboarding Playbook tab (rendered after this one).
    st.session_state["growth_ranked"] = ranked
    st.session_state["growth_sss_pct"] = sss_growth_pct(before, after)

    # 1. Before / after projection
    st.divider()
    st.markdown("#### Same-store sales projection")
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Monthly digital sales",
        f"${after.sales:,.0f}",
        delta=f"${after.sales - before.sales:,.0f}",
    )
    m2.metric(
        "Annualized",
        f"${after.sales * 12:,.0f}",
        delta=f"${(after.sales - before.sales) * 12:,.0f}",
    )
    m3.metric("SSS growth (digital)", f"{sss_growth_pct(before, after):.1f}%")
    st.dataframe(_projection_table(before, after), width="stretch")
    if after.conversion_capped:
        st.warning("Conversion lifts push the rate past 100%, so it has been capped at 100%.")

    if not ranked:
        st.info("Enable at least one lever to see impact and prioritization.")
        return

    ranked_df = pd.DataFrame(
        [
            {
                "Rank": r.rank,
                "Lever": r.lever.name,
                "Priority": r.quadrant,
                "Applies to": r.lever.driver.value,
                "Lift %": r.lever.lift_pct,
                "Incremental": r.incremental_monthly_sales,
                "Effort": r.lever.effort,
                "Impact / effort pt": r.impact_per_effort,
            }
            for r in ranked
        ]
    )

    # 2. Lever comparison chart
    st.markdown("#### Projected impact by lever")
    st.altair_chart(_impact_chart(ranked_df), width="stretch")
    isolated_sum = ranked_df["Incremental"].sum()
    st.caption(
        f"Isolated impacts sum to ${isolated_sum:,.0f}/mo. Combined they give "
        f"${after.sales - before.sales:,.0f}/mo, because lifts on different drivers multiply."
    )

    # 3. Prioritization
    st.markdown("#### Recommended prioritization")
    top = ranked[0]
    st.success(
        f"**Start with {top.lever.name}**: ${top.incremental_monthly_sales:,.0f}/mo at "
        f"effort {top.lever.effort}, the best impact per effort point "
        f"({top.quadrant.lower()})."
    )
    st.dataframe(
        ranked_df[["Rank", "Lever", "Priority", "Incremental", "Effort", "Impact / effort pt"]],
        hide_index=True,
        width="stretch",
        column_config={
            "Incremental": st.column_config.NumberColumn(
                "Incremental / month", format="dollar"
            ),
            "Impact / effort pt": st.column_config.NumberColumn(format="dollar"),
        },
    )
    st.caption(
        "Ranked by incremental monthly sales ÷ effort. Priority labels: high impact = at or "
        f"above the median of enabled levers; low effort = {LOW_EFFORT_MAX} or less. "
        "Quick win (high/low), Big bet (high/high), Fill-in (low/low), Deprioritize (low/high)."
    )
