"""3. Rollout Plan tab — UI only. Plan logic lives in playbook.py."""

import re

import altair as alt
import pandas as pd
import streamlit as st

from modules.playbook import PHASE_NAMES, PHASE_WEEKS, Playbook, build_playbook
from modules.playbook_pdf import playbook_to_pdf

BAR_COLOR = "#2a78d6"


def _timeline_chart(pb: Playbook) -> alt.Chart:
    df = pd.DataFrame(
        [
            {"Phase": p.name, "Start": p.start_week, "End": p.end_week, "Weeks": p.weeks}
            for p in pb.phases
        ]
    )
    base = alt.Chart(df).encode(
        y=alt.Y("Phase:N", sort=list(PHASE_NAMES), title=None),
        tooltip=[
            alt.Tooltip("Phase:N"),
            alt.Tooltip("Start:Q", title="Starts week"),
            alt.Tooltip("End:Q", title="Ends week"),
            alt.Tooltip("Weeks:Q"),
        ],
    )
    bars = base.mark_bar(color=BAR_COLOR, cornerRadius=4, size=22).encode(
        x=alt.X("Start:Q", title="Week", axis=alt.Axis(tickMinStep=1)),
        x2="End:Q",
    )
    labels = base.mark_text(align="left", dx=6).encode(
        x="End:Q", text=alt.Text("Weeks:Q", format="d")
    )
    return (bars + labels).properties(height=170)


def _file_name(merchant: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", merchant.lower()).strip("-") or "merchant"
    return f"dcp-rollout-plan-{slug}.pdf"


def _assumptions() -> None:
    with st.expander("How long each phase takes"):
        rows = [
            {"Difficulty": lvl.label, **dict(zip(PHASE_NAMES, weeks)), "Total weeks": sum(weeks)}
            for lvl, weeks in PHASE_WEEKS.items()
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption("Rough planning estimates in weeks. Harder switches take longer.")


def render() -> None:
    assessment = st.session_state.get("fit_assessment")
    if assessment is None:
        st.info(
            "Start with **1. Stack Fit**: choose the merchant's POS / online ordering "
            "setup and your rollout plan will appear here. Or click **Load example "
            "merchant** above.",
            icon=":material/arrow_back:",
        )
        return

    pb = build_playbook(
        assessment,
        st.session_state.get("growth_ranked", []),
        st.session_state.get("growth_sss_pct"),
    )
    extra = st.session_state.get("growth_extra_per_year")

    head, button = st.columns([3, 1], vertical_alignment="center")
    head.markdown(f"#### Rollout plan: {pb.merchant}")
    button.download_button(
        "Download as PDF",
        data=playbook_to_pdf(pb),
        file_name=_file_name(pb.merchant),
        mime="application/pdf",
        type="primary",
        icon=":material/download:",
        width="stretch",
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Integration complexity", pb.complexity_label)
    m2.metric("Total timeline", f"~{pb.total_weeks} weeks")
    m3.metric("Extra sales per year", "—" if extra is None else f"${extra:,.0f}")
    for note in pb.notes:
        st.caption(f":material/info: {note}")

    st.altair_chart(_timeline_chart(pb), width="stretch")

    cols = st.columns(len(pb.phases))
    for col, phase in zip(cols, pb.phases):
        with col, st.container(border=True):
            st.markdown(f"**{phase.name}** · {phase.weeks} wks")
            for line in phase.highlights[:2]:
                st.markdown(f"- {line}")
    st.caption("The PDF includes the full detail: every step, exit criteria and risks.")
    _assumptions()
