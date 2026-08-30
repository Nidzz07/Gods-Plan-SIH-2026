"""The measurement. Structural, and with no fabricated value anywhere in it.

**The one rule this module exists to obey.** For a field MoSPI does not
publish, this module does NOT invent, impute or simulate a value and re-score
a work as if the field were present. Not for one work, not for a sample, not
"for illustration". A score derived from a value nobody published is a
fabricated score, and this project has already rejected one: fixture C was
corrected FROM 42 TO 20 because reaching 42 would have meant giving a
labelled synthetic control a fabricated corpus around it - sibling works to be
similar to, a second vendor to be concentrated against, an allocation to be a
fraction of - for the sole purpose of landing a target number
(`docs/contract/fixtures.md`, standing caveats 7 and 9). This phase is the
place in the build where that pressure is highest, because its entire premise
is "what if a field existed that does not". So it measures structurally
instead.

**What is measured, and what is extrapolated - the line, drawn once.**

MEASURED, exactly, from facts already recorded in the corpus and the trace:

    (a) which rules skip because of this field's absence, counted by applying
        the field's declared `Attribution` against the `skip_reason` values
        `engine/derive.py`'s Availability companions actually produced. Not an
        estimate and not a proportion - a count of trace rows.
    (b) the rulebook WEIGHT those skips leave unrealised, summed over the
        corpus.
    (c) the number of distinct WORKS carrying at least one such skip.
    (d) the corpus-wide mean `coverage_pct` as it stands, and as it would
        stand if those specific skips became EVALUABLE - not fired, evaluable.
        Both figures come from `engine.score.coverage_pct`, the same function
        the case body uses, called with the attributable weight removed from
        the skipped total. This module does not carry its own coverage
        formula, because two coverage formulas would eventually disagree.

EXTRAPOLATED, and labelled as such wherever it appears:

    (e) how many ADDITIONAL rule fires there would be, if a newly evaluable
        rule fired at the same rate it fires today among the works where it IS
        evaluable. The rate is real - `fired / (fired + passed)`, measured over
        a named population. Multiplying a real rate by a real count is an
        extrapolation a reader can check and disagree with.

REFUSED, and this is the important half:

    Deciding WHICH works those extrapolated fires land on. That step would
    assign a hypothetical outcome to a specific work, which is the fabrication
    the method exists to prevent. So the severity-band effect is reported as a
    RANGE and never as a number:

        floor    0, when the affected population can absorb every extrapolated
                 fire without any case crossing a band edge. Checked, not
                 assumed: `_absorb_capacity` counts how many fires can be
                 placed on works that would still not cross, and the floor is
                 0 exactly when that capacity covers the extrapolated total.
        ceiling  the largest number of cases that COULD cross, given the
                 extrapolated fire budget. Computed by taking, for each work,
                 the minimum number of its newly evaluable rules that would
                 have to fire together to carry it over the next band edge,
                 sorting the corpus by that number, and paying for as many
                 works as the budget allows. Per-rule budgets are relaxed into
                 one total, which can only allow MORE works, so the result is
                 an upper bound rather than a construction.

    Between those two endpoints this module says nothing, because the
    measurement does not license anything. A point estimate in the middle
    would be a guess wearing a decimal point.

**A second refusal, worth stating.** The ceiling holds the corroboration bonus
at its measured value. Re-resolving the bonus would mean deciding which cases
became HIGH, which agencies then cleared three HIGH peers, and which further
cases therefore gained ten points - a cascade that begins by assigning outcomes
to named works. The ceiling is therefore an undercount in that one respect, and
saying so is cheaper than fabricating the cascade.

**Nothing here can move a score.** This module imports `engine.score` for
`coverage_pct` and for the band cut-offs and reads them; it never calls
`compute`, never writes a `rule_hits` row and is never imported by anything
under `engine/` or `ml/` (`tests/test_ml_boundary.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field

from ..constants import (
    RULE_STATUS_FIRED,
    RULE_STATUS_PASSED,
    RULE_STATUS_SKIPPED,
    SCORE_CAP,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from ..engine.rulebook import severity_bands, weight_total
from ..engine.score import coverage_pct
from .fields import (
    CONDITION_NO_COMPLETION_ROW,
    CONDITION_NO_PAYMENT_ROW,
    AblationField,
)


# --------------------------------------------------------------------------
# The corpus as this module needs to see it
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleTrace:
    """One row of one case's reasoning trace, as the engine produced it."""

    rule_id: str
    status: str
    weight: int
    skip_reason: str | None = None


