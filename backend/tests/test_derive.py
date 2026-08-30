"""F1 - the derived feature dictionary, both ladders, and their null semantics.

Every branch that produces `None` is exercised here with the reason it carries,
including the ones the current corpus never reaches. A derivation branch nothing
tests is the declared-but-never-computed defect CLAUDE.md invariant 3 exists to
prevent, and "it never happens on this download" is not the same as "it cannot
happen on the next one".
"""

from __future__ import annotations

from datetime import date

import pytest

from app.constants import DATA_AS_OF, Availability
from app.engine import derive as derive_mod
from app.engine.derive import (
    FEATURE_KEYS,
    CorpusContext,
    asset_image_absent,
    completed_without_payment,
    days_since_last_payment,
    derive,
    disbursed_amount,
    duplicate_similarity,
    execution_days,
    first_payment_to_completion_days,
    fund_ladder,
    hop_tolerance,
    lifecycle_ladder,
    locate_gap,
    mp_utilisation_pct,
    normalise_description,
    same_desc_same_agency_count,
    sanction_lag_days,
    sanction_to_first_payment_days,
    slowest_lag,
    variance_disbursement_to_certification,
    variance_sanction_to_disbursement,
    vendor_share_in_agency_pct,
)

from .conftest import certification, completion, context, payment, sanction, work


# ---------------------------------------------------------------------------
# Fund ladder - hop 1
# ---------------------------------------------------------------------------


def test_variance_is_signed_and_expressed_against_the_upper_rung():
    value, availability = variance_sanction_to_disbursement(
        sanction(sanctioned_amt=199_539), [payment(paid_amt=119_711)]
    )
    assert round(value, 2) == -40.01
    assert availability == Availability.PUBLISHED


def test_no_payment_row_is_not_published_not_a_zero_variance():
    """The whole of F5 in one assertion.

    23,549 of 27,078 sanctioned works are in this state because the expenditure
    export is truncated. Reporting them as a 0.00% variance would turn a
    reporting gap into 23,549 clean records.
    """
    value, availability = variance_sanction_to_disbursement(sanction(), [])
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_zero_payment_is_published_zero_not_missing():
    """A payment published AS zero is a fact about the work, not an absence.

    Named in docs/contract/fixtures.md as the test that covers the third
    availability state, which none of the three fixtures exercises. The
    variance is computed - -100% - and the rule FIRES; it is not skipped.
    """
    with_zero = [payment(paid_amt=0)]
    disbursed, disbursed_availability = disbursed_amount(with_zero)
    assert disbursed == 0
    assert disbursed_availability == Availability.PUBLISHED_ZERO

    value, availability = variance_sanction_to_disbursement(
        sanction(sanctioned_amt=1_000_000), with_zero
    )
    assert value == -100.0
    assert availability == Availability.PUBLISHED

    # And the absence is a different object entirely.
    missing, missing_availability = variance_sanction_to_disbursement(sanction(), [])
    assert missing is None
    assert missing_availability == Availability.NOT_PUBLISHED


def test_a_sanctioned_amount_of_zero_cannot_be_a_denominator():
    """`published_zero` as a SKIP reason, not as a value: a zero rung cannot
    carry a percentage, and that is different from never having been published."""
    value, availability = variance_sanction_to_disbursement(
        sanction(sanctioned_amt=0), [payment(paid_amt=100)]
    )
    assert value is None
    assert availability == Availability.PUBLISHED_ZERO


def test_payments_sum_across_multiple_rows():
    value, _ = variance_sanction_to_disbursement(
        sanction(sanctioned_amt=1_000_000),
        [payment(paid_amt=400_000), payment(paid_amt=200_000)],
    )
    assert value == -40.0


# ---------------------------------------------------------------------------
# Fund ladder - hop 2, which no real row can populate
# ---------------------------------------------------------------------------


def test_certification_hop_is_not_published_when_there_is_no_certificate():
    value, availability = variance_disbursement_to_certification(
        [payment(paid_amt=3_880_000)], None
    )
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_certification_hop_computes_against_a_labelled_control():
    value, availability = variance_disbursement_to_certification(
        [payment(paid_amt=3_880_000)], certification(certified_amt=2_910_000)
    )
    assert round(value, 2) == -25.00
    assert availability == Availability.PUBLISHED


def test_certification_hop_needs_a_disbursement_to_measure_against():
    value, availability = variance_disbursement_to_certification(
        [], certification(certified_amt=100)
    )
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


# ---------------------------------------------------------------------------
# Lifecycle ladder
# ---------------------------------------------------------------------------


