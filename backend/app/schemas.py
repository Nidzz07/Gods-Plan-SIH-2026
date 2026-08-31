"""Pydantic v2 response shapes.

`CaseDetail` mirrors `docs/contract/case_detail.json` key for key. The two move
together or not at all (CLAUDE.md invariant 9): renaming a key on one side
breaks the frontend silently, so a change here is a change there in the same
commit.

**What changed in Phase 5, and why the contract file moved rather than this
one.** `case_detail.json` was written in Phase 0, before `engine/`, `ml/` and
`ablation/` existed. Six of its statements have since been overtaken by code
that produces a measured shape, and the contract is the stale side:

1. `concentration` is a new top-level block. `ml/badges.py` emits it and its
   own docstring says it "becomes contractual when the API is built", because
   the tier-4 graph has to reach a screen and adding a key to the contract was
   not Phase 3's to do. It is worth zero points, like the other two badges.
2. `statistical` gains `anomaly_flagged`, `availability`, `detail` and
   `peer_group_size`; its values are no longer null. `z_score` stays null and
   `ml/badges.py` explains why: no document in the repository defines what the
   z-score is a z-score OF, and filling it would mean inventing a measure and
   printing it beside measured ones.
3. `forecast` gains `risk_percentile`, `horizon_meaning`, `availability`,
   `outcome`, `elapsed_days`, `detail` and `holdout`, and its `note` is the
   model's own reading rather than a placeholder.
4. `rulebook_version_sha256` carries a real digest. The contract's
   `PLACEHOLDER-PENDING-PHASE-3-RULEBOOK` was honest when there was no
   rulebook; there is one now, snapshotted into `rulebook_versions`, and this
   field is the sha256 of that snapshot.
5. `opened_at` is `2026-08-24T00:00:00`, the corpus as-of date, not a wall
   clock. `app/derive_all.py` gives the reason: a wall clock would make the
   audit hash chain unreproducible for no gain.
6. Every rung, date and lag now carries the same key set, with nulls where a
   key does not apply, instead of some rows carrying `recommended_amt` or
   `note` and others omitting them. A table component renders one row shape;
   the alternative was three shapes and a conditional in the frontend.

Everything else - the ladders, the trace, `unavailable_fields`, the
corroboration block, the memo - is the shape Phase 0 froze, now filled by the
engine rather than by hand.

**`unavailable_fields` is a list of objects, not of strings** (`fixtures.md`,
design decision 4). A bare field name would say that something is missing
without saying whether MoSPI never published it, published it as zero, or the
work has not reached the stage that produces it - and keeping those three apart
end to end is what CLAUDE.md invariant 2 is for.

**Role scoping does not appear in these models, and that is deliberate.** What
a role changes is which rows a query returns, never which keys a case carries
(DOMAIN-MODEL.md (k)). A District Authority reading a case in their district
gets the same object a Ministry user does. See `docs/api/ROLE-SCOPING-PLAN.md`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Vocabularies. Every one of these is `app.constants`' vocabulary spelled as a
# type, so an impossible value cannot leave the API even if it reached the row.
# ---------------------------------------------------------------------------

Severity = Literal["HIGH", "MEDIUM", "LOW"]
RuleSeverity = Literal["high", "medium", "low"]
RuleStatus = Literal["fired", "passed", "skipped"]
CaseStatus = Literal["open", "under_review", "escalated", "resolved"]
Availability = Literal["published", "not_published", "published_zero", "not_applicable"]
# `published` is absent on purpose: a rule that read a value is never skipped.
SkipReason = Literal["not_published", "published_zero", "not_applicable"]
House = Literal["lok_sabha", "rajya_sabha"]
# `app.constants.ROLES` spelled as a type. The four personas and no fifth.
Role = Literal["ministry", "state_nodal", "district_authority", "member_of_parliament"]
GapHop = Literal["sanction_to_disbursement", "disbursement_to_certification"]
SlowestLag = Literal[
    "recommend_to_sanction", "sanction_to_first_payment", "first_payment_to_completion"
]
LadderState = Literal["open", "closed", "unavailable"]
LagState = Literal["computed", "unavailable"]

# A trace row quotes the value it read as the engine measured it: a percentage,
# a whole number of days, a boolean, or nothing at all. One column carries all
# four, because the officer reading the row reads one column.
TraceValue = float | int | bool | str | None

# `LifecycleDate` has a field literally called `date`, which shadows the
# imported type inside that class body. The alias is what the annotation there
# names; renaming the field instead would rename a key in the frozen contract.
IsoDate = date


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


class WorkRef(BaseModel):
    """The work a case is about, in the words the portal published it in."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    work_id: str
    work_id_raw: str
    category: str | None = None
    description: str | None = None
    state: str
    district: str | None = None
    agency: str | None = None
    # The raw published agency string that `rapidfuzz` folded into `agency`.
    # Kept beside the canonical name because a merge an officer disputes has to
    # be visible, not silent (declared limitation 9).
    agency_name_raw: str | None = None
    status: str | None = None
    # Null is a real answer: the Image column is published only in the
    # completed export, so a work not yet reported complete has no value here
    # either way. It is not "no photograph".
    asset_image_present: bool | None = None
    fy: str
    # Labelled on screen wherever it is true, and excluded from every published
    # aggregate (CLAUDE.md invariant 12).
    is_synthetic: bool = False


