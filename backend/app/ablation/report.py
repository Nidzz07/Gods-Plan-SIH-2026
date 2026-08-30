"""The output, in two forms: a dict for the API and a document for MoSPI.

`as_dict` is the shape `GET /api/ablation` will return in Phase 6, and it is
the shape `tests/test_ablation.py` asserts over: **corpus-level aggregates and
bounded ranges only, never a per-work hypothetical.** There is no work id, no
case id and no per-work container anywhere in it, and that is enforced by a
test rather than promised by this sentence.

`render_markdown` writes the same content as a document addressed to MoSPI's
Data Informatics and Innovation Division. Its register is the one
`DATA-PROFILE.md` and `docs/contract/fixtures.md` already use: findings are
stated as measurements with their method shown and their population named, a
figure that was extrapolated says so on the same line, and nothing is described
as fraud, as certain, or as a national total. NIGRANI is asking a ministry to
publish a field; it is not accusing anyone of anything, and a document that
overclaimed would be the wrong thing to hand a ministry even if every number in
it were right.

**The document is generated, never hand-written**, so it can be regenerated
after any fresh download rather than going stale beside a corpus it no longer
describes - the same standing `DATA-PROFILE.md` has. It carries the corpus
as-of date rather than a wall-clock timestamp, so two runs over the same corpus
produce byte-identical output (`run.py`, and a test asserts it).
"""

from __future__ import annotations

from ..constants import DATA_AS_OF
from .fields import (
    BASIS_MEASURED_SKIPS,
    GAP_NEVER_COLLECTED,
    GAP_PUBLISHED_INCOMPLETELY,
    SOURCE_SURFACED_BY_MEASUREMENT,
)
from .rank import RANKING_CRITERION, RANKING_CRITERION_DETAIL

TITLE = "NIGRANI data-gap measurement and reporting recommendation"
ADDRESSEE = "Ministry of Statistics and Programme Implementation - Data Informatics and Innovation Division"

METHOD = {
    "summary": (
        "For each field, measure what its absence costs the rulebook that exists today, "
        "using only facts already recorded in the corpus and in the reasoning trace."
    ),
    "measured": [
        "Which rules skip because the field is absent, counted from the skip reasons the "
        "engine recorded, on works meeting a stated condition read straight off the row.",
        "The rulebook weight those skips leave unrealised, summed over the corpus.",
        "The number of distinct works carrying at least one such skip.",
        "The corpus mean coverage as it stands and as it would stand if those skips became "
        "evaluable - evaluable, not fired. Both come from the same coverage function the "
        "case body uses.",
    ],
    "extrapolated": [
        "How many additional rule fires there would be, if a newly evaluable rule fired at "
        "the rate it fires today among the works where it IS evaluable. The rate is "
        "measured over a named population; multiplying it by a measured skip count is an "
        "extrapolation a reader can check.",
    ],
    "refused": [
        "No value is invented, imputed or simulated for a field MoSPI does not publish, "
        "and no work is re-scored as if the field were present. A score derived from a "
        "value nobody published would be a fabricated score.",
        "The extrapolated fire counts are never allocated to specific works, so the "
        "severity-band effect is reported as a floor and a ceiling and never as a point "
        "estimate. Between the two endpoints the measurement licenses nothing.",
        "The corroboration bonus is held at its measured value inside the ceiling, because "
        "re-resolving it would mean deciding which cases became HIGH.",
    ],
}


def as_dict(ranked, context) -> dict:
    """The structured shape. Phase 6 returns this from `GET /api/ablation`."""
    return {
        "title": TITLE,
        "addressed_to": ADDRESSEE,
        "corpus": dict(context),
        "method": METHOD,
        "ranking": {
            "criterion": RANKING_CRITERION,
            "detail": RANKING_CRITERION_DETAIL,
            "ranked_fields": sum(1 for entry in ranked if entry.position is not None),
            "unranked_fields": sum(1 for entry in ranked if entry.position is None),
        },
        "findings": [_finding(entry) for entry in ranked],
    }


