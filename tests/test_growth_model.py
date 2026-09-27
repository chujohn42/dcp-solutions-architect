import pytest

from modules.growth_model import (
    DEFAULT_LEVERS,
    Baseline,
    Driver,
    Lever,
    baseline_projection,
    isolated_impact,
    prioritize,
    project,
    sss_growth_pct,
)

BASE = Baseline(monthly_orders=10_000, aov=20.0, conversion_rate=0.05)


def test_baseline_reconstructs_current_sales():
    p = baseline_projection(BASE)
    assert p.sessions == pytest.approx(200_000)
    assert p.orders == pytest.approx(10_000)
    assert p.sales == pytest.approx(200_000)


@pytest.mark.parametrize("driver", list(Driver))
def test_single_lever_lifts_sales_by_its_pct(driver):
    after = project(BASE, [Lever("x", driver, lift_pct=10, effort=1)])
    assert sss_growth_pct(baseline_projection(BASE), after) == pytest.approx(10)


def test_lifts_compound_across_drivers():
    levers = [
        Lever("a", Driver.TRAFFIC, 10, 1),
        Lever("b", Driver.AOV, 10, 1),
    ]
    growth = sss_growth_pct(baseline_projection(BASE), project(BASE, levers))
    assert growth == pytest.approx(21)


def test_disabled_levers_are_ignored():
    after = project(BASE, [Lever("a", Driver.TRAFFIC, 50, 1, enabled=False)])
    assert after.sales == pytest.approx(baseline_projection(BASE).sales)
    assert prioritize(BASE, [Lever("a", Driver.TRAFFIC, 50, 1, enabled=False)]) == []


def test_conversion_capped_at_100_pct():
    high = Baseline(monthly_orders=10, aov=10, conversion_rate=0.95)
    after = project(high, [Lever("c", Driver.CONVERSION, 20, 1)])
    assert after.conversion_rate == 1.0
    assert after.conversion_capped


def test_ranking_is_by_impact_per_effort():
    levers = [
        Lever("big-hard", Driver.TRAFFIC, 20, effort=5),  # 40k / 5 = 8k
        Lever("small-easy", Driver.TRAFFIC, 5, effort=1),  # 10k / 1 = 10k
    ]
    ranked = prioritize(BASE, levers)
    assert [r.lever.name for r in ranked] == ["small-easy", "big-hard"]
    assert ranked[0].quadrant == "Fill-in"
    assert ranked[1].quadrant == "Big bet"


def test_isolated_impact_ignores_enabled_flag():
    lever = Lever("a", Driver.AOV, 10, 1, enabled=False)
    assert isolated_impact(BASE, lever) == pytest.approx(20_000)


def test_defaults_cover_all_four_levers():
    assert {l.name for l in DEFAULT_LEVERS} == {
        "Loyalty promo",
        "Checkout flow optimization",
        "Paid marketing spend",
        "Menu/UX redesign",
    }
    assert all(1 <= l.effort <= 5 for l in DEFAULT_LEVERS)
