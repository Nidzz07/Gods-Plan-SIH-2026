"""The fields to ablate, and what each one's absence actually costs today.

Nine entries. Seven come from `docs/data/DATA-PROFILE.md` section 8, the
profile's own table of fields the portal never publishes. The eighth is the
expenditure export's INCOMPLETENESS, which is a different kind of gap and is
labelled as one. The ninth was surfaced by the measurement itself and is
labelled as that; see below.

**Two kinds of gap, never mixed in one column.**

`never_collected`
    MoSPI publishes no such column anywhere, for any work. Closing the gap
    means the portal starts collecting and exporting something new.

`published_incompletely`
    MoSPI publishes the column, and publishes it for only part of the corpus.
    Closing the gap costs no new field and no new collection - only a complete
    export of what the districts have already filed.

**The traceability below is measured, not assumed.** Each entry declares the
`Attribution` that says which rule ids skip because of this field, under which
`skip_reason`, on which works. `measure.py` applies that declaration against
the trace the engine actually produced and `tests/test_ablation.py` asserts the
correspondence is exact in BOTH directions - every skip the declaration claims
is a skip the engine recorded, and every skip matching the condition is a skip
the declaration claims. On this corpus both directions hold with zero
mismatches for the two attributed fields.

**Seven of the nine attribute to nothing, and that is the headline finding.**
`utilisation_certificate`, `revised_cost_estimate`, `milestone_progress`,
`tender_records`, `work_geocoordinates`, `asset_photo_geotag` and
`beneficiary_counts` cost the current rulebook exactly ZERO unrealised points -
not because their absence does not matter, but because rulebook v1.0.0 contains
no rule that reads them. A rule cannot be skipped if it was never written. The
`unlocks_rules` on each of those entries names rules that DO NOT EXIST in
`rules.yaml`, and `tests/test_ablation.py` asserts they do not, which is what
makes the zero a proof rather than a claim.

That is a real distinction and the report keeps it: publishing the utilisation
certificate would not recover a single point of the 144 that are on the books
today. It would let a rule be written that is not currently writable at all.

**The ninth entry, `asset_image_publication_scope`, is not on the profile's
list.** It was found by running the attribution the other way: asking which
skip reasons the corpus actually records, and which field each traces back to.
14,104 skips of `asset_evidence_missing` trace to the `Image` column being
published only in the completed export - which is neither the geotag the
profile's list names nor the expenditure linkage, but a third gap of the
`published_incompletely` kind. It is the second-largest measured gap in the
corpus, and omitting it from a recommendation to MoSPI because it was not on a
list written before the measurement would be the wrong way round. It is
labelled `surfaced_by_measurement` so a reader can tell it apart from the
seven the profile named.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field

from ..constants import Availability

# --------------------------------------------------------------------------
# Vocabularies - closed, so a new entry cannot invent its own label
# --------------------------------------------------------------------------

GAP_NEVER_COLLECTED = "never_collected"
GAP_PUBLISHED_INCOMPLETELY = "published_incompletely"
GAP_KINDS = (GAP_NEVER_COLLECTED, GAP_PUBLISHED_INCOMPLETELY)

# Where the entry came from, so the report can say so on its face.
SOURCE_PROFILE_SECTION_8 = "DATA-PROFILE.md section 8"
SOURCE_SURFACED_BY_MEASUREMENT = "surfaced_by_measurement"

# `basis` - what kind of figure this field's measurement produced. It is the
# availability companion of this module: it records WHY `unrealised_weight` is
# zero, so a field that costs nothing today because nobody wrote the rule
# cannot be read as a field whose absence is harmless.
BASIS_MEASURED_SKIPS = "measured_skips"
BASIS_NO_RULE_READS_IT = "no_rule_reads_it"
BASES = (BASIS_MEASURED_SKIPS, BASIS_NO_RULE_READS_IT)

# The per-work conditions an attribution may name. Closed on purpose: each one
# is a fact read straight off the corpus - not a judgement, not a threshold -
# and `measure.py` is the only place they are evaluated.
CONDITION_NO_PAYMENT_ROW = "no_payment_row"
CONDITION_NO_COMPLETION_ROW = "no_completion_row"
CONDITIONS = (CONDITION_NO_PAYMENT_ROW, CONDITION_NO_COMPLETION_ROW)


@dataclass(frozen=True)
class Attribution:
    """Which rule skips trace to this field's absence, and on which works.

    `rule_ids` are rules that EXIST in `rules.yaml` today. `skip_reason` is one
    of `app.constants.SKIP_REASONS`. `condition` names the per-work fact that
    must also hold, so an attribution cannot quietly absorb a skip that arose
    for another cause - `utilisation_shortfall` also skips with
    `published_zero` when the sanctioned amount was published as zero, and that
    is a fact about the row rather than a gap in the expenditure export.
    """

    rule_ids: tuple
    skip_reason: str
    condition: str

    def __post_init__(self) -> None:
        if self.condition not in CONDITIONS:
            raise ValueError(
                f"unknown attribution condition {self.condition!r}; expected one of "
                f"{CONDITIONS}. Conditions are read straight off the corpus and the "
                "vocabulary is closed so that one cannot be invented per field."
            )
        if self.skip_reason not in [member.value for member in Availability]:
            raise ValueError(f"unknown skip reason {self.skip_reason!r}")


@dataclass(frozen=True)
class AblationField:
    """One field, what it would unlock, and how its absence is traced."""

    key: str
    label: str
    gap_kind: str
    source: str
    # What MoSPI would have to publish, in one sentence an officer could act on.
    publish_as: str
    # Why this field matters, stated without claiming what it would find.
    reads_as: str
    # Rule ids the field would make WRITABLE. On seven of the nine entries
    # every id here is absent from rules.yaml, which is exactly why those
    # fields measure zero. A test asserts the absence.
    unlocks_rules: tuple = ()
    # Existing rules the field would make better evidence without unlocking.
    improves_rules: tuple = ()
    # None on the seven fields whose absence skips nothing today.
    attribution: "Attribution | None" = None
    # Why the measured figure is zero, in plain language. Non-empty exactly
    # when `attribution` is None.
    zero_reason: str = ""
    # Real corpus figures that describe the gap's shape. They are CONTEXT and
    # never ranking inputs - see rank.py for why the module refuses to blend
    # them into a composite. Each is (label, measure_key).
    corroborating: tuple = dataclass_field(default_factory=tuple)
    # What it would take MoSPI to close it, stated as a scoping judgement and
    # labelled as one rather than as a costing.
    effort: str = ""

    def __post_init__(self) -> None:
        if self.gap_kind not in GAP_KINDS:
            raise ValueError(f"unknown gap kind {self.gap_kind!r}; expected one of {GAP_KINDS}")
        if (self.attribution is None) != bool(self.zero_reason.strip()):
            raise ValueError(
                f"field {self.key!r} must carry an attribution or a zero_reason, and "
                "exactly one of them. A field measuring zero owes the reader the reason "
                "it measures zero; a field measuring more than zero owes them the trace."
            )

    @property
    def basis(self) -> str:
        return BASIS_MEASURED_SKIPS if self.attribution else BASIS_NO_RULE_READS_IT


# --------------------------------------------------------------------------
# The nine fields
# --------------------------------------------------------------------------
#
# Numbered as the phase brief numbers them. 1-7 are DATA-PROFILE.md section 8's
# own list, 8 is the export-completeness gap, 9 was surfaced by measurement.

FIELDS = (
    AblationField(
        key="revised_cost_estimate",
        label="Revised cost estimate",
        gap_kind=GAP_NEVER_COLLECTED,
        source=SOURCE_PROFILE_SECTION_8,
        publish_as=(
            "One revised estimate per work, with the date it was approved, wherever a "
            "sanction has been revised. Works never revised need publish nothing."
        ),
        reads_as=(
            "A sanctioned amount can only be read against a second cost figure. The "
            "portal publishes a recommended amount and a sanctioned amount and they are "
            "the same number on every matched work in the corpus, so there is no second "
            "figure and no variance to measure."
        ),
        unlocks_rules=("cost_overrun",),
        zero_reason=(
            "No rule in rulebook v1.0.0 reads a revised estimate. A `cost_overrun` rule "
            "was designed at weight 20 and REMOVED when the profile measured recommended "
            "amount equal to sanctioned amount in 14,831 of 14,831 matched works "
            "(DATA-PROFILE.md section 5, DOMAIN-MODEL.md section g). A rule that does not "
            "exist cannot be skipped, so this field's absence costs the current rulebook "
            "exactly zero points. What it costs is a rule that cannot be written at all."
        ),
        corroborating=(
            ("Matched works where recommended and sanctioned differ", "degeneracy_differing"),
            ("Matched works compared", "degeneracy_matched"),
            ("Sanctioned works with no recommendation row at all", "recommended_not_published"),
        ),
        effort=(
            "Medium. A revision is already an administrative act at district level; the "
            "field exists in the workflow and is not exported."
        ),
    ),
    AblationField(
        key="utilisation_certificate",
        label="Utilisation certificate date and certified amount",
        gap_kind=GAP_NEVER_COLLECTED,
        source=SOURCE_PROFILE_SECTION_8,
        publish_as=(
            "One certificate date and one certified amount per work, carried in the "
            "existing expenditure export beside the disbursed amount."
        ),
        reads_as=(
            "The second rung of the fund ladder. Money leaving the account is published; "
            "money certified as spent on the sanctioned asset is not, so the hop between "
            "them is unreadable on every real work in the corpus."
        ),
        unlocks_rules=("certification_shortfall",),
        zero_reason=(
            "No rule in rulebook v1.0.0 reads `variance_disbursement_to_certification`, "
            "because there is no published data to calibrate a threshold against "
            "(CLAUDE.md invariant 6). The hop is derived, and it returns None with reason "
            "`not_published` on every real work. Fixture C is the demonstration: a "
            "labelled synthetic control whose fund ladder shows hop 2 OPEN at -25.00%, "
            "beside a score of 20 and a LOW band, because the open hop contributes exactly "
            "zero points (docs/contract/fixtures.md, fixture C). The gap is visible on "
            "screen and unscoreable, and that is the shape of this entry."
        ),
        corroborating=(
            ("Works whose certification rung is not published", "certification_not_published"),
            ("Rows in the certifications table", "certification_rows"),
            (
                "Works with a published disbursement a certificate could be read against",
                "works_with_payment",
            ),
        ),
        effort=(
            "Low. The utilisation certificate already exists in the district MPLADS "
            "workflow as a paper artefact; it is simply not exported."
        ),
    ),
    AblationField(
        key="milestone_progress",
        label="Milestone or physical progress percentage",
        gap_kind=GAP_NEVER_COLLECTED,
        source=SOURCE_PROFILE_SECTION_8,
        publish_as=(
            "One physical progress percentage per work, with the date it was assessed, "
            "for works not yet reported complete."
        ),
        reads_as=(
            "Money released against progress made. The portal publishes a work status "
            "from a six-value vocabulary and no quantity, so a work three years in at "
            "`Physical Inspection` and a work three months in at `Physical Inspection` "
            "read identically."
        ),
        unlocks_rules=("physical_financial_mismatch",),
        zero_reason=(
            "No rule in rulebook v1.0.0 reads a progress percentage. `execution_delay` "
            "reads `execution_days`, which needs a completion date, so it is skipped with "
            "reason `not_applicable` on works still in progress - but that skip is caused "
            "by the work being unfinished, not by this field's absence, and it is not "
            "attributed here. Attributing it would be the assumption the method forbids."
        ),
        corroborating=(
            (
                "Works with no completion date, where no progress figure exists",
                "works_without_completion",
            ),
            ("Of those, works where a payment has already been made", "paid_without_completion"),
        ),
        effort=(
            "Medium. Progress is assessed at inspection; the portal already publishes the "
            "inspection status and not the quantity behind it."
        ),
    ),
    AblationField(
        key="tender_records",
        label="Tender and bid records",
        gap_kind=GAP_NEVER_COLLECTED,
        source=SOURCE_PROFILE_SECTION_8,
        publish_as=(
            "Per work: the number of bids received, the identity of each bidder and the "
            "winning bid amount, for works awarded through tender."
        ),
        reads_as=(
            "Competition, or its failure. The portal publishes who was PAID and never who "
            "bid, so a vendor who won on price and a vendor who was the only bidder are "
            "the same row."
        ),
        unlocks_rules=("single_bid_award", "bid_rotation"),
        zero_reason=(
            "No rule in rulebook v1.0.0 reads a bid record, and no derived feature is "
            "built from one - the whole class of competition detection is absent from the "
            "rulebook rather than skipped within it. `vendor_concentration` reads payment "
            "concentration after the fact, which is a consequence of a competition failure "
            "and not evidence of one."
        ),
        corroborating=(
            (
                "Works where `vendor_concentration` fires - one vendor above 60% of the "
                "agency's disbursement",
                "vendor_concentration_fires",
            ),
            ("Distinct vendors in the corpus", "vendors"),
            ("Implementing agencies", "agencies"),
        ),
        effort=(
            "High. Bid records sit in state e-procurement systems rather than in the "
            "MPLADS workflow, so this is an integration and not an export."
        ),
    ),
    AblationField(
        key="work_geocoordinates",
        label="Work geo-coordinates",
        gap_kind=GAP_NEVER_COLLECTED,
        source=SOURCE_PROFILE_SECTION_8,
        publish_as=(
            "One latitude and longitude per work, captured at sanction or at first "
            "inspection."
        ),
        reads_as=(
            "Whether two works with the same description are two assets or one. NIGRANI "
            "detects repeated descriptions and says plainly that a cluster is a candidate "
            "for review and never an accusation, because 244 street lights across a "
            "constituency are very probably 244 street lights. A coordinate would let the "
            "officer separate the two cases instead of reading both."
        ),
        unlocks_rules=("asset_colocation_conflict",),
        improves_rules=("duplicate_work", "split_sanction"),
        zero_reason=(
            "No rule in rulebook v1.0.0 reads a coordinate. This field would not recover "
            "skipped weight; it would raise the precision of two rules that already "
            "evaluate. That is a different benefit and it is not measurable as unrealised "
            "weight, so it is reported as zero with the two rules' current firing counts "
            "beside it rather than converted into a number it has not earned."
        ),
        corroborating=(
            ("Works currently flagged by `duplicate_work`", "duplicate_work_fires"),
            ("Works inside an exact-repetition cluster of three or more", "split_sanction_fires"),
        ),
        effort=(
            "Low to medium. A coordinate is one GPS reading at the inspection the portal "
            "already records; MPLADS publishes no coordinates today, so maps in NIGRANI "
            "join at state and district level only."
        ),
    ),
    AblationField(
        key="asset_photo_geotag",
        label="Asset photograph geotag and timestamp",
        gap_kind=GAP_NEVER_COLLECTED,
        source=SOURCE_PROFILE_SECTION_8,
        publish_as=(
            "For each photograph already filed: its capture coordinates, its capture "
            "timestamp, and a stable image reference."
        ),
        reads_as=(
            "Whether the photograph is of this asset. The `Image` column is binary - it "
            "asserts that an image exists and carries no geotag, no timestamp and no URL "
            "(DATA-PROFILE.md section 7), so nobody can check what it shows or whether the "
            "same photograph was filed against several works."
        ),
        unlocks_rules=("asset_photo_reuse",),
        improves_rules=("asset_evidence_missing",),
        zero_reason=(
            "No rule in rulebook v1.0.0 reads a geotag or a timestamp. "
            "`asset_evidence_missing` IS skipped on 14,104 works - but the measurement "
            "traces every one of those skips to the `Image` column being published only in "
            "the completed export, which is a separate gap and is entry 9 in this list, "
            "not this one. Attributing them here would be the assumption the method exists "
            "to prevent."
        ),
        corroborating=(
            (
                "Works where `asset_evidence_missing` PASSED on an unverifiable assertion "
                "that a photograph exists",
                "asset_evidence_passes",
            ),
            ("Works where it fired because no photograph was filed", "asset_evidence_fires"),
        ),
        effort=(
            "Low. Phone cameras write both fields; the portal accepts the image and "
            "discards the metadata."
        ),
    ),
    AblationField(
        key="beneficiary_counts",
        label="Beneficiary counts",
        gap_kind=GAP_NEVER_COLLECTED,
        source=SOURCE_PROFILE_SECTION_8,
        publish_as=(
            "One estimated beneficiary count per work, on the same basis across states, "
            "recorded at sanction."
        ),
        reads_as=(
            "Cost against reach. Every rule in the rulebook reads process - time, "
            "repetition, concentration, evidence. None reads outcome, because the portal "
            "publishes no measure of what a work was for."
        ),
        unlocks_rules=("cost_per_beneficiary_outlier",),
        zero_reason=(
            "No rule in rulebook v1.0.0 reads a beneficiary count, and no derived feature "
            "is built from one. This is the only entry in the list where the missing field "
            "would add a new KIND of finding rather than sharpen an existing one, and it "
            "is also the one whose comparability across states is least assured - a count "
            "collected on different bases in 36 states would not be a measure."
        ),
        corroborating=(
            ("Sanctioned works carrying no reach measure of any kind", "corpus_works"),
            ("Sanctioned value those works represent", "sanctioned_value"),
        ),
        effort=(
            "Medium, and the difficulty is definitional rather than technical: the count "
            "is only useful if every state counts the same way."
        ),
    ),
    AblationField(
        key="expenditure_linkage",
        label="Complete expenditure linkage",
        gap_kind=GAP_PUBLISHED_INCOMPLETELY,
        source="DATA-PROFILE.md section 3",
        publish_as=(
            "The existing expenditure export, complete. Every payment row for every "
            "sanctioned work, rather than the first 34,000 rows."
        ),
        reads_as=(
            "Where the money actually went. The expenditure export joins to 3,529 of the "
            "27,078 sanctioned works - 15.70% - so on the other 23,549 NIGRANI cannot say "
            "how much of the sanction reached a vendor, when it last moved, or who "
            "received it."
        ),
        improves_rules=("utilisation_shortfall", "stalled_work", "vendor_concentration"),
        attribution=Attribution(
            rule_ids=("utilisation_shortfall", "stalled_work", "vendor_concentration"),
            skip_reason=Availability.NOT_PUBLISHED.value,
            condition=CONDITION_NO_PAYMENT_ROW,
        ),
        corroborating=(
            ("Sanctioned works an expenditure row joins to", "works_with_payment"),
            ("Sanctioned works with no payment row at all", "works_without_payment"),
        ),
        effort=(
            "The lowest on this list, and it is not a publication decision at all. MoSPI "
            "already collects and already publishes this field. Closing the gap means "
            "exporting it completely rather than to a row limit."
        ),
    ),
    AblationField(
        key="asset_image_publication_scope",
        label="Asset evidence published for works not yet complete",
        gap_kind=GAP_PUBLISHED_INCOMPLETELY,
        source=SOURCE_SURFACED_BY_MEASUREMENT,
        publish_as=(
            "The existing `Image` column, carried in the sanctioned export as well as the "
            "completed one, so that a work under execution can say whether a photograph "
            "has been filed."
        ),
        reads_as=(
            "Whether a photograph was ever filed. The `Image` column appears only in the "
            "completed export, so a sanctioned work not yet reported complete has no image "
            "field at all. That is a reporting gap and NIGRANI records it as one - it is "
            "not a finding that no photograph exists."
        ),
        improves_rules=("asset_evidence_missing",),
        attribution=Attribution(
            rule_ids=("asset_evidence_missing",),
            skip_reason=Availability.NOT_PUBLISHED.value,
            condition=CONDITION_NO_COMPLETION_ROW,
        ),
        corroborating=(
            ("Sanctioned works where the Image column is published", "asset_image_published"),
            ("Sanctioned works where it is not", "works_without_completion"),
        ),
        effort=(
            "As low as complete expenditure linkage. The column exists and the export "
            "that would carry it exists; only its scope would change."
        ),
    ),
)

FIELDS_BY_KEY = {entry.key: entry for entry in FIELDS}


def field_for(key: str) -> AblationField:
    try:
        return FIELDS_BY_KEY[key]
    except KeyError:
        raise KeyError(
            f"unknown ablation field {key!r}; the list is closed and lives in "
            "app/ablation/fields.py"
        ) from None