class MPRef(BaseModel):
    """The recommending member. `constituency` is null for every Rajya Sabha seat."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    house: House
    constituency: str | None = None
    state: str
    # "2022-2028", or null where the portal published the suffix as (NaN-NaN).
    term: str | None = None


# ---------------------------------------------------------------------------
# The fund ladder
# ---------------------------------------------------------------------------


class FundRung(BaseModel):
    """One rung: an amount, or the reason there is no amount.

    Every rung carries the same keys. `recommended_amt` and
    `recommended_equals_sanctioned` are meaningful only on the sanctioned rung
    and `note` only on the certified one; on the others they are null.
    """

    model_config = ConfigDict(from_attributes=True)

    key: Literal["sanctioned_amt", "disbursed_amt", "certified_amt"]
    label: str
    # Whole rupees. The portal publishes no paise.
    amount: int | None = None
    availability: Availability
    recommended_amt: int | None = None
    recommended_equals_sanctioned: bool | None = None
    note: str | None = None


class FundHop(BaseModel):
    """One hop: a signed variance against the rung above, and what to do about it.

    `state` is `unavailable`, never `closed`, when the variance could not be
    computed. A hop nobody could measure is not a hop that came through clean.
    """

    model_config = ConfigDict(from_attributes=True)

    key: GapHop
    label: str
    variance_pct: float | None = None
    tolerance_pct: float
    state: LadderState
    unavailable_reason: SkipReason | None = None
    # What the officer physically checks. DOMAIN-MODEL.md (b), HOP_ACTION.
    hop_action: str


class FundLadder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rungs: list[FundRung]
    hops: list[FundHop]


# ---------------------------------------------------------------------------
# The lifecycle ladder
# ---------------------------------------------------------------------------


class LifecycleDate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: Literal["recommended_date", "sanction_date", "first_payment_date", "completion_date"]
    label: str
    date: IsoDate | None = None
    availability: Availability
    unavailable_reason: SkipReason | None = None


class LifecycleLag(BaseModel):
    """One lag, in whole days. Never clamped: a negative lag is an ingest reject."""

    model_config = ConfigDict(from_attributes=True)

    key: SlowestLag
    label: str
    days: int | None = None
    state: LagState
    unavailable_reason: SkipReason | None = None


class LifecycleLadder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dates: list[LifecycleDate]
    lags: list[LifecycleLag]
    last_payment_date: date | None = None
    # Never null. Zero payments is a fact about the work, not an unmeasured
    # field (DOMAIN-MODEL.md (f)).
    payment_count: int


# ---------------------------------------------------------------------------
# The trace
# ---------------------------------------------------------------------------


class DuplicateCitation(BaseModel):
    """The evidence a fired `duplicate_work` row owes the officer.

    `duplicate_work` is the one rule fed by a model output, and it is
    admissible only because this block hands over the records the number came
    from (DOMAIN-MODEL.md (h)). A fired hit with a null citation is a failed
    test in `engine/score.py`, not a degraded row.

    `reading` says in the response what the UI must say on screen: a cluster is
    a candidate for review, never an accusation.
    """

    model_config = ConfigDict(from_attributes=True)

    matched_work_ids: list[str]
    matched_case_ids: list[str]
    cluster_size: int | None = None
    shared_description: str
    agency: str | None = None
    similarity: float
    components: dict[str, float]
    method: str
    reading: str


class RuleHitOut(BaseModel):
    """One trace row. All ten are always present, including passes and skips.

    A trace that omitted the passes would not be re-derivable, and one that
    omitted the skips would be a lie about what was checked.

    `raw_value` and `threshold` are stored as text - one column has to carry a
    percentage, a count, a boolean and a null - and are returned in their
    measured types, so the response prints -40.01, 333, false and null exactly
    as the frozen contract does.
    """

    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    # As snapshotted under the rulebook version this case was scored with, not
    # as rules.yaml reads today.
    label: str
    field: str
    raw_value: TraceValue = None
    operator: Literal["lt", "lte", "gt", "gte", "eq", "ne"]
    threshold: TraceValue
    weight: int
    # The rule's full undivided weight when fired, else 0. Never rescaled: an
    # officer adding the printed contributions must reach the printed
    # `raw_score`.
    contribution: int
    severity: RuleSeverity
    status: RuleStatus
    # Non-null exactly when status is `skipped`.
    skip_reason: SkipReason | None = None
    citation: DuplicateCitation | None = None
    # Travels with the flag, never in a footnote.
    caveat: str | None = None


class UnavailableField(BaseModel):
    """One thing this case could not read, and which of the three reasons it was.

    An object rather than a bare field name (`fixtures.md`, design decision 4).
    "MoSPI does not publish this" and "the portal published it as zero" and
    "the work has not reached this stage" are three different findings, and
    collapsing them is what CLAUDE.md invariant 2 exists to prevent.
    """

    model_config = ConfigDict(from_attributes=True)

    field: str
    reason: SkipReason
    detail: str | None = None


class Corroboration(BaseModel):
    """F4's agency pattern bonus - the only source of score that is not a rule.

    Rendered whether or not it was applied. An officer has to be able to see
    the bonus NOT fire and understand why, which is why `applied: false` comes
    with the count and the minimum rather than with an omitted block.
    """

    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    applied: bool
    weight: int
    contribution: int
    min_high_cases: int
    window: str
    agency: str | None = None
    high_case_count: int
    matched_case_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# The badges. Tiers 3 and 4, worth zero points each (CLAUDE.md invariant 1).
# ---------------------------------------------------------------------------


class Statistical(BaseModel):
    """Tier 3: the peer group and the IsolationForest badge. Zero points.

    `contribution` is typed as a literal zero rather than as an int. The
    invariant is not "this is usually zero"; it is that no model output can
    reach the addition `engine/score.py` performs, and a response that could
    serialise any other number here would be describing a different product.
    """

    model_config = ConfigDict(from_attributes=True)

    # Null, deliberately: nothing in the repository defines which quantity this
    # would be a z-score of. See ml/badges.statistical_block.
    z_score: float | None = None
    z_peer_group: str | None = None
    anomaly_score: float | None = None
    anomaly_model_version: str | None = None
    anomaly_flagged: bool | None = None
    # Whether the forest agrees with what the rulebook already found. It raises
    # an officer's confidence; it does not raise the number.
    confirms: bool | None = None
    contribution: Literal[0] = 0
    availability: Availability
    detail: str | None = None
    peer_group_size: int | None = None
    note: str


class Forecast(BaseModel):
    """Tier 3: the delay-risk badge. Zero points, illustrative horizon.

    Trained on a truncated portal sample. The horizon is a demonstration, not a
    commitment, and `horizon_meaning` says so in the response rather than only
    on a slide.
    """

    model_config = ConfigDict(from_attributes=True)

    delay_risk: float | None = None
    risk_percentile: float | None = None
    horizon_days: int | None = None
    horizon_meaning: str | None = None
    model_version: str | None = None
    contribution: Literal[0] = 0
    availability: Availability
    outcome: str | None = None
    elapsed_days: int | None = None
    detail: str | None = None
    # The agency-grouped holdout report for the fit this badge came from.
    holdout: dict[str, Any] | None = None
    note: str | None = None


class WorkVendor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_id: int
    vendor: str | None = None
    # How many agencies this vendor is paid by. Only the graph knows this.
    agency_span: int


class Concentration(BaseModel):
    """Tier 4: the agency-vendor bipartite graph. Zero points.

    New in Phase 5 and new to the contract; `ml/badges.py` emitted it from
    Phase 3 with no key to land in. `component_agencies` is null on the current
    corpus - `ml/concentration.measures` publishes the component size under a
    different name - and the key is kept rather than dropped because the block
    is the graph's contract and a Phase 7 change there should have somewhere to
    arrive.
    """

    model_config = ConfigDict(from_attributes=True)

    # Herfindahl-Hirschman index over the agency's vendor shares.
    hhi: float | None = None
    agency: str | None = None
    vendor_count: int | None = None
    top_vendor: str | None = None
    top_vendor_share_pct: float | None = None
    shared_vendor_exposure_pct: float | None = None
    widest_vendor_span: int | None = None
    component_agencies: int | None = None
    work_vendors: list[WorkVendor] | None = None
    model_version: str | None = None
    contribution: Literal[0] = 0
    availability: Availability
    detail: str | None = None
    note: str


# ---------------------------------------------------------------------------
# The case
# ---------------------------------------------------------------------------


class CaseDetail(BaseModel):
    """GET /api/cases/{case_id} - the frozen contract shape.

    The score, the severity and the whole trace are the STORED ones: what was
    decided on the day, under the rulebook version named here. The ladders and
    the memo are re-derived from the same raw rows through the same functions,
    because they are presentation of the case rather than a second scoring
    path - there is no second scoring path.
    """

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    work: WorkRef
    mp: MPRef

    score: int
    raw_score: int
    score_cap: int
    severity: Severity
    status: CaseStatus
    opened_at: datetime
    # Every "days since" figure is measured against this and never against
    # today, so a case re-derived months from now reproduces the number the
    # officer acted on.
    data_as_of: date

    fund_ladder: FundLadder
    lifecycle_ladder: LifecycleLadder
    gap_hop: GapHop | None = None
    slowest_lag: SlowestLag | None = None

    coverage_pct: int
    coverage_basis: str
    unavailable_fields: list[UnavailableField] = Field(default_factory=list)

    rulebook_version: str
    rulebook_version_sha256: str
    rule_hits: list[RuleHitOut]
    corroboration: Corroboration

    statistical: Statistical
    forecast: Forecast
    concentration: Concentration

    # engine/memo.py template output. NOT AI-generated, and the memo's own last
    # sentence says so.
    memo: str


class CaseListItem(BaseModel):
    """One row of the ranked list. Enough to triage without opening the case."""

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    work_id: str
    description: str | None = None
    category: str | None = None
    state: str
    district: str | None = None
    agency: str | None = None
    mp_name: str
    score: int
    raw_score: int
    severity: Severity
    status: CaseStatus
    coverage_pct: int
    gap_hop: GapHop | None = None
    slowest_lag: SlowestLag | None = None
    corroboration_bonus: int
    sanctioned_amt: int | None = None
    opened_at: datetime
    is_synthetic: bool = False


class CaseListPage(BaseModel):
    """A page of the ranked list, plus what the filter matched before paging.

    `total` is the count the filter selected, not the count returned, so a
    screen can say "37 HIGH cases" without asking for all of them.
    """

    model_config = ConfigDict(from_attributes=True)

    total: int
    limit: int
    offset: int
    ranked_by: str
    items: list[CaseListItem]


# ---------------------------------------------------------------------------
# Works, browsed independently of whether a case has been derived
# ---------------------------------------------------------------------------


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor: str | None = None
    paid_amt: int | None = None
    # `published_zero` is common and meaningful here: the portal published a
    # payment row carrying zero, which is a fact about the row and not a gap.
    paid_availability: Availability
    payment_date: date | None = None
    payment_status: str


class WorkDetail(BaseModel):
    """GET /api/works/{work_id} - the raw published record, before derivation.

    Deliberately independent of `cases`: a work with no case (an unsanctioned
    recommendation) is still browsable, and what this endpoint shows is what
    MoSPI published rather than what NIGRANI concluded. `case_id` is present
    when a case has been opened for it and null otherwise.
    """

    model_config = ConfigDict(from_attributes=True)

    work: WorkRef
    mp: MPRef
    case_id: str | None = None
    recommended_amt: int | None = None
    recommended_availability: Availability
    recommended_date: date | None = None
    sanctioned_amt: int | None = None
    sanction_date: date | None = None
    completion_date: date | None = None
    completed_amt: int | None = None
    certified_amt: int | None = None
    certification_date: date | None = None
    payments: list[PaymentOut] = Field(default_factory=list)
    source_file: str


# ---------------------------------------------------------------------------
# Analytics. Pre-aggregated at materialisation time; see app/derive_all.py.
# ---------------------------------------------------------------------------


class RollupRow(BaseModel):
    """One pre-aggregated row. The measures are identical at every grain.

    `undisbursed_amt` is narrow on purpose: sanctioned minus disbursed, and
    only on cases whose fund hop 1 is actually open. A work with no expenditure
    row has an unavailable hop and contributes nothing, because counting it
    would report the truncation of MoSPI's export as undelivered money.
    `cases_without_expenditure_row` is that population, reported beside the sum
    rather than folded into it.
    """

    model_config = ConfigDict(from_attributes=True)

    state: str | None = None
    district: str | None = None
    agency: str | None = None
    agency_id: int | None = None
    mp_id: int | None = None
    mp_name: str | None = None
    cases: int
    high_cases: int
    medium_cases: int
    low_cases: int
    corroborated_cases: int
    sanctioned_amt: int | None = None
    undisbursed_amt: int | None = None
    cases_without_expenditure_row: int
    mean_coverage_pct: float | None = None
    worst_score: int | None = None
    districts: int | None = None
    agencies: int | None = None


class NationalAnalytics(BaseModel):
    """GET /api/analytics/national - state-level rollups over real works only.

    The labelled synthetic control is excluded from every figure here
    (invariant 12). The corpus is a truncated portal sample, so no total below
    is a national total, and `caption` says so on the same object rather than
    in a footnote.
    """

    model_config = ConfigDict(from_attributes=True)

    caption: str
    data_as_of: date
    rulebook_version: str
    total_cases: int
    high_cases: int
    medium_cases: int
    low_cases: int
    corroborated_cases: int
    sanctioned_amt: int
    undisbursed_amt: int
    cases_without_expenditure_row: int
    mean_coverage_pct: float
    states: list[RollupRow]
    top_states_by_high: list[RollupRow]


class StateAnalytics(BaseModel):
    """GET /api/analytics/state/{state} - the districts inside one state."""

    model_config = ConfigDict(from_attributes=True)

    caption: str
    data_as_of: date
    state: str
    summary: RollupRow
    districts: list[RollupRow]


class DistrictAnalytics(BaseModel):
    """GET /api/analytics/district/{district} - the queue, plus who implements it."""

    model_config = ConfigDict(from_attributes=True)

    caption: str
    data_as_of: date
    district: str
    state: str | None = None
    summary: RollupRow
    agencies: list[RollupRow]
    cases: list[CaseListItem]


class AccountLadderRung(BaseModel):
    """One rung of the per-MP account ladder, with why it is null if it is."""

    model_config = ConfigDict(from_attributes=True)

    key: Literal["allocated_amt", "sanctioned_amt", "disbursed_amt"]
    label: str
    amount: int | None = None
    availability: Availability


class AccountLadder(BaseModel):
    """allocated -> sanctioned -> disbursed, for one MP and one window.

    `fy` reads `term_to_date` on the row carrying the published allocation: the
    portal publishes one cumulative allocation per member and no per-year
    breakdown, so the utilisation ratio is computable only there. The per-FY
    rows carry the sanction and disbursement rollups, which genuinely are
    per-FY, and a null allocation with reason `not_published`.
    """

    model_config = ConfigDict(from_attributes=True)

    fy: str
    rungs: list[AccountLadderRung]
    mp_utilisation_pct: float | None = None


class MPAnalytics(BaseModel):
    """GET /api/analytics/mp/{mp_id} - the account, the portfolio, the percentile.

    The MP view exists because MPLADS criticism often lands on the member for a
    delay that happened entirely inside the district administration. The
    account ladder says where the allocation stands; the case portfolio says
    what the works are doing; `utilisation_percentile` places the member among
    peers holding both an allocation and a sanction, and names that population
    rather than implying a national ranking.
    """

    model_config = ConfigDict(from_attributes=True)

    caption: str
    data_as_of: date
    mp: MPRef
    account: list[AccountLadder]
    utilisation_percentile: float | None = None
    utilisation_peer_group: str
    utilisation_peers: int
    portfolio: RollupRow | None = None
    worst_cases: list[CaseListItem]


# ---------------------------------------------------------------------------
# Operational shapes. Not part of the frozen case-detail contract: these carry
# requests and the trail, and case_detail.json says nothing about them.
# ---------------------------------------------------------------------------


class NoteIn(BaseModel):
    """POST /api/cases/{case_id}/notes - an officer's note.

    There is no notes table. A note IS an audit event: writing it anywhere else
    would create a second place a case's history lives, and only one of the two
    would be hash-chained.
    """

    text: str = Field(min_length=1, max_length=4000)
    # Phase 6 replaces this with the authenticated user's role; until then the
    # caller declares it and the audit row records what was declared. It is
    # constrained to the four roles so the trail cannot carry a role that does
    # not exist.
    actor_role: Role = "district_authority"


class AuditEventOut(BaseModel):
    """One row of the append-only, hash-chained trail.

    Both hashes are returned. An auditor recomputes `row_hash` from the other
    columns with a shell one-liner and does not have to trust the server to
    have done it (`engine/audit.row_hash`).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    at: datetime
    actor_role: str
    actor_id: int | None = None
    event: str
    case_id: str | None = None
    # Decoded from the stored JSON text so the client does not parse twice.
    payload: dict[str, Any] | None = None
    prev_hash: str | None = None
    row_hash: str


