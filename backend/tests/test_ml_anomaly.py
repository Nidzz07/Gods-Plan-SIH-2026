"""`app/ml/anomaly.py` - the IsolationForest badge, and its zero points.

The central test in this module is
`test_the_real_anomaly_output_cannot_move_the_score`. Phase 2 proved invariant
1 by injecting a z-score and a duplicate reading into a hand-built feature set
and asserting the score did not move. This proves it one step further out: the
forest is actually fitted on the real corpus, its real output is wired into the
case body's `statistical` block the way an API layer would wire it, and the
score, the raw score, the severity and the coverage are asserted unchanged
against the values `docs/contract/fixtures.md` fixes for fixtures A, B and C.
"""

from __future__ import annotations

import pytest

from app.constants import (
    ANOMALY_CONTAMINATION,
    ANOMALY_MIN_PEER_GROUP,
    Availability,
    ML_KIND_ANOMALY,
)
from app.engine import derive as derive_mod
from app.engine import rulebook as rulebook_mod
from app.engine.score import compute
from app.ml import anomaly
from app.ml.badges import ScoreMutatedError, attach

from .conftest import FIXTURE_A, FIXTURE_B, FIXTURE_C

pytestmark = pytest.mark.corpus


# ---------------------------------------------------------------------------
# Invariant 1, extended to this module's real output
# ---------------------------------------------------------------------------

FIXTURE_SCORES = {
    # work id: (score, raw_score, severity, coverage_pct) - fixtures.md summary
    FIXTURE_A: (92, 92, "HIGH", 79),
    FIXTURE_B: (60, 60, "MEDIUM", 65),
    FIXTURE_C: (20, 20, "LOW", 74),
}


@pytest.mark.parametrize("work_id", sorted(FIXTURE_SCORES))
def test_the_real_anomaly_output_cannot_move_the_score(ml_run, work_id):
    """The forest's actual reading, attached to the case body, changes nothing.

    Not a stand-in and not a perturbed constant: this is the value
    `anomaly.run()` produced over the ingested corpus, put into the block the
    frozen contract calls `statistical`, on the three cases fixtures.md fixes
    the arithmetic for.
    """
    expected = FIXTURE_SCORES[work_id]
    body = ml_run.rescore(work_id)
    assert (
        body["score"],
        body["raw_score"],
        body["severity"],
        body["coverage_pct"],
    ) == expected

    badged = attach(body, anomaly=ml_run.finding("anomaly", work_id))
    assert (
        badged["score"],
        badged["raw_score"],
        badged["severity"],
        badged["coverage_pct"],
    ) == expected
    assert badged["rule_hits"] == body["rule_hits"]
    assert badged["corroboration"] == body["corroboration"]
    assert badged["statistical"]["contribution"] == 0


def test_perturbing_the_forest_output_leaves_every_score_untouched(ml_run):
    """The perturbation test, run over every case the forest could read.

    Multiplying a real anomaly score by a million and flipping its flag must
    leave the case body it is attached to byte-identical in every scored key.
    `attach()` raises if it does not, so this asserts the guard fires rather
    than trusting it.
    """
    from dataclasses import replace as dataclass_replace

    findings = ml_run.findings_for("anomaly")
    checked = 0
    for work_pk, body in list(ml_run.bodies.items()):
        finding = findings[work_pk]
        if finding.availability != Availability.PUBLISHED:
            continue
        loud = dataclass_replace(
            finding,
            value=finding.value * 1_000_000 - 500,
            payload={**finding.payload, "flagged": not finding.payload["flagged"]},
        )
        before = attach(body, anomaly=finding)
        after = attach(body, anomaly=loud)
        for key in ("score", "raw_score", "severity", "coverage_pct", "rule_hits"):
            assert after[key] == before[key] == body[key]
        checked += 1
        if checked >= 500:
            break
    assert checked == 500