def test_sanction_lag_is_whole_days_date_to_date():
    value, availability = sanction_lag_days(
        sanction(recommended_date=date(2024, 12, 19), sanction_date=date(2025, 11, 17))
    )
    assert value == 333
    assert availability == Availability.PUBLISHED


def test_sanction_lag_is_not_published_without_a_recommendation_date():
    value, availability = sanction_lag_days(
        sanction(
            recommended_date=None,
            recommended_date_availability=Availability.NOT_PUBLISHED,
        )
    )
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_first_payment_lag_is_not_applicable_when_no_payment_exists():
    """The work has not reached the stage, which is not a reporting failure."""
    value, availability = sanction_to_first_payment_days(sanction(), [])
    assert value is None
    assert availability == Availability.NOT_APPLICABLE


def test_first_payment_lag_is_not_published_when_a_payment_carries_no_date():
    """Zero rows are in this state on the current corpus, and the branch still
    has a test: a later download that starts omitting payment dates must not
    read as a set of works that never reached the payment stage."""
    value, availability = sanction_to_first_payment_days(
        sanction(), [payment(payment_date=None)]
    )
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_first_payment_lag_takes_the_earliest_payment():
    value, _ = sanction_to_first_payment_days(
        sanction(sanction_date=date(2025, 4, 8)),
        [payment(payment_date=date(2026, 2, 11)), payment(payment_date=date(2025, 5, 20))],
    )
    assert value == 42


def test_a_negative_completion_lag_is_carried_through_and_never_clamped():
    """163 works are reported complete BEFORE their first payment.

    Neither source row is malformed - the completed export and the expenditure
    export simply disagree - so clamping to zero would erase the disagreement
    instead of showing an officer that it exists.
    """
    value, availability = first_payment_to_completion_days(
        [payment(payment_date=date(2026, 1, 1))], completion(completion_date=date(2025, 6, 1))
    )
    assert value == -214
    assert availability == Availability.PUBLISHED


def test_execution_days_is_computed_directly_not_as_a_sum_of_lags():
    """A work with a completion and NO payment still has execution days.

    This is fixture B's shape. Under a sum-of-lags definition the value would
    be None and the 20-point `execution_delay` rule would never fire on any of
    the 14,104 works the payment join does not reach.
    """
    value, availability = execution_days(
        sanction(sanction_date=date(2024, 11, 21)),
        completion(completion_date=date(2026, 5, 14)),
    )
    assert value == 539
    assert availability == Availability.PUBLISHED

    lag, _ = sanction_to_first_payment_days(sanction(sanction_date=date(2024, 11, 21)), [])
    assert lag is None


def test_execution_days_is_not_applicable_without_a_completion():
    value, availability = execution_days(sanction(), None)
    assert value is None
    assert availability == Availability.NOT_APPLICABLE


def test_the_sum_identity_holds_where_both_lags_exist():
    """42 + 439 = 481, fixture C. Asserted only where all three are computable."""
    s = sanction(sanction_date=date(2025, 4, 8))
    payments = [payment(payment_date=date(2025, 5, 20)), payment(payment_date=date(2026, 2, 11))]
    finished = completion(completion_date=date(2026, 8, 2))
    first, _ = sanction_to_first_payment_days(s, payments)
    rest, _ = first_payment_to_completion_days(payments, finished)
    whole, _ = execution_days(s, finished)
    assert (first, rest, whole) == (42, 439, 481)
    assert first + rest == whole


def test_days_since_last_payment_is_measured_to_the_corpus_as_of_date():
    """Never against `today`: a case re-derived in six months must reproduce
    the number the officer acted on, or the audit trail is a lie."""
    assert DATA_AS_OF == date(2026, 8, 24)
    value, availability = days_since_last_payment(
        [payment(payment_date=date(2025, 11, 26)), payment(payment_date=date(2025, 3, 1))]
    )
    assert value == 271
    assert availability == Availability.PUBLISHED


def test_days_since_last_payment_is_not_published_with_no_payment():
    value, availability = days_since_last_payment([])
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


# ---------------------------------------------------------------------------
# Status, evidence and the account rung
# ---------------------------------------------------------------------------


def test_completed_without_payment_needs_both_halves():
    assert completed_without_payment(work(status="Work Completed"), [])[0] is True
    assert completed_without_payment(work(status="Work Completed"), [payment()])[0] is False
    assert completed_without_payment(work(status="Physical Inspection"), [])[0] is False


