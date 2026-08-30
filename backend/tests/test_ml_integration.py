"""The whole pipeline, and the claim this phase rests on: the numbers did not move.

`derive -> score -> badges`, run end to end over fixtures A, B and C, asserting
that every scored value `docs/contract/fixtures.md` fixes is byte-identical
after all four ML tiers are attached. Not one tier at a time - all four at once,
which is the arrangement an API layer will actually assemble.

**What "byte-identical" means here.** Not "the score is still 92", which a
coincidence could satisfy. Every key in `badges.SCORED_KEYS` is compared as a
whole object: the full ten-row `rule_hits` trace with its raw values,
thresholds, statuses, skip reasons, contributions, citations and caveats; the
corroboration block with its count and its cited case ids; the coverage figure
and the sentence that explains it. If this phase had moved anything an officer
re-derives on paper, this test says which key.

`test_ml_anomaly.py` and `test_ml_forecast.py` prove the same thing per module
and by perturbation. This one proves it for the assembled body, which is the
thing that reaches a screen.
"""

from __future__ import annotations

import json

import pytest

from app.constants import Availability
from app.ml.badges import SCORED_KEYS, attach, kinds_are_badges

from .conftest import FIXTURE_A, FIXTURE_B, FIXTURE_C

pytestmark = pytest.mark.corpus

FIXTURES = (FIXTURE_A, FIXTURE_B, FIXTURE_C)

# docs/contract/fixtures.md, the summary table. Transcribed from the document
# and from nowhere else.
EXPECTED = {
    FIXTURE_A: {
        "case_id": "NG-8F0E3213D8",
        "score": 92,
        "raw_score": 92,
        "severity": "HIGH",
        "coverage_pct": 79,
        "gap_hop": "sanction_to_disbursement",
        "slowest_lag": "recommend_to_sanction",
        "fired": 5,
        "passed": 3,
        "skipped": 2,
        "corroboration": 10,
    },
    FIXTURE_B: {
        "case_id": "NG-736D95571D",
        "score": 60,
        "raw_score": 60,
        "severity": "MEDIUM",
        "coverage_pct": 65,
        "gap_hop": None,
        "slowest_lag": "recommend_to_sanction",
        "fired": 4,
        "passed": 3,
        "skipped": 3,
        "corroboration": 0,
    },
    FIXTURE_C: {
        "case_id": "NG-622268C00E",
        "score": 20,
        "raw_score": 20,
        "severity": "LOW",
        "coverage_pct": 74,
        "gap_hop": "disbursement_to_certification",
        "slowest_lag": "first_payment_to_completion",
        "fired": 1,
        "passed": 6,
        "skipped": 3,
        "corroboration": 0,
    },
}


@pytest.fixture(scope="module")
def badged(ml_run):
    """Each fixture's case body, scored, then badged with all four tiers."""
    out = {}
    for work_id in FIXTURES:
        body = ml_run.rescore(work_id)
        out[work_id] = (
            body,
            attach(
                body,
                anomaly=ml_run.finding("anomaly", work_id),
                forecast=ml_run.finding("forecast", work_id),
                concentration=ml_run.finding("graph", work_id),
            ),
        )
    return out


# ---------------------------------------------------------------------------
# The claim
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("work_id", FIXTURES)
def test_every_scored_key_survives_the_whole_ml_phase_unchanged(badged, work_id):
    """The one assertion this phase exists to be able to make.

    Adding duplicate clustering, an IsolationForest, a delay classifier and a
    bipartite graph to NIGRANI changed nothing about what Phase 2 validated.
    Compared object by object, not number by number.
    """
    body, out = badged[work_id]
    for key in SCORED_KEYS:
        assert out[key] == body[key], key
    assert json.dumps(out["rule_hits"], sort_keys=True, default=str) == json.dumps(
        body["rule_hits"], sort_keys=True, default=str
    )


@pytest.mark.parametrize("work_id", FIXTURES)
def test_the_badged_body_still_reproduces_the_fixture_document(badged, work_id):
    """And the surviving numbers are the documented ones, not merely stable."""
    from app.constants import case_id_for

    expected = EXPECTED[work_id]
    _, out = badged[work_id]
    assert case_id_for(work_id) == expected["case_id"]
    assert out["score"] == expected["score"]
    assert out["raw_score"] == expected["raw_score"]
    assert out["severity"] == expected["severity"]
    assert out["coverage_pct"] == expected["coverage_pct"]
    assert out["gap_hop"] == expected["gap_hop"]
    assert out["slowest_lag"] == expected["slowest_lag"]
    assert out["corroboration"]["contribution"] == expected["corroboration"]

    statuses = {"fired": 0, "passed": 0, "skipped": 0}
    for hit in out["rule_hits"]:
        statuses[hit["status"]] += 1
    assert statuses["fired"] == expected["fired"]
    assert statuses["passed"] == expected["passed"]
    assert statuses["skipped"] == expected["skipped"]
    assert len(out["rule_hits"]) == 10


@pytest.mark.parametrize("work_id", FIXTURES)
def test_the_score_is_still_the_sum_an_officer_can_add_on_paper(badged, work_id):
    """Invariant 1 as arithmetic: fired weights plus the bonus, and nothing else.

    If any badge had contributed so much as a point, the printed contributions
    would no longer add to the printed raw score - which is the failure an
    officer would find first, and the one the cap deliberately does not hide.
    """
    _, out = badged[work_id]
    fired = sum(hit["contribution"] for hit in out["rule_hits"] if hit["status"] == "fired")
    assert fired + out["corroboration"]["contribution"] == out["raw_score"]
    assert all(
        hit["contribution"] == 0 for hit in out["rule_hits"] if hit["status"] != "fired"
    )


