"""Tech Stack Fit tab — UI only. All scoring logic lives in fit_scoring.py."""

import pandas as pd
import streamlit as st

from modules.fit_scoring import (
    BASE_COMPLEXITY,
    PUNCHH_TIER_BUMP,
    FitAssessment,
    LoyaltyPlatform,
    MerchantProfile,
    PosSetup,
    assess_fit,
)
from modules.styles import score_card


def _input_form() -> MerchantProfile | None:
    with st.form("fit_inputs", border=True):
        name = st.text_input(
            "Merchant name", key="fit_name", placeholder="e.g. Harvest Lane Kitchen"
        )
        c1, c2 = st.columns(2)
        pos = c1.selectbox(
            "Current POS / ordering setup", [p.value for p in PosSetup], key="fit_pos"
        )
        loyalty = c2.selectbox(
            "Loyalty platform", [l.value for l in LoyaltyPlatform], key="fit_loyalty"
        )
        c3, c4 = st.columns(2)
        orders = c3.number_input(
            "Annual digital order volume", min_value=0, step=10_000, key="fit_orders"
        )
        locations = c4.number_input(
            "Number of locations", min_value=1, step=1, key="fit_locations"
        )
        submitted = st.form_submit_button(
            "Assess fit", type="primary", icon=":material/fact_check:"
        )

    if not submitted:
        return None
    return MerchantProfile(
        name=name.strip() or "Unnamed merchant",
        pos_setup=PosSetup(pos),
        loyalty=LoyaltyPlatform(loyalty),
        annual_digital_orders=int(orders),
        locations=int(locations),
    )


def _render_assessment(a: FitAssessment) -> None:
    st.divider()
    st.markdown(f"### Fit assessment: {a.profile.name}")
    st.caption(f"{a.profile.pos_setup.value} · Loyalty: {a.profile.loyalty.value}")

    # 1. Complexity score
    score = a.score
    c1, c2, c3 = st.columns(3)
    with c1:
        if score.level is None:
            score_card("Integration complexity", "Not scored", "none", "Needs discovery")
        else:
            score_card(
                "Integration complexity",
                score.level.label,
                score.level.name.lower(),
                "Capped at High, with Punchh risk on top" if score.capped else "",
            )
    c2.metric("Digital orders / day", f"{a.orders_per_day:,.0f}")
    c3.metric("Orders / location / year", f"{a.orders_per_location_per_year:,.0f}")

    for line in score.reasoning:
        st.markdown(f"- {line}")

    # 2. Risks
    st.markdown("#### Key migration risks")
    for risk in a.risks:
        with st.container(border=True):
            st.markdown(f"**{risk.title}**")
            st.write(risk.detail)

    # 3. Phased approach
    st.markdown("#### Recommended phased approach")
    cols = st.columns(len(a.phases))
    for col, phase in zip(cols, a.phases):
        with col, st.container(border=True):
            st.markdown(f"**{phase.name}**")
            for step in phase.steps:
                st.markdown(f"- {step}")


def _render_scoring_table() -> None:
    with st.expander("Scoring table used"):
        rows = [
            {"Current stack": pos.value, "Complexity": lvl.label, "Reasoning": why}
            for pos, (lvl, why) in BASE_COMPLEXITY.items()
        ]
        rows.append(
            {
                "Current stack": "Any stack + live Punchh loyalty",
                "Complexity": f"+{PUNCHH_TIER_BUMP} tier",
                "Reasoning": "Real-time bidirectional loyalty sync adds checkout-level risk",
            }
        )
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption(
            "Order volume and location count don't change the score. They size the "
            "pilot and the loyalty write-back load. Stacks marked 'Other' go to "
            "discovery and aren't given a guessed tier."
        )


def render() -> None:
    st.subheader("Tech Stack Fit Assessment")
    st.caption(
        "Map a merchant's current POS, ordering, and loyalty stack to DCP "
        "integration complexity, migration risks, and a phased plan."
    )
    _render_scoring_table()

    profile = _input_form()
    if profile is not None:
        st.session_state["fit_assessment"] = assess_fit(profile)

    # Form widgets only commit on submit, so the stored assessment always
    # matches the last submitted inputs.
    if "fit_assessment" in st.session_state:
        _render_assessment(st.session_state["fit_assessment"])