def _finding(entry) -> dict:
    measurement = entry.measurement
    field = measurement.field
    attributed = field.basis == BASIS_MEASURED_SKIPS
    return {
        "field": field.key,
        "label": field.label,
        "gap_kind": field.gap_kind,
        "source": field.source,
        "basis": field.basis,
        "rank": entry.position,
        "rank_note": entry.note,
        "publish_as": field.publish_as,
        "reads_as": field.reads_as,
        "effort": field.effort,
        "unlocks_rules": list(field.unlocks_rules),
        "improves_rules": list(field.improves_rules),
        "zero_reason": field.zero_reason or None,
        "measured": {
            "rule_skips": measurement.rule_skips,
            "works_affected": measurement.works_affected,
            "unrealised_weight": measurement.unrealised_weight,
            "coverage_pct_now": round(measurement.coverage_now, 2),
            "coverage_pct_if_published": round(measurement.coverage_if_published, 2),
            "coverage_uplift_pct": round(measurement.coverage_uplift, 2),
            "coverage_uplift_pct_unrounded": round(measurement.coverage_uplift_unrounded, 2),
            "per_rule": [
                {
                    "rule_id": attribution.rule_id,
                    "weight": attribution.weight,
                    "skips": attribution.skips,
                    "unrealised_weight": attribution.unrealised_weight,
                    "evaluable_today": attribution.evaluable,
                    "fired_today": attribution.fired,
                    "passed_today": attribution.passed,
                }
                for attribution in measurement.attributions
            ],
        },
        "extrapolated": (
            {
                "basis": "observed firing rate on the population where the rule is evaluable",
                "additional_fires_total": measurement.band_range.extrapolated_fires,
                "per_rule": [
                    {
                        "rule_id": attribution.rule_id,
                        "observed_firing_rate_pct": round(attribution.firing_rate * 100, 3),
                        "measured_over_works": attribution.evaluable,
                        "applied_to_skips": attribution.skips,
                        "additional_fires": attribution.extrapolated_fires,
                    }
                    for attribution in measurement.attributions
                ],
            }
            if attributed
            else None
        ),
        "severity_band_effect": measurement.band_range.as_dict() if attributed else None,
        "corroborating": [
            {"label": label, "value": value} for label, value in measurement.corroborating
        ],
    }


# --------------------------------------------------------------------------
# The document
# --------------------------------------------------------------------------


def render_markdown(ranked, context) -> str:
    """The recommendation, as a document. Deterministic over a fixed corpus."""
    lines = []
    write = lines.append

    write(f"# {TITLE}")
    write("")
    write(f"**To:** {ADDRESSEE}")
    write("**From:** NIGRANI, team ExploreeTinkerBell - Smart India Hackathon, PS 26102")
    write(f"**Measured against:** the committed MPLADS corpus as of {DATA_AS_OF.isoformat()}")
    write("")
    write(
        "> This document is generated by `python -m app.ablation.run` from the ingested "
        "corpus. It is not written by hand and it is not written by a language model. "
        "Regenerate it after any fresh download; a recommendation that describes a "
        "different download is worse than none."
    )
    write("")
    _write_standing(write, context)
    _write_method(write)
    _write_headline(write, ranked, context)
    _write_table(write, ranked)
    _write_findings(write, ranked)
    _write_limits(write, context)
    return "\n".join(lines) + "\n"


def _write_standing(write, context) -> None:
    write("---")
    write("")
    write("## What this is, and what it is not")
    write("")
    write(
        "NIGRANI evaluates each sanctioned MPLADS work against a versioned rulebook of "
        f"ten rules carrying {context['rule_weight_total']} points of weight. A rule it "
        "cannot evaluate is recorded as **skipped**, with the reason it could not be "
        "evaluated, and its weight is never redistributed to the rules that did run. The "
        "share of rulebook weight a case could actually be checked against is its "
        "**coverage**."
    )
    write("")
    write(
        f"On the {context['corpus_works']:,} sanctioned works in this corpus, mean coverage "
        f"is **{context['mean_coverage_pct']:.1f}%**. A little under three-fifths of the "
        "rulebook can be run on the average published work. This document measures where "
        "the other two-fifths went, and what MoSPI would have to publish to get it back."
    )
    write("")
    write(
        "**Nothing here is an allegation.** Every figure is a count of rules NIGRANI could "
        "or could not evaluate. A skipped rule is not a finding against a work, an agency "
        "or a member; it is a statement about what the published record does not say."
    )
    write("")