def test_the_rulebook_cannot_be_edited_to_read_an_anomaly_score():
    """The other half of the guarantee: there is no field to point a rule at.

    `rulebook.validate` rejects a rule naming a field outside
    `derive.FEATURE_KEYS`, and no key this module produces is on that list. So
    even an officer with write access to rules.yaml cannot route a forest
    reading into the addition `compute()` performs.
    """
    for field in ("anomaly_score", "anomaly_confirms", "delay_risk", "hhi"):
        assert field not in derive_mod.FEATURE_KEYS
        book = {
            "rules": [
                {
                    "id": "smuggled_model_output",
                    "label": "should not load",
                    "field": field,
                    "operator": "gt",
                    "threshold": 0,
                    "severity": "high",
                    "weight": 50,
                }
            ]
        }
        with pytest.raises(rulebook_mod.RulebookError, match="not in the derived"):
            rulebook_mod.validate(book, derive_mod.FEATURE_KEYS)


def test_attach_refuses_to_emit_a_body_whose_score_moved(ml_run, monkeypatch):
    """The guard itself, exercised rather than trusted.

    `attach()` writes three keys and compares every scored key before and
    after. To make it actually catch something, the scored list is widened for
    one call to include a key `attach()` does write. The guard must RAISE - a
    silent restore would leave the breach in place and hide the evidence of it.
    """
    import app.ml.badges as badges_mod

    monkeypatch.setattr(
        badges_mod, "SCORED_KEYS", badges_mod.SCORED_KEYS + ("statistical",)
    )
    with pytest.raises(ScoreMutatedError, match="statistical"):
        badges_mod.attach(
            ml_run.body(FIXTURE_A), anomaly=ml_run.finding("anomaly", FIXTURE_A)
        )


# ---------------------------------------------------------------------------
# The population, and the works the forest cannot speak about
# ---------------------------------------------------------------------------


def test_only_works_with_a_complete_vector_are_scored(ml_run):
    """3,380 real works can be vectorised; 3,261 clear the peer-group floor.

    Nothing is imputed, so a work missing any of the nine readings is not
    compared rather than compared against filled-in values. The gap is large -
    the forest speaks about 12% of the corpus - and that is the honest ceiling
    of an ML tier over a truncated expenditure export, not a shortfall to
    engineer around.
    """
    assert ml_run.anomaly_model.trained_on == 3380
    published = [
        f for f in ml_run.anomaly_findings if f.availability == Availability.PUBLISHED
    ]
    assert len(published) == 3261
    skipped = [
        f for f in ml_run.anomaly_findings if f.availability != Availability.PUBLISHED
    ]
    assert len(skipped) == 23818
    # Every one of them is not_applicable with a reason. None is a zero.
    for finding in skipped:
        assert finding.availability == Availability.NOT_APPLICABLE
        assert finding.value is None
        assert finding.payload["detail"]


def test_the_flagging_rate_matches_the_measured_contamination(ml_run):
    """10.6% flagged against a contamination of 11%, as set.

    The rate was chosen to match the share of this same population the rulebook
    places above the LOW band, so that a `confirms` badge is informative rather
    than arithmetically inevitable (app/constants.py).
    """
    published = [
        f for f in ml_run.anomaly_findings if f.availability == Availability.PUBLISHED
    ]
    flagged = [f for f in published if f.payload["flagged"]]
    assert len(flagged) == pytest.approx(
        len(published) * ANOMALY_CONTAMINATION, rel=0.10
    )
    # The sign carries the verdict, exactly: flagged iff the score is positive.
    for finding in published:
        assert finding.payload["flagged"] is (finding.value > 0)


def test_the_forest_independently_flags_most_of_the_high_cases_it_can_see(ml_run):
    """What the badge is FOR, measured rather than asserted.

    All 37 of the corpus's HIGH cases carry a complete vector; 35 of them also
    clear the peer-group floor, and the forest flags 30 of those 35 without
    reading a single rule. That agreement is the badge's whole value, and it is
    worth zero points.
    """
    findings = ml_run.findings_for("anomaly")
    high = ml_run.high_severity()
    assert len(high) == 37
    scored = [
        work_pk
        for work_pk in high
        if findings[work_pk].availability == Availability.PUBLISHED
    ]
    assert len(scored) == 35
    flagged = [pk for pk in scored if findings[pk].payload["flagged"]]
    assert len(flagged) == 30
    assert all(findings[pk].payload["confirms"] is True for pk in flagged)


