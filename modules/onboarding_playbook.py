"""Onboarding Playbook tab — UI only. Plan logic lives in playbook.py."""

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
            alt.Tooltip("Start:Q", title="Start week"),
            alt.Tooltip("End:Q", title="End week"),
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
    return (bars + labels).properties(height=190)


def _render_assumptions() -> None:
    with st.expander("Timeline assumptions (weeks per phase)"):
        rows = [
            {"Complexity": lvl.label, **dict(zip(PHASE_NAMES, weeks)), "Total": sum(weeks)}
            for lvl, weeks in PHASE_WEEKS.items()
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption(
            "Rough planning durations, not benchmarks. Edit `PHASE_WEEKS` in "
            "modules/playbook.py. Unscored stacks use the High row."
        )


def _file_name(merchant: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", merchant.lower()).strip("-") or "merchant"
    return f"dcp-onboarding-playbook-{slug}.pdf"


def render() -> None:
    st.subheader("Onboarding Playbook")
    st.caption(
        "Built from the Tech Stack Fit assessment and the Growth Simulator's "
        "prioritized levers."
    )
    _render_assumptions()

    assessment = st.session_state.get("fit_assessment")
    if assessment is None:
        st.info("Run an assessment on the **Tech Stack Fit** tab first to generate a playbook.")
        return

    pb = build_playbook(
        assessment,
        st.session_state.get("growth_ranked", []),
        st.session_state.get("growth_sss_pct"),
    )

    st.divider()
    head, button = st.columns([3, 1])
    with head:
        st.markdown(f"### {pb.merchant}")
        st.caption(pb.stack)
    button.download_button(
        "Download as PDF",
        data=playbook_to_pdf(pb),
        file_name=_file_name(pb.merchant),
        mime="application/pdf",
        type="primary",
        width="stretch",
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Integration complexity", pb.complexity_label)
    m2.metric("Total timeline", f"~{pb.total_weeks} weeks")
    m3.metric(
        "Projected digital SSS growth",
        "—" if pb.sss_growth_pct is None else f"{pb.sss_growth_pct:.1f}%",
    )
    for note in pb.notes:
        st.warning(note)

    st.altair_chart(_timeline_chart(pb), width="stretch")

    cols = st.columns(len(pb.phases))
    for col, phase in zip(cols, pb.phases):
        with col, st.container(border=True):
            st.markdown(f"**{phase.name}**")
            st.caption(f"Weeks {phase.start_week}–{phase.end_week} · {phase.weeks} wks")
            for a in phase.activities:
                st.markdown(f"- {a}")
            st.markdown(f"**Exit:** {phase.exit_criteria}")

    if pb.risks:
        with st.expander(f"Risk register ({len(pb.risks)})"):
            for r in pb.risks:
                st.markdown(f"**{r.title}**: {r.detail}")
