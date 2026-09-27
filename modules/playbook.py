"""Onboarding playbook generation — pure logic, no Streamlit.

Combines the Tech Stack Fit assessment (complexity, risks, phased approach) and
the Growth Simulator ranking into a four-phase rollout plan:

    Discovery → Migration → Launch → Optimization

Mapping:
- Discovery    ← fit Phase 1 (discovery & decision) + owning each risk
- Migration    ← fit Phase 2 (pilot build and validation)
- Launch       ← fit Phase 3 (rollout)
- Optimization ← enabled growth levers, in prioritized order

Phase durations come from PHASE_WEEKS, keyed by complexity. They are rough
planning assumptions, shown in the UI, not derived from data. Unscored stacks
use the High row as a conservative placeholder.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.fit_scoring import Complexity, FitAssessment, LoyaltyPlatform, PosSetup, Risk
from modules.growth_model import RankedLever

PHASE_NAMES = ("Discovery", "Migration", "Launch", "Optimization")

# Weeks per phase (Discovery, Migration, Launch, Optimization) by complexity.
PHASE_WEEKS: dict[Complexity, tuple[int, int, int, int]] = {
    Complexity.LOW: (2, 3, 2, 4),
    Complexity.MEDIUM: (3, 6, 3, 6),
    Complexity.HIGH: (4, 10, 4, 8),
}


@dataclass(frozen=True)
class PlaybookPhase:
    name: str
    start_week: int
    weeks: int
    activities: list[str]
    exit_criteria: str

    @property
    def end_week(self) -> int:
        return self.start_week + self.weeks


@dataclass(frozen=True)
class Playbook:
    merchant: str
    stack: str
    complexity_label: str
    phases: list[PlaybookPhase]
    risks: list[Risk]
    notes: list[str]
    sss_growth_pct: float | None

    @property
    def total_weeks(self) -> int:
        return self.phases[-1].end_week


def _discovery_exit(pos: PosSetup) -> str:
    return {
        PosSetup.TOAST: "Additive vs. replacement decided; Toast API access confirmed.",
        PosSetup.OLO: "Coexistence vs. replacement decided; affected Olo layers identified.",
        PosSetup.LEGACY: "POS inventory complete; POS-level integration scoped per system.",
    }.get(pos, "Stack identified and re-scored.")


def _optimization_activities(ranked: list[RankedLever]) -> list[str]:
    if not ranked:
        return ["No growth levers enabled in the Growth Simulator."]
    return [
        f"Priority {r.rank}: {r.lever.name} ({r.quadrant}). +{r.lever.lift_pct:g}% "
        f"{r.lever.driver.value}, projected +${r.incremental_monthly_sales:,.0f}/mo, "
        f"effort {r.lever.effort}/5."
        for r in ranked
    ]


def build_playbook(
    assessment: FitAssessment,
    ranked: list[RankedLever],
    sss_growth_pct: float | None = None,
) -> Playbook:
    profile = assessment.profile
    score = assessment.score
    fit_phases = assessment.phases
    punchh = profile.loyalty is LoyaltyPlatform.PUNCHH

    notes: list[str] = []
    if score.level is None:
        durations = PHASE_WEEKS[Complexity.HIGH]
        complexity_label = "Not scored"
        notes.append(
            "Stack not scored: timeline uses High durations as a conservative placeholder "
            "until discovery re-scores it."
        )
    else:
        durations = PHASE_WEEKS[score.level]
        complexity_label = score.level.label
    if score.capped:
        notes.append(
            "Complexity is capped at High (legacy POS + Punchh). Treat this timeline "
            "as a floor."
        )

    migration_exit = "Pilot live" + (" at the single location" if profile.locations == 1 else "")
    migration_exit += "; Punchh earn/redeem validated end-to-end." if punchh else "."

    activities = [
        fit_phases[0].steps + ["Assign an owner to each item in the risk register."],
        fit_phases[1].steps,
        fit_phases[2].steps,
        _optimization_activities(ranked),
    ]
    exits = [
        _discovery_exit(profile.pos_setup),
        migration_exit,
        f"All {profile.locations:,} locations live on DCP.",
        "Each lever measured against its projected lift; re-rank for the next cycle.",
    ]

    phases, week = [], 0
    for name, weeks, acts, exit_ in zip(PHASE_NAMES, durations, activities, exits):
        phases.append(PlaybookPhase(name, week, weeks, acts, exit_))
        week += weeks

    return Playbook(
        merchant=profile.name,
        stack=f"{profile.pos_setup.value} · Loyalty: {profile.loyalty.value}",
        complexity_label=complexity_label,
        phases=phases,
        risks=assessment.risks,
        notes=notes,
        sss_growth_pct=sss_growth_pct,
    )
