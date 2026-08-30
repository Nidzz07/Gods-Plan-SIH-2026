"""F3 + F5 - the composite score, the cap, coverage and the corroboration step.

The first test in this module is the one that matters most: it is NIGRANI's
equivalent of the inherited `test_zscore_is_not_an_input_to_the_score`, and it
is written now, before the ML tier of Phase 4 exists, so invariant 1 is
enforced from day one rather than retrofitted around a model that has already
been wired in.
"""

from __future__ import annotations

import pytest

from app.constants import Availability
from app.engine import derive as derive_mod
from app.engine.rulebook import loads
from app.engine.score import (
    CITATION_REQUIRED,
    MissingCitationError,
    compute,
    corroboration,
    coverage_pct,
    severity,
)

# A feature vector that fires five rules and skips none, so a perturbation has
# somewhere to show up.
BASELINE = {
    "variance_sanction_to_disbursement": -40.01,
    "variance_disbursement_to_certification": None,
    "sanction_lag_days": 333,
    "sanction_to_first_payment_days": 9,
    "first_payment_to_completion_days": 100,
    "execution_days": 400,
    "days_since_last_payment": 271,
    "duplicate_similarity": 0.4,
    "same_desc_same_agency_count": 15,
    "vendor_share_in_agency_pct": 17.35,
    "completed_without_payment": False,
    "asset_image_absent": True,
    "mp_utilisation_pct": 73.8,
    "payment_count": 1,
}


# ---------------------------------------------------------------------------
# Invariant 1 - structurally, not by convention
# ---------------------------------------------------------------------------


def test_an_ml_shaped_feature_cannot_move_the_score(rulebook, features_factory):
    """Perturb the model outputs; assert the score is byte-identical.

    The NIGRANI equivalent of LEAKPROOF's `test_zscore_is_not_an_input_to_the
    _score`, written before Phase 4 builds the models it guards against. An
    anomaly score, a z-score and a delay forecast are badges worth exactly
    zero: they may confirm what the rulebook found and they may not raise the
    number.
    """
    before = compute(features_factory(BASELINE), rulebook, 0)

    perturbed = features_factory(BASELINE)
    perturbed["anomaly_score"] = 0.9999
    perturbed["z_score"] = 12.5
    perturbed["delay_risk"] = 1.0
    perturbed["graph_centrality"] = 999.0
    perturbed.availability["anomaly_score"] = Availability.PUBLISHED
    after = compute(perturbed, rulebook, 0)

    assert after["score"] == before["score"]
    assert after["raw_score"] == before["raw_score"]
    assert after["severity"] == before["severity"]
    assert after["coverage_pct"] == before["coverage_pct"]
    assert after["rule_hits"] == before["rule_hits"]


def test_the_scorer_reads_only_fields_the_rulebook_names(rulebook, features_factory):
    """A second lock on the same door: a rule cannot even be WRITTEN to read a
    badge, because `rulebook.validate` rejects a field outside the dictionary."""
    from app.engine.rulebook import RulebookError, validate

    book = loads(
        """
        version: "v-test"
        rules:
          - id: anomaly_rule
            label: Anomaly model says so
            field: anomaly_score
            operator: gt
            threshold: 0.5
            severity: high
            weight: 50
        """
    )
    with pytest.raises(RulebookError):
        validate(book, derive_mod.FEATURE_KEYS)


def test_duplicate_similarity_is_the_single_declared_exception(rulebook):
    """It reads a model output AND contributes points, and that is admissible
    only because the trace row cites its evidence."""
    fields = {rule["field"] for rule in rulebook["rules"]}
    assert "duplicate_similarity" in fields
    assert CITATION_REQUIRED == ("duplicate_work",)


def test_a_fired_duplicate_hit_without_a_citation_is_an_error(rulebook, features_factory):
    features = features_factory(dict(BASELINE, duplicate_similarity=0.99))
    with pytest.raises(MissingCitationError, match="duplicate_work"):
        compute(features, rulebook, 0)


def test_a_fired_duplicate_hit_with_a_citation_carries_it(rulebook, features_factory):
    features = features_factory(
        dict(BASELINE, duplicate_similarity=0.99),
        evidence={"duplicate_work": {"matched_work_ids": ["WS/MP001/2025-2026/2"]}},
    )
    hit = next(h for h in compute(features, rulebook, 0)["rule_hits"] if h["rule_id"] == "duplicate_work")
    assert hit["citation"]["matched_work_ids"] == ["WS/MP001/2025-2026/2"]


# ---------------------------------------------------------------------------
# The arithmetic
# ---------------------------------------------------------------------------