@pytest.mark.parametrize("work_id", FIXTURES)
def test_the_badges_are_attached_and_all_three_declare_zero(badged, work_id):
    """The badges are really there - this is not a test that passes on nothing."""
    _, out = badged[work_id]
    for block in ("statistical", "forecast", "concentration"):
        assert block in out
        assert out[block]["contribution"] == 0
        assert out[block]["availability"] in {
            Availability.PUBLISHED.value,
            Availability.NOT_APPLICABLE.value,
            Availability.NOT_PUBLISHED.value,
        }


def test_the_badge_blocks_carry_real_content_on_fixture_a(badged, ml_run):
    """A is the case the frozen contract prints, so it is the one to check.

    All four tiers have something to say about it: it sits in a 15-work
    duplicate cluster, the forest flags it and confirms the rulebook, its
    execution outcome is still open so it is forecast, and its agency has a
    measurable position in the vendor graph.
    """
    _, out = badged[FIXTURE_A]
    assert out["statistical"]["anomaly_score"] is not None
    assert out["statistical"]["confirms"] is True
    assert out["statistical"]["anomaly_model_version"].startswith("iso1-")
    assert out["forecast"]["delay_risk"] is not None
    assert out["forecast"]["horizon_days"] == 365
    assert out["forecast"]["model_version"].startswith("fc1-")
    assert out["concentration"]["hhi"] is not None
    assert out["concentration"]["model_version"].startswith("gr1-")
    assert ml_run.finding("duplicate", FIXTURE_A).payload["cluster_size"] == 15


def test_a_case_the_ml_tier_cannot_speak_about_still_renders_every_block(badged):
    """B and C keep the contract's shape while saying they have nothing to say.

    A block is never omitted because a model was silent. The case body's shape
    does not change with how much the ML tier could say, and every null carries
    its reason - which is CLAUDE.md invariant 2 applied to the badge layer.
    """
    for work_id in (FIXTURE_B, FIXTURE_C):
        _, out = badged[work_id]
        assert out["statistical"]["anomaly_score"] is None
        assert out["statistical"]["availability"] == Availability.NOT_APPLICABLE.value
        assert out["statistical"]["detail"]
        assert out["forecast"]["delay_risk"] is None
        assert out["forecast"]["availability"] == Availability.NOT_APPLICABLE.value
        assert out["forecast"]["detail"]


# ---------------------------------------------------------------------------
# The same claim, over the whole corpus rather than three rows
# ---------------------------------------------------------------------------


def test_no_case_in_the_corpus_changes_when_every_badge_is_attached(ml_run):
    """27,079 cases, all four tiers, and not one scored key moves.

    Three fixtures prove the arrangement is right. This proves it holds
    everywhere, including on the cases where a model has the most to say.
    """
    anomaly_by_pk = ml_run.findings_for("anomaly")
    forecast_by_pk = ml_run.findings_for("forecast")
    graph_by_pk = ml_run.findings_for("graph")
    for work_pk, body in ml_run.bodies.items():
        out = attach(
            body,
            anomaly=anomaly_by_pk[work_pk],
            forecast=forecast_by_pk[work_pk],
            concentration=graph_by_pk[work_pk],
        )
        for key in SCORED_KEYS:
            assert out[key] == body[key], (work_pk, key)


def test_the_corpus_wide_bands_are_the_ones_the_profile_records(ml_run):
    """37 HIGH, 1,006 MEDIUM, 26,035 LOW, unchanged by this phase.

    DATA-PROFILE.md section 6. The labelled control is excluded, as it is from
    every published aggregate (CLAUDE.md invariant 12).
    """
    bands = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for work_pk, body in ml_run.bodies.items():
        if ml_run.corpus.works[work_pk].is_synthetic:
            continue
        bands[body["severity"]] += 1
    assert bands == {"HIGH": 37, "MEDIUM": 1006, "LOW": 26035}


def test_only_the_duplicate_kind_is_marked_as_reaching_a_rule(ml_run):
    """`ml_findings.contributes_to_score`, as `models.py` declares it.

    False for every kind except `duplicate`. And True on `duplicate` does not
    mean `score.py` reads that table - it does not, and no module under
    `engine/` imports this package. It means the number a duplicate finding
    records is the number `duplicate_work` reads, and that the rule is
    admissible only because the matched work ids travel with it
    (DOMAIN-MODEL.md (h)).
    """
    assert kinds_are_badges(ml_run.anomaly_findings)
    assert kinds_are_badges(ml_run.forecast_findings)
    assert kinds_are_badges(ml_run.graph_findings)
    assert all(f.contributes_to_score is False for f in ml_run.anomaly_findings)
    assert all(f.contributes_to_score is False for f in ml_run.forecast_findings)
    assert all(f.contributes_to_score is False for f in ml_run.graph_findings)
    assert all(f.contributes_to_score is True for f in ml_run.duplicate_findings)


def test_every_tier_speaks_about_every_sanctioned_work_or_says_why_not(ml_run):
    """Four findings per work, 27,079 works, no silent exclusions anywhere.

    A work the ML tier cannot read is `not_applicable` or `not_published` with
    a detail line an officer can read. This is the ML layer's whole debt to
    invariant 2, paid in one assertion.
    """
    expected = set(ml_run.corpus.features)
    for findings in (
        ml_run.duplicate_findings,
        ml_run.anomaly_findings,
        ml_run.forecast_findings,
        ml_run.graph_findings,
    ):
        assert {f.work_pk for f in findings} == expected
        for finding in findings:
            if finding.value is None:
                assert finding.availability != Availability.PUBLISHED
                assert finding.payload.get("detail"), (finding.kind, finding.work_pk)
            else:
                assert finding.availability == Availability.PUBLISHED
