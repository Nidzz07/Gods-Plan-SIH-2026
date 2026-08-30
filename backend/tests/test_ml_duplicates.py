"""`app/ml/duplicates.py` - clusters, citations, and the shipped numbers held still.

The first job of this module is to prove the decision recorded in
`app/ml/duplicates.py`'s docstring: this package does NOT replace the
computation `engine/derive.py` performs for `duplicate_similarity`, and the
figures three documents already publish - `DATA-PROFILE.md` section 6,
`docs/contract/fixtures.md` and `docs/contract/case_detail.json` - are
unchanged by its existence.

The second is to prove the addition is real: the trace citation can be built
from the cluster rather than only from the pairwise ranking, and the corpus's
447 and 275 clusters are addressable objects with stable ids.
"""

from __future__ import annotations

import pytest

from app.constants import Availability, ML_KIND_DUPLICATE
from app.engine import derive as derive_mod
from app.ml import duplicates as dup

from .conftest import FIXTURE_A, FIXTURE_B, FIXTURE_C

pytestmark = pytest.mark.corpus


# ---------------------------------------------------------------------------
# The shipped numbers, unmoved
# ---------------------------------------------------------------------------


def test_clusters_reproduce_the_profile(ml_run):
    """DATA-PROFILE.md section 6, exactly: 447 / 3,584 and 275 / 3,240."""
    clusters = ml_run.clusters
    assert len(clusters.clusters_of_at_least(2)) == 447
    assert clusters.works_in_clusters_of_at_least(2) == 3584
    assert len(clusters.clusters_of_at_least(3)) == 275
    assert clusters.works_in_clusters_of_at_least(3) == 3240


def test_the_three_largest_clusters_are_the_ones_the_profile_names(ml_run):
    """244 Budaun, 115 Jalaun, 108 Siddharth Nagar."""
    clusters = ml_run.clusters
    largest = [
        (size, ml_run.agency_names[clusters.agency_of[clusters.members[cid][0]]])
        for cid, size in clusters.largest(3)
    ]
    assert largest == [
        (244, "DISTRICT MAGISTRATE BUDAUN"),
        (115, "DISTRICT MAGISTRATE JALAUN"),
        (108, "DISTRICT MAGISTRATE SIDDHARTH NAGAR"),
    ]


def test_cluster_size_agrees_with_the_feature_split_sanction_reads(ml_run):
    """`same_desc_same_agency_count` and `cluster_size` are the same count.

    They must be: `split_sanction` fires on the first and the citation prints
    the second, and a case whose trace said 15 in one row and 14 in another
    would be unreadable. This asserts it over the whole corpus rather than on
    a fixture, because a drift would be a drift of definitions.
    """
    for work_pk, features in ml_run.corpus.features.items():
        expected = features.get("same_desc_same_agency_count")
        if expected is None:
            continue
        assert ml_run.clusters.size_of(work_pk) == expected, work_pk


def test_the_engine_still_owns_the_number_the_rulebook_reads(ml_run):
    """`derive.py` computes `duplicate_similarity`; this module mirrors it.

    The decision, made explicit: `engine/` does not import `ml/`, so the
    similarity the rule reads is derived on the scoring path and this module
    carries the same value through. Asserting equality over the corpus is what
    stops the two from drifting while the structural separation holds.
    """
    findings = ml_run.findings_for("duplicate")
    for work_pk, features in ml_run.corpus.features.items():
        assert findings[work_pk].value == features.get("duplicate_similarity"), work_pk


# ---------------------------------------------------------------------------
# Fixture A - the citation, built from the cluster
# ---------------------------------------------------------------------------


def test_fixture_a_cluster_holds_fifteen_works(ml_run):
    clusters = ml_run.clusters
    work_pk = ml_run.pk(FIXTURE_A)
    assert clusters.size_of(work_pk) == 15
    assert ml_run.agency_names[clusters.agency_of[work_pk]] == "DISTRICT MAGISTRATE JALAUN"
    assert clusters.cluster_of[work_pk].startswith(dup.CLUSTER_ID_PREFIX)


