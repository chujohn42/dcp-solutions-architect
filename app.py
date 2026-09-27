"""DCP Solutions Architect — Streamlit entry point.

Run with:  streamlit run app.py
"""

import streamlit as st

from modules import onboarding_playbook, sales_simulator, tech_stack_fit
from modules.example_data import EXAMPLE_BLURB
from modules.state import init_state, load_example, reset
from modules.styles import hero, inject_css, role_card

st.set_page_config(
    page_title="DCP Solutions Architect",
    page_icon=":material/hub:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TABS = ["Tech Stack Fit", "Growth Simulator", "Onboarding Playbook"]


def render_header() -> None:
    left, right = st.columns([4, 1.4], vertical_alignment="center")
    with left:
        hero(
            "Commerce Platform · Solutions Architect Toolkit",
            "Merchant fit, growth case & onboarding plan",
            "Assess a merchant's stack, model the same-store sales upside, and turn "
            "both into a phased rollout plan.",
        )
    with right:
        st.button(
            "Load example merchant",
            icon=":material/storefront:",
            type="primary",
            on_click=load_example,
            width="stretch",
        )
        st.button("Reset", icon=":material/restart_alt:", on_click=reset, width="stretch")


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Workflow")
        st.markdown(
            "1. **Tech Stack Fit**: complexity, risks, phased approach\n"
            "2. **Growth Simulator**: same-store sales levers, ranked by impact vs. effort\n"
            "3. **Onboarding Playbook**: combined rollout plan, exportable to PDF"
        )
        st.divider()
        st.markdown("### Example merchant")
        st.markdown(EXAMPLE_BLURB)


def render_role_mapping() -> None:
    st.divider()
    st.markdown("### How this maps to the DCP Solutions Architect role")
    st.markdown(
        "A Commerce Platform Solutions Architect sits between sales and implementation. "
        "They work out whether a merchant's existing systems can support DCP, build the "
        "business case for switching, and hand off a plan the onboarding team can execute. "
        "This toolkit is a lightweight version of that workflow, one tab per step."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        role_card(
            "Technical discovery",
            "Tech Stack Fit",
            "Scope integration complexity against the merchant's POS, ordering and "
            "loyalty systems, and surface the decisions (coexist vs. replace) and "
            "risks (loyalty sync) that drive effort.",
        )
    with c2:
        role_card(
            "Value engineering",
            "Growth Simulator",
            "Quantify the same-store sales case with transparent, editable "
            "assumptions, and rank growth levers by impact vs. effort so the pitch "
            "leads with quick wins.",
        )
    with c3:
        role_card(
            "Implementation planning",
            "Onboarding Playbook",
            "Turn fit and growth outputs into a phased rollout with timelines scaled "
            "to complexity, ready to share with the merchant and internal teams.",
        )
    st.caption(
        "Personal portfolio project, not affiliated with or endorsed by DoorDash. "
        "Integration patterns come from public research; all numbers are editable "
        "assumptions."
    )


def main() -> None:
    init_state()
    inject_css()
    render_sidebar()
    render_header()

    # A keyed st.tabs keeps the selected tab across reruns (button clicks, form
    # submits). All tabs render every run, so inputs in other tabs stay live.
    tab_fit, tab_growth, tab_playbook = st.tabs(TABS, key="main_tab")
    with tab_fit:
        tech_stack_fit.render()
    with tab_growth:
        sales_simulator.render()
    with tab_playbook:
        onboarding_playbook.render()

    render_role_mapping()


if __name__ == "__main__":
    main()