def test_the_score_is_the_sum_of_fired_weights(rulebook, features_factory):
    body = compute(features_factory(BASELINE), rulebook, 0)
    fired = [hit for hit in body["rule_hits"] if hit["status"] == "fired"]
    assert body["raw_score"] == sum(hit["weight"] for hit in fired)
    assert body["raw_score"] == 22 + 20 + 16 + 16 + 10 + 10  # incl. asset evidence


def test_the_cap_does_not_renormalise(rulebook, features_factory):
    """A case over 100 stores its raw total and keeps every weight undivided.

    An officer re-deriving the trace on paper must be able to add the printed
    weights and reach the printed raw total. Dividing them by 1.54 to make the
    cap disappear would make the printed arithmetic wrong.
    """
    everything = dict(
        BASELINE,
        duplicate_similarity=0.99,
        completed_without_payment=True,
        mp_utilisation_pct=6.8,
        vendor_share_in_agency_pct=90.0,
    )
    features = derive_mod.FeatureSet(
        everything,
        {key: Availability.PUBLISHED for key in everything},
        {"duplicate_work": {"matched_work_ids": ["WS/MP001/2025-2026/2"]}},
    )
    features["variance_disbursement_to_certification"] = None
    features.availability["variance_disbursement_to_certification"] = Availability.NOT_PUBLISHED

    body = compute(features, rulebook, 3)
    # All ten rules fire: 144, plus the 10-point bonus.
    assert body["raw_score"] == 154
    assert body["score"] == 100
    assert body["score_cap"] == 100
    assert body["severity"] == "HIGH"
    for hit in body["rule_hits"]:
        assert hit["contribution"] == hit["weight"]
    assert sum(hit["contribution"] for hit in body["rule_hits"]) == 144


def test_a_case_over_the_cap_still_stores_its_raw_score(rulebook, features_factory):
    """fixtures.md's summary names 118 explicitly: stored raw, displayed 100.

    118 is 144 minus 26, and the only way to drop exactly 26 points of weight
    is to let `stalled_work` (16) and `split_sanction` (10) pass while every
    other rule fires. Eight rules firing without a skip is also the honest
    shape of a case over the cap: the cap is reached by evidence, not by
    absence of it, so no rule here is skipped and coverage stays at 100%.
    """
    features = features_factory(
        dict(
            BASELINE,
            duplicate_similarity=0.99,
            vendor_share_in_agency_pct=90.0,
            completed_without_payment=True,
            mp_utilisation_pct=6.8,
            # The two that pass, and the two that make 118 rather than 144.
            days_since_last_payment=100,
            same_desc_same_agency_count=1,
        ),
        evidence={"duplicate_work": {"matched_work_ids": ["WS/MP001/2025-2026/2"]}},
    )
    body = compute(features, rulebook, 0)
    # 22 + 20 + 18 + 16 + 12 + 12 + 10 + 8 = 118.
    assert body["raw_score"] == 118
    assert body["score"] == 100
    assert body["coverage_pct"] == 100
    passed = {hit["rule_id"] for hit in body["rule_hits"] if hit["status"] == "passed"}
    assert passed == {"stalled_work", "split_sanction"}
    # Undivided: an officer adding the printed weights must reach 118, not a
    # set of shares scaled by 1.18 to make the cap disappear.
    assert all(hit["contribution"] in (0, hit["weight"]) for hit in body["rule_hits"])
    assert sum(hit["contribution"] for hit in body["rule_hits"]) == 118


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------


def test_coverage_is_measured_by_weight_not_by_rule_count(rulebook, features_factory):
    """Fixture B's exact figure: (144 - 22 - 16 - 12) / 144 = 65%.

    Three of ten rules skipped is 70% by count and 65% by weight, and weight is
    the honest number: losing utilisation_shortfall costs 22 points of evidence
    and losing account_underutilisation costs 8.
    """
    features = features_factory(
        dict(
            BASELINE,
            variance_sanction_to_disbursement=None,
            days_since_last_payment=None,
            vendor_share_in_agency_pct=None,
        )
    )
    body = compute(features, rulebook, 0)
    skipped = [hit for hit in body["rule_hits"] if hit["status"] == "skipped"]
    assert sum(hit["weight"] for hit in skipped) == 50
    assert body["coverage_pct"] == 65