def test_confirms_is_never_true_where_no_rule_fired(ml_run):
    """A badge cannot confirm a finding that was never made."""
    findings = ml_run.findings_for("anomaly")
    for work_pk, fired in ml_run.fired_counts.items():
        finding = findings[work_pk]
        if fired == 0:
            assert finding.payload["confirms"] in (False, None)


def test_confirms_is_none_rather_than_false_when_no_score_was_supplied(ml_run):
    """Not stated is different from stated as no.

    A badge run without the rulebook's fired counts has not FAILED to confirm
    anything; it has not been asked. The distinction is the same one invariant
    2 protects between a null and a zero.
    """
    model = ml_run.anomaly_model
    unasked = anomaly.findings(
        model, ml_run.corpus.features, ml_run.corpus.works, None, ml_run.state_names
    )
    published = [f for f in unasked if f.availability == Availability.PUBLISHED]
    assert published
    assert all(f.payload["confirms"] is None for f in published)
    assert all(f.payload["rules_fired"] is None for f in published)


# ---------------------------------------------------------------------------
# The three fixtures
# ---------------------------------------------------------------------------


def test_fixture_a_is_scored_and_named_against_its_peer_group(ml_run):
    finding = ml_run.finding("anomaly", FIXTURE_A)
    assert finding.availability == Availability.PUBLISHED
    assert finding.kind == ML_KIND_ANOMALY
    assert finding.contributes_to_score is False
    assert (
        finding.payload["peer_group"]
        == "Normal/Others works sanctioned in Uttar Pradesh, FY2025-2026"
    )
    assert finding.payload["peer_group_size"] == 439
    # A is HIGH on five fired rules, and the forest agrees without reading one.
    assert finding.payload["flagged"] is True
    assert finding.payload["confirms"] is True
    assert finding.value > 0


@pytest.mark.parametrize(
    "work_id,missing",
    [
        (
            FIXTURE_B,
            [
                "variance_sanction_to_disbursement",
                "sanction_to_first_payment_days",
                "days_since_last_payment",
                "vendor_share_in_agency_pct",
            ],
        ),
        (
            FIXTURE_C,
            [
                "vendor_share_in_agency_pct",
                "duplicate_similarity",
                "mp_utilisation_pct",
            ],
        ),
    ],
)
def test_b_and_c_are_not_applicable_and_name_what_they_are_missing(
    ml_run, work_id, missing
):
    """The genuine absence of comparable data, reported rather than filled.

    B has no expenditure row at all, so four of the nine readings do not exist.
    C is the labelled control: one work, one agency, one member, one vendor,
    with no corpus around it - the state `docs/contract/fixtures.md` standing
    caveat 9 records and which Phase 2 refused to close by inventing peers.
    Neither is given a score of 0.
    """
    finding = ml_run.finding("anomaly", work_id)
    assert finding.value is None
    assert finding.availability == Availability.NOT_APPLICABLE
    assert finding.payload["missing_features"] == missing
    assert "Nothing is imputed" in finding.payload["detail"]
    assert finding.payload["flagged"] is None
    assert finding.payload["confirms"] is None


def test_the_labelled_control_never_enters_the_fitted_population(ml_run):
    """Invariant 12: one injected row may not sit inside a measured aggregate."""
    control_pk = ml_run.pk(FIXTURE_C)
    assert ml_run.corpus.works[control_pk].is_synthetic is True
    assert control_pk not in ml_run.anomaly_model.order


# ---------------------------------------------------------------------------
# The unit branches the corpus does not reach
# ---------------------------------------------------------------------------


def test_a_thin_peer_group_is_not_applicable_rather_than_an_outlier_verdict():
    """Below the floor, "unusual among its peers" carries no content."""
    from types import SimpleNamespace

    from app.constants import Availability as A

    values = {key: 1.0 for key in anomaly.ANOMALY_FEATURES}
    features = derive_mod.FeatureSet(values, {k: A.PUBLISHED for k in values})
    works = {
        pk: SimpleNamespace(
            category="Normal/Others", state_id=1, fy="2025-2026", is_synthetic=False
        )
        for pk in range(1, ANOMALY_MIN_PEER_GROUP)
    }
    model, findings = anomaly.run({pk: features for pk in works}, works)
    assert model.trained_on == ANOMALY_MIN_PEER_GROUP - 1
    for finding in findings:
        assert finding.value is None
        assert finding.availability == A.NOT_APPLICABLE
        assert "below the floor" in finding.payload["detail"]


