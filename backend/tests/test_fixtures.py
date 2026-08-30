"""Acceptance: the engine reproduces docs/contract/fixtures.md on real rows.

`docs/contract/fixtures.md` standing caveat 2 gives these values the standing of
a contract: "Phase 3's engine/derive.py and engine/score.py must reproduce every
number below; a difference is a bug in one of the two, not a matter of taste."
The same standing is given to the firing-count table in
`docs/data/DATA-PROFILE.md` section 6.

Every expected value in this module is transcribed from those two documents and
nothing else. The engine derives; a wrong derivation fails here rather than
being handed the right answer.

**Fixture C is a special case and it is documented, not papered over.** Four of
C's stated inputs - its vendor share, its similarity, its member's utilisation
and its agency's HIGH-case count - are properties of a corpus around the work,
and `ingest/synthetic.py` inserts the control with a synthetic member holding no
allocation, a synthetic agency holding one work, and a single vendor paid
Rs 38.8 lakh, which is below the Rs 50 lakh floor. Those four cannot be derived
from the row that exists. Everything C was built to prove - the certification
hop, `gap_hop`, the slowest lag at the third stage, the sum identity - is
derived from the real row and asserted here; the score of 42 is asserted
against the input vector fixtures.md stipulates. See
`test_fixture_c_context_features_are_not_derivable_from_the_control`.
"""

from __future__ import annotations

import pytest

from app.constants import Availability
from app.engine.score import compute

from .conftest import FIXTURE_A, FIXTURE_B, FIXTURE_C

pytestmark = pytest.mark.corpus


# ---------------------------------------------------------------------------
# Case ids - deterministic from the work id, never from row order (invariant 8)
# ---------------------------------------------------------------------------

FIXTURE_CASE_IDS = {
    FIXTURE_A: "NG-8F0E3213D8",
    FIXTURE_B: "NG-736D95571D",
    FIXTURE_C: "NG-622268C00E",
}


@pytest.mark.parametrize("work_id,case_id", sorted(FIXTURE_CASE_IDS.items()))
def test_case_ids_are_deterministic_from_the_work_id(work_id, case_id):
    from app.constants import case_id_for

    assert case_id_for(work_id) == case_id
    # Whitespace and case in the published spelling must not change the id:
    # `WS/<TAB> MP620/...` and `WS/MP620/...` are the same work.
    assert case_id_for(f"  ws/\t{work_id[3:].lower()}  ") == case_id


# ---------------------------------------------------------------------------
# Fixture A - WS/MP847/2025-2026/160261
# ---------------------------------------------------------------------------

A_FEATURES = {
    "variance_sanction_to_disbursement": -40.01,
    "sanction_lag_days": 333,
    "sanction_to_first_payment_days": 9,
    "first_payment_to_completion_days": None,
    "execution_days": None,
    "days_since_last_payment": 271,
    "duplicate_similarity": 1.000,
    "same_desc_same_agency_count": 15,
    "vendor_share_in_agency_pct": 17.35,
    "completed_without_payment": False,
    "asset_image_absent": None,
    "mp_utilisation_pct": 73.80,
    "payment_count": 1,
    "variance_disbursement_to_certification": None,
}

A_STATUSES = {
    "utilisation_shortfall": ("fired", None, 22),
    "execution_delay": ("skipped", "not_applicable", 0),
    "duplicate_work": ("fired", None, 18),
    "sanction_delay": ("fired", None, 16),
    "stalled_work": ("fired", None, 16),
    "vendor_concentration": ("passed", None, 0),
    "status_payment_mismatch": ("passed", None, 0),
    "split_sanction": ("fired", None, 10),
    "asset_evidence_missing": ("skipped", "not_published", 0),
    "account_underutilisation": ("passed", None, 0),
}


def _rounded(features):
    return {
        key: (round(value, 2) if isinstance(value, float) else value)
        for key, value in features.items()
    }