@dataclass(frozen=True)
class WorkRecord:
    """One scored work, reduced to what the measurement reads.

    Built by `run.py` from `engine.score.compute`'s own output plus two raw
    facts off the corpus. Kept as a plain frozen dataclass so every function
    below is testable with a handful of hand-written records and no database -
    the same separation `tests/conftest.py` already draws between corpus tests
    and unit tests.

    `payment_count` and `has_completion_date` are the only two per-work facts
    an attribution condition may read. Both are published facts about the row,
    not derivations: `payment_count` is never None because zero payments is a
    real zero (DOMAIN-MODEL.md section f), and `has_completion_date` is the
    presence of a completion row carrying a date.
    """

    work_pk: int
    raw_score: int
    score: int
    severity: str
    hits: tuple
    payment_count: int
    has_completion_date: bool
    is_synthetic: bool = False

    def skipped_weight(self) -> int:
        return sum(h.weight for h in self.hits if h.status == RULE_STATUS_SKIPPED)


def satisfies(record: WorkRecord, condition: str) -> bool:
    """Evaluate one attribution condition against one work. No other place does.

    Both conditions read a published fact off the row rather than a judgement,
    which is what lets `tests/test_ablation.py` assert the attribution holds in
    both directions: every skip the condition selects is a skip the engine
    recorded for that reason, and every such skip is selected.
    """
    if condition == CONDITION_NO_PAYMENT_ROW:
        return record.payment_count == 0
    if condition == CONDITION_NO_COMPLETION_ROW:
        return not record.has_completion_date
    raise ValueError(f"unknown attribution condition {condition!r}")


# --------------------------------------------------------------------------
# (a) (b) (c) - the exact counts
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleAttribution:
    """One rule's share of one field's gap. Every number here is a count."""

    rule_id: str
    weight: int
    # Trace rows the engine recorded as skipped, for this reason, on works
    # meeting the condition.
    skips: int
    # Where the rule CAN be read today.
    evaluable: int
    fired: int
    passed: int

    @property
    def unrealised_weight(self) -> int:
        return self.skips * self.weight

    @property
    def firing_rate(self) -> float:
        """`fired / (fired + passed)`, over the population that can be read.

        The denominator is deliberately the evaluable population and not the
        corpus: a rate over the corpus would divide by works the rule was never
        able to look at, which is the arithmetic invariant 2 exists to prevent
        at the case level and the same mistake one level up.
        """
        return self.fired / self.evaluable if self.evaluable else 0.0

    @property
    def extrapolated_fires(self) -> int:
        """The rate, times the skips. An extrapolation, labelled everywhere."""
        return round(self.firing_rate * self.skips)


def attribute(entry: AblationField, records, rulebook) -> tuple:
    """(a) and (b): the rule-by-rule trace of one field's gap.

    Returns an empty tuple for a field with no attribution - the seven whose
    absence skips nothing today because no rule reads them. That empty tuple is
    a measurement, not a missing measurement, and `fields.AblationField.basis`
    is what records which of the two it is.
    """
    if entry.attribution is None:
        return ()

    weights = {rule["id"]: rule["weight"] for rule in rulebook.get("rules") or []}
    counters = {
        rule_id: {"skips": 0, "fired": 0, "passed": 0}
        for rule_id in entry.attribution.rule_ids
    }
    for record in records:
        matches = satisfies(record, entry.attribution.condition)
        for hit in record.hits:
            counter = counters.get(hit.rule_id)
            if counter is None:
                continue
            if hit.status == RULE_STATUS_FIRED:
                counter["fired"] += 1
            elif hit.status == RULE_STATUS_PASSED:
                counter["passed"] += 1
            elif (
                hit.status == RULE_STATUS_SKIPPED
                and hit.skip_reason == entry.attribution.skip_reason
                and matches
            ):
                counter["skips"] += 1

    return tuple(
        RuleAttribution(
            rule_id=rule_id,
            weight=weights.get(rule_id, 0),
            skips=counter["skips"],
            evaluable=counter["fired"] + counter["passed"],
            fired=counter["fired"],
            passed=counter["passed"],
        )
        for rule_id, counter in counters.items()
    )


def works_affected(entry: AblationField, records) -> int:
    """(c): distinct works carrying at least one skip attributable to the field."""
    if entry.attribution is None:
        return 0
    reason = entry.attribution.skip_reason
    rule_ids = set(entry.attribution.rule_ids)
    return sum(
        1
        for record in records
        if satisfies(record, entry.attribution.condition)
        and any(
            hit.rule_id in rule_ids
            and hit.status == RULE_STATUS_SKIPPED
            and hit.skip_reason == reason
            for hit in record.hits
        )
    )


