"""1. Stack Fit tab — UI only. All scoring logic lives in fit_scoring.py."""

import pandas as pd
import streamlit as st

from modules.fit_scoring import (
    BASE_COMPLEXITY,
    PUNCHH_TIER_BUMP,
    LoyaltyPlatform,
    MerchantProfile,
    PosSetup,
    approach_summary,
    assess_fit,
    plain_reason,
    top_risks,
)
from modules.styles import result_card

POS_LABELS = {
    PosSetup.TOAST.value: "Toast (register + online ordering)",
    PosSetup.OLO.value: "Olo (online ordering platform)",
    PosSetup.LEGACY.value: "Older POS only (Aloha, Micros, PAR Brink)",
    PosSetup.OTHER.value: "Other / not sure",
}
LOYALTY_LABELS = {
    LoyaltyPlatform.PUNCHH.value: "Punchh",
    LoyaltyPlatform.OTHER.value: "Another loyalty program",
    LoyaltyPlatform.NONE.value: "No loyalty program",
}


def _inputs() -> None:
    c1, c2, c3 = st.columns([1.1, 1.3, 1])
    c1.text_input("Merchant name", key="fit_name", placeholder="e.g. Harvest Lane Kitchen")
    c2.selectbox(
        "POS / online ordering setup",
        list(POS_LABELS),
        format_func=POS_LABELS.get,
        key="fit_pos",
        placeholder="Choose one…",
        help="POS (point of sale) is the restaurant's register system.",
    )
    c3.selectbox(
        "Loyalty program",
        list(LOYALTY_LABELS),
        format_func=LOYALTY_LABELS.get,
        key="fit_loyalty",
    )


def _scoring_table() -> None:
    with st.expander("How the score works"):
        rows = [
            {"Current setup": POS_LABELS[pos.value], "Difficulty": lvl.label, "Why": why}
            for pos, (lvl, why) in BASE_COMPLEXITY.items()
        ]
        rows.append(
            {
                "Current setup": "Any setup + Punchh loyalty",
                "Difficulty": f"+{PUNCHH_TIER_BUMP} level (max High)",
                "Why": "Every order must sync loyalty points in real time, which adds "
                "risk at checkout",
            }
        )
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption("Setups marked 'Other / not sure' aren't scored; they need discovery first.")


def render() -> None:
    st.caption(
        "Tell us what the merchant uses today. We'll rate how hard switching to "
        "DCP (DoorDash Commerce Platform) would be."
    )
    _inputs()

    ss = st.session_state
    if ss["fit_pos"] is None:
        ss.pop("fit_assessment", None)
        st.info("Choose the merchant's POS / online ordering setup to see the result.")
        _scoring_table()
        return

    # Annual volume comes from the Growth tab (monthly × 12); it only affects
    # wording in the PDF, never the score.
    a = assess_fit(
        MerchantProfile(
            name=ss["fit_name"].strip() or "Your merchant",
            pos_setup=PosSetup(ss["fit_pos"]),
            loyalty=LoyaltyPlatform(ss["fit_loyalty"]),
            annual_digital_orders=int(ss["growth_orders"]) * 12,
        )
    )
    ss["fit_assessment"] = a

    score = a.score
    result_card(
        "How hard is the switch to DCP?",
        "Not scored" if score.level is None else score.level.label,
        plain_reason(score, a.profile.pos_setup, a.profile.loyalty),
        level="none" if score.level is None else score.level.name.lower(),
    )

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Top 2 risks**")
        for r in top_risks(a):
            st.markdown(f"- {r.short}")
    with right:
        st.markdown("**Recommended approach**")
        for i, line in enumerate(approach_summary(a.profile), start=1):
            phase, text = line.split(": ", 1)
            st.markdown(f"{i}. **{phase}:** {text}")

    _scoring_table()
