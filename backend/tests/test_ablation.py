"""F9 - the data-gap measurement, and the fabrication it is built not to commit.

Four claims are under test, and the second is the one the whole phase turns on.

**The attribution is real.** Every skip this module attributes to a field is a
skip the engine actually recorded, for that reason, on a work meeting a
condition read straight off the row - and every skip matching that condition is
attributed. Both directions, with exact counts, cross-checked against
`docs/data/DATA-PROFILE.md` section 6's firing-count table and against
`docs/contract/fixtures.md`. An attribution that held in only one direction
would be a plausible story rather than a measurement.

**Nothing is fabricated.** The module's premise - "what if a field existed that
does not" - is exactly the premise under which a project invents supporting
data. This suite asserts the shape of the output: corpus-level aggregates and
bounded ranges, and nowhere a per-work hypothetical score, a per-work
hypothetical rule status, or a list of works said to be affected in a way the
measurement cannot support. That is a check on the SHAPE, deliberately, because
a fabricated per-work outcome has to appear in the output shape in order to
reach a screen.

**Zero means what it says.** Seven of the nine fields measure zero unrealised
weight because no rule reads them, and this suite proves the antecedent: every
rule id those fields name is absent from the shipped rulebook. That turns
"measures zero" from a claim into an arithmetic consequence.

**It is idempotent.** Two runs over the same corpus produce a byte-identical
document, because the measurement is arithmetic over stored rows and the only
date in it is the corpus as-of date.

The boundary test - that `engine/` and `ml/` never import `ablation/` - lives in
`tests/test_ml_boundary.py` beside the ML one, because it is the same claim
about the same kind of arrow and splitting it across two files would let one of
them be forgotten.
"""

from __future__ import annotations

import json

import pytest

from app.ablation import fields as fields_mod
from app.ablation import measure as measure_mod
from app.ablation import rank as rank_mod
from app.ablation import report as report_mod
from app.ablation import run as run_mod
from app.ablation.fields import (
    BASIS_MEASURED_SKIPS,
    BASIS_NO_RULE_READS_IT,
    CONDITION_NO_COMPLETION_ROW,
    CONDITION_NO_PAYMENT_ROW,
    FIELDS,
    Attribution,
)
from app.ablation.measure import RuleTrace, WorkRecord
from app.constants import (
    RULE_STATUS_FIRED,
    RULE_STATUS_PASSED,
    RULE_STATUS_SKIPPED,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    Availability,
)

# The two fields whose absence skips something today. Every exact-value
# assertion below is against one of these; the other seven measure zero and are
# asserted to measure zero for a stated reason rather than by coincidence.
EXPENDITURE = "expenditure_linkage"
IMAGE_SCOPE = "asset_image_publication_scope"


# ---------------------------------------------------------------------------
# The corpus, measured
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def analysis(db_session):
    """The whole measurement over the ingested corpus, run once."""
    return run_mod.analyse(db_session)


@pytest.fixture(scope="module")
def measurements(analysis):
    ranked, _, _ = analysis
    return {entry.key: entry.measurement for entry in ranked}


@pytest.fixture(scope="module")
def records(analysis):
    _, _, records = analysis
    return records


def test_the_measured_population_is_the_real_corpus_without_the_control(records):
    """27,078 real sanctioned works. The labelled control is excluded (invariant 12)."""
    assert len(records) == 27_078
    assert not any(record.is_synthetic for record in records)


def test_the_scoring_pass_reproduces_the_profiles_bands_and_coverage(records, analysis):
    """The measurement reads the same corpus the fixture tests read.

    If this diverges from `DATA-PROFILE.md` section 6 then every figure in the
    ablation report is measured against a different corpus from the one the
    rest of the project describes, and the report is worthless. Asserted here
    rather than assumed, even though `tests/test_fixtures.py` asserts it too:
    this module builds its own scoring pass and could drift from that one.
    """
    _, context, _ = analysis
    assert measure_mod.band_counts(records) == {"HIGH": 37, "MEDIUM": 1_006, "LOW": 26_035}
    assert context["mean_coverage_pct"] == pytest.approx(58.47, abs=0.01)
    assert context["rule_weight_total"] == 144
    assert context["rulebook_version"] == "v1.0.0"