def attributable_weight_on(entry: AblationField, record: WorkRecord) -> int:
    """The weight this ONE work loses to this field. Used only inside (d) and (e)."""
    if entry.attribution is None or not satisfies(record, entry.attribution.condition):
        return 0
    reason = entry.attribution.skip_reason
    rule_ids = set(entry.attribution.rule_ids)
    return sum(
        hit.weight
        for hit in record.hits
        if hit.rule_id in rule_ids
        and hit.status == RULE_STATUS_SKIPPED
        and hit.skip_reason == reason
    )


# --------------------------------------------------------------------------
# (d) - coverage, through score.py's own formula
# --------------------------------------------------------------------------


def mean_coverage(records, total_weight: int) -> float:
    """Corpus mean `coverage_pct`, as the engine computes it per case.

    Calls `engine.score.coverage_pct` rather than restating
    `(144 - skipped) / 144`, so a change to the coverage rule moves this
    module with it instead of leaving two formulas to drift apart.
    """
    if not records:
        return 0.0
    values = [_coverage_of(record, total_weight, 0) for record in records]
    return sum(values) / len(values)


def mean_coverage_if_published(entry: AblationField, records, total_weight: int) -> float:
    """The same mean, with this field's skips treated as EVALUABLE, not fired.

    The distinction matters and the report repeats it: making a rule evaluable
    raises coverage whether the rule then fires or passes. Coverage measures
    what could be checked, not what was found.
    """
    if not records:
        return 0.0
    values = [
        _coverage_of(record, total_weight, attributable_weight_on(entry, record))
        for record in records
    ]
    return sum(values) / len(values)


def _coverage_of(record: WorkRecord, total_weight: int, recovered: int) -> int:
    """One work's coverage with `recovered` points of its skipped weight restored.

    Built by handing `engine.score.coverage_pct` a trace whose recovered rows
    are no longer skipped. The rows are rebuilt rather than mutated so the
    engine's own output is never touched by this package.
    """
    remaining = record.skipped_weight() - recovered
    hits = [{"weight": remaining, "status": RULE_STATUS_SKIPPED}] if remaining else []
    return coverage_pct(hits or [{"weight": 0, "status": RULE_STATUS_PASSED}], total_weight)


# --------------------------------------------------------------------------
# (e) - the bounded range, and the two things it refuses to do
# --------------------------------------------------------------------------


def _band_gap(record: WorkRecord, high: int, medium: int) -> int | None:
    """Points this case needs to reach the next band. None when already HIGH."""
    if record.severity == SEVERITY_HIGH:
        return None
    edge = high if record.severity == SEVERITY_MEDIUM else medium
    return max(edge - record.score, 0)


def _min_fires_to_cross(weights, gap: int) -> int | None:
    """Fewest of these rules that must fire TOGETHER to carry the case over.

    Greedy on the heaviest first, which is exact for a "smallest count whose
    sum clears a target" question: if k of them can clear the gap at all, the k
    heaviest clear it.
    """
    running = 0
    for index, weight in enumerate(sorted(weights, reverse=True), start=1):
        running += weight
        if running >= gap:
            return index
    return None


def _max_fires_without_crossing(weights, gap: int) -> int:
    """Most of these rules that can fire on this case and still not cross.

    Lightest first, for the mirror-image reason: if any k of them stay under
    the gap, the k lightest do.
    """
    running = 0
    absorbed = 0
    for weight in sorted(weights):
        if running + weight >= gap:
            break
        running += weight
        absorbed += 1
    return absorbed


@dataclass(frozen=True)
class BandRange:
    """The bounded severity-band effect. Two integers and their method.

    Carries no per-work anything. `tests/test_ablation.py` asserts that on the
    shape of this object and on the report dict built from it, because the
    output shape is where a fabricated per-work outcome would have to surface
    in order to reach a screen.
    """

    floor: int
    ceiling: int
    extrapolated_fires: int
    absorb_capacity: int
    crossable_works: int
    method: str

    def as_dict(self) -> dict:
        return {
            "floor": self.floor,
            "ceiling": self.ceiling,
            "extrapolated_fires": self.extrapolated_fires,
            "absorb_capacity": self.absorb_capacity,
            "crossable_works": self.crossable_works,
            "method": self.method,
        }


BAND_RANGE_METHOD = (
    "Floor and ceiling only. The extrapolated fire count is corpus-level; deciding which "
    "works those fires land on would assign a hypothetical outcome to a named work, which "
    "this module refuses to do. The floor is 0 when the affected population can absorb "
    "every extrapolated fire without any case crossing a band edge, which is checked "
    "rather than assumed. The ceiling relaxes the per-rule budgets into one total, so it "
    "is an upper bound and not a construction. Both hold the corroboration bonus at its "
    "measured value: re-resolving it would mean deciding which cases became HIGH."
)


