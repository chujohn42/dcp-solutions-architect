"""End-to-end smoke test of the demo flow using Streamlit's headless AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def _button(at, label):
    return next(b for b in at.button if b.label == label)


def test_app_renders_without_errors():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception


def test_load_example_populates_every_tab_and_reset_clears():
    at = AppTest.from_file(APP, default_timeout=30).run()
    _button(at, "Load example merchant").click().run()
    assert not at.exception
    assert at.text_input(key="fit_name").value == "Harvest Lane Kitchen"
    assert at.number_input(key="growth_orders").value == 200_000
    labels = {m.label: m.value for m in at.metric}
    assert labels["Integration complexity"] == "High"
    assert labels["Total timeline"] == "~26 weeks"

    at.run()  # plain rerun keeps state
    assert "fit_assessment" in at.session_state

    _button(at, "Reset").click().run()
    assert not at.exception
    assert at.text_input(key="fit_name").value == ""
    assert "fit_assessment" not in at.session_state
