"""`app/ml/concentration.py` - the bipartite graph, and what it adds.

Two claims to check.

**The graph agrees with the rulebook it does not feed.** It builds the same
edge weights from the same payments, so it must reproduce the 65 agency-vendor
pairs above 60% and the Rs 50 lakh floor that `DATA-PROFILE.md` section 6
measured, and the 650 vendors spanning more than one agency with the widest at
10. A different count means the graph and `engine/derive.py` have drifted,
which is a bug in one of them.

**And it adds something a single ratio cannot.** Vendor span, shared-vendor
exposure, an HHI over an agency's vendors and the size of the component an
agency sits in are all properties of the structure. None of them can be
computed from `vendor_share_in_agency_pct`, which is one number about one edge.
"""

from __future__ import annotations

import pytest

from app.constants import (
    Availability,
    ML_KIND_GRAPH,
    VENDOR_CONCENTRATION_AGENCY_FLOOR,
)
from app.engine import derive as derive_mod
from app.ml import concentration
from app.ml.badges import attach

from .conftest import FIXTURE_A, FIXTURE_B, FIXTURE_C

pytestmark = pytest.mark.corpus


# ---------------------------------------------------------------------------
# Agreement with the numbers the rulebook is calibrated on
# ---------------------------------------------------------------------------


def test_the_graph_reproduces_the_profiles_65_concentrated_pairs(ml_run):
    """DATA-PROFILE.md section 6: 65 agency-vendor pairs above 60% and the floor.

    A consistency check on the graph, not a second source the rule might read.
    `engine/derive.vendor_share_in_agency_pct` remains the only computation
    `vendor_concentration` sees, and this module does not recompute it.
    """
    real = concentration.ConcentrationGraph(
        concentration.build(
            (agency_id, vendor_id, paid)
            for agency_id, vendor_id, paid in ml_run.payment_rows()
            if not ml_run.synthetic_agency(agency_id)
        )
    )
    assert len(real.concentrated_pairs(60)) == 65


def test_the_graph_reproduces_the_vendor_span_figures(ml_run):
    """650 vendors under more than one agency, widest span 10."""
    graph = ml_run.graph
    assert len(graph.spanning_vendors(2)) == 650
    assert graph.max_span() == 10


def test_span_read_off_the_graph_agrees_with_the_stored_rollup(ml_run):
    """`vendors.agency_span` is a rollup ingest writes; this is the same number.

    Two routes to one figure, checkable against each other. If they part, one
    of them is wrong and the graph is the one that can be re-derived.
    """
    from sqlalchemy import select

    from app.models import Vendor

    stored = dict(
        ml_run.session.execute(
            select(Vendor.id, Vendor.agency_span).where(Vendor.is_synthetic.is_(False))
        ).all()
    )
    mismatches = [
        vendor_id
        for vendor_id, span in stored.items()
        if ml_run.graph.span(vendor_id) != span
    ]
    assert mismatches == []


def test_the_top_vendor_share_matches_the_feature_the_rulebook_reads(ml_run):
    """Where a work's own vendor IS its agency's largest, the two agree.

    The per-work feature answers "what share went to THIS work's vendor" and
    the graph answers "what share went to the agency's largest". They are
    different questions, so the check is confined to the works where the answer
    must coincide - and there it must coincide exactly.
    """
    checked = 0
    for work_pk, features in ml_run.corpus.features.items():
        share = features.get("vendor_share_in_agency_pct")
        if share is None:
            continue
        work = ml_run.corpus.works[work_pk]
        measures = ml_run.graph.measures(work.agency_id)
        if measures is None:
            continue
        vendors = {
            p.vendor_id for p in ml_run.corpus.payments.get(work_pk, []) if p.vendor_id
        }
        if measures["top_vendor_id"] in vendors and len(vendors) == 1:
            assert measures["top_vendor_share_pct"] == pytest.approx(share, abs=0.01)
            checked += 1
    assert checked > 500