def test_the_vector_is_none_the_moment_one_reading_is_missing():
    """There is no imputation branch, and this is what says so."""
    from app.constants import Availability as A

    values = {key: 1.0 for key in anomaly.ANOMALY_FEATURES}
    reasons = {key: A.PUBLISHED for key in values}
    assert anomaly.vector(derive_mod.FeatureSet(values, reasons)) is not None
    for key in anomaly.ANOMALY_FEATURES:
        holed = dict(values, **{key: None})
        holed_reasons = dict(reasons, **{key: A.NOT_PUBLISHED})
        features = derive_mod.FeatureSet(holed, holed_reasons)
        assert anomaly.vector(features) is None
        assert anomaly.missing_features(features) == [key]


def test_every_anomaly_feature_is_a_derived_feature_the_rulebook_could_read():
    """The badge looks at what the rulebook looks at, and nothing private.

    A work the forest calls unusual is unusual in facts already on the trace,
    so an officer can go and read why rather than being asked to trust a
    representation nobody can see.
    """
    for key in anomaly.ANOMALY_FEATURES:
        assert key in derive_mod.FEATURE_KEYS


def test_a_finding_is_produced_for_every_work_it_was_asked_about(ml_run):
    assert len(ml_run.anomaly_findings) == len(ml_run.corpus.features)
    assert {f.work_pk for f in ml_run.anomaly_findings} == set(ml_run.corpus.features)
    assert all(f.contributes_to_score is False for f in ml_run.anomaly_findings)


def test_the_model_version_names_the_fit_that_produced_the_badge(ml_run):
    """A badge an auditor cannot trace to a fit is a number nobody can check."""
    version = ml_run.anomaly_model.version
    assert version.startswith("iso1-")
    assert all(f.model_version == version for f in ml_run.anomaly_findings)


def test_the_forest_is_reproducible(ml_run):
    """Two fits over the same corpus agree, because the seed is fixed."""
    again = anomaly.fit(ml_run.corpus.features, ml_run.corpus.works)
    assert again.version == ml_run.anomaly_model.version
    anomaly.score(again, ml_run.corpus.features, ml_run.corpus.works)
    for work_pk in list(ml_run.anomaly_model.order)[:400]:
        assert again.score_for(work_pk) == pytest.approx(
            ml_run.anomaly_model.score_for(work_pk)
        )


def test_the_case_body_this_module_produces_carries_the_contract_keys(ml_run):
    """`statistical` is a key the frozen contract already declares."""
    badged = attach(
        ml_run.body(FIXTURE_A), anomaly=ml_run.finding("anomaly", FIXTURE_A)
    )
    block = badged["statistical"]
    for key in ("z_score", "z_peer_group", "anomaly_score", "anomaly_model_version",
                "confirms", "contribution", "note"):
        assert key in block
    # z_score stays null: no document in the repository defines what it is a
    # z-score OF, and filling it would mean inventing a measure.
    assert block["z_score"] is None
    assert block["contribution"] == 0
    assert "zero points" in block["note"]


def test_compute_is_indifferent_to_a_smuggled_anomaly_key(ml_run, rulebook):
    """Even inside the feature dict, the number is unreachable.

    `rulebook.evaluate` reads only the fields the rulebook names, so a key
    added to a feature set by hand is not read by anything. Belt and braces
    against the field-name test above.
    """
    features = ml_run.corpus.features_for(FIXTURE_A)
    smuggled = derive_mod.FeatureSet(
        {**features, "anomaly_score": 999.0, "delay_risk": 1.0},
        {**features.availability, "anomaly_score": Availability.PUBLISHED,
         "delay_risk": Availability.PUBLISHED},
        features.evidence,
        features.detail,
    )
    count = ml_run.corpus.corroboration_count(ml_run.pk(FIXTURE_A))
    assert compute(smuggled, rulebook, count)["raw_score"] == 92