def _write_method(write) -> None:
    write("## Method")
    write("")
    write(METHOD["summary"])
    write("")
    write("**Measured exactly, from the recorded trace:**")
    write("")
    for item in METHOD["measured"]:
        write(f"- {item}")
    write("")
    write("**Extrapolated, and labelled as such wherever it appears:**")
    write("")
    for item in METHOD["extrapolated"]:
        write(f"- {item}")
    write("")
    write("**Refused, deliberately:**")
    write("")
    for item in METHOD["refused"]:
        write(f"- {item}")
    write("")
    write(
        "The last group is the reason this document can be checked. Every number below "
        "either counts rows the engine wrote, or multiplies a stated rate by a stated "
        "count. None of them is the output of a work re-scored against a value nobody "
        "published."
    )
    write("")


def _write_headline(write, ranked, context) -> None:
    """The lead paragraph, DERIVED from the measurement rather than asserted.

    The striking sentence below - that every never-collected field costs the
    current rulebook zero - is true on this corpus and this rulebook, and it
    would stop being true the moment somebody adds a rule reading one of those
    fields. So it is written only when the measurement still supports it, and
    the alternative wording is written when it does not. A generated document
    that kept printing a claim after the claim expired would be the worst kind
    of stale figure: a confident one.
    """
    measured = [entry for entry in ranked if entry.position is not None]
    write("## The finding, in one paragraph")
    write("")
    if not measured:
        write(
            "No field measures above zero on the ranking criterion, so this document "
            "ranks nothing. Every entry below reports what its absence does and does not "
            "cost, and says so."
        )
        write("")
        return

    absent = [
        entry
        for entry in ranked
        if entry.measurement.field.gap_kind == GAP_NEVER_COLLECTED
    ]
    absent_all_zero = all(entry.measurement.unrealised_weight == 0 for entry in absent)
    incomplete_only = all(
        entry.measurement.field.gap_kind == GAP_PUBLISHED_INCOMPLETELY
        for entry in measured
    )

    if absent and absent_all_zero:
        write(
            f"**All {len(absent)} of the fields MoSPI does not collect at all cost the "
            f"current rulebook exactly zero unrealised points.** Not because their absence "
            f"does not matter, but because NIGRANI contains no rule that reads them: a "
            f"rule that could never be written cannot be skipped. They tie at zero, and "
            f"this document reports them as tied rather than inventing an order for them."
        )
        write("")

    top = measured[0].measurement
    lead = (
        "The entire **measured** detection loss in NIGRANI today comes from "
        f"{len(measured)} field{'s' if len(measured) != 1 else ''} that MoSPI "
        "**already publishes, and publishes incompletely**. "
        if incomplete_only
        else "The largest measured losses are these. "
    )
    write(
        f"{lead}The largest is **{top.field.label.lower()}**: "
        f"{top.rule_skips:,} skipped rules across {top.works_affected:,} works, "
        f"{top.unrealised_weight:,} points of rulebook weight left unrealised, and a mean "
        f"coverage over all {context['corpus_works']:,} sanctioned works that would rise "
        f"from {top.coverage_now:.1f}% to {top.coverage_if_published:.1f}% if that gap "
        f"were closed."
    )
    write("")
    if incomplete_only:
        write(
            "That is the recommendation this document leads with, and it is the cheapest "
            "one on the list: it asks MoSPI to collect nothing new."
        )
        write("")