def test_fixture_a_derives_every_documented_value(corpus):
    derived = _rounded(corpus.features_for(FIXTURE_A))
    for key, expected in A_FEATURES.items():
        assert derived[key] == expected, key


def test_fixture_a_skips_carry_the_documented_reasons(corpus):
    features = corpus.features_for(FIXTURE_A)
    # One not_applicable and one not_published on a single case: the point of
    # re-pinning A (fixtures.md standing caveat 3).
    assert features.availability["execution_days"] == Availability.NOT_APPLICABLE
    assert features.availability["asset_image_absent"] == Availability.NOT_PUBLISHED
    assert features.availability["variance_disbursement_to_certification"] == (
        Availability.NOT_PUBLISHED
    )


def test_fixture_a_trace_matches_the_contract(corpus):
    body = corpus.score(FIXTURE_A)
    hits = {hit["rule_id"]: hit for hit in body["rule_hits"]}
    assert len(body["rule_hits"]) == 10
    for rule_id, (status, skip_reason, contribution) in A_STATUSES.items():
        hit = hits[rule_id]
        assert (hit["status"], hit["skip_reason"], hit["contribution"]) == (
            status,
            skip_reason,
            contribution,
        ), rule_id


def test_fixture_a_scores_92_high_on_79_percent_coverage(corpus):
    body = corpus.score(FIXTURE_A)
    # 22 + 18 + 16 + 16 + 10 = 82 rule subtotal, + 10 corroboration = 92.
    assert body["raw_score"] == 92
    assert body["score"] == 92
    assert body["severity"] == "HIGH"
    # (144 - 20 - 10) / 144 = 0.7917 -> 79. The 30 skipped points are not
    # redistributed: 92 is 92 of a possible 154, evaluated over 79% of the
    # rulebook, not 92 of a rescaled 114.
    assert body["coverage_pct"] == 79
    assert body["gap_hop"] == "sanction_to_disbursement"
    assert body["slowest_lag"] == "recommend_to_sanction"


def test_fixture_a_corroboration_fires_on_25_other_high_cases(corpus):
    corroboration = corpus.score(FIXTURE_A)["corroboration"]
    assert corroboration["applied"] is True
    assert corroboration["high_case_count"] == 25
    assert corroboration["contribution"] == 10
    assert corroboration["window"] == "FY2025-2026"
    assert corroboration["agency"] == "DISTRICT MAGISTRATE JALAUN"
    assert corroboration["matched_case_ids"] == [
        "NG-D4BA75C468",
        "NG-436EB11F68",
        "NG-BDC980159E",
    ]


def test_fixture_a_duplicate_hit_cites_its_evidence(corpus):
    """A fired duplicate_work with a null citation is a failed test, not a row."""
    hit = next(
        h for h in corpus.score(FIXTURE_A)["rule_hits"] if h["rule_id"] == "duplicate_work"
    )
    citation = hit["citation"]
    assert citation is not None
    assert citation["matched_work_ids"] == [
        "WS/MP847/2025-2026/160262",
        "WS/MP847/2025-2026/160263",
    ]
    assert citation["matched_case_ids"] == ["NG-D4BA75C468", "NG-436EB11F68"]
    assert citation["cluster_size"] == 15
    assert citation["agency"] == "DISTRICT MAGISTRATE JALAUN"
    assert citation["similarity"] == 1.0
    assert citation["shared_description"] == (
        "led semi high mast light 6led with 200 watt 9 5 meter pole"
    )
    # Byte-identical after normalisation, so every component reads exactly 1.0.
    # This is exact repetition, not a fuzzy near-match, and the trace says so.
    assert citation["components"] == {
        "token_set_ratio": 1.0,
        "partial_ratio": 1.0,
        "token_sort_ratio": 1.0,
    }
    assert "review" in citation["reading"].lower()
    assert "fraud" not in citation["reading"].lower()


