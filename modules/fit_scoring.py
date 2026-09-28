"""Tech stack fit scoring — pure logic, no Streamlit.

Every conclusion the Tech Stack Fit tab shows comes from this file. The rules
encode a fixed body of research on enterprise restaurant integration patterns
(Toast, Olo, Punchh, legacy POS) and deliberately do not go beyond it:

    | Current stack                          | Complexity | Reasoning                                        |
    |----------------------------------------|------------|--------------------------------------------------|
    | Toast (POS + online ordering)          | Medium     | Documented API, but likely replaces a Toast-     |
    |                                        |            | owned revenue surface                            |
    | Olo (Ordering + Rails)                 | Medium     | Architecturally similar to DCP; coexistence vs.  |
    |                                        |            | replacement decision, not a POS problem          |
    | Legacy POS only, no abstraction layer  | High       | No middleware; integration is close to POS-level |
    | Any stack + live Punchh loyalty        | +1 tier    | Real-time bidirectional loyalty sync adds        |
    |                                        |            | checkout-level risk                              |

Design choices worth calling out:
- Stacks the research doesn't cover ("Other" POS) are left unscored and routed
  to discovery rather than given a guessed tier.
- The Punchh bump is capped at High; the cap is reported, not hidden.
- Order volume and location count do NOT change the score (the research doesn't
  tie them to complexity). They only size the pilot and loyalty write-back load.
- LOW exists for completeness, but no stack in the table maps to it.

Entry points: `score_complexity()` (the table) and `assess_fit()` (score + risks
+ phased plan).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

class PosSetup(str, Enum):
    TOAST = "Toast"
    OLO = "Olo"
    LEGACY = "Legacy POS only"
    OTHER = "Other"


class LoyaltyPlatform(str, Enum):
    PUNCHH = "Punchh"
    OTHER = "Other"
    NONE = "None"


@dataclass(frozen=True)
class MerchantProfile:
    name: str
    pos_setup: PosSetup
    loyalty: LoyaltyPlatform
    annual_digital_orders: int | None = None
    locations: int | None = None


# ---------------------------------------------------------------------------
# The scoring table
# ---------------------------------------------------------------------------

class Complexity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @property
    def label(self) -> str:
        return self.name.capitalize()


BASE_COMPLEXITY: dict[PosSetup, tuple[Complexity, str]] = {
    PosSetup.TOAST: (
        Complexity.MEDIUM,
        "Well-documented API, but likely replacing a Toast-owned revenue surface",
    ),
    PosSetup.OLO: (
        Complexity.MEDIUM,
        "Architecturally similar to DCP; a coexistence vs. replacement decision, "
        "not a POS problem",
    ),
    PosSetup.LEGACY: (
        Complexity.HIGH,
        "No existing middleware; integration work is closer to POS-level",
    ),
}

PUNCHH_TIER_BUMP = 1


@dataclass(frozen=True)
class ComplexityScore:
    level: Complexity | None  # None = not scored (stack outside the research)
    base_level: Complexity | None
    reasoning: list[str]
    capped: bool = False


def score_complexity(pos_setup: PosSetup, loyalty: LoyaltyPlatform) -> ComplexityScore:
    """Apply the scoring table: base tier from the stack, +1 tier for Punchh."""
    if pos_setup not in BASE_COMPLEXITY:
        reasoning = [
            "Not scored: this stack is outside the research the scoring table is "
            "built on. Run discovery to map it to Toast, Olo, or legacy-POS "
            "patterns, then re-score."
        ]
        if loyalty is LoyaltyPlatform.PUNCHH:
            reasoning.append(
                "Punchh is live, so whatever base tier discovery lands on moves up "
                "one tier for bidirectional loyalty sync."
            )
        return ComplexityScore(level=None, base_level=None, reasoning=reasoning)

    base, why = BASE_COMPLEXITY[pos_setup]
    level, capped = base, False
    reasoning = [f"{pos_setup.value} → {base.label}: {why}."]

    if loyalty is LoyaltyPlatform.PUNCHH:
        bumped = base + PUNCHH_TIER_BUMP
        capped = bumped > Complexity.HIGH
        level = Complexity(min(bumped, Complexity.HIGH))
        note = (
            f"Punchh → +{PUNCHH_TIER_BUMP} tier ({base.label} → {level.label}): "
            "real-time bidirectional loyalty sync adds checkout-level risk."
        )
        if capped:
            note += (
                " Already at the top tier, so the score is capped at High, but the "
                "loyalty risk stacks on top of POS-level integration work."
            )
        reasoning.append(note)
    elif loyalty is LoyaltyPlatform.OTHER:
        reasoning.append(
            "Loyalty platform not scored: the research covers Punchh only. If it "
            "needs real-time bidirectional order sync, apply the same +1 tier."
        )

    return ComplexityScore(level=level, base_level=base, reasoning=reasoning, capped=capped)


# ---------------------------------------------------------------------------
# Risks and phased approach
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Risk:
    title: str
    detail: str
    short: str = ""  # one plain-language line for the UI


@dataclass(frozen=True)
class Phase:
    name: str
    steps: list[str]


@dataclass(frozen=True)
class FitAssessment:
    profile: MerchantProfile
    score: ComplexityScore
    risks: list[Risk]
    phases: list[Phase]
    orders_per_day: float | None
    orders_per_location_per_year: float | None


def _write_back_channels(pos_setup: PosSetup) -> str:
    channels = ["POS", "DCP"]
    if pos_setup is PosSetup.OLO:
        channels.append("marketplace orders via Olo Rails")
    if pos_setup is PosSetup.TOAST:
        channels.append("Toast online ordering (if it stays live)")
    return ", ".join(channels)


def identify_risks(profile: MerchantProfile, orders_per_day: float | None) -> list[Risk]:
    risks: list[Risk] = []
    pos = profile.pos_setup

    if pos is PosSetup.TOAST:
        risks += [
            Risk(
                "Revenue-surface replacement",
                "Toast bundles POS, payments, hardware and its own online ordering. "
                "If DCP replaces Toast's ordering surface instead of adding a channel, "
                "that's a vendor lock-in and commercial problem, not an API problem.",
                short="Replacing Toast's own online ordering is a business decision with Toast, not just a tech task.",
            ),
            Risk(
                "Additive vs. replacement not yet decided",
                "Reading from Toast's REST API (OAuth 2.0) is low-complexity, so the "
                "technical work isn't what's holding things up; scoping depends on "
                "the positioning decision.",
                short="Decide first: add DCP as an extra ordering channel, or replace Toast's ordering?",
            ),
        ]
    elif pos is PosSetup.OLO:
        risks += [
            Risk(
                "Coexistence vs. replacement",
                "Olo's Ordering API is the closest architectural analog to DCP. The "
                "POS-abstraction problem is already solved, so the real question is "
                "whether DCP runs alongside Olo or replaces it.",
                short="Decide first: run DCP alongside Olo, or replace Olo?",
            ),
            Risk(
                "Responsibilities currently owned by Rails and Omnivore",
                "Rails normalizes DoorDash/UberEats/Grubhub orders into the POS "
                "(menu, modifier and tax mapping); Omnivore/OloCloud abstracts the "
                "POS behind one REST layer. Replacement means those responsibilities "
                "need a new owner; coexistence means deciding which path DCP orders take.",
                short="Olo currently translates marketplace orders and menus for the POS; replacing Olo means rebuilding that.",
            ),
        ]
    elif pos is PosSetup.LEGACY:
        risks += [
            Risk(
                "No abstraction layer",
                "With no Olo/Omnivore-style middleware in place, DCP integration work "
                "falls close to POS-level (Aloha, Micros, PAR Brink).",
                short="There's no middleware (a translation layer), so DCP has to connect to the POS directly.",
            ),
        ]
        if profile.locations is None or profile.locations > 1:
            which = (
                "all locations"
                if profile.locations is None
                else f"all {profile.locations:,} locations"
            )
            risks.append(
                Risk(
                    "Mixed POS across locations",
                    f"Confirm {which} run the same POS. "
                    "Without middleware, each distinct POS system is its own "
                    "POS-level integration.",
                    short="Each different POS brand across locations is a separate integration.",
                )
            )
    else:
        risks.append(
            Risk(
                "Unscored stack",
                "This stack isn't covered by the research behind the scoring. Treat "
                "integration effort as unknown until discovery maps it.",
                short="This setup isn't covered by our research, so the effort is unknown until discovery.",
            )
        )

    if profile.loyalty is LoyaltyPlatform.PUNCHH:
        risks += [
            Risk(
                "Bidirectional loyalty sync",
                "Every order from every channel must write back to Punchh for points "
                f"and redemption to work: {_write_back_channels(pos)}.",
                short="Every order, from every channel, must sync to Punchh for points and rewards to work.",
            ),
            Risk(
                "Checkout failure surface",
                "Punchh adds a distinct failure point at checkout regardless of POS. "
                + (
                    f"At this volume that's roughly {orders_per_day:,.0f} digital orders "
                    "per day, each depending on a loyalty write-back."
                    if orders_per_day is not None
                    else "Every digital order depends on a loyalty write-back."
                ),
                short="If Punchh is slow or down, checkout can fail.",
            ),
        ]
    elif profile.loyalty is LoyaltyPlatform.OTHER:
        risks.append(
            Risk(
                "Unknown loyalty sync requirements",
                "Confirm whether the loyalty platform needs real-time order write-back "
                "from every channel. If it does, it carries the same checkout risk as Punchh.",
                short="Check whether the loyalty program needs every order synced in real time.",
            )
        )

    return risks


def recommend_phases(profile: MerchantProfile) -> list[Phase]:
    pos = profile.pos_setup
    punchh = profile.loyalty is LoyaltyPlatform.PUNCHH
    pilot_scope = (
        "the single location"
        if profile.locations == 1
        else "a few pilot locations"
        if profile.locations is None
        else f"a small subset of the {profile.locations:,} locations"
    )

    discovery: list[str] = []
    pilot: list[str] = []
    rollout: list[str] = []

    if pos is PosSetup.TOAST:
        discovery += [
            "Decide with the merchant: is DCP an additional channel or a replacement "
            "for Toast online ordering?",
            "Confirm Toast API access (OAuth 2.0) for the pilot locations.",
        ]
        pilot.append(
            f"Launch DCP as an additive channel at {pilot_scope}, even if replacement "
            "is the end state, so no Toast revenue surface is removed before DCP is proven."
        )
        rollout += [
            "Additive: expand the DCP channel to remaining locations.",
            "Replacement: retire Toast online ordering location by location, only "
            "after DCP reaches parity.",
        ]
    elif pos is PosSetup.OLO:
        discovery += [
            "Decide coexistence vs. replacement with the merchant.",
            "Inventory which Olo layers are live (Ordering API, Rails, "
            "Omnivore/OloCloud) and which the decision affects.",
        ]
        pilot.append(
            f"Run DCP at {pilot_scope}; validate that menu, modifier and tax data "
            "matches what Rails produces today."
        )
        rollout += [
            "Coexistence: expand DCP to remaining locations with the agreed order path.",
            "Replacement: move Rails/Omnivore responsibilities to their new owner "
            "before decommissioning Olo at each location.",
        ]
    elif pos is PosSetup.LEGACY:
        discovery += [
            "Inventory the POS system at each location (Aloha, Micros, PAR Brink).",
            "Scope a POS-level integration for each distinct POS system.",
        ]
        pilot.append(
            f"Build and validate the POS-level integration at {pilot_scope}, "
            "all on a single POS system."
        )
        rollout.append(
            "Roll out one POS system at a time; each additional system repeats pilot "
            "validation."
        )
    else:
        discovery.append(
            "Identify the POS and ordering setup, and whether an Omnivore-style "
            "abstraction layer already exists. Re-score before committing to a plan."
        )
        pilot.append(f"Hold the pilot at {pilot_scope} until discovery re-scores the stack.")
        rollout.append("Define after re-scoring.")

    if punchh:
        discovery.append(
            f"Map every channel that must write back to Punchh: {_write_back_channels(pos)}."
        )
        pilot.append(
            "Pilot exit gate: points earn and redemption work end-to-end on DCP orders, "
            "including checkout behaviour when Punchh is slow or unavailable."
        )
        rollout.append("Track loyalty write-back success as a rollout gate at each wave.")
    elif profile.loyalty is LoyaltyPlatform.OTHER:
        discovery.append("Confirm the loyalty platform's order write-back requirements.")

    return [
        Phase("Phase 1 — Discovery & decision", discovery),
        Phase("Phase 2 — Pilot", pilot),
        Phase("Phase 3 — Rollout", rollout),
    ]


def assess_fit(profile: MerchantProfile) -> FitAssessment:
    """Full structured assessment: complexity score, risks, phased approach."""
    orders = profile.annual_digital_orders
    orders_per_day = orders / 365 if orders is not None else None
    per_location = (
        orders / max(profile.locations, 1)
        if orders is not None and profile.locations is not None
        else None
    )
    return FitAssessment(
        profile=profile,
        score=score_complexity(profile.pos_setup, profile.loyalty),
        risks=identify_risks(profile, orders_per_day),
        phases=recommend_phases(profile),
        orders_per_day=orders_per_day,
        orders_per_location_per_year=per_location,
    )


# ---------------------------------------------------------------------------
# Plain-language summaries for the simplified UI (presentation only; they
# read the score, they don't change it)
# ---------------------------------------------------------------------------

_STACK_REASON = {
    PosSetup.TOAST: "Toast's API is easy to connect to, but DCP may replace Toast's own "
    "online ordering, which is a business decision",
    PosSetup.OLO: "Olo already works a lot like DCP, so the real question is whether to "
    "run both or replace Olo",
    PosSetup.LEGACY: "there's no middleware (a translation layer), so DCP has to connect "
    "to the POS directly",
}


def plain_reason(score: ComplexityScore, pos_setup: PosSetup, loyalty: LoyaltyPlatform) -> str:
    """One plain-English sentence explaining the score."""
    if score.level is None:
        return (
            "This setup isn't covered by the scoring research, so start with discovery "
            "and re-score."
        )
    reason = _STACK_REASON[pos_setup]
    if loyalty is LoyaltyPlatform.PUNCHH:
        if score.capped:
            reason += (
                ", and Punchh loyalty adds more risk because every order must sync "
                "points in real time (already at the top level)"
            )
        else:
            reason += (
                ", and Punchh loyalty bumps it up a level because every order must "
                "sync points in real time"
            )
    return reason[0].upper() + reason[1:] + "."


def top_risks(assessment: FitAssessment, n: int = 2) -> list[Risk]:
    """Up to n risks, taking the stack's lead risk and the loyalty lead risk first."""
    loyalty_titles = {
        "Bidirectional loyalty sync",
        "Checkout failure surface",
        "Unknown loyalty sync requirements",
    }
    stack = [r for r in assessment.risks if r.title not in loyalty_titles]
    loyalty = [r for r in assessment.risks if r.title in loyalty_titles]
    picked = stack[:1] + loyalty[:1]
    picked += [r for r in assessment.risks if r not in picked]
    return picked[:n]