# ---------------------------------------------------------------------------
# (a) (b) (c) - exact values, cross-checked against the documents
# ---------------------------------------------------------------------------


def test_expenditure_linkage_skip_counts_and_unrealised_weight(measurements):
    """Field 8, rule by rule. Every skip count is DATA-PROFILE section 6's.

    The profile records `utilisation_shortfall` skipped on 23,549 works,
    `stalled_work` on 23,549, and `vendor_concentration` on 23,686 - of which
    23,549 are `not_published` for want of a payment row and 137 are
    `not_applicable` because the agency sits below the Rs 50 lakh floor. Only
    the first 23,549 belong to this field, and the 137 must NOT be swept in:
    an agency being small is a fact about the agency, not a gap in MoSPI's
    export.
    """
    measurement = measurements[EXPENDITURE]
    by_rule = {a.rule_id: a for a in measurement.attributions}

    assert by_rule["utilisation_shortfall"].skips == 23_549
    assert by_rule["utilisation_shortfall"].weight == 22
    assert by_rule["utilisation_shortfall"].unrealised_weight == 23_549 * 22 == 518_078

    assert by_rule["stalled_work"].skips == 23_549
    assert by_rule["stalled_work"].unrealised_weight == 23_549 * 16 == 376_784

    # 23,549 and not 23,686: the 137 agency-floor skips are a different finding.
    assert by_rule["vendor_concentration"].skips == 23_549
    assert by_rule["vendor_concentration"].unrealised_weight == 23_549 * 12 == 282_588

    assert measurement.rule_skips == 70_647
    assert measurement.unrealised_weight == 1_177_450
    assert measurement.works_affected == 23_549


def test_asset_image_publication_scope_skip_count_and_unrealised_weight(measurements):
    """Field 9. 14,104 skips of a 10-point rule, and DATA-PROFILE section 6 agrees.

    The profile records `asset_evidence_missing` firing on 4,493 works and
    skipped on 14,104 - 52% of the corpus - because the `Image` column is
    published only in the completed export. Those 14,104 are this field's, and
    they are NOT the asset-photo-geotag field's, which is what the next test
    exists to hold.
    """
    measurement = measurements[IMAGE_SCOPE]
    assert measurement.rule_skips == 14_104
    assert measurement.unrealised_weight == 14_104 * 10 == 141_040
    assert measurement.works_affected == 14_104
    assert measurement.attributions[0].fired == 4_493
    assert measurement.attributions[0].evaluable == 12_974


def test_the_geotag_field_is_not_credited_with_the_image_scope_skips(measurements):
    """The two gaps are adjacent and different, and conflating them is the easy error.

    `asset_evidence_missing` skips because a column was not published for works
    that are not complete. That is a publication-scope gap. A geotag would tell
    an officer whether a photograph that WAS filed shows this asset, which is a
    different question and recovers no skipped weight at all.
    """
    assert measurements["asset_photo_geotag"].unrealised_weight == 0
    assert measurements["asset_photo_geotag"].rule_skips == 0
    assert measurements[IMAGE_SCOPE].unrealised_weight == 141_040


def test_the_certification_gap_is_the_one_fixture_c_demonstrates(measurements, db_session):
    """Field 2, cross-checked against fixture C rather than against a claim.

    `docs/contract/fixtures.md` records C's fund ladder with hop 2 OPEN at
    -25.00% beside a score of 20 and a LOW band, "because rulebook v1.0.0 has
    no rule reading `variance_disbursement_to_certification`". This asserts the
    same two facts from the other end: no rule reads that feature, so the field
    measures zero; and the `certifications` table holds exactly one row, which
    is the labelled control, so no real work has a certificate at all.
    """
    from sqlalchemy import func, select

    from app.engine import rulebook as rulebook_mod
    from app.models import Certification

    measurement = measurements["utilisation_certificate"]
    assert measurement.unrealised_weight == 0
    assert measurement.field.basis == BASIS_NO_RULE_READS_IT

    book = rulebook_mod.load()
    read_fields = {rule["field"] for rule in book["rules"]}
    assert "variance_disbursement_to_certification" not in read_fields

    assert db_session.scalar(select(func.count()).select_from(Certification)) == 1
    corroborating = dict(measurement.corroborating)
    assert corroborating["Rows in the certifications table"] == 1
    assert corroborating["Works whose certification rung is not published"] == 27_078


