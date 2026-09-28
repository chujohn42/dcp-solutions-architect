"""Same-store sales growth model — pure logic, no Streamlit.

Model (monthly, digital channel, existing stores only):

    sales = sessions × conversion rate × AOV
    sessions = current monthly orders ÷ current conversion rate

Each growth lever applies a relative lift to one driver (traffic, conversion or
AOV). Lifts on the same driver compound multiplicatively. Conversion is capped
at 100%.

Two views of impact:
- Combined: every enabled lever applied together → the before/after projection.
- Isolated: each lever applied alone → per-lever impact used for the chart and
  ranking. Isolated impacts don't sum exactly to the combined total because
  lifts on different drivers multiply.

Ranking: enabled levers are ordered by their isolated impact, biggest first.

Every number here is an assumption the user can edit in the UI; DEFAULT_LEVERS
is only a starting point, not a benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class Driver(str, Enum):
    TRAFFIC = "Traffic"
    CONVERSION = "Conversion"
    AOV = "AOV"


@dataclass(frozen=True)
class Baseline:
    monthly_orders: float
    aov: float
    conversion_rate: float  # fraction, e.g. 0.04 for 4%

    @property
    def sessions(self) -> float:
        return self.monthly_orders / self.conversion_rate


@dataclass(frozen=True)
class Lever:
    name: str
    driver: Driver
    lift_pct: float
    enabled: bool = True


# Placeholder assumptions: visible and editable in the UI, meant to be replaced.
DEFAULT_LEVERS: list[Lever] = [
    Lever("Loyalty promo", Driver.TRAFFIC, lift_pct=5.0),
    Lever("Checkout flow optimization", Driver.CONVERSION, lift_pct=4.0),
    Lever("Paid marketing spend", Driver.TRAFFIC, lift_pct=8.0),
    Lever("Menu/UX redesign", Driver.AOV, lift_pct=3.0),
]

# Plain-language UI labels and descriptions, keyed by lever name.
LEVER_INFO: dict[str, tuple[str, str]] = {
    "Loyalty promo": (
        "Loyalty promo",
        "Rewards that bring existing customers back more often.",
    ),
    "Checkout flow optimization": (
        "Checkout optimization",
        "Fewer steps and faster payment, so more visitors finish their order.",
    ),
    "Paid marketing spend": (
        "Paid marketing",
        "Ads that bring more visitors to the ordering site.",
    ),
    "Menu/UX redesign": (
        "Menu/UX redesign",
        "Better photos and add-on suggestions, so people spend more per order.",
    ),
}


# How each driver reads in plain English.
DRIVER_PLAIN: dict[Driver, str] = {
    Driver.TRAFFIC: "more visitors",
    Driver.CONVERSION: "more visitors ordering",
    Driver.AOV: "bigger orders",
}


def display_name(lever: Lever) -> str:
    return LEVER_INFO.get(lever.name, (lever.name, ""))[0]


@dataclass(frozen=True)
class Projection:
    sessions: float
    conversion_rate: float
    aov: float
    conversion_capped: bool = False

    @property
    def orders(self) -> float:
        return self.sessions * self.conversion_rate

    @property
    def sales(self) -> float:
        return self.orders * self.aov


def baseline_projection(baseline: Baseline) -> Projection:
    return Projection(baseline.sessions, baseline.conversion_rate, baseline.aov)


def project(baseline: Baseline, levers: list[Lever]) -> Projection:
    """Apply every enabled lever's lift to its driver and return the result."""
    multiplier = {d: 1.0 for d in Driver}
    for lever in levers:
        if lever.enabled:
            multiplier[lever.driver] *= 1 + lever.lift_pct / 100

    conversion = baseline.conversion_rate * multiplier[Driver.CONVERSION]
    return Projection(
        sessions=baseline.sessions * multiplier[Driver.TRAFFIC],
        conversion_rate=min(conversion, 1.0),
        aov=baseline.aov * multiplier[Driver.AOV],
        conversion_capped=conversion > 1.0,
    )


def sss_growth_pct(before: Projection, after: Projection) -> float:
    return (after.sales / before.sales - 1) * 100 if before.sales else 0.0


def isolated_impact(baseline: Baseline, lever: Lever) -> float:
    """Incremental monthly sales from this lever alone."""
    alone = replace(lever, enabled=True)
    return project(baseline, [alone]).sales - baseline_projection(baseline).sales


@dataclass(frozen=True)
class RankedLever:
    rank: int
    lever: Lever
    incremental_monthly_sales: float


def rank_by_impact(baseline: Baseline, levers: list[Lever]) -> list[RankedLever]:
    """Enabled levers ordered by extra sales when applied alone, biggest first."""
    impacts = [(l, isolated_impact(baseline, l)) for l in levers if l.enabled]
    impacts.sort(key=lambda pair: pair[1], reverse=True)
    return [
        RankedLever(rank=i, lever=l, incremental_monthly_sales=impact)
        for i, (l, impact) in enumerate(impacts, start=1)
    ]