def test_fixture_a_stalled_work_clears_its_threshold_by_one_day(corpus):
    """271 against 270, recorded rather than smoothed away.

    The threshold was set from the measured distribution (p90 = 268 d) before
    this row was chosen, and a case that clears a threshold by a single day is
    exactly the kind an officer should be able to see the arithmetic for.
    """
    hit = next(h for h in corpus.score(FIXTURE_A)["rule_hits"] if h["rule_id"] == "stalled_work")
    assert (hit["raw_value"], hit["threshold"], hit["status"]) == (271, 270, "fired")
    assert "2026-08-24" in hit["caveat"]


# ---------------------------------------------------------------------------
# Fixture B - WS/MP163/2024-2025/136111
# ---------------------------------------------------------------------------

B_FEATURES = {
    "variance_sanction_to_disbursement": None,
    "variance_disbursement_to_certification": None,
    "sanction_lag_days": 96,
    "sanction_to_first_payment_days": None,
    "first_payment_to_completion_days": None,
    "execution_days": 539,
    "days_since_last_payment": None,
    "duplicate_similarity": 0.90,
    "same_desc_same_agency_count": 1,
    "vendor_share_in_agency_pct": None,
    "completed_without_payment": True,
    "asset_image_absent": True,
    "mp_utilisation_pct": 71.37,
    "payment_count": 0,
}

B_STATUSES = {
    "utilisation_shortfall": ("skipped", "not_published", 0),
    "execution_delay": ("fired", None, 20),
    "duplicate_work": ("fired", None, 18),
    "sanction_delay": ("passed", None, 0),
    "stalled_work": ("skipped", "not_published", 0),
    "vendor_concentration": ("skipped", "not_published", 0),
    "status_payment_mismatch": ("fired", None, 12),
    "split_sanction": ("passed", None, 0),
    "asset_evidence_missing": ("fired", None, 10),
    "account_underutilisation": ("passed", None, 0),
}


def test_fixture_b_derives_every_documented_value(corpus):
    derived = _rounded(corpus.features_for(FIXTURE_B))
    for key, expected in B_FEATURES.items():
        assert derived[key] == expected, key


def test_fixture_b_execution_days_is_not_the_sum_of_the_two_lags(corpus):
    """The proof case for keeping execution_days its own derivation.

    B has ZERO payment rows, so both payment-side lags are None. Had
    execution_days been defined as their sum it would be None too, and B's
    highest-weighted fired rule - 20 points of execution_delay - would have
    vanished. It is computed directly from 2024-11-21 to 2026-05-14.
    """
    features = corpus.features_for(FIXTURE_B)
    assert features["payment_count"] == 0
    assert features["sanction_to_first_payment_days"] is None
    assert features["first_payment_to_completion_days"] is None
    assert features["execution_days"] == 539


def test_fixture_b_three_skips_are_all_not_published(corpus):
    """50 of 144 points unevaluable, and not one of them treated as a pass.

    If these three had been silently passed, B would look like a work that was
    checked for utilisation shortfall, stalling and vendor concentration and
    came through clean. It was not checked for any of them.
    """
    body = corpus.score(FIXTURE_B)
    skipped = [hit for hit in body["rule_hits"] if hit["status"] == "skipped"]
    assert {hit["rule_id"] for hit in skipped} == {
        "utilisation_shortfall",
        "stalled_work",
        "vendor_concentration",
    }
    assert all(hit["skip_reason"] == "not_published" for hit in skipped)
    assert sum(hit["weight"] for hit in skipped) == 50
    assert all(hit["contribution"] == 0 for hit in skipped)


def test_fixture_b_trace_matches_the_contract(corpus):
    hits = {hit["rule_id"]: hit for hit in corpus.score(FIXTURE_B)["rule_hits"]}
    for rule_id, (status, skip_reason, contribution) in B_STATUSES.items():
        hit = hits[rule_id]
        assert (hit["status"], hit["skip_reason"], hit["contribution"]) == (
            status,
            skip_reason,
            contribution,
        ), rule_id