def test_every_rule_a_zero_field_would_unlock_is_absent_from_the_rulebook(measurements):
    """This is what makes the seven zeros a proof rather than an assertion.

    A field measures zero unrealised weight because no rule reads it. That
    premise is checkable: the rule ids those fields name must not appear in
    `rules.yaml`. If one ever does, the field stops measuring zero and this
    test fails before the report can print a stale claim.
    """
    from app.engine import rulebook as rulebook_mod

    shipped = {rule["id"] for rule in rulebook_mod.load()["rules"]}
    for entry in FIELDS:
        if entry.basis != BASIS_NO_RULE_READS_IT:
            continue
        assert measurements[entry.key].unrealised_weight == 0, entry.key
        assert measurements[entry.key].rule_skips == 0, entry.key
        assert measurements[entry.key].works_affected == 0, entry.key
        for rule_id in entry.unlocks_rules:
            assert rule_id not in shipped, (
                f"{entry.key} claims to unlock {rule_id!r}, but that rule is in "
                "rules.yaml today - so the field no longer measures zero and its "
                "zero_reason has gone stale."
            )


def test_the_attribution_holds_in_both_directions(records, measurements):
    """No skip is claimed that the engine did not record, and none is missed.

    The forward direction alone would let an attribution quietly under-count;
    the reverse alone would let it over-count. Both are checked because the
    whole method rests on the attribution being a measurement rather than a
    plausible story about the corpus.
    """
    for key in (EXPENDITURE, IMAGE_SCOPE):
        entry = measurements[key].field
        attribution = entry.attribution
        claimed = 0
        for record in records:
            matches = measure_mod.satisfies(record, attribution.condition)
            for hit in record.hits:
                if hit.rule_id not in attribution.rule_ids:
                    continue
                is_claimed_skip = (
                    hit.status == RULE_STATUS_SKIPPED
                    and hit.skip_reason == attribution.skip_reason
                )
                if is_claimed_skip:
                    # Forward: everything claimed really is a skip on a work
                    # meeting the condition.
                    assert matches, (
                        f"{key} claims a skip on a work that does not meet "
                        f"{attribution.condition!r}"
                    )
                    claimed += 1
                elif matches:
                    # Reverse: a work meeting the condition cannot have that
                    # rule in any state OTHER than the claimed skip.
                    raise AssertionError(
                        f"{key}: work meets {attribution.condition!r} but "
                        f"{hit.rule_id} is {hit.status!r}, not the attributed skip"
                    )
        assert claimed == measurements[key].rule_skips


# ---------------------------------------------------------------------------
# (d) - coverage, through score.py's own arithmetic
# ---------------------------------------------------------------------------


def test_coverage_uplift_is_measured_with_the_engines_own_formula(measurements, analysis):
    """58.47% today, 88.91% if the expenditure export were complete.

    The baseline must equal the corpus mean the rest of the project quotes, or
    the uplift is measured from the wrong floor. The `_unrounded` figure is the
    same quantity straight from the weights - 1,177,450 / (144 x 27,078) - and
    the small gap between the two is `engine.score.coverage_pct` rounding each
    case to a whole percent, which is asserted rather than explained away.
    """
    _, context, _ = analysis
    measurement = measurements[EXPENDITURE]
    assert measurement.coverage_now == pytest.approx(context["mean_coverage_pct"], abs=0.01)
    assert measurement.coverage_now == pytest.approx(58.4691, abs=0.001)
    assert measurement.coverage_if_published == pytest.approx(88.9076, abs=0.001)
    assert measurement.coverage_uplift == pytest.approx(30.4385, abs=0.001)

    straight = 1_177_450 / (144 * 27_078) * 100
    assert measurement.coverage_uplift_unrounded == pytest.approx(straight, abs=0.001)
    assert abs(measurement.coverage_uplift - straight) < 0.5


def test_the_image_scope_coverage_uplift(measurements):
    measurement = measurements[IMAGE_SCOPE]
    assert measurement.coverage_if_published == pytest.approx(62.1151, abs=0.001)
    assert measurement.coverage_uplift == pytest.approx(3.6460, abs=0.001)


def test_a_field_that_skips_nothing_moves_coverage_by_nothing(measurements):
    for entry in FIELDS:
        if entry.basis != BASIS_NO_RULE_READS_IT:
            continue
        measurement = measurements[entry.key]
        assert measurement.coverage_if_published == measurement.coverage_now
        assert measurement.coverage_uplift == 0