class AuditTrail(BaseModel):
    """GET /api/audit/{case_id} - this case's trail, oldest first.

    A narrative runs forwards. `rows_intact` is the result of recomputing each
    returned row's hash from its own stored columns: it catches a row whose
    content was altered. It does NOT catch a row that was removed - only
    walking the whole chain does that, and `GET /api/audit/chain` is where that
    walk lives, because it reads every audit row in the database.

    False is a finding an auditor needs to see, not an error to hide.
    """

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    events: list[AuditEventOut]
    rows_intact: bool
    first_broken_row: int | None = None


class ChainStatus(BaseModel):
    """GET /api/audit/chain - the whole hash chain, walked.

    The only check that detects a removed row: a deletion leaves the survivors
    individually valid and breaks the links between them. `broken_at` is the id
    of the first row whose link does not hold. Nothing is repaired.
    """

    rows: int
    intact: bool
    broken_at: int | None = None


class NoteOut(BaseModel):
    """What a written note looks like coming back: the audit row it became."""

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    event: AuditEventOut


class RecomputeOut(BaseModel):
    """POST /api/cases/{case_id}/recompute - stored against freshly re-derived.

    Re-derived against the rulebook SNAPSHOT the case was scored under, read
    through `cases.rulebook_version_id`, not against today's `rules.yaml`
    (CLAUDE.md invariant 5). The comparison is of the full trace - rule ids,
    raw values, thresholds, contributions, statuses - and not of the scalar
    score, because an auditor's question is "which rule moved", not "did the
    number move".

    Nothing about the stored case is rewritten. If the two disagree, the
    disagreement IS the finding, and overwriting the old score would destroy
    the evidence that anything moved.
    """

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    rulebook_version: str
    identical: bool
    stored: dict[str, Any]
    recomputed: dict[str, Any]
    trace_diff: list[dict[str, Any]] = Field(default_factory=list)
    stored_trace: list[dict[str, Any]] = Field(default_factory=list)
    recomputed_trace: list[dict[str, Any]] = Field(default_factory=list)


