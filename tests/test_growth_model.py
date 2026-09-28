import pytest

from modules.growth_model import (
    DEFAULT_LEVERS,
    Baseline,
    Driver,
    Lever,
    baseline_projection,
    isolated_impact,
    project,
    rank_by_impact,
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
    after = project(BASE, [Lever("x", driver, lift_pct=10)])
    assert sss_growth_pct(baseline_projection(BASE), after) == pytest.approx(10)


def test_lifts_compound_across_drivers():
    levers = [
        Lever("a", Driver.TRAFFIC, 10),
        Lever("b", Driver.AOV, 10),
    ]
    growth = sss_growth_pct(baseline_projection(BASE), project(BASE, levers))
    assert growth == pytest.approx(21)


def test_disabled_levers_are_ignored():
    after = project(BASE, [Lever("a", Driver.TRAFFIC, 50, enabled=False)])
    assert after.sales == pytest.approx(baseline_projection(BASE).sales)
    assert rank_by_impact(BASE, [Lever("a", Driver.TRAFFIC, 50, enabled=False)]) == []


def test_conversion_capped_at_100_pct():
    high = Baseline(monthly_orders=10, aov=10, conversion_rate=0.95)
    after = project(high, [Lever("c", Driver.CONVERSION, 20)])
    assert after.conversion_rate == 1.0
    assert after.conversion_capped


def test_ranking_is_by_impact_biggest_first():
    levers = [
        Lever("small", Driver.TRAFFIC, 5),  # +10k/mo
        Lever("off", Driver.TRAFFIC, 50, enabled=False),
        Lever("big", Driver.AOV, 20),  # +40k/mo
    ]
    ranked = rank_by_impact(BASE, levers)
    assert [r.lever.name for r in ranked] == ["big", "small"]
    assert [r.rank for r in ranked] == [1, 2]
    assert ranked[0].incremental_monthly_sales == pytest.approx(40_000)


def test_isolated_impact_ignores_enabled_flag():
    lever = Lever("a", Driver.AOV, 10, enabled=False)
    assert isolated_impact(BASE, lever) == pytest.approx(20_000)


def test_defaults_cover_all_four_levers():
    assert {l.name for l in DEFAULT_LEVERS} == {
        "Loyalty promo",
        "Checkout flow optimization",
        "Paid marketing spend",
        "Menu/UX redesign",
    }
