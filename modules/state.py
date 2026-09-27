"""Session state shared across tabs: defaults, example loading, reset.

Every input widget is created with a `key` and no `value=`. Its value lives in
st.session_state, so it survives reruns and tab switches and can be set
programmatically (Load Example / Reset) before the widgets render.
"""

import streamlit as st

from modules.example_data import EXAMPLE_BASELINE, EXAMPLE_LEVERS, EXAMPLE_MERCHANT
from modules.fit_scoring import LoyaltyPlatform, MerchantProfile, PosSetup, assess_fit
from modules.growth_model import DEFAULT_LEVERS

DEFAULTS = {
    "fit_name": "",
    "fit_pos": PosSetup.TOAST.value,
    "fit_loyalty": LoyaltyPlatform.NONE.value,
    "fit_orders": 500_000,
    "fit_locations": 50,
    "growth_orders": 40_000,
    "growth_aov": 28.00,
    "growth_conv": 4.0,
    "lever_rows": DEFAULT_LEVERS,
    "lever_editor_version": 0,
}

# Derived results written by tabs; cleared on reset.
_RESULTS = ("fit_assessment", "growth_ranked", "growth_sss_pct")


def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def _bump_lever_editor() -> None:
    # A new key makes st.data_editor drop its old edits and show lever_rows.
    st.session_state["lever_editor_version"] += 1


def load_example() -> None:
    ss = st.session_state
    m = EXAMPLE_MERCHANT
    ss["fit_name"] = m["name"]
    ss["fit_pos"] = m["pos_setup"]
    ss["fit_loyalty"] = m["loyalty"]
    ss["fit_orders"] = m["annual_digital_orders"]
    ss["fit_locations"] = m["locations"]
    ss["growth_orders"] = EXAMPLE_BASELINE["monthly_orders"]
    ss["growth_aov"] = EXAMPLE_BASELINE["aov"]
    ss["growth_conv"] = EXAMPLE_BASELINE["conversion_pct"]
    ss["lever_rows"] = EXAMPLE_LEVERS
    _bump_lever_editor()
    # Pre-run the assessment so the Playbook tab is populated immediately.
    ss["fit_assessment"] = assess_fit(
        MerchantProfile(
            name=m["name"],
            pos_setup=PosSetup(m["pos_setup"]),
            loyalty=LoyaltyPlatform(m["loyalty"]),
            annual_digital_orders=m["annual_digital_orders"],
            locations=m["locations"],
        )
    )


def reset() -> None:
    ss = st.session_state
    for key, value in DEFAULTS.items():
        if key != "lever_editor_version":
            ss[key] = value
    _bump_lever_editor()
    for key in _RESULTS:
        ss.pop(key, None)