# ---------------------------------------------------------------------------
# What the graph adds
# ---------------------------------------------------------------------------


def test_the_graph_native_measures_are_present_and_are_not_the_ratio(ml_run):
    """Four readings a single share cannot express, on fixture A's agency."""
    measures = ml_run.graph.measures(
        ml_run.corpus.works[ml_run.pk(FIXTURE_A)].agency_id
    )
    assert measures is not None
    for key in (
        "hhi",
        "shared_vendor_exposure_pct",
        "widest_vendor_span",
        "component_agencies",
    ):
        assert key in measures
    assert 0.0 < measures["hhi"] <= 1.0
    assert measures["vendor_count"] >= 1
    # An HHI is a sum of squared shares, so it is bounded below by the square of
    # the largest share and above by that share itself. Asserting the identity
    # rather than a literal keeps the test a check on the measure, not a
    # transcription of one run's output.
    top = measures["top_vendor_share_pct"] / 100
    assert top**2 <= measures["hhi"] + 1e-9
    assert measures["hhi"] <= top + 1e-9


def test_an_hhi_separates_two_agencies_a_single_share_cannot_tell_apart():
    """The reason the index is worth computing, in four rows.

    Both offices give 60% to their largest vendor. One splits the rest between
    two vendors and the other between forty. A ratio calls them identical; the
    index does not.
    """
    concentrated = concentration.ConcentrationGraph(
        concentration.build([(1, 1, 60), (1, 2, 20), (1, 3, 20)])
    )
    dispersed_rows = [(2, 1, 6000)] + [(2, 100 + i, 100) for i in range(40)]
    dispersed = concentration.ConcentrationGraph(concentration.build(dispersed_rows))
    a = concentrated.measures(1)
    b = dispersed.measures(2)
    assert a["top_vendor_share_pct"] == b["top_vendor_share_pct"] == 60.0
    assert a["hhi"] > b["hhi"]


def test_shared_vendor_exposure_needs_the_far_end_of_every_edge():
    """A weighted sum over the DEGREE of the node at the other end.

    Agency 1 pays two vendors equally; one of them also works for agency 2. Half
    of agency 1's disbursement is therefore exposed to a shared contractor, and
    no ratio about agency 1's own edges can say so.
    """
    graph = concentration.ConcentrationGraph(
        concentration.build([(1, 10, 50), (1, 11, 50), (2, 11, 90)])
    )
    assert graph.measures(1)["shared_vendor_exposure_pct"] == 50.0
    assert graph.measures(2)["shared_vendor_exposure_pct"] == 100.0
    assert graph.span(11) == 2
    assert graph.span(10) == 1
    # And both agencies sit in one component, reachable only through vendor 11.
    assert graph.measures(1)["component_agencies"] == 2


def test_the_corpus_is_mostly_one_structure_through_shared_contractors(ml_run):
    """418 real components, the largest holding 9,430 nodes.

    Context rather than a finding: a vendor working for several district offices
    is very often a firm that works across a region.

    The labelled control is its own 419th component - one synthetic agency
    paying one synthetic vendor, connected to nothing - which is exactly what
    invariant 12 asks of it: it cannot land inside a real agency's structure,
    and it is excluded from the published figure.
    """
    real = concentration.ConcentrationGraph(
        concentration.build(
            (agency_id, vendor_id, paid)
            for agency_id, vendor_id, paid in ml_run.payment_rows()
            if not ml_run.synthetic_agency(agency_id)
        )
    )
    assert max(real.component_size.values()) == 9430
    assert len(set(real.component_of.values())) == 418
    assert len(set(ml_run.graph.component_of.values())) == 419


# ---------------------------------------------------------------------------
# Invariant 1, and the availability discipline
# ---------------------------------------------------------------------------

FIXTURE_SCORES = {
    FIXTURE_A: (92, 92, "HIGH", 79),
    FIXTURE_B: (60, 60, "MEDIUM", 65),
    FIXTURE_C: (20, 20, "LOW", 74),
}