def test_completed_without_payment_is_not_published_without_a_status():
    value, availability = completed_without_payment(
        work(status=None, status_availability=Availability.NOT_PUBLISHED), []
    )
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_asset_image_has_three_states_and_they_stay_apart():
    """The correction DOMAIN-MODEL.md section (f) records, asserted.

    Published-and-absent fires the rule on 4,493 works. Not-published skips it
    on 14,104. Collapsing them would fire an evidence rule on a reporting gap
    across 52% of the corpus.
    """
    present = asset_image_absent(work(asset_image_present=True))
    absent = asset_image_absent(work(asset_image_present=False))
    unpublished = asset_image_absent(
        work(
            asset_image_present=None,
            asset_image_availability=Availability.NOT_PUBLISHED,
        )
    )
    assert present == (False, Availability.PUBLISHED)
    assert absent == (True, Availability.PUBLISHED)
    assert unpublished == (None, Availability.NOT_PUBLISHED)


def test_mp_utilisation_is_sanctioned_over_allocated():
    value, availability = mp_utilisation_pct(
        work(mp_id=1),
        context(mp_account={1: (196_063_957, Availability.PUBLISHED, 144_700_484)}),
    )
    assert round(value, 2) == 73.80
    assert availability == Availability.PUBLISHED


def test_mp_utilisation_is_not_published_without_an_allocation_row():
    value, availability = mp_utilisation_pct(work(mp_id=99), context())
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_an_allocation_published_as_zero_is_published_zero_not_missing():
    """The third availability state again, on the other side of the ladder."""
    value, availability = mp_utilisation_pct(
        work(mp_id=1), context(mp_account={1: (0, Availability.PUBLISHED_ZERO, 500)})
    )
    assert value is None
    assert availability == Availability.PUBLISHED_ZERO


def test_vendor_share_is_measured_over_the_agencys_whole_disbursement():
    """Restricting the denominator to sanctioned works turns a 17% vendor into
    a 100% one, which DATA-PROFILE.md section 6 records as the wrong answer."""
    ctx = context(
        agency_disbursed={1: 17_936_298}, agency_vendor_disbursed={(1, 7): 3_112_486}
    )
    value, availability = vendor_share_in_agency_pct(
        work(agency_id=1), [payment(vendor_id=7, paid_amt=119_711)], ctx
    )
    assert round(value, 2) == 17.35
    assert availability == Availability.PUBLISHED


def test_vendor_share_is_not_applicable_below_the_fifty_lakh_floor():
    """A small office with one work is not a concentrated one."""
    ctx = context(agency_disbursed={1: 3_880_000}, agency_vendor_disbursed={(1, 1): 3_880_000})
    value, availability = vendor_share_in_agency_pct(
        work(agency_id=1), [payment(vendor_id=1, paid_amt=3_880_000)], ctx
    )
    assert value is None
    assert availability == Availability.NOT_APPLICABLE


def test_vendor_share_is_not_published_without_a_payment():
    value, availability = vendor_share_in_agency_pct(work(agency_id=1), [], context())
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


# ---------------------------------------------------------------------------
# Description normalisation, repetition and similarity
# ---------------------------------------------------------------------------


def test_normalisation_lowercases_strips_punctuation_and_collapses_space():
    assert normalise_description("Led Semi High Mast Light (6LED) with 200-watt, 9.5-meter pole") == (
        "led semi high mast light 6led with 200 watt 9 5 meter pole"
    )


def test_a_description_with_no_readable_text_normalises_to_nothing():
    """79 sanctioned works: the portal exported non-Latin text as question marks."""
    assert normalise_description("???? ????? ??? ??????") == ""
    assert normalise_description(None) == ""


def _loaded(rows):
    ctx = context()
    ctx.load_descriptions(rows)
    return ctx


def test_cluster_count_is_exact_repetition_blocked_by_agency():
    ctx = _loaded(
        [
            (1, "WS/MP001/2025-2026/1", 1, "High mast LED light"),
            (2, "WS/MP001/2025-2026/2", 1, "high mast led light"),
            (3, "WS/MP001/2025-2026/3", 1, "HIGH MAST LED LIGHT!"),
            (4, "WS/MP001/2025-2026/4", 2, "High mast LED light"),
            (5, "WS/MP001/2025-2026/5", 1, "Repair of a school boundary wall"),
        ]
    )
    assert same_desc_same_agency_count(work(id=1, agency_id=1), ctx)[0] == 3
    # A different agency does not join the cluster, even on identical text.
    assert same_desc_same_agency_count(work(id=4, agency_id=2), ctx)[0] == 1
    assert same_desc_same_agency_count(work(id=5, agency_id=1), ctx)[0] == 1