def _write_table(write, ranked) -> None:
    write("## Ranked recommendation")
    write("")
    write(f"**Ranking criterion: {RANKING_CRITERION}.**")
    write("")
    write(RANKING_CRITERION_DETAIL)
    write("")
    write(
        "| # | Field | Gap | Rule skips | Works affected | Unrealised weight | "
        "Coverage now | If published | Uplift |"
    )
    write("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for entry in ranked:
        measurement = entry.measurement
        position = str(entry.position) if entry.position is not None else "—"
        gap = (
            "incomplete"
            if measurement.field.gap_kind == GAP_PUBLISHED_INCOMPLETELY
            else "absent"
        )
        write(
            f"| {position} | {measurement.field.label} | {gap} | "
            f"{measurement.rule_skips:,} | {measurement.works_affected:,} | "
            f"{measurement.unrealised_weight:,} | {measurement.coverage_now:.1f}% | "
            f"{measurement.coverage_if_published:.1f}% | "
            f"{measurement.coverage_uplift:+.1f} pp |"
        )
    write("")
    write(
        "Coverage figures are the corpus mean over every sanctioned work, not over the "
        "affected subset, so the uplift column reads as the whole corpus would feel it. "
        "A dash in the first column means the field is unranked: it measures zero on the "
        "criterion and the criterion does not separate it from the others that do."
    )
    write("")


def _write_findings(write, ranked) -> None:
    write("## Findings, one field at a time")
    write("")
    for index, entry in enumerate(ranked, start=1):
        measurement = entry.measurement
        field = measurement.field
        heading = f"### {index}. {field.label}"
        if entry.position is not None:
            heading += f"  ·  rank {entry.position}"
        else:
            heading += "  ·  unranked"
        write(heading)
        write("")
        write(f"*{field.reads_as}*")
        write("")
        write(f"**Publish:** {field.publish_as}")
        write("")
        write(f"**Effort:** {field.effort}")
        write("")
        if field.source == SOURCE_SURFACED_BY_MEASUREMENT:
            write(
                "> **This entry is not on `DATA-PROFILE.md` section 8's list.** It was "
                "found by running the attribution the other way round - asking which skip "
                "reasons the corpus records, and which field each one traces back to. It "
                "is reported because it is what the measurement found, not because it was "
                "expected."
            )
            write("")

        if field.basis == BASIS_MEASURED_SKIPS:
            _write_measured_field(write, measurement)
        else:
            _write_zero_field(write, entry)

        if measurement.corroborating:
            write("Corroborating figures, measured on this corpus and **not** used in the "
                  "ranking:")
            write("")
            write("| Measure | Value |")
            write("| --- | ---: |")
            for label, value in measurement.corroborating:
                rendered = f"{value:,}" if isinstance(value, int) else str(value)
                write(f"| {label} | {rendered} |")
            write("")
        write("---")
        write("")


def _write_measured_field(write, measurement) -> None:
    write("**Measured, exactly.**")
    write("")
    write("| Rule skipped | Weight | Skips | Unrealised weight | Evaluable today | Fires today |")
    write("| --- | ---: | ---: | ---: | ---: | ---: |")
    for attribution in measurement.attributions:
        write(
            f"| `{attribution.rule_id}` | {attribution.weight} | {attribution.skips:,} | "
            f"{attribution.unrealised_weight:,} | {attribution.evaluable:,} | "
            f"{attribution.fired:,} |"
        )
    write(
        f"| **total** | | **{measurement.rule_skips:,}** | "
        f"**{measurement.unrealised_weight:,}** | | |"
    )
    write("")
    write(
        f"Distinct works carrying at least one of these skips: "
        f"**{measurement.works_affected:,}** of {measurement.corpus_works:,}."
    )
    write("")
    write(
        f"Corpus mean coverage would rise from **{measurement.coverage_now:.2f}%** to "
        f"**{measurement.coverage_if_published:.2f}%** - "
        f"**{measurement.coverage_uplift:+.2f} percentage points** - if these rules became "
        f"evaluable. *Evaluable, not fired:* coverage measures what could be checked, not "
        f"what was found, so the figure holds whether the newly readable rules then fire "
        f"or pass. Straight from the weights the uplift is "
        f"{measurement.coverage_uplift_unrounded:+.2f} pp; the difference is that each "
        f"case's coverage is rounded to a whole percent before the mean is taken, and "
        f"nothing else."
    )
    write("")
    write("**Extrapolated, from a real observed firing rate.**")
    write("")
    write("| Rule | Fires today | Measured over | Rate | Applied to | Additional fires |")
    write("| --- | ---: | ---: | ---: | ---: | ---: |")
    for attribution in measurement.attributions:
        write(
            f"| `{attribution.rule_id}` | {attribution.fired:,} | "
            f"{attribution.evaluable:,} works | {attribution.firing_rate * 100:.2f}% | "
            f"{attribution.skips:,} skips | {attribution.extrapolated_fires:,} |"
        )
    write(f"| **total** | | | | | **{measurement.band_range.extrapolated_fires:,}** |")
    write("")
    write(
        "Each rate is that rule's own firing rate among the works where it can be read "
        "today. Applying it to the works where it cannot is an extrapolation, and it is "
        "the only extrapolation in this document."
    )
    write("")
    band = measurement.band_range
    write("**Severity-band effect: a range, and deliberately not a number.**")
    write("")
    write(
        f"Between **{band.floor:,}** and **{band.ceiling:,}** cases could change severity "
        f"band."
    )
    write("")
    write(
        f"The extrapolation above says how MANY rules would fire. It does not say which "
        f"works they would fire on, and deciding that would mean assigning a hypothetical "
        f"outcome to a named work - which is the one thing this measurement will not do. "
        f"So the effect is bounded instead. The floor is {band.floor:,} because the "
        f"affected population can absorb {band.absorb_capacity:,} fires without any case "
        f"crossing a band edge, against an extrapolated {band.extrapolated_fires:,}. The "
        f"ceiling of {band.ceiling:,} is the most cases that budget could carry across, "
        f"over the {band.crossable_works:,} affected cases that are close enough to an "
        f"edge to cross at all. Both endpoints hold the agency-corroboration bonus at its "
        f"measured value, so the ceiling understates by whatever that cascade would add."
    )
    write("")


def _write_zero_field(write, entry) -> None:
    measurement = entry.measurement
    field = measurement.field
    write("**Measured: zero points of currently unrealised rulebook weight.**")
    write("")
    write(field.zero_reason)
    write("")
    if field.unlocks_rules:
        rules = ", ".join(f"`{rule}`" for rule in field.unlocks_rules)
        write(
            f"Rule(s) this field would make writable, none of which exists in rulebook "
            f"v1.0.0 today: {rules}."
        )
        write("")
    if field.improves_rules:
        rules = ", ".join(f"`{rule}`" for rule in field.improves_rules)
        write(
            f"Existing rule(s) it would make better evidence without unlocking: {rules}. "
            f"That benefit is real and it is not measurable as unrealised weight, so it is "
            f"reported as zero rather than converted into a number it has not earned."
        )
        write("")
    write(f"*{entry.note}*")
    write("")


def _write_limits(write, context) -> None:
    write("## Standing limits on everything above")
    write("")
    write(
        f"1. **The corpus is a truncated portal sample**, {context['corpus_works']:,} "
        "sanctioned works out of the twelve exports committed to this repository, "
        "several of which stop at round row limits. No figure in this document is a "
        "national total and none may be presented as one."
    )
    write(
        "2. **Every figure must be re-measured after a fresh download.** The rulebook "
        "thresholds these counts depend on are calibrated against the distributions in "
        "`docs/data/DATA-PROFILE.md`, and a new download invalidates that calibration "
        "until the profile is regenerated."
    )
    write(
        "3. **`duplicate_work` is not yet calibrated.** Its similarity threshold fires on "
        "61% of the corpus, which is recorded in the profile and carried on the rule's own "
        "trace row. It does not enter the two ranked measurements, but it does appear in "
        "the corroborating figures for `work_geocoordinates`, and it should be read with "
        "that caveat attached."
    )
    write(
        "4. **The labelled synthetic control is excluded from every figure here.** One "
        "work in the corpus is injected, carries `is_synthetic = true`, and exists only "
        "because no real MPLADS row can populate the certification rung. It is excluded "
        "from every count in this document."
    )
    write(
        "5. **A skipped rule is not a finding.** Where this document says a rule could not "
        "be evaluated on a work, it is describing the published record and not the work."
    )
    write("")
    write(
        f"Rulebook `{context['rulebook_version']}`, sha256 "
        f"`{context['rulebook_sha256'][:16]}...`. Coverage arithmetic is "
        "`engine/score.py`'s own; this document does not carry a second copy of it."
    )