def test_fixture_a_citation_is_byte_identical_to_the_engine_citation(ml_run):
    """The claim that the trace citation can be built from ml_findings, checked.

    `docs/contract/case_detail.json` prints this object on fixture A's fired
    `duplicate_work` row. If this module can reproduce it exactly, then a
    future API layer may serve the citation from `ml_findings` without the
    officer seeing a different record from the one the trace was scored on.
    """
    work_pk = ml_run.pk(FIXTURE_A)
    work = ml_run.corpus.works[work_pk]
    from_cluster = ml_run.clusters.citation_for(
        work_pk, agency_name=ml_run.agency_names[work.agency_id]
    )
    from_engine = derive_mod.duplicate_citation(work, ml_run.corpus.context)
    assert from_cluster == from_engine


def test_fixture_a_citation_carries_the_contract_values(ml_run):
    work_pk = ml_run.pk(FIXTURE_A)
    citation = ml_run.clusters.citation_for(
        work_pk, agency_name=ml_run.agency_names[ml_run.corpus.works[work_pk].agency_id]
    )
    assert citation["matched_work_ids"] == [
        "WS/MP847/2025-2026/160262",
        "WS/MP847/2025-2026/160263",
    ]
    assert citation["matched_case_ids"] == ["NG-D4BA75C468", "NG-436EB11F68"]
    assert citation["cluster_size"] == 15
    assert citation["similarity"] == 1.0
    assert citation["components"] == {
        "token_set_ratio": 1.0,
        "partial_ratio": 1.0,
        "token_sort_ratio": 1.0,
    }
    assert citation["shared_description"] == (
        "led semi high mast light 6led with 200 watt 9 5 meter pole"
    )
    # A cluster is a candidate for review, never an accusation.
    assert "review" in citation["reading"].lower()
    assert "fraud" not in citation["reading"].lower()


def test_cluster_ids_are_deterministic_and_not_positional(ml_run):
    """The invariant-8 discipline, applied to a cluster id.

    Two works in the same cluster derive the same id from the agency and the
    text, and it survives being computed from either member. Nothing about row
    order enters it.
    """
    clusters = ml_run.clusters
    work_pk = ml_run.pk(FIXTURE_A)
    cluster_id = clusters.cluster_of[work_pk]
    members = clusters.members[cluster_id]
    assert len(members) == 15
    for member in members:
        assert clusters.cluster_of[member] == cluster_id
        assert (
            dup.cluster_id_for(clusters.agency_of[member], clusters.normalised[member])
            == cluster_id
        )


# ---------------------------------------------------------------------------
# B and C - a work with no peers, and the skips that says so
# ---------------------------------------------------------------------------


def test_fixture_b_is_its_own_cluster_of_one(ml_run):
    """B's nearest neighbour is a different road, so exact repetition is 1.

    fixtures.md records the disagreement deliberately: `duplicate_work` fires
    on B at 0.900 while `split_sanction` correctly passes at a cluster of 1,
    and the two rules disagreeing on one work is the clearest demonstration
    that the SCORER, not the repetition count, is what needs calibration.
    """
    work_pk = ml_run.pk(FIXTURE_B)
    assert ml_run.clusters.size_of(work_pk) == 1
    assert ml_run.findings_for("duplicate")[work_pk].value == pytest.approx(0.90, abs=0.005)


def test_fixture_c_has_no_peer_and_says_so_rather_than_scoring_zero(ml_run):
    """The control has no corpus around it, and Phase 2's decision stands.

    `docs/contract/fixtures.md` standing caveat 9 records that C's similarity
    is `not_applicable` because a single work under a single agency has nothing
    to be similar to, and that giving the control synthetic peers to close the
    gap was rejected. This phase does not reopen it: the finding carries the
    reason, not a zero.
    """
    finding = ml_run.finding("duplicate", FIXTURE_C)
    assert finding.value is None
    assert finding.availability == Availability.NOT_APPLICABLE
    assert "no population to compare" in finding.payload["detail"]
    assert finding.payload["cluster_size"] == 1
    # And the engine agrees, on the same row, for the same reason.
    features = ml_run.corpus.features_for(FIXTURE_C)
    assert features["duplicate_similarity"] is None
    assert features.availability["duplicate_similarity"] == Availability.NOT_APPLICABLE