def test_cluster_count_is_not_published_without_a_readable_description():
    ctx = _loaded([(1, "WS/MP001/2025-2026/1", 1, "a wall"), (2, "WS/MP001/2025-2026/2", 1, "??")])
    value, availability = same_desc_same_agency_count(work(id=2, agency_id=1), ctx)
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_cluster_count_is_not_published_without_an_agency():
    ctx = _loaded([(1, "WS/MP001/2025-2026/1", None, "a wall")])
    value, availability = same_desc_same_agency_count(work(id=1, agency_id=None), ctx)
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_similarity_is_the_best_match_against_another_work_in_the_agency():
    ctx = _loaded(
        [
            (1, "WS/MP001/2025-2026/1", 1, "construction of community hall at ward no 7"),
            (2, "WS/MP001/2025-2026/2", 1, "construction of community hall at ward no 9"),
        ]
    )
    value, availability = duplicate_similarity(work(id=1, agency_id=1), ctx)
    assert availability == Availability.PUBLISHED
    assert 0.8 < value < 1.0


def test_similarity_is_not_applicable_when_the_agency_holds_only_this_work():
    """52 works on the corpus. A comparison needs something to compare to, and
    that is a different finding from a description nobody published."""
    ctx = _loaded([(1, "WS/MP001/2025-2026/1", 1, "a lone work")])
    value, availability = duplicate_similarity(work(id=1, agency_id=1), ctx)
    assert value is None
    assert availability == Availability.NOT_APPLICABLE


def test_similarity_is_not_published_without_a_readable_description():
    ctx = _loaded([(1, "WS/MP001/2025-2026/1", 1, "a wall"), (2, "WS/MP001/2025-2026/2", 1, "???")])
    value, availability = duplicate_similarity(work(id=2, agency_id=1), ctx)
    assert value is None
    assert availability == Availability.NOT_PUBLISHED


def test_citation_cites_tied_peers_in_work_id_order():
    """Fourteen peers all scoring exactly 1.000 must still cite the same two on
    every run, or the trace is not reproducible."""
    rows = [
        (index, f"WS/MP001/2025-2026/{160260 + index}", 1, "identical text")
        for index in range(1, 6)
    ]
    ctx = _loaded(rows)
    citation = derive_mod.duplicate_citation(work(id=1, agency_id=1), ctx)
    assert citation["matched_work_ids"] == [
        "WS/MP001/2025-2026/160262",
        "WS/MP001/2025-2026/160263",
    ]
    assert citation["similarity"] == 1.0
    assert citation["cluster_size"] == 5
    assert citation["components"]["token_set_ratio"] == 1.0
    assert "review" in citation["reading"].lower()


# ---------------------------------------------------------------------------
# payment_count is never None
# ---------------------------------------------------------------------------


def test_payment_count_of_zero_is_a_real_zero_and_never_none():
    """Making it nullable would let a real zero masquerade as an unmeasured
    field, which is the confusion invariant 2 exists to prevent."""
    features = derive(work(), sanction(), None, None, [], context())
    assert features["payment_count"] == 0
    assert features.availability["payment_count"] == Availability.PUBLISHED


# ---------------------------------------------------------------------------
# Ladder localisation
# ---------------------------------------------------------------------------


def _features(**values):
    full = {key: None for key in FEATURE_KEYS}
    full.update(values)
    availability = {
        key: (Availability.PUBLISHED if full[key] is not None else Availability.NOT_PUBLISHED)
        for key in full
    }
    return derive_mod.FeatureSet(full, availability)


def test_locate_gap_names_the_first_open_hop(rulebook):
    features = _features(
        variance_sanction_to_disbursement=-40.0,
        variance_disbursement_to_certification=-90.0,
    )
    assert locate_gap(features, rulebook) == "sanction_to_disbursement"


def test_locate_gap_skips_over_an_unmeasurable_hop(rulebook):
    """An unmeasured hop is not a closed hop. Fixture C's shape."""
    features = _features(
        variance_sanction_to_disbursement=-3.0,
        variance_disbursement_to_certification=-25.0,
    )
    assert locate_gap(features, rulebook) == "disbursement_to_certification"


def test_locate_gap_is_none_when_neither_hop_is_measurable(rulebook):
    assert locate_gap(_features(), rulebook) is None


def test_locate_gap_is_none_when_every_measurable_hop_is_closed(rulebook):
    assert locate_gap(_features(variance_sanction_to_disbursement=-1.0), rulebook) is None


def test_hop_tolerance_follows_the_rulebook_and_falls_back_for_hop_two(rulebook):
    assert hop_tolerance(rulebook, "sanction_to_disbursement") == -15
    # No rule reads hop 2, because there is no public data to calibrate one.
    assert hop_tolerance(rulebook, "disbursement_to_certification") == -15
    assert hop_tolerance(None, "sanction_to_disbursement") == -15


