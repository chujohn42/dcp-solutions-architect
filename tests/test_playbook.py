import pytest

from modules.fit_scoring import LoyaltyPlatform, MerchantProfile, PosSetup, assess_fit
from modules.growth_model import DEFAULT_LEVERS, Baseline, display_name, rank_by_impact
from modules.playbook import PHASE_NAMES, PHASE_WEEKS, build_playbook
from modules.playbook_pdf import playbook_to_pdf
from modules.fit_scoring import Complexity

RANKED = rank_by_impact(Baseline(40_000, 28.0, 0.04), DEFAULT_LEVERS)


def _pb(pos, loyalty=LoyaltyPlatform.NONE, locations=20):
    profile = MerchantProfile("Test Co", pos, loyalty, 500_000, locations)
    return build_playbook(assess_fit(profile), RANKED, 21.5)


def test_four_phases_in_order_and_contiguous():
    pb = _pb(PosSetup.OLO)
    assert [p.name for p in pb.phases] == list(PHASE_NAMES)
    for prev, nxt in zip(pb.phases, pb.phases[1:]):
        assert nxt.start_week == prev.end_week


@pytest.mark.parametrize(
    "pos, loyalty, level",
    [
        (PosSetup.TOAST, LoyaltyPlatform.NONE, Complexity.MEDIUM),
        (PosSetup.OLO, LoyaltyPlatform.PUNCHH, Complexity.HIGH),
        (PosSetup.LEGACY, LoyaltyPlatform.NONE, Complexity.HIGH),
    ],
)
def test_timeline_follows_complexity(pos, loyalty, level):
    assert _pb(pos, loyalty).total_weeks == sum(PHASE_WEEKS[level])


def test_higher_complexity_takes_longer():
    assert _pb(PosSetup.LEGACY).total_weeks > _pb(PosSetup.TOAST).total_weeks


def test_unscored_uses_high_with_note():
    pb = _pb(PosSetup.OTHER)
    assert pb.complexity_label == "Not scored"
    assert pb.total_weeks == sum(PHASE_WEEKS[Complexity.HIGH])
    assert pb.notes


def test_capped_score_is_noted():
    assert any("floor" in n for n in _pb(PosSetup.LEGACY, LoyaltyPlatform.PUNCHH).notes)


def test_optimization_lists_levers_in_rank_order():
    opt = _pb(PosSetup.TOAST).phases[-1].activities
    biggest = max(RANKED, key=lambda r: r.incremental_monthly_sales)
    assert opt[0].startswith(f"Priority 1: {display_name(biggest.lever)}")
    assert len(opt) == len(RANKED)


def test_punchh_gate_in_migration_exit():
    assert "Punchh" in _pb(PosSetup.OLO, LoyaltyPlatform.PUNCHH).phases[1].exit_criteria


def test_no_levers_message():
    profile = MerchantProfile("X", PosSetup.TOAST, LoyaltyPlatform.NONE, 1_000, 1)
    pb = build_playbook(assess_fit(profile), [])
    assert "No growth levers" in pb.phases[-1].activities[0]


def test_pdf_renders_with_special_characters():
    profile = MerchantProfile("Joe's <Tacos> & Co → ≤", PosSetup.LEGACY, LoyaltyPlatform.PUNCHH, 1_000, 3)
    pdf = playbook_to_pdf(build_playbook(assess_fit(profile), RANKED, 12.0))
    assert pdf.startswith(b"%PDF")