# ---------------------------------------------------------------------------
# (e) - the bounded range, and what it refuses to do
# ---------------------------------------------------------------------------


def test_the_extrapolation_uses_the_rules_own_observed_firing_rate(measurements):
    """The rate is real: fired over evaluable, on a population the report names.

    `utilisation_shortfall` fires on 1,140 of the 3,529 works where it can be
    read - DATA-PROFILE section 6 - which is 32.30%. Applying that rate to the
    23,549 works where it cannot be read yields 7,607 extrapolated fires. That
    multiplication is the only extrapolation in the module, and it is checked
    here against both of its inputs rather than against its output alone.
    """
    by_rule = {a.rule_id: a for a in measurements[EXPENDITURE].attributions}
    shortfall = by_rule["utilisation_shortfall"]
    assert shortfall.fired == 1_140
    assert shortfall.evaluable == 3_529
    assert shortfall.firing_rate == pytest.approx(1_140 / 3_529)
    assert shortfall.extrapolated_fires == round(1_140 / 3_529 * 23_549) == 7_607
    assert measurements[EXPENDITURE].band_range.extrapolated_fires == 10_242


def test_the_band_effect_is_a_range_and_the_floor_is_checked_not_assumed(measurements):
    """0 to 9,271, and the floor is a measurement of absorbable capacity.

    The floor is only zero if the affected population can take every
    extrapolated fire without a single case crossing a band edge. That is a
    fact about the corpus, so it is computed - 33,406 fires of capacity against
    10,242 extrapolated - and the floor follows from it rather than being
    written down as a rhetorical zero.
    """
    band = measurements[EXPENDITURE].band_range
    assert band.floor == 0
    assert band.absorb_capacity == 33_406
    assert band.absorb_capacity >= band.extrapolated_fires
    assert band.ceiling == 9_271
    assert band.floor <= band.ceiling <= band.crossable_works

    image = measurements[IMAGE_SCOPE].band_range
    assert (image.floor, image.ceiling) == (0, 764)


def test_the_ceiling_never_exceeds_what_the_fire_budget_could_pay_for(measurements):
    """One case cannot cross on fewer than one fire, so the budget bounds it."""
    for key in (EXPENDITURE, IMAGE_SCOPE):
        band = measurements[key].band_range
        assert band.ceiling <= band.extrapolated_fires


def test_the_range_endpoints_carry_their_method_with_them(measurements):
    method = measurements[EXPENDITURE].band_range.method
    assert "refuses" in method
    assert "corroboration bonus" in method


# ---------------------------------------------------------------------------
# The fabrication check - on the SHAPE of the output
# ---------------------------------------------------------------------------

# Keys that would have to exist for a per-work hypothetical to reach a screen.
FORBIDDEN_KEY_FRAGMENTS = (
    "work_id",
    "work_pk",
    "case_id",
    "hypothetical",
    "simulated",
    "imputed",
    "revised_cost",
    "certified_amt",
    "per_work",
)

# The whole-number keys this output may carry. A numeric leaf must name itself
# as a corpus aggregate, a bound or a rate; anything else is a number nobody
# can tell the population of, and a per-work hypothetical would have to arrive
# as exactly that. The three severity names are here because `corpus.bands`
# counts CASES per band over the whole corpus - the same aggregate
# DATA-PROFILE section 6 publishes.
AGGREGATE_KEY_FRAGMENTS = (
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
    "weight",
    "works",
    "skips",
    "fires",
    "pct",
    "rate",
    "rank",
    "floor",
    "ceiling",
    "capacity",
    "count",
    "fields",
    "affected",
    "evaluable",
    "fired",
    "passed",
    "total",
    "value",
)