def test_skipped_weight_is_never_redistributed(rulebook, features_factory):
    """The same fired rules, with and without a skip, score the SAME number.

    If the skipped weight were redistributed, dropping evidence would raise the
    score of a case built on less of it.
    """
    full = features_factory(dict(BASELINE, execution_days=400))
    partial = features_factory(dict(BASELINE, execution_days=400, vendor_share_in_agency_pct=None))
    full_body = compute(full, rulebook, 0)
    partial_body = compute(partial, rulebook, 0)
    assert partial_body["raw_score"] == full_body["raw_score"]
    assert partial_body["coverage_pct"] < full_body["coverage_pct"]


def test_full_coverage_is_100(rulebook, features_factory):
    features = features_factory(dict(BASELINE, variance_disbursement_to_certification=-25.0))
    assert compute(features, rulebook, 0)["coverage_pct"] == 100


def test_coverage_helper_handles_an_empty_trace():
    assert coverage_pct([], 144) == 100


def test_coverage_basis_states_the_arithmetic(rulebook, features_factory):
    body = compute(
        features_factory(dict(BASELINE, variance_sanction_to_disbursement=None)), rulebook, 0
    )
    assert "122 of 144" in body["coverage_basis"]
    assert "never redistributed" in body["coverage_basis"]


# ---------------------------------------------------------------------------
# Corroboration - a step function, not a slope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "count,applied,contribution",
    [(0, False, 0), (1, False, 0), (2, False, 0), (3, True, 10), (4, True, 10), (25, True, 10)],
)
def test_corroboration_is_a_step_at_three(rulebook, count, applied, contribution):
    block = corroboration(rulebook, count)
    assert block["applied"] is applied
    assert block["contribution"] == contribution
    assert block["high_case_count"] == count


def test_corroboration_is_never_partial(rulebook):
    """One bad work is an incident; a pattern is a posture. There is no
    half-posture, so the bonus is never scaled by how far past three it sits."""
    assert corroboration(rulebook, 3)["contribution"] == corroboration(rulebook, 300)["contribution"]


def test_corroboration_falls_back_when_the_rulebook_omits_the_block():
    block = corroboration({}, 3)
    assert block["min_high_cases"] == 3
    assert block["contribution"] == 10


def test_the_bonus_reaches_the_raw_score(rulebook, features_factory):
    without = compute(features_factory(BASELINE), rulebook, 2)
    with_bonus = compute(features_factory(BASELINE), rulebook, 3)
    assert with_bonus["raw_score"] - without["raw_score"] == 10


def test_the_bonus_can_move_a_case_across_a_band(rulebook, features_factory):
    """65 + 10 = 75, exactly the HIGH edge. Recorded because it is the whole
    reason the bonus exists: a pattern under one agency changes the triage."""
    features = features_factory(
        dict(
            BASELINE,
            variance_sanction_to_disbursement=None,
            execution_days=400,
            sanction_lag_days=333,
            days_since_last_payment=271,
            same_desc_same_agency_count=15,
            asset_image_absent=True,
            vendor_share_in_agency_pct=17.0,
        )
    )
    assert compute(features, rulebook, 2)["severity"] == "MEDIUM"
    assert compute(features, rulebook, 3)["severity"] == "HIGH"


# ---------------------------------------------------------------------------
# Bands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score,band",
    [(0, "LOW"), (49, "LOW"), (50, "MEDIUM"), (74, "MEDIUM"), (75, "HIGH"), (100, "HIGH")],
)
def test_severity_bands_are_inclusive_at_their_edges(rulebook, score, band):
    assert severity(score, rulebook) == band


def test_severity_falls_back_to_75_and_50_without_a_rulebook_block():
    assert severity(75, {}) == "HIGH"
    assert severity(50, {}) == "MEDIUM"
    assert severity(49, {}) == "LOW"


def test_severity_is_banded_on_the_capped_score(rulebook, features_factory):
    features = features_factory(
        dict(BASELINE, duplicate_similarity=0.99, completed_without_payment=True),
        evidence={"duplicate_work": {"matched_work_ids": ["x"]}},
    )
    body = compute(features, rulebook, 0)
    assert body["raw_score"] > body["score"] or body["raw_score"] == body["score"]
    assert body["severity"] == severity(body["score"], rulebook)


# ---------------------------------------------------------------------------
# The case body shape
# ---------------------------------------------------------------------------


def test_the_case_body_carries_everything_the_contract_needs(rulebook, features_factory):
    body = compute(features_factory(BASELINE), rulebook, 3)
    for key in (
        "score",
        "raw_score",
        "score_cap",
        "severity",
        "coverage_pct",
        "coverage_basis",
        "gap_hop",
        "slowest_lag",
        "rulebook_version",
        "rule_hits",
        "corroboration",
        "unavailable_fields",
    ):
        assert key in body, key
    assert body["rulebook_version"] == "v1.0.0"