def approach_summary(profile: MerchantProfile) -> list[str]:
    """Three one-line phases: discover, pilot, roll out."""
    pos = profile.pos_setup
    if pos is PosSetup.TOAST:
        lines = [
            "Discover: decide whether DCP is an extra channel or replaces Toast's ordering.",
            "Pilot: launch DCP as an extra channel at a few locations.",
            "Roll out: expand, and retire Toast ordering only once DCP matches it.",
        ]
    elif pos is PosSetup.OLO:
        lines = [
            "Discover: decide whether DCP runs alongside Olo or replaces it.",
            "Pilot: run DCP at a few locations and check that menus, options and tax match.",
            "Roll out: expand; if replacing Olo, move its order routing over first.",
        ]
    elif pos is PosSetup.LEGACY:
        lines = [
            "Discover: list which POS system each location uses.",
            "Pilot: build the direct POS connection at a few locations on one POS.",
            "Roll out: one POS system at a time.",
        ]
    else:
        lines = [
            "Discover: identify the POS and ordering setup, then re-score.",
            "Pilot: hold until the setup is scored.",
            "Roll out: plan after re-scoring.",
        ]
    if profile.loyalty is LoyaltyPlatform.PUNCHH:
        lines[1] = lines[1][:-1] + ", and confirm Punchh points and rewards work."
    return lines
