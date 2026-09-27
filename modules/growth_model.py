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

Prioritization: rank enabled levers by incremental monthly sales per effort
point (effort is a user-editable 1–5 score). Each lever also gets a 2×2 label
using the visible thresholds below.

Every number here is an assumption the user can edit in the UI; DEFAULT_LEVERS
is only a starting point, not a benchmark.
"""

from __future__ import annotations

import statistics
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
    effort: int  # 1 (easy) – 5 (hard)
    enabled: bool = True


# Placeholder assumptions: visible and editable in the UI, meant to be replaced.
DEFAULT_LEVERS: list[Lever] = [
    Lever("Loyalty promo", Driver.TRAFFIC, lift_pct=5.0, effort=2),
    Lever("Checkout flow optimization", Driver.CONVERSION, lift_pct=4.0, effort=3),
    Lever("Paid marketing spend", Driver.TRAFFIC, lift_pct=8.0, effort=2),
    Lever("Menu/UX redesign", Driver.AOV, lift_pct=3.0, effort=4),
]

# 2×2 thresholds: effort at or below LOW_EFFORT_MAX counts as low effort;
# impact at or above the median of enabled levers counts as high impact.
LOW_EFFORT_MAX = 2


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
    impact_per_effort: float
    quadrant: str


def _quadrant(high_impact: bool, low_effort: bool) -> str:
    if high_impact and low_effort:
        return "Quick win"
    if high_impact:
        return "Big bet"
    if low_effort:
        return "Fill-in"
    return "Deprioritize"


def prioritize(baseline: Baseline, levers: list[Lever]) -> list[RankedLever]:
    """Rank enabled levers by impact per effort point (ties: higher impact first)."""
    enabled = [l for l in levers if l.enabled]
    if not enabled:
        return []

    impacts = {l.name: isolated_impact(baseline, l) for l in enabled}
    median_impact = statistics.median(impacts.values())

    ordered = sorted(
        enabled,
        key=lambda l: (impacts[l.name] / l.effort, impacts[l.name]),
        reverse=True,
    )
    return [
        RankedLever(
            rank=i,
            lever=l,
            incremental_monthly_sales=impacts[l.name],
            impact_per_effort=impacts[l.name] / l.effort,
            quadrant=_quadrant(
                high_impact=impacts[l.name] >= median_impact,
                low_effort=l.effort <= LOW_EFFORT_MAX,
            ),
        )
        for i, l in enumerate(ordered, start=1)
    ]