def test_fixture_b_scores_60_medium_on_65_percent_coverage(corpus):
    body = corpus.score(FIXTURE_B)
    assert body["raw_score"] == 60
    assert body["score"] == 60
    assert body["severity"] == "MEDIUM"
    # (144 - 50) / 144 = 0.6528 -> 65.
    assert body["coverage_pct"] == 65
    # Both hops unavailable: no payment row and no certificate.
    assert body["gap_hop"] is None
    assert body["slowest_lag"] == "recommend_to_sanction"


def test_fixture_b_slowest_lag_is_a_comparison_over_a_set_of_one(corpus):
    """Only one of B's three lags is computable, and that is a valid answer."""
    features = corpus.features_for(FIXTURE_B)
    computable = [
        key
        for key in (
            "sanction_lag_days",
            "sanction_to_first_payment_days",
            "first_payment_to_completion_days",
        )
        if features[key] is not None
    ]
    assert computable == ["sanction_lag_days"]
    assert corpus.score(FIXTURE_B)["slowest_lag"] == "recommend_to_sanction"


def test_fixture_b_corroboration_does_not_fire_and_says_why(corpus):
    """The negative control for F4: the bonus must be visibly NOT awarded."""
    corroboration = corpus.score(FIXTURE_B)["corroboration"]
    assert corroboration["applied"] is False
    assert corroboration["high_case_count"] == 0
    assert corroboration["contribution"] == 0
    assert corroboration["min_high_cases"] == 3


def test_fixture_b_status_payment_mismatch_carries_the_truncation_caveat(corpus):
    """The caveat travels with the flag, not in a footnote."""
    hit = next(
        h
        for h in corpus.score(FIXTURE_B)["rule_hits"]
        if h["rule_id"] == "status_payment_mismatch"
    )
    assert hit["status"] == "fired"
    assert "truncated" in hit["caveat"]
    assert "3,529" in hit["caveat"]


# ---------------------------------------------------------------------------
# Fixture C - the labelled synthetic control
# ---------------------------------------------------------------------------

# Every value here is derivable from the row ingest/synthetic.py inserts.
C_DERIVABLE = {
    "variance_sanction_to_disbursement": -3.00,
    "variance_disbursement_to_certification": -25.00,
    "sanction_lag_days": 84,
    "sanction_to_first_payment_days": 42,
    "first_payment_to_completion_days": 439,
    "execution_days": 481,
    "days_since_last_payment": 194,
    "completed_without_payment": False,
    "asset_image_absent": False,
    "payment_count": 4,
}

# fixtures.md's raw-input table for C. The last four are stipulated rather than
# derivable - see the module docstring and the divergence test below.
C_STIPULATED = dict(
    C_DERIVABLE,
    duplicate_similarity=0.31,
    same_desc_same_agency_count=2,
    vendor_share_in_agency_pct=67.3,
    mp_utilisation_pct=44.9,
)
C_CORROBORATION_COUNT = 4


def test_fixture_c_derives_every_value_the_control_can_support(corpus):
    derived = _rounded(corpus.features_for(FIXTURE_C))
    for key, expected in C_DERIVABLE.items():
        assert derived[key] == expected, key


def test_fixture_c_is_labelled_synthetic(corpus):
    work = corpus.works[corpus.by_work_id[FIXTURE_C]]
    assert work.is_synthetic is True


def test_fixture_c_opens_the_certification_hop_no_real_row_can(corpus):
    """The only row in the corpus where fund hop 2 is computable at all.

    MoSPI publishes no utilisation certificate, so without this labelled
    control `variance_disbursement_to_certification` would have a derivation
    function that never once ran - the declared-but-never-computed failure
    CLAUDE.md invariant 3 exists to prevent.
    """
    body = corpus.score(FIXTURE_C)
    features = corpus.features_for(FIXTURE_C)
    assert round(features["variance_disbursement_to_certification"], 2) == -25.00
    assert body["gap_hop"] == "disbursement_to_certification"
    # And the open hop contributes exactly zero points. No rule reads that
    # variance, because there is no public data to calibrate a threshold
    # against. That is the ablation report's headline, not a bug to fix by
    # inventing a rule.
    assert all(
        hit["field"] != "variance_disbursement_to_certification" for hit in body["rule_hits"]
    )