@pytest.mark.parametrize("work_id", sorted(FIXTURE_SCORES))
def test_the_real_graph_output_cannot_move_the_score(ml_run, work_id):
    expected = FIXTURE_SCORES[work_id]
    body = ml_run.rescore(work_id)
    badged = attach(body, concentration=ml_run.finding("graph", work_id))
    assert (
        badged["score"],
        badged["raw_score"],
        badged["severity"],
        badged["coverage_pct"],
    ) == expected
    assert badged["concentration"]["contribution"] == 0


def test_no_graph_key_is_addressable_from_the_rulebook():
    for field in ("hhi", "shared_vendor_exposure_pct", "widest_vendor_span"):
        assert field not in derive_mod.FEATURE_KEYS


def test_an_agency_with_no_payment_edge_is_not_applicable_rather_than_even(ml_run):
    """An office that has disbursed nothing is not an office with an even spread."""
    skipped = [
        f for f in ml_run.graph_findings if f.availability != Availability.PUBLISHED
    ]
    assert len(skipped) == 713
    for finding in skipped[:100]:
        assert finding.value is None
        assert finding.availability == Availability.NOT_APPLICABLE
        assert "no measurable structure" in finding.payload["detail"]


def test_a_finding_is_produced_for_every_work_and_every_one_is_a_badge(ml_run):
    assert len(ml_run.graph_findings) == len(ml_run.corpus.features)
    assert {f.work_pk for f in ml_run.graph_findings} == set(ml_run.corpus.features)
    for finding in ml_run.graph_findings:
        assert finding.kind == ML_KIND_GRAPH
        assert finding.contributes_to_score is False


def test_a_works_own_vendors_carry_the_span_only_the_graph_knows(ml_run):
    finding = ml_run.finding("graph", FIXTURE_A)
    assert finding.availability == Availability.PUBLISHED
    assert finding.payload["work_vendors"]
    for vendor in finding.payload["work_vendors"]:
        assert vendor["agency_span"] >= 1
        assert vendor["agency_span"] == ml_run.graph.span(vendor["vendor_id"])


def test_fixture_b_has_no_vendor_of_its_own_and_the_block_says_so(ml_run):
    """B has no payment row at all, so it names no vendor.

    Its agency still has a graph position - other works of the same office were
    paid - and the block reports that position while listing no vendor for this
    work. The two facts are different and stay apart.
    """
    finding = ml_run.finding("graph", FIXTURE_B)
    assert finding.payload["work_vendors"] == []
    assert ml_run.corpus.features_for(FIXTURE_B)["payment_count"] == 0


def test_fixture_c_sits_below_the_floor_and_the_block_records_it(ml_run):
    """The control's agency disbursed Rs 38.8 lakh, under the Rs 50 lakh floor.

    The graph still measures the structure - one agency, one vendor, an HHI of
    1.0 - and records that the agency is BELOW the floor, which is why
    `vendor_concentration` is not_applicable on this work rather than firing at
    100%. Phase 2's reading of the control is unchanged.
    """
    finding = ml_run.finding("graph", FIXTURE_C)
    assert finding.availability == Availability.PUBLISHED
    assert finding.payload["above_floor"] is False
    assert finding.payload["disbursed_total"] <= VENDOR_CONCENTRATION_AGENCY_FLOOR
    assert finding.payload["hhi"] == 1.0
    assert finding.payload["vendor_count"] == 1
    features = ml_run.corpus.features_for(FIXTURE_C)
    assert features["vendor_share_in_agency_pct"] is None
    assert features.availability["vendor_share_in_agency_pct"] == (
        Availability.NOT_APPLICABLE
    )


def test_the_block_never_calls_a_shared_vendor_a_finding(ml_run):
    reading = ml_run.finding("graph", FIXTURE_A).payload["reading"]
    lowered = reading.lower()
    assert "zero points" in reading
    assert "context" in lowered
    for overclaim in ("fraud", "collusion", "cartel", "ai-detected"):
        assert overclaim not in lowered
