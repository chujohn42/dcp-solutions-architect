import pytest

from modules.fit_scoring import (
    Complexity,
    LoyaltyPlatform,
    MerchantProfile,
    PosSetup,
    assess_fit,
    score_complexity,
)


@pytest.mark.parametrize(
    "pos, loyalty, expected",
    [
        (PosSetup.TOAST, LoyaltyPlatform.NONE, Complexity.MEDIUM),
        (PosSetup.OLO, LoyaltyPlatform.NONE, Complexity.MEDIUM),
        (PosSetup.LEGACY, LoyaltyPlatform.NONE, Complexity.HIGH),
        (PosSetup.TOAST, LoyaltyPlatform.PUNCHH, Complexity.HIGH),
        (PosSetup.OLO, LoyaltyPlatform.PUNCHH, Complexity.HIGH),
        (PosSetup.LEGACY, LoyaltyPlatform.PUNCHH, Complexity.HIGH),
        (PosSetup.TOAST, LoyaltyPlatform.OTHER, Complexity.MEDIUM),
    ],
)
def test_scoring_table(pos, loyalty, expected):
    assert score_complexity(pos, loyalty).level is expected


def test_punchh_on_legacy_is_capped_and_flagged():
    score = score_complexity(PosSetup.LEGACY, LoyaltyPlatform.PUNCHH)
    assert score.capped
    assert score.base_level is Complexity.HIGH


def test_punchh_bump_not_capped_from_medium():
    assert not score_complexity(PosSetup.OLO, LoyaltyPlatform.PUNCHH).capped


def test_other_pos_is_not_scored():
    score = score_complexity(PosSetup.OTHER, LoyaltyPlatform.PUNCHH)
    assert score.level is None
    assert any("Punchh" in r for r in score.reasoning)


def test_reasoning_is_combination_specific():
    olo = " ".join(score_complexity(PosSetup.OLO, LoyaltyPlatform.NONE).reasoning)
    assert "coexistence vs. replacement" in olo
    punchh = " ".join(score_complexity(PosSetup.TOAST, LoyaltyPlatform.PUNCHH).reasoning)
    assert "bidirectional" in punchh


def test_volume_and_locations_do_not_change_score():
    small = MerchantProfile("A", PosSetup.OLO, LoyaltyPlatform.NONE, 1_000, 1)
    large = MerchantProfile("B", PosSetup.OLO, LoyaltyPlatform.NONE, 50_000_000, 2_000)
    assert assess_fit(small).score.level is assess_fit(large).score.level


def test_olo_punchh_write_back_includes_rails():
    profile = MerchantProfile("M", PosSetup.OLO, LoyaltyPlatform.PUNCHH, 365_000, 10)
    a = assess_fit(profile)
    sync = next(r for r in a.risks if r.title == "Bidirectional loyalty sync")
    assert "Rails" in sync.detail
    assert a.orders_per_day == pytest.approx(1_000)
    assert len(a.phases) == 3