def band_change_range(entry: AblationField, records, rulebook, attributions) -> BandRange:
    """(e): how many cases could change band. A range, never a point.

    The budget is the sum of the per-rule extrapolated fire counts, each of
    which is a real observed firing rate times a real skip count.
    """
    high, medium = severity_bands(rulebook)
    budget = sum(attribution.extrapolated_fires for attribution in attributions)

    needed = []
    capacity = 0
    for record in records:
        weights = _attributable_weights(entry, record)
        if not weights:
            continue
        gap = _band_gap(record, high, medium)
        if gap is None:
            # Already HIGH. Every fire it takes is absorbed, because there is
            # no band above it to cross into.
            capacity += len(weights)
            continue
        capacity += _max_fires_without_crossing(weights, gap)
        fires = _min_fires_to_cross(weights, min(gap, SCORE_CAP))
        if fires is not None:
            needed.append(fires)

    needed.sort()
    spent = 0
    ceiling = 0
    for fires in needed:
        if spent + fires > budget:
            break
        spent += fires
        ceiling += 1

    return BandRange(
        floor=0 if capacity >= budget else budget - capacity,
        ceiling=ceiling,
        extrapolated_fires=budget,
        absorb_capacity=capacity,
        crossable_works=len(needed),
        method=BAND_RANGE_METHOD,
    )


def _attributable_weights(entry: AblationField, record: WorkRecord) -> list:
    if entry.attribution is None or not satisfies(record, entry.attribution.condition):
        return []
    reason = entry.attribution.skip_reason
    rule_ids = set(entry.attribution.rule_ids)
    return [
        hit.weight
        for hit in record.hits
        if hit.rule_id in rule_ids
        and hit.status == RULE_STATUS_SKIPPED
        and hit.skip_reason == reason
    ]


# --------------------------------------------------------------------------
# One field's whole measurement
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldMeasurement:
    """Everything measured about one field. Corpus-level aggregates only."""

    field: AblationField
    corpus_works: int
    rule_weight_total: int
    attributions: tuple
    works_affected: int
    coverage_now: float
    coverage_if_published: float
    band_range: BandRange
    corroborating: tuple = dataclass_field(default_factory=tuple)

    @property
    def rule_skips(self) -> int:
        return sum(attribution.skips for attribution in self.attributions)

    @property
    def unrealised_weight(self) -> int:
        return sum(attribution.unrealised_weight for attribution in self.attributions)

    @property
    def coverage_uplift(self) -> float:
        return self.coverage_if_published - self.coverage_now

    @property
    def coverage_uplift_unrounded(self) -> float:
        """The same uplift straight from the weights, before per-case rounding.

        `engine.score.coverage_pct` rounds each case to a whole percent, so the
        mean of the rounded figures differs slightly from
        `unrealised_weight / (rule_weight_total * corpus_works)`. Both are
        reported: the first is what an officer reads on a case, the second is
        what the arithmetic says, and the gap between them is rounding and
        nothing else.
        """
        denominator = self.rule_weight_total * self.corpus_works
        return self.unrealised_weight / denominator * 100 if denominator else 0.0


def measure_field(entry: AblationField, records, rulebook, corroborating=None) -> FieldMeasurement:
    """Measure one field against the scored corpus."""
    total_weight = weight_total(rulebook)
    attributions = attribute(entry, records, rulebook)
    return FieldMeasurement(
        field=entry,
        corpus_works=len(records),
        rule_weight_total=total_weight,
        attributions=attributions,
        works_affected=works_affected(entry, records),
        coverage_now=mean_coverage(records, total_weight),
        coverage_if_published=mean_coverage_if_published(entry, records, total_weight),
        band_range=band_change_range(entry, records, rulebook, attributions),
        corroborating=tuple(corroborating or ()),
    )


def measure_all(entries, records, rulebook, corroborating_by_field=None) -> tuple:
    """Measure every field. Order follows `fields.FIELDS`, never a score."""
    corroborating_by_field = corroborating_by_field or {}
    return tuple(
        measure_field(entry, records, rulebook, corroborating_by_field.get(entry.key))
        for entry in entries
    )


def band_counts(records) -> dict:
    """Severity bands as they stand. Context for the report, not a criterion."""
    counts = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 0, SEVERITY_LOW: 0}
    for record in records:
        counts[record.severity] = counts.get(record.severity, 0) + 1
    return counts