class Health(BaseModel):
    """GET /health - liveness, plus whether the build steps have actually run.

    A green service over an empty database is the most misleading answer this
    API could give, so the counts travel with the status.
    """

    status: str
    service: str
    version: str
    data_as_of: date
    corpus_works: int
    cases: int
    rulebook_version: str | None = None
    ml_findings: int
    ablation_findings: int


# ---------------------------------------------------------------------------
# Identity and scope. Not part of the frozen case-detail contract: what a role
# changes is which rows a query returns, never which keys a case carries
# (schemas module docstring, DOMAIN-MODEL.md (k)).
# ---------------------------------------------------------------------------


class LoginIn(BaseModel):
    """POST /api/auth/login.

    There is no registration shape here and there will not be one. Accounts are
    provisioned by `python -m app.seed_users`, which is how a government
    deployment grants access and also what keeps a scope from being chosen by
    the person it restricts.
    """

    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class ScopeOut(BaseModel):
    """The rows this account may reach, named rather than left to be inferred.

    All four keys are present on every response, null where the role does not
    use them, so a client renders one shape instead of four. `describes` is the
    same fact in a sentence, for a screen that shows the officer what they are
    looking at without translating a null pattern into English itself.
    """

    state: str | None = None
    state_id: int | None = None
    district: str | None = None
    mp_id: int | None = None
    mp_name: str | None = None
    describes: str


class MeOut(BaseModel):
    """GET /api/auth/me - who the token belongs to, and what it can reach.

    `can_write` is stated rather than left for the frontend to derive from the
    role, because the derivation is a rule about the domain and not about the
    screen: the member of parliament is read-only everywhere (DOMAIN-MODEL.md
    (k)), and a UI that recomputed that would be a second place it could be got
    wrong. The server refuses the write regardless - this key is what lets the
    screen not offer a button that would be refused.
    """

    id: int
    email: str
    display_name: str
    role: Role
    is_active: bool
    can_write: bool
    scope: ScopeOut


class TokenOut(BaseModel):
    """The signed access token, plus who it is for and when it stops working.

    `expires_at` travels with the token so a client can see the session end
    coming rather than discovering it as a 401 mid-form. `user` is embedded so
    a login is one round trip: the screen that follows a login needs the role
    and the scope immediately, and a second call to `/api/auth/me` for facts the
    server already had would be a round trip spent on nothing.
    """

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    expires_in_hours: int
    user: MeOut