def test_fixture_c_sum_identity_holds_where_both_lags_exist(corpus):
    """42 + 439 = 481. Asserted here and NOT on A or B, where a lag is None."""
    features = corpus.features_for(FIXTURE_C)
    assert (
        features["sanction_to_first_payment_days"]
        + features["first_payment_to_completion_days"]
        == features["execution_days"]
    )


def test_fixture_c_slowest_lag_is_the_third_stage(corpus):
    assert corpus.score(FIXTURE_C)["slowest_lag"] == "first_payment_to_completion"


def test_fixture_c_scores_42_low_on_its_stipulated_inputs(rulebook, features_factory):
    """The score fixtures.md works, from the input vector fixtures.md states.

    20 (execution_delay) + 12 (vendor_concentration) = 32, + 10 corroboration
    = 42, LOW, on 100% coverage because no rule is skipped.
    """
    features = features_factory(C_STIPULATED)
    body = compute(features, rulebook, C_CORROBORATION_COUNT)
    fired = {hit["rule_id"] for hit in body["rule_hits"] if hit["status"] == "fired"}
    assert fired == {"execution_delay", "vendor_concentration"}
    assert body["raw_score"] == 42
    assert body["score"] == 42
    assert body["severity"] == "LOW"
    assert body["coverage_pct"] == 100
    assert body["corroboration"]["applied"] is True


def test_fixture_c_context_features_are_not_derivable_from_the_control(corpus):
    """DOCUMENTED DIVERGENCE, asserted so it cannot drift unnoticed.

    Four of fixture C's stated inputs are facts about a corpus AROUND the work
    rather than about the work, and the control `ingest/synthetic.py` inserts
    has no such corpus around it:

      vendor_share_in_agency_pct  fixtures 67.3   engine None, not_applicable
          The synthetic agency has disbursed Rs 38.8 lakh in total, below the
          Rs 50 lakh floor in app.constants; and all of it went to one vendor,
          so the share would read 100%, not 67.3%.
      duplicate_similarity        fixtures 0.31   engine None, not_applicable
          The synthetic agency holds exactly one work, so there is nothing to
          compare its description against.
      same_desc_same_agency_count fixtures 2      engine 1
          Same reason. Both values pass the rule, so the score is unaffected.
      mp_utilisation_pct          fixtures 44.9   engine None, not_published
          The synthetic member holds no allocation row: `fund_accounts` is
          materialised before the control is inserted, so it has no
          term-to-date row at all.
      agency HIGH cases this FY   fixtures 4      engine 0
          The synthetic agency holds one work, which is C itself, and a case
          never corroborates itself.

    Consequence: scored against the ingested row, C reads 20 / LOW / 74%
    instead of 42 / LOW / 100%. Everything C was BUILT to exercise - the
    certification hop, `gap_hop`, the third-stage slowest lag and the sum
    identity - is derived from the real row and asserted above.

    This is reported rather than resolved. Closing it means giving the control
    sibling works, a second vendor, an allocation row and three HIGH peers,
    which is a change to `ingest/synthetic.py` and would move the row counts
    pinned in `docs/data/INGEST-EXPECTATIONS.md`.
    """
    features = corpus.features_for(FIXTURE_C)
    assert features["vendor_share_in_agency_pct"] is None
    assert features.availability["vendor_share_in_agency_pct"] == Availability.NOT_APPLICABLE
    assert features["duplicate_similarity"] is None
    assert features.availability["duplicate_similarity"] == Availability.NOT_APPLICABLE
    assert features["same_desc_same_agency_count"] == 1
    assert features["mp_utilisation_pct"] is None
    assert features.availability["mp_utilisation_pct"] == Availability.NOT_PUBLISHED
    assert corpus.score(FIXTURE_C)["corroboration"]["high_case_count"] == 0