def _walk(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield f"{path}.{key}", key, value
            yield from _walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield f"{path}[{index}]", None, value
            yield from _walk(value, f"{path}[{index}]")


def test_the_output_shape_carries_no_per_work_hypothetical(analysis):
    """The fabrication this phase exists not to commit, checked at the boundary.

    A hypothetical score for a named work would have to appear in the API shape
    or the document in order to reach anybody. So the assertion is on the
    shape: no key naming a work, a case or a hypothetical value; no list long
    enough to be a per-work collection; and every numeric leaf carrying a name
    that says it is an aggregate, a bound or a rate.

    This is a check on structure and not on intent, which is the point. Intent
    is not testable and structure is.
    """
    ranked, context, _ = analysis
    payload = report_mod.as_dict(ranked, context)

    for path, key, value in _walk(payload):
        if key is not None:
            lowered = key.lower()
            for fragment in FORBIDDEN_KEY_FRAGMENTS:
                assert fragment not in lowered, f"{path} names {fragment!r}"
        if isinstance(value, list):
            assert len(value) <= 32, (
                f"{path} holds {len(value)} entries. Nothing in this output is per work; "
                "a list this long is the shape a per-work collection would have."
            )
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            assert key is None or any(
                fragment in key for fragment in AGGREGATE_KEY_FRAGMENTS
            ), f"{path} is a number named {key!r}, which does not read as an aggregate"


def test_the_output_is_json_serialisable_because_phase_6_will_return_it(analysis):
    ranked, context, _ = analysis
    text = json.dumps(report_mod.as_dict(ranked, context), sort_keys=True)
    assert '"findings"' in text
    assert len(json.loads(text)["findings"]) == len(FIELDS)


def test_every_finding_declares_whether_its_zero_is_measured_or_structural(analysis):
    """`basis` is this module's availability companion and it is never absent."""
    ranked, context, _ = analysis
    for finding in report_mod.as_dict(ranked, context)["findings"]:
        assert finding["basis"] in (BASIS_MEASURED_SKIPS, BASIS_NO_RULE_READS_IT)
        if finding["basis"] == BASIS_NO_RULE_READS_IT:
            assert finding["measured"]["unrealised_weight"] == 0
            assert finding["zero_reason"], finding["field"]
            assert finding["extrapolated"] is None
            assert finding["severity_band_effect"] is None
            assert finding["rank"] is None
            assert finding["rank_note"]
        else:
            assert finding["measured"]["unrealised_weight"] > 0
            assert finding["zero_reason"] is None
            assert finding["extrapolated"]["additional_fires_total"] > 0


# ---------------------------------------------------------------------------
# Ranking - one criterion, ties reported as ties
# ---------------------------------------------------------------------------


def test_the_ranking_is_the_criterion_and_nothing_else(analysis):
    ranked, _, _ = analysis
    ordered = [entry for entry in ranked if entry.position is not None]
    assert [entry.key for entry in ordered] == [EXPENDITURE, IMAGE_SCOPE]
    assert [entry.position for entry in ordered] == [1, 2]
    weights = [rank_mod.criterion(entry.measurement) for entry in ordered]
    assert weights == sorted(weights, reverse=True)


def test_the_seven_that_tie_at_zero_are_reported_as_tied_not_ordered(analysis):
    ranked, _, _ = analysis
    tied = [entry for entry in ranked if entry.position is None]
    assert len(tied) == 7
    assert all(entry.note == rank_mod.TIE_NOTE_NO_RULE for entry in tied)
    # Declaration order, which is DATA-PROFILE section 8's order. Not a ranking.
    declared = [entry.key for entry in FIELDS if entry.basis == BASIS_NO_RULE_READS_IT]
    assert [entry.key for entry in tied] == declared


def test_a_tie_above_zero_would_also_be_reported_as_a_tie():
    """The tie handling is not a special case for zero, and this proves it.

    Built from stand-in measurements rather than from the corpus, because the
    corpus happens to contain no tie above zero and a behaviour nothing
    exercises is the declared-but-never-computed defect invariant 3 exists to
    prevent.
    """

    class Stub:
        def __init__(self, key, weight):
            self.field = type("F", (), {"key": key})()
            self.unrealised_weight = weight

    ranked = rank_mod.rank([Stub("a", 10), Stub("b", 10), Stub("c", 4)])
    positions = {entry.measurement.field.key: entry.position for entry in ranked}
    assert positions == {"a": None, "b": None, "c": 2}
    assert all(
        entry.note == rank_mod.TIE_NOTE_EQUAL
        for entry in ranked
        if entry.measurement.field.key in ("a", "b")
    )


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_two_runs_produce_a_byte_identical_document(db_session):
    """Read-only analysis over stored rows, so a second run must not differ.

    The one thing that could have broken this is a timestamp, and there is
    none: every date in the document is `DATA_AS_OF`, the corpus as-of date
    (`app.constants`), never a wall clock.
    """
    first = report_mod.render_markdown(*run_mod.analyse(db_session)[:2])
    second = report_mod.render_markdown(*run_mod.analyse(db_session)[:2])
    assert first == second
    assert first.encode("utf-8") == second.encode("utf-8")


def test_the_committed_document_matches_what_the_code_generates_today(analysis):
    """The report in `docs/reports/` is generated output, not a hand-written page.

    If this fails, somebody edited the document instead of the code that writes
    it, and the next run would silently discard their edit. The fix is to
    change the generator and re-run, never to patch the markdown.
    """
    ranked, context, _ = analysis
    generated = report_mod.render_markdown(ranked, context)
    committed = run_mod.REPORT_PATH.read_text(encoding="utf-8")
    assert generated == committed


def test_storing_twice_rebuilds_rather_than_doubling(analysis, tmp_path):
    """`ablation_findings` is a derived cache, rebuilt the way `ml_findings` is."""
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import sessionmaker

    from app import models  # noqa: F401 - registers the tables on Base
    from app.db import Base
    from app.models import AblationFinding

    ranked, context, _ = analysis
    engine = create_engine(f"sqlite:///{tmp_path / 'scratch.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        rows = run_mod.rows_for(ranked, context)
        assert run_mod.store(session, rows) == len(FIELDS)
        assert run_mod.store(session, rows) == len(FIELDS)
        assert session.scalar(select(func.count()).select_from(AblationFinding)) == len(FIELDS)

        stored = session.scalars(
            select(AblationFinding).order_by(AblationFinding.field_key)
        ).all()
        by_key = {row.field_key: row for row in stored}
        assert by_key[EXPENDITURE].rank == 1
        assert by_key[EXPENDITURE].unrealised_weight == 1_177_450
        assert by_key[EXPENDITURE].band_change_ceiling == 9_271
        # `rank` and `extrapolation_json` are null exactly when no rule reads
        # the field, and `basis` is what records why - see models.py.
        assert by_key["tender_records"].rank is None
        assert by_key["tender_records"].extrapolation_json is None
        assert by_key["tender_records"].basis == BASIS_NO_RULE_READS_IT
        assert by_key["tender_records"].rank_note
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Unit tests - the branches the corpus does not reach
# ---------------------------------------------------------------------------


def _record(work_pk, score, severity, hits, payments=0, completion=False):
    return WorkRecord(
        work_pk=work_pk,
        raw_score=score,
        score=score,
        severity=severity,
        hits=tuple(hits),
        payment_count=payments,
        has_completion_date=completion,
    )


def _skip(rule_id, weight):
    return RuleTrace(rule_id, RULE_STATUS_SKIPPED, weight, Availability.NOT_PUBLISHED.value)


def test_a_field_declaring_neither_an_attribution_nor_a_reason_is_refused():
    with pytest.raises(ValueError, match="attribution or a zero_reason"):
        fields_mod.AblationField(
            key="x", label="X", gap_kind=fields_mod.GAP_NEVER_COLLECTED,
            source="test", publish_as="", reads_as="",
        )


def test_a_field_declaring_both_is_also_refused():
    with pytest.raises(ValueError, match="attribution or a zero_reason"):
        fields_mod.AblationField(
            key="x", label="X", gap_kind=fields_mod.GAP_NEVER_COLLECTED,
            source="test", publish_as="", reads_as="",
            attribution=Attribution(("a",), Availability.NOT_PUBLISHED.value,
                                    CONDITION_NO_PAYMENT_ROW),
            zero_reason="both",
        )


def test_an_attribution_cannot_invent_its_own_condition():
    with pytest.raises(ValueError, match="unknown attribution condition"):
        Attribution(("a",), Availability.NOT_PUBLISHED.value, "looks_suspicious")


def test_the_condition_vocabulary_is_evaluated_in_exactly_one_place():
    paid = _record(1, 0, "LOW", [], payments=2, completion=True)
    unpaid = _record(2, 0, "LOW", [], payments=0, completion=False)
    assert not measure_mod.satisfies(paid, CONDITION_NO_PAYMENT_ROW)
    assert measure_mod.satisfies(unpaid, CONDITION_NO_PAYMENT_ROW)
    assert not measure_mod.satisfies(paid, CONDITION_NO_COMPLETION_ROW)
    assert measure_mod.satisfies(unpaid, CONDITION_NO_COMPLETION_ROW)
    with pytest.raises(ValueError, match="unknown attribution condition"):
        measure_mod.satisfies(paid, "vibes")


def test_a_skip_with_the_right_rule_but_the_wrong_reason_is_not_attributed():
    """`published_zero` is a fact about the row, not a gap in MoSPI's export.

    `utilisation_shortfall` skips with `published_zero` when the sanctioned
    amount was published AS zero. Zero such works exist on this corpus, so the
    branch is exercised here rather than by the corpus - a branch nothing
    exercises is the defect CLAUDE.md invariant 3 exists to prevent.
    """
    entry = fields_mod.field_for(EXPENDITURE)
    rulebook = {"rules": [{"id": "utilisation_shortfall", "weight": 22}]}
    records = [
        _record(
            1, 0, "LOW",
            [RuleTrace("utilisation_shortfall", RULE_STATUS_SKIPPED, 22,
                       Availability.PUBLISHED_ZERO.value)],
            payments=0,
        )
    ]
    assert measure_mod.attribute(entry, records, rulebook)[0].skips == 0
    assert measure_mod.works_affected(entry, records) == 0


def test_a_rule_that_is_never_evaluable_extrapolates_to_no_fires():
    """A rate over an empty population is zero, not a division by zero.

    No rule on this corpus is in that state. The branch exists because a later
    download could produce one, and a crash in the report generator would be a
    worse answer than an honest zero.
    """
    entry = fields_mod.field_for(EXPENDITURE)
    rulebook = {"rules": [{"id": "stalled_work", "weight": 16}]}
    records = [_record(index, 0, "LOW", [_skip("stalled_work", 16)]) for index in range(5)]
    attribution = measure_mod.attribute(entry, records, rulebook)[0]
    assert attribution.evaluable == 0
    assert attribution.firing_rate == 0.0
    assert attribution.extrapolated_fires == 0


def test_a_case_already_high_absorbs_fires_and_never_crosses():
    """There is no band above HIGH, so a HIGH case is pure absorbing capacity."""
    weights = [22, 16]
    assert measure_mod._max_fires_without_crossing(weights, 50) == 2
    assert measure_mod._min_fires_to_cross(weights, 50) is None
    assert measure_mod._min_fires_to_cross(weights, 22) == 1
    assert measure_mod._min_fires_to_cross(weights, 30) == 2
    assert measure_mod._max_fires_without_crossing(weights, 16) == 0


def test_the_floor_rises_above_zero_when_the_population_cannot_absorb_the_fires():
    """Constructed, because this corpus never reaches it - and it could.

    Every affected case here sits one point below the MEDIUM edge with a single
    22-point rule skipped, so every fire that lands anywhere crosses a case.
    The floor must then be the number of fires that cannot be placed safely,
    not a reflexive zero.
    """
    entry = fields_mod.field_for(IMAGE_SCOPE)
    rulebook = {"rules": [{"id": "asset_evidence_missing", "weight": 10}]}
    records = [
        _record(index, 49, "LOW",
                [RuleTrace("asset_evidence_missing", RULE_STATUS_SKIPPED, 10,
                           Availability.NOT_PUBLISHED.value)])
        for index in range(10)
    ]
    # Ten evaluable works, all firing, so the rate is 1.0 and every skip
    # extrapolates to a fire.
    records += [
        _record(100 + index, 0, "LOW",
                [RuleTrace("asset_evidence_missing", RULE_STATUS_FIRED, 10, None)],
                completion=True)
        for index in range(10)
    ]
    attributions = measure_mod.attribute(entry, records, rulebook)
    band = measure_mod.band_change_range(entry, records, rulebook, attributions)
    assert band.extrapolated_fires == 10
    assert band.absorb_capacity == 0
    assert band.floor == 10
    assert band.ceiling == 10


def test_coverage_of_a_case_with_no_skips_is_a_hundred():
    record = _record(1, 0, "LOW", [RuleTrace("r", RULE_STATUS_PASSED, 22, None)])
    assert measure_mod._coverage_of(record, 144, 0) == 100