def test_every_sanctioned_work_gets_a_finding_and_every_null_carries_a_reason(ml_run):
    """CLAUDE.md invariant 2, applied to the ML layer.

    27,079 findings, one per sanctioned work including the labelled control.
    A work with nothing to say about it is `not_applicable` or `not_published`
    with a detail line, never absent and never zero.
    """
    findings = ml_run.duplicate_findings
    assert len(findings) == len(ml_run.corpus.features)
    assert {f.work_pk for f in findings} == set(ml_run.corpus.features)
    for finding in findings:
        assert finding.kind == ML_KIND_DUPLICATE
        if finding.value is None:
            assert finding.availability != Availability.PUBLISHED
            assert finding.payload["detail"]
        else:
            assert finding.availability == Availability.PUBLISHED


def test_the_two_skip_reasons_stay_apart(ml_run):
    """`not_published` and `not_applicable` are different findings.

    No readable description at all is a reporting gap that belongs in the
    ablation report; an agency with no second described work is a fact about a
    work with no peers. 129 and 53 on this corpus, and collapsing them is what
    invariant 2 exists to prevent.
    """
    reasons = {}
    for finding in ml_run.duplicate_findings:
        reasons[finding.availability] = reasons.get(finding.availability, 0) + 1
    assert reasons[Availability.NOT_PUBLISHED] == 129
    assert reasons[Availability.NOT_APPLICABLE] == 53
    assert reasons[Availability.PUBLISHED] == 26897


# ---------------------------------------------------------------------------
# The cross-check - measurement for the calibration question, not a decision
# ---------------------------------------------------------------------------


def test_the_cross_check_measures_and_decides_nothing(ml_run):
    """A second opinion on the scorer `DATA-PROFILE.md` section 6 left open.

    At the shipped threshold of 0.85, `token_set_ratio` fires on 16,491 works -
    61% of the corpus - because MPLADS descriptions share heavy boilerplate.
    A TF-IDF cosine over the same normalised text, against the same
    best-matching peer, clears 0.85 on 3,212 of the same 26,897 works, and
    every one of those 3,212 is inside the rapidfuzz set. 3,212 sits close to
    the 3,240 works `split_sanction` fires on by exact repetition, which is
    evidence that the cosine tracks repetition where `token_set_ratio` tracks
    boilerplate.

    That is a MEASUREMENT and not a recalibration. Choosing a scorer and a
    threshold together, and re-measuring the resulting distribution into the
    profile, is the pass that document reserves for itself; nothing in this
    phase touches `rules.yaml` or the number the rule reads.
    """
    threshold = 0.85
    cross_check = ml_run.cross_check
    rapidfuzz_fires = {
        pk
        for pk, value in ml_run.clusters.similarity.items()
        if value >= threshold and not ml_run.corpus.works[pk].is_synthetic
    }
    cosine_fires = {
        pk
        for pk, value in cross_check.items()
        if value >= threshold and not ml_run.corpus.works[pk].is_synthetic
    }
    assert len(rapidfuzz_fires) == 16491
    assert len(cosine_fires) == 3212
    assert cosine_fires <= rapidfuzz_fires
    # The rule still reads the rapidfuzz number, unchanged, on every work.
    for work_pk in list(rapidfuzz_fires)[:200]:
        assert (
            ml_run.corpus.features[work_pk]["duplicate_similarity"]
            == ml_run.clusters.similarity[work_pk]
        )


def test_the_cross_check_rides_beside_the_citation_and_never_replaces_it(ml_run):
    work_pk = ml_run.pk(FIXTURE_A)
    citation = ml_run.clusters.citation_for(
        work_pk,
        agency_name=ml_run.agency_names[ml_run.corpus.works[work_pk].agency_id],
        cross_check=ml_run.cross_check[work_pk],
    )
    assert citation["similarity"] == 1.0
    assert citation["method"] == derive_mod.SIMILARITY_METHOD
    assert citation["cross_check"]["method"] == dup.CROSS_CHECK_METHOD
    assert "contributes nothing" in citation["cross_check"]["reading"]