# ---------------------------------------------------------------------------
# The whole corpus - DATA-PROFILE.md section 6
# ---------------------------------------------------------------------------

FIRING_COUNTS = {
    # rule_id: (fired, passed, skipped)
    "utilisation_shortfall": (1140, 2389, 23549),
    "execution_delay": (2568, 10406, 14104),
    "duplicate_work": (16491, 10406, 181),
    "sanction_delay": (4800, 22278, 0),
    "stalled_work": (345, 3184, 23549),
    "vendor_concentration": (48, 3344, 23686),
    "status_payment_mismatch": (1371, 25707, 0),
    "split_sanction": (3240, 23709, 129),
    "asset_evidence_missing": (4493, 8481, 14104),
    "account_underutilisation": (6371, 20707, 0),
}


@pytest.fixture(scope="session")
def real_bodies(corpus):
    """Every REAL sanctioned case, scored. The synthetic control is excluded.

    The control is excluded from this aggregate and from every other published
    one (CLAUDE.md invariant 12), which is also what makes these counts
    comparable to DATA-PROFILE.md section 6's 27,078.
    """
    return {
        work_pk: body
        for work_pk, body in corpus.score_all().items()
        if not corpus.works[work_pk].is_synthetic
    }


def test_the_corpus_holds_27078_real_sanctioned_works(real_bodies):
    assert len(real_bodies) == 27078


@pytest.mark.parametrize("rule_id,expected", sorted(FIRING_COUNTS.items()))
def test_firing_counts_reproduce_the_profile(real_bodies, rule_id, expected):
    """DATA-PROFILE.md section 6: a difference is a bug, not a matter of taste."""
    counts = {"fired": 0, "passed": 0, "skipped": 0}
    for body in real_bodies.values():
        hit = next(h for h in body["rule_hits"] if h["rule_id"] == rule_id)
        counts[hit["status"]] += 1
    assert (counts["fired"], counts["passed"], counts["skipped"]) == expected


def test_severity_bands_reproduce_the_profile(real_bodies):
    bands = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for body in real_bodies.values():
        bands[body["severity"]] += 1
    assert bands == {"HIGH": 37, "MEDIUM": 1006, "LOW": 26035}


def test_corroboration_is_awarded_to_191_cases(real_bodies):
    awarded = sum(1 for body in real_bodies.values() if body["corroboration"]["applied"])
    assert awarded == 191


def test_coverage_reproduces_the_profile(real_bodies):
    """58.5% mean, 1,011 cases at 100%, minimum 25%.

    That mean is the honest headline of the whole corpus: NIGRANI can evaluate
    a little under three-fifths of its own rulebook on the average published
    work, and it says so on every case rather than scoring the rest as passes.
    """
    coverage = [body["coverage_pct"] for body in real_bodies.values()]
    assert round(sum(coverage) / len(coverage), 1) == 58.5
    assert sum(1 for value in coverage if value == 100) == 1011
    assert min(coverage) == 25


def test_every_case_carries_all_ten_rules_including_passes_and_skips(real_bodies):
    """A trace that omitted the passes would not be re-derivable."""
    for body in real_bodies.values():
        assert len(body["rule_hits"]) == 10


def test_no_skipped_rule_ever_contributes_weight(real_bodies):
    for body in real_bodies.values():
        for hit in body["rule_hits"]:
            if hit["status"] != "fired":
                assert hit["contribution"] == 0
            if hit["status"] == "skipped":
                assert hit["skip_reason"] is not None
            else:
                assert hit["skip_reason"] is None


def test_every_fired_duplicate_hit_cites_its_evidence(real_bodies):
    """16,491 fired hits, and not one of them without the records behind it."""
    for body in real_bodies.values():
        for hit in body["rule_hits"]:
            if hit["rule_id"] == "duplicate_work" and hit["status"] == "fired":
                assert hit["citation"] is not None
                assert hit["citation"]["matched_work_ids"]
