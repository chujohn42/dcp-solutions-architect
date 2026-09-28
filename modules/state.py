"""Session state shared across tabs: defaults, example loading, reset.

Every input widget is created with a `key` and no `value=`. Its value lives in
st.session_state, so it survives reruns and tab switches and can be set
programmatically (Load Example / Reset) before the widgets render.
"""

import streamlit as st

from modules.example_data import EXAMPLE_BASELINE, EXAMPLE_LEVERS, EXAMPLE_MERCHANT
from modules.fit_scoring import LoyaltyPlatform
from modules.growth_model import DEFAULT_LEVERS

DEFAULTS = {
    "fit_name": "",
    "fit_pos": None,  # nothing chosen yet → Stack Fit and Rollout Plan wait for input
    "fit_loyalty": LoyaltyPlatform.NONE.value,
    "growth_orders": 40_000,
    "growth_aov": 28.00,
    "growth_conv": 4.0,
}
for _i, _lever in enumerate(DEFAULT_LEVERS):
    DEFAULTS[f"lever_on_{_i}"] = True
    DEFAULTS[f"lift_{_i}"] = _lever.lift_pct

# Derived results written by tabs; cleared on reset.
_RESULTS = ("fit_assessment", "growth_ranked", "growth_sss_pct", "growth_extra_per_year")


def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def load_example() -> None:
    ss = st.session_state
    ss["fit_name"] = EXAMPLE_MERCHANT["name"]
    ss["fit_pos"] = EXAMPLE_MERCHANT["pos_setup"]
    ss["fit_loyalty"] = EXAMPLE_MERCHANT["loyalty"]
    ss["growth_orders"] = EXAMPLE_BASELINE["monthly_orders"]
    ss["growth_aov"] = EXAMPLE_BASELINE["aov"]
    ss["growth_conv"] = EXAMPLE_BASELINE["conversion_pct"]
    for i, lever in enumerate(EXAMPLE_LEVERS):
        ss[f"lever_on_{i}"] = True
        ss[f"lift_{i}"] = lever.lift_pct


def reset() -> None:
    ss = st.session_state
    for key, value in DEFAULTS.items():
        ss[key] = value
    for key in _RESULTS:
        ss.pop(key, None)
