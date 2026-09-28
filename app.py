"""DCP Solutions Architect — Streamlit entry point.

Run with:  streamlit run app.py
"""

import streamlit as st

from modules import onboarding_playbook, sales_simulator, tech_stack_fit
from modules.state import init_state, load_example, reset
from modules.styles import hero, inject_css

st.set_page_config(
    page_title="DCP Solutions Architect",
    page_icon=":material/hub:",
    layout="wide",
)

TABS = ["1. Stack Fit", "2. Growth", "3. Rollout Plan"]


def render_header() -> None:
    left, right = st.columns([4, 1.4], vertical_alignment="center")
    with left:
        hero(
            "DoorDash Commerce Platform · Solutions Architect toolkit",
            "Will DCP fit this merchant, and what's it worth?",
            "Three steps: check their tech setup, estimate extra sales, get a rollout plan.",
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


def render_about() -> None:
    with st.expander("About this tool"):
        st.markdown(
            "This is a lightweight version of a DoorDash Commerce Platform Solutions "
            "Architect's workflow: judge how hard it is to connect a restaurant's "
            "existing systems, estimate the sales upside, and turn both into a rollout "
            "plan. All numbers are editable assumptions, and the example merchant is "
            "fictional. Personal portfolio project, not affiliated with DoorDash."
        )


def main() -> None:
    init_state()
    inject_css()
    render_header()

    # A keyed st.tabs keeps the selected tab across reruns. All tabs render every
    # run, in order, so later tabs can read what earlier ones computed.
    tab_fit, tab_growth, tab_plan = st.tabs(TABS, key="main_tab")
    with tab_fit:
        tech_stack_fit.render()
    with tab_growth:
        sales_simulator.render()
    with tab_plan:
        onboarding_playbook.render()

    render_about()


if __name__ == "__main__":
    main()