def test_slowest_lag_takes_the_largest_computable_lag():
    features = _features(
        sanction_lag_days=84,
        sanction_to_first_payment_days=42,
        first_payment_to_completion_days=439,
    )
    assert slowest_lag(features) == "first_payment_to_completion"


def test_slowest_lag_over_a_set_of_one_is_that_one():
    """Fixture B: not an error, and not a reason to report None."""
    assert slowest_lag(_features(sanction_lag_days=96)) == "recommend_to_sanction"


def test_slowest_lag_breaks_ties_in_ladder_order():
    features = _features(sanction_lag_days=100, sanction_to_first_payment_days=100)
    assert slowest_lag(features) == "recommend_to_sanction"


def test_slowest_lag_is_none_when_no_lag_is_computable():
    assert slowest_lag(_features()) is None


# ---------------------------------------------------------------------------
# The ladders in the shape the frozen contract prints them
# ---------------------------------------------------------------------------


def test_fund_ladder_marks_an_unavailable_hop_with_its_reason(rulebook):
    payments = [payment(paid_amt=119_711)]
    features = derive(work(), sanction(sanctioned_amt=199_539), None, None, payments, context())
    ladder = fund_ladder(features, sanction(sanctioned_amt=199_539), payments, None, rulebook)

    assert [rung["key"] for rung in ladder["rungs"]] == [
        "sanctioned_amt",
        "disbursed_amt",
        "certified_amt",
    ]
    assert ladder["rungs"][2]["availability"] == "not_published"
    first, second = ladder["hops"]
    assert (first["state"], round(first["variance_pct"], 2)) == ("open", -40.01)
    assert first["tolerance_pct"] == -15
    assert second["state"] == "unavailable"
    assert second["unavailable_reason"] == "not_published"
    assert "utilisation certificate" in second["hop_action"]


def test_lifecycle_ladder_shows_an_unavailable_lag_with_its_reason_never_zero():
    payments = [payment(payment_date=date(2025, 11, 26), paid_amt=119_711)]
    s = sanction(recommended_date=date(2024, 12, 19), sanction_date=date(2025, 11, 17))
    features = derive(work(), s, None, None, payments, context())
    ladder = lifecycle_ladder(features, s, payments, None)

    lags = {row["key"]: row for row in ladder["lags"]}
    assert lags["recommend_to_sanction"]["days"] == 333
    assert lags["sanction_to_first_payment"]["days"] == 9
    assert lags["first_payment_to_completion"]["days"] is None
    assert lags["first_payment_to_completion"]["state"] == "unavailable"
    assert lags["first_payment_to_completion"]["unavailable_reason"] == "not_applicable"

    dates = {row["key"]: row for row in ladder["dates"]}
    assert dates["completion_date"]["date"] is None
    assert dates["completion_date"]["unavailable_reason"] == "not_applicable"
    assert ladder["payment_count"] == 1
    assert ladder["last_payment_date"] == date(2025, 11, 26)


# ---------------------------------------------------------------------------
# The feature set itself
# ---------------------------------------------------------------------------


def test_derive_records_an_availability_for_every_declared_feature():
    features = derive(work(), sanction(), None, None, [], context())
    assert set(features) == set(FEATURE_KEYS)
    assert set(features.availability) == set(FEATURE_KEYS)


def test_the_feature_dictionary_holds_no_ml_field():
    """Invariant 1, structurally: there is nothing here a badge could be named.

    A rulebook may address only these keys, so no rulebook edit can reach an
    anomaly score, a z-score, a delay forecast or a graph centrality figure.
    """
    for banned in ("anomaly_score", "z_score", "delay_risk", "centrality", "forecast"):
        assert banned not in FEATURE_KEYS


def test_unavailable_fields_reports_each_gap_with_a_reason_and_a_detail():
    features = derive(work(), sanction(), None, None, [], context())
    reported = {row["field"]: row for row in features.unavailable_fields()}
    assert reported["variance_sanction_to_disbursement"]["reason"] == "not_published"
    assert "expenditure" in reported["variance_sanction_to_disbursement"]["detail"]
    assert reported["execution_days"]["reason"] == "not_applicable"


def test_a_context_can_be_built_without_any_cross_work_facts():
    """A single work with no corpus around it still derives, with reasons."""
    features = derive(work(agency_id=None, mp_id=None), sanction(), None, None, [], CorpusContext())
    assert features["same_desc_same_agency_count"] is None
    assert features["mp_utilisation_pct"] is None
    assert features["payment_count"] == 0
