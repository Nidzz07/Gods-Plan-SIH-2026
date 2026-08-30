"""F1 - the derived feature dictionary, and both ladders.

This module replaces the inherited `reconcile.py`. Nothing of the PDS domain
survives: the ladders, the null semantics and every formula below come from
`docs/domain/DOMAIN-MODEL.md` sections (b), (c) and (f), and every count quoted
in a docstring is measured in `docs/data/DATA-PROFILE.md`.

**Two ladders, and they answer different questions.**

    fund       sanctioned_amt -> disbursed_amt -> certified_amt
    lifecycle  recommended -> sanctioned -> first payment -> completed

The fund ladder reconciles AMOUNT and the lifecycle ladder reconciles TIME. On
MPLADS data, which is financially flat and temporally rich, the lifecycle
ladder carries most of the signal (DATA-PROFILE.md section 5), which is why
seven of the ten rules read a date difference, a repetition count or a
concentration share, and only one reads an amount variance.

**`execution_days` is not the sum of the two payment-side lags.** It is
`completion_date - sanction_date`, computed directly, and it is computable on a
work that has no payment row at all. Fixture B is the proof: 539 days of
execution on a work with zero payments, where a sum-of-lags definition would
have returned None and lost the highest-weighted rule the case fires. Where all
three are computable the identity does hold - fixture C, 42 + 439 = 481 - and a
test asserts it there rather than everywhere.

**A missing reading is None, and it carries the reason it is missing.** Every
feature this module produces is accompanied by an `Availability` saying why it
is None, and that reason travels into `rule_hits.skip_reason` and onto the
screen (CLAUDE.md invariant 2). "MoSPI does not publish this" and "the portal
published zero" and "this work has not reached that stage" are three different
findings, and the first of them is the input to the ablation report.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field as dataclass_field

from ..constants import (
    DATA_AS_OF,
    FUND_HOP_DEFAULT_TOLERANCE_PCT,
    FY_TERM_TO_DATE,
    HOP_DISBURSEMENT_TO_CERTIFICATION,
    HOP_SANCTION_TO_DISBURSEMENT,
    LAG_FIRST_PAYMENT_TO_COMPLETION,
    LAG_RECOMMEND_TO_SANCTION,
    LAG_SANCTION_TO_FIRST_PAYMENT,
    STATUS_WORK_COMPLETED,
    VENDOR_CONCENTRATION_AGENCY_FLOOR,
    Availability,
    case_id_for,
)

# --------------------------------------------------------------------------
# The derived feature dictionary (DOMAIN-MODEL.md section f)
# --------------------------------------------------------------------------

# Every key the rulebook may reference, and nothing else is addressable from
# rules.yaml. `engine.rulebook.validate` rejects a rule naming a field that is
# not on this list, which is also what structurally bars the ML tier from the
# score (CLAUDE.md invariant 1): there is no `anomaly_score`, no `z_score` and
# no `delay_risk` here, so no rulebook edit can reach one. `duplicate_similarity`
# is the single declared exception and earns its place by citing its evidence
# on the trace row (DOMAIN-MODEL.md section h).
FEATURE_KEYS = (
    "work_id",
    "variance_sanction_to_disbursement",
    "variance_disbursement_to_certification",
    "sanction_lag_days",
    "sanction_to_first_payment_days",
    "first_payment_to_completion_days",
    "execution_days",
    "days_since_last_payment",
    "duplicate_similarity",
    "same_desc_same_agency_count",
    "vendor_share_in_agency_pct",
    "completed_without_payment",
    "asset_image_absent",
    "mp_utilisation_pct",
    "payment_count",
)

# The similarity method named on every duplicate_work citation. Recorded as a
# string so the trace says which scorer produced the number an officer is
# looking at, and so a Phase 7 recalibration is visible in the audit trail
# rather than silent.
SIMILARITY_METHOD = (
    "rapidfuzz.token_set_ratio over normalised description, blocked by agency_id"
)

_PUNCTUATION = re.compile(r"[^a-z0-9]+")
_WHITESPACE = re.compile(r"\s+")


def normalise_description(text) -> str:
    """Lowercase, punctuation to spaces, whitespace collapsed.

    This is the normalisation DATA-PROFILE.md section 6 measured the duplicate
    clusters with, and it reproduces them exactly: 447 clusters of two or more
    over 3,584 works, 275 of three or more over 3,240, Rs 166.59 crore of
    sanctioned value inside the second set, and the three largest clusters at
    244, 115 and 108 works.

    It returns the empty string for a description that carries no comparable
    text. 79 sanctioned works are in that state: the portal exported
    non-Latin descriptions as runs of question marks, so a value was published
    but nothing readable was. Those 79 plus the 50 works with no description at
    all are the 129 skips `split_sanction` records.
    """
    if text is None:
        return ""
    return _WHITESPACE.sub(" ", _PUNCTUATION.sub(" ", str(text).lower())).strip()


class FeatureSet(dict):
    """A feature dict that also knows why each of its values is missing.

    It IS a dict, so `features["execution_days"]` and `features.get(...)` behave
    exactly as the inherited engine expected and a test can build one by hand.
    What it adds is `availability`, a parallel mapping from feature key to
    `Availability`, which is what lets `rulebook.evaluate` write a *reason* onto
    a skipped row instead of a bare null (CLAUDE.md invariant 2).

    `evidence` carries what a fired rule must cite - currently only the
    duplicate cluster. It is not a feature and no rule reads it; it is the
    record an officer opens instead of trusting the number.
    """

    def __init__(self, values=None, availability=None, evidence=None, detail=None):
        super().__init__(values or {})
        self.availability: dict[str, Availability] = dict(availability or {})
        self.evidence: dict[str, dict] = dict(evidence or {})
        # Plain-language detail for the unavailable_fields block of the frozen
        # contract, keyed by feature name.
        self.detail: dict[str, str] = dict(detail or {})

    def reason_for(self, key: str) -> Availability | None:
        return self.availability.get(key)

    def unavailable_fields(self) -> list[dict]:
        """The contract's `unavailable_fields` block: field, reason, detail."""
        return [
            {
                "field": key,
                "reason": self.availability[key].value,
                "detail": self.detail.get(key),
            }
            for key in FEATURE_KEYS
            if self.get(key) is None and key in self.availability
        ]


def _field(obj, name):
    """Read one field off a SQLAlchemy row, a SimpleNamespace or a dict.

    The engine is fed ORM rows in the app and plain objects in the tests. It
    should not care which, and should never explode on a shape it has not met.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _availability_of(obj, name, default=Availability.NOT_PUBLISHED) -> Availability:
    """Read an availability companion, tolerating the string form SQLite returns."""
    raw = _field(obj, name)
    if raw is None:
        return default
    if isinstance(raw, Availability):
        return raw
    return Availability(str(raw))


# --------------------------------------------------------------------------
# Corpus context - the cross-work facts a single work's features depend on
# --------------------------------------------------------------------------


@dataclass
class CorpusContext:
    """Everything about the rest of the corpus that one work's features need.

    Built once per scoring run and handed to every `derive()` call. Four of the
    fourteen features are not properties of a work at all - they are properties
    of its agency, its vendor, its description's neighbourhood or its member's
    account - and computing them per work would be O(n^2) queries.

    **`duplicate_similarity` and `same_desc_same_agency_count` are inputs here,
    not derivations.** Phase 4 will write them into `ml_findings` and wire them
    in through `similarity` and `cluster_size` directly. Until then
    `from_session()` computes them inline with `rapidfuzz.token_set_ratio` over
    the normalised description, blocked by agency - the same method
    DATA-PROFILE.md section 6 measured and the same method the citation names.
    Recomputing inline was chosen over reading a stale table because the two
    must not be allowed to disagree silently, and because the whole corpus
    takes under four seconds.
    """

    similarity: dict = dataclass_field(default_factory=dict)
    similarity_peers: dict = dataclass_field(default_factory=dict)
    similarity_best_text: dict = dataclass_field(default_factory=dict)
    cluster_size: dict = dataclass_field(default_factory=dict)
    normalised: dict = dataclass_field(default_factory=dict)
    agency_disbursed: dict = dataclass_field(default_factory=dict)
    agency_vendor_disbursed: dict = dataclass_field(default_factory=dict)
    agency_name: dict = dataclass_field(default_factory=dict)
    # mp_id -> (allocated_amt, allocated_availability, sanctioned_amt)
    mp_account: dict = dataclass_field(default_factory=dict)

    @classmethod
    def from_session(cls, session) -> "CorpusContext":
        """Build the context from the ingested corpus."""
        from sqlalchemy import select

        from ..models import Agency, FundAccount, Payment, Sanction, Work

        context = cls()

        for agency_id, name in session.execute(select(Agency.id, Agency.name_canon)):
            context.agency_name[agency_id] = name

        # Agency and agency-vendor disbursement, over EVERY work of the agency
        # and not only its sanctioned ones. Restricting the denominator to
        # sanctioned works turns a 17% vendor into a 100% one, which is the
        # error DATA-PROFILE.md section 6 warns against.
        rows = session.execute(
            select(Work.agency_id, Payment.vendor_id, Payment.paid_amt)
            .join(Payment, Payment.work_id == Work.id)
            .where(Work.agency_id.is_not(None), Payment.paid_amt.is_not(None))
        )
        agency_total: dict = defaultdict(int)
        vendor_total: dict = defaultdict(int)
        for agency_id, vendor_id, paid in rows:
            agency_total[agency_id] += paid
            if vendor_id is not None:
                vendor_total[(agency_id, vendor_id)] += paid
        context.agency_disbursed = dict(agency_total)
        context.agency_vendor_disbursed = dict(vendor_total)

        # The account ladder rungs, from the term-to-date row. The portal
        # publishes one cumulative allocation per member and no per-year
        # breakdown, so the ratio is computable only there (DOMAIN-MODEL.md (d)).
        for mp_id, allocated, availability, sanctioned in session.execute(
            select(
                FundAccount.mp_id,
                FundAccount.allocated_amt,
                FundAccount.allocated_availability,
                FundAccount.sanctioned_amt,
            ).where(FundAccount.fy == FY_TERM_TO_DATE)
        ):
            context.mp_account[mp_id] = (allocated, availability, sanctioned)

        # Descriptions, blocked by agency, over the sanctioned works only -
        # the population a case can be opened for (DOMAIN-MODEL.md (a)).
        descriptions = session.execute(
            select(Work.id, Work.work_id_canon, Work.agency_id, Work.description).join(
                Sanction, Sanction.work_id == Work.id
            )
        ).all()
        context.load_descriptions(descriptions)
        return context

    def load_descriptions(self, rows, peer_limit: int = 8) -> None:
        """Compute the cluster counts and similarities for (id, work_id, agency, text).

        Split out from `from_session` so a test can drive it with a handful of
        tuples instead of a database.

        Members are sorted by work id inside each agency block before the
        similarity matrix is built, and the ranking is a STABLE sort on the
        negated score, so peers tied on similarity come back in work-id order.
        That is what makes a citation reproducible: fixture A's fourteen peers
        all score exactly 1.000, and the two the trace cites are the two
        immediately after it in id order, on every run and on any machine.
        """
        import numpy as np
        from rapidfuzz import fuzz, process

        blocks: dict = defaultdict(list)
        for work_pk, work_id_canon, agency_id, description in rows:
            text = normalise_description(description)
            if agency_id is None or not text:
                continue
            self.normalised[work_pk] = text
            blocks[agency_id].append((work_id_canon, work_pk, text))

        counts: dict = defaultdict(int)
        for agency_id, members in blocks.items():
            for _, _, text in members:
                counts[(agency_id, text)] += 1
        for work_pk, _, agency_id, _ in rows:
            text = self.normalised.get(work_pk)
            if text is not None:
                self.cluster_size[work_pk] = counts[(agency_id, text)]

        for members in blocks.values():
            if len(members) < 2:
                # A work alone under its agency has no population to be
                # compared against. That is `not_applicable`, not a reporting
                # gap - 52 works on this corpus.
                continue
            members.sort()
            texts = [text for _, _, text in members]
            matrix = process.cdist(texts, texts, scorer=fuzz.token_set_ratio, workers=-1)
            np.fill_diagonal(matrix, -1)
            order = np.argsort(-matrix, axis=1, kind="stable")
            best = matrix.max(axis=1)
            for index, (_, work_pk, _) in enumerate(members):
                self.similarity[work_pk] = float(best[index]) / 100.0
                ranked = order[index][:peer_limit]
                self.similarity_peers[work_pk] = [members[j][0] for j in ranked]
                self.similarity_best_text[work_pk] = members[order[index][0]][2]


# --------------------------------------------------------------------------
# Fund ladder
# --------------------------------------------------------------------------


def disbursed_amount(payments) -> tuple[int | None, Availability]:
    """The disbursed rung: the sum of this work's published payment amounts.

    **Phase 2 decision, recorded in DATA-PROFILE.md section 10.** The completed
    export also publishes an `Amount Disbursed` figure, and the two disagree on
    1,329 of 12,953 published pairs. The ladder reads the PAYMENTS ROLLUP,
    because a payment row names its vendor, its date and its status and can
    therefore be walked by an officer, while the completion figure is a single
    unattributable total. The consequence is visible and deliberate: fixture B
    publishes a completed amount of 996,458 and has no payment row, so its
    `variance_sanction_to_disbursement` is `not_published` rather than computed
    from a number nobody can trace.

    Returns `not_published` when no payment row joins, and `published_zero`
    when payments exist and sum to zero - a real zero is a fact about the work,
    not a missing measurement.
    """
    amounts = [
        _field(payment, "paid_amt") for payment in payments or [] if _field(payment, "paid_amt") is not None
    ]
    if not amounts:
        return None, Availability.NOT_PUBLISHED
    total = sum(amounts)
    return total, (Availability.PUBLISHED_ZERO if total == 0 else Availability.PUBLISHED)


def _variance_pct(before, before_availability, after, after_availability):
    """Signed percentage change from one rung to the next.

    Negative when less money arrived than left, which on this corpus is always:
    the maximum measured variance is exactly 0.00%, so no work in the sample is
    disbursed more than it was sanctioned.

    Returns None with a reason rather than 0.0 when either rung is missing or
    the upper rung is zero. "We could not measure this hop" and "this hop is
    clean" are different findings and everything downstream depends on telling
    them apart.
    """
    if before is None:
        return None, before_availability
    if before == 0:
        # A published zero cannot be a denominator, and saying so is different
        # from saying the figure was never published.
        return None, Availability.PUBLISHED_ZERO
    if after is None:
        return None, after_availability
    return (after - before) / before * 100, Availability.PUBLISHED


def variance_sanction_to_disbursement(sanction, payments):
    """Fund hop 1. Computable for the 3,529 works an expenditure row joins to.

    None with reason `not_published` on the other 23,549 sanctioned works,
    because the expenditure export is truncated and joins to 15.70% of them
    (DATA-PROFILE.md section 3). That is a reporting gap, and `utilisation_shortfall`
    is skipped rather than passed on every one of them.
    """
    sanctioned = _field(sanction, "sanctioned_amt")
    disbursed, disbursed_availability = disbursed_amount(payments)
    return _variance_pct(
        sanctioned,
        Availability.NOT_PUBLISHED,
        disbursed,
        disbursed_availability,
    )


def variance_disbursement_to_certification(payments, certification):
    """Fund hop 2. `not_published` on every real work in the corpus, forever.

    MoSPI publishes no utilisation certificate date and no certified amount, so
    the `certifications` table holds exactly one row and that row is the
    labelled synthetic control (DATA-PROFILE.md section 8). The hop is retained
    with a derivation function and a test precisely so that the gap is measured
    rather than hidden - it is entry one in the ablation report, and it is what
    fixture C exists to exercise.
    """
    disbursed, disbursed_availability = disbursed_amount(payments)
    certified = _field(certification, "certified_amt")
    certified_availability = _availability_of(certification, "certified_availability")
    if certification is None:
        certified_availability = Availability.NOT_PUBLISHED
    return _variance_pct(
        disbursed,
        disbursed_availability,
        certified,
        certified_availability,
    )


# --------------------------------------------------------------------------
# Lifecycle ladder
# --------------------------------------------------------------------------


def _days_between(start, end):
    return (end - start).days if start is not None and end is not None else None


def sanction_lag_days(sanction):
    """Lag 1: recommendation to sanction. Whole days, date to date.

    Never skipped on the current corpus: both dates are published in the
    sanctioned export itself, so the population is all 27,078 sanctioned works
    and not only the 14,831 that also appear in the recommended export
    (DATA-PROFILE.md section 6). A work can have no recommendation *amount* and
    still have a recommendation *date*, which is fixture A exactly.
    """
    recommended = _field(sanction, "recommended_date")
    sanctioned = _field(sanction, "sanction_date")
    days = _days_between(recommended, sanctioned)
    if days is None:
        return None, _availability_of(sanction, "recommended_date_availability")
    return days, Availability.PUBLISHED


def sanction_to_first_payment_days(sanction, payments):
    """Lag 2: sanction to the earliest payment date.

    None with reason `not_applicable` when the work has no payment row: as far
    as the published record goes it has not reached the payment stage, which is
    a statement about the work rather than about MoSPI's reporting. It is
    `not_published` in the one other case - payment rows exist but none carries
    a date, which is a portal omission. Zero rows are in that state on this
    corpus and the branch is covered by a unit test, because a branch nothing
    exercises is the defect invariant 3 exists to prevent.
    """
    dates = _payment_dates(payments)
    if not dates:
        if payments:
            return None, Availability.NOT_PUBLISHED
        return None, Availability.NOT_APPLICABLE
    return _days_between(_field(sanction, "sanction_date"), dates[0]), Availability.PUBLISHED


def first_payment_to_completion_days(payments, completion):
    """Lag 3: first payment to completion. **Signed, and never clamped.**

    163 works in the corpus are reported complete BEFORE their first recorded
    payment, the earliest by 446 days (DATA-PROFILE.md section 6). Neither
    source row is malformed - the completed export and the expenditure export
    simply disagree - so this is not an ingest reject, and clamping the lag to
    zero would erase the disagreement instead of showing it. The negative value
    is carried through to the ladder, where an officer can see it.
    """
    dates = _payment_dates(payments)
    completed = _field(completion, "completion_date")
    if not dates:
        return None, (Availability.NOT_PUBLISHED if payments else Availability.NOT_APPLICABLE)
    if completed is None:
        return None, Availability.NOT_APPLICABLE
    return _days_between(dates[0], completed), Availability.PUBLISHED


def execution_days(sanction, completion):
    """Sanction to completion, computed DIRECTLY and not as a sum of lags.

    This is the whole reason `execution_delay` can fire on 2,568 works when the
    payment join only reaches 3,529 of them. It is None with reason
    `not_applicable` when no completion has been reported - the work is not
    finished, which is not a reporting gap - and that is 14,104 of the 27,078
    sanctioned works.
    """
    completed = _field(completion, "completion_date")
    if completed is None:
        return None, Availability.NOT_APPLICABLE
    return _days_between(_field(sanction, "sanction_date"), completed), Availability.PUBLISHED


def days_since_last_payment(payments):
    """Silence since the most recent payment, measured to `DATA_AS_OF`.

    Measured against 2026-08-24, the maximum payment date in the corpus, and
    never against `today`. Otherwise a case re-derived six months from now
    would score differently from the case the officer acted on and the audit
    trail would be a lie (DOMAIN-MODEL.md section f).
    """
    dates = _payment_dates(payments)
    if not dates:
        return None, Availability.NOT_PUBLISHED
    return _days_between(dates[-1], DATA_AS_OF), Availability.PUBLISHED


def _payment_dates(payments):
    return sorted(
        d for d in (_field(p, "payment_date") for p in payments or []) if d is not None
    )


# --------------------------------------------------------------------------
# Repetition, concentration, evidence and the account rung
# --------------------------------------------------------------------------


def vendor_share_in_agency_pct(work, payments, context: CorpusContext):
    """One vendor's share of everything its agency has disbursed, on any work.

    The vendor is this work's largest recipient. The denominator is the
    agency's total disbursement across all of its works, not just its
    sanctioned ones: restricting it turns a 17% vendor into a 100% one
    (DATA-PROFILE.md section 6).

    None with reason `not_published` when the work has no payment to attribute,
    and `not_applicable` when the agency has disbursed Rs 50 lakh or less in
    total - below that floor a single vendor's share means nothing, and the
    rule genuinely does not apply rather than passing. 137 of the 3,529 works
    with a payment are in the second state.
    """
    agency_id = _field(work, "agency_id")
    if not payments:
        return None, Availability.NOT_PUBLISHED
    if agency_id is None:
        return None, Availability.NOT_PUBLISHED
    total = context.agency_disbursed.get(agency_id, 0)
    if total <= VENDOR_CONCENTRATION_AGENCY_FLOOR:
        return None, Availability.NOT_APPLICABLE
    by_vendor: dict = defaultdict(int)
    for payment in payments:
        vendor_id = _field(payment, "vendor_id")
        amount = _field(payment, "paid_amt")
        if vendor_id is not None and amount is not None:
            by_vendor[vendor_id] += amount
    if not by_vendor:
        return None, Availability.NOT_PUBLISHED
    vendor_id = max(by_vendor, key=lambda v: (by_vendor[v], -v))
    share = context.agency_vendor_disbursed.get((agency_id, vendor_id), 0)
    return share / total * 100, Availability.PUBLISHED


def completed_without_payment(work, payments):
    """Reported complete with no payment row at all. Fires on 1,371 works.

    None with reason `not_published` when the portal published no status. Zero
    works are in that state on this corpus: the status column is published on
    every sanctioned row.
    """
    status = _field(work, "status")
    if status is None:
        return None, _availability_of(work, "status_availability")
    return (status == STATUS_WORK_COMPLETED and not payments), Availability.PUBLISHED


def asset_image_absent(work):
    """No photograph filed - but only where the portal published the column.

    The `Image` column appears ONLY in the completed export, so a sanctioned
    work not yet reported complete has no image field to read. That is
    `not_published` on 14,104 of 27,078 sanctioned works, and it is a different
    finding from the 4,493 whose column WAS published reading `N/A`. Collapsing
    the two would fire `asset_evidence_missing` on a reporting gap across 52%
    of the corpus, which is exactly what invariant 2 exists to prevent.
    """
    availability = _availability_of(work, "asset_image_availability")
    if availability == Availability.NOT_PUBLISHED:
        return None, availability
    present = _field(work, "asset_image_present")
    if present is None:
        return None, Availability.NOT_PUBLISHED
    return (not present), Availability.PUBLISHED


def mp_utilisation_pct(work, context: CorpusContext):
    """Sanctioned over allocated for this work's member, term to date.

    The portal publishes one cumulative allocation per member and no per-year
    breakdown, so the ratio is term-to-date and the rule's trace row says so.
    None with reason `not_published` when no allocation is published for the
    member, and `published_zero` when the allocation was published AS zero - a
    zero cannot be a denominator, and that is a fact about the published row
    rather than a missing measurement.
    """
    account = context.mp_account.get(_field(work, "mp_id"))
    if account is None:
        return None, Availability.NOT_PUBLISHED
    allocated, availability, sanctioned = account
    if allocated is None:
        return None, _coerce_availability(availability)
    if allocated == 0:
        return None, Availability.PUBLISHED_ZERO
    return (sanctioned or 0) / allocated * 100, Availability.PUBLISHED


def _coerce_availability(raw) -> Availability:
    if isinstance(raw, Availability):
        return raw
    return Availability(str(raw)) if raw is not None else Availability.NOT_PUBLISHED


def duplicate_similarity(work, context: CorpusContext):
    """Best `token_set_ratio` against another work under the same agency, 0-1.

    None with reason `not_published` when the portal published no readable
    description - 50 works with none at all, plus 79 whose description exported
    as question marks and carries no comparable text. None with reason
    `not_applicable` when the agency has no other work with a readable
    description, which is 52 works: a comparison needs something to compare to.
    181 skips in total, matching DATA-PROFILE.md section 6 exactly.

    The value is NOT rounded here. Rounding before the comparison moves 11
    works across the 0.85 threshold and would put the engine out of step with
    the profile's firing count for a reason no officer could see; the trace row
    rounds for display.
    """
    work_pk = _field(work, "id")
    if not context.normalised.get(work_pk):
        return None, Availability.NOT_PUBLISHED
    value = context.similarity.get(work_pk)
    if value is None:
        return None, Availability.NOT_APPLICABLE
    return value, Availability.PUBLISHED


def same_desc_same_agency_count(work, context: CorpusContext):
    """How many sanctioned works under this agency share this exact description.

    Exact match on the normalised description, blocked by canonical agency.
    Fires `split_sanction` on 3,240 works in 275 clusters. None with reason
    `not_published` when there is no readable description or no agency - 129
    works.

    A cluster is a candidate for review and never an accusation. The largest in
    the corpus is 244 high-mast street lights under one district magistrate,
    which is overwhelmingly likely to be 244 street lights.
    """
    work_pk = _field(work, "id")
    if _field(work, "agency_id") is None or not context.normalised.get(work_pk):
        return None, Availability.NOT_PUBLISHED
    return context.cluster_size.get(work_pk), Availability.PUBLISHED


def duplicate_citation(work, context: CorpusContext) -> dict | None:
    """The evidence a fired `duplicate_work` hit must carry.

    A `duplicate_work` hit with status `fired` and a null citation is a failed
    test, not a degraded row (DOMAIN-MODEL.md section h). This is the whole
    justification for letting one model output into the score: the officer is
    handed the matched records and judges for themselves, rather than being
    asked to trust a similarity number.
    """
    from rapidfuzz import fuzz

    from ..constants import DUPLICATE_CITATION_LIMIT

    work_pk = _field(work, "id")
    text = context.normalised.get(work_pk)
    peers = context.similarity_peers.get(work_pk)
    if not text or not peers:
        return None
    cited = peers[:DUPLICATE_CITATION_LIMIT]
    # The components are read against the single best-matching peer, so a
    # reader can see WHY the headline token_set_ratio is what it is - a
    # token_set_ratio of 1.00 beside a partial_ratio of 0.62 is a very
    # different claim from three components all reading 1.00.
    match = context.similarity_best_text.get(work_pk, text)
    return {
        "matched_work_ids": list(cited),
        "matched_case_ids": [case_id_for(work_id) for work_id in cited],
        "cluster_size": context.cluster_size.get(work_pk),
        "shared_description": text,
        "agency": context.agency_name.get(_field(work, "agency_id")),
        "similarity": round(context.similarity.get(work_pk, 0.0), 3),
        "components": {
            "token_set_ratio": round(fuzz.token_set_ratio(text, match) / 100.0, 3),
            "partial_ratio": round(fuzz.partial_ratio(text, match) / 100.0, 3),
            "token_sort_ratio": round(fuzz.token_sort_ratio(text, match) / 100.0, 3),
        },
        "method": SIMILARITY_METHOD,
        "reading": (
            "A cluster for review, not an accusation. Repeated works of this kind - "
            "street lights across a constituency, hand pumps across a block - are "
            "routinely legitimate. Open the cited works and judge."
        ),
    }


# --------------------------------------------------------------------------
# The derivation itself
# --------------------------------------------------------------------------

# Plain-language detail for the contract's `unavailable_fields` block, keyed by
# (feature, reason). What an officer reads when a rung or a rule is blank.
_DETAIL = {
    ("variance_sanction_to_disbursement", Availability.NOT_PUBLISHED): (
        "No expenditure row joins to this work. The expenditure export is truncated and "
        "joins to 3,529 of 27,078 sanctioned works."
    ),
    ("variance_disbursement_to_certification", Availability.NOT_PUBLISHED): (
        "Derived from a certified amount, which MoSPI does not publish for any work."
    ),
    ("execution_days", Availability.NOT_APPLICABLE): (
        "No completion has been reported for this work, so there is no completion date to "
        "measure execution against."
    ),
    ("sanction_to_first_payment_days", Availability.NOT_APPLICABLE): (
        "No payment has been recorded against this work."
    ),
    ("first_payment_to_completion_days", Availability.NOT_APPLICABLE): (
        "The work has not reached both ends of this lag - either no payment or no "
        "completion has been reported."
    ),
    ("days_since_last_payment", Availability.NOT_PUBLISHED): (
        "No payment row joins to this work, so there is no last payment to measure from."
    ),
    ("asset_image_absent", Availability.NOT_PUBLISHED): (
        "The Image column is published only in the completed export. This work has not been "
        "reported complete, so no photograph was ever asked for. This is a reporting gap, "
        "not a finding that no photograph was filed."
    ),
    ("duplicate_similarity", Availability.NOT_PUBLISHED): (
        "The portal published no readable description for this work."
    ),
    ("duplicate_similarity", Availability.NOT_APPLICABLE): (
        "No other work under this agency carries a readable description to compare against."
    ),
    ("same_desc_same_agency_count", Availability.NOT_PUBLISHED): (
        "The portal published no readable description, or no implementing agency, for this work."
    ),
    ("vendor_share_in_agency_pct", Availability.NOT_PUBLISHED): (
        "No payment row joins to this work, so it cannot be attributed to a vendor."
    ),
    ("vendor_share_in_agency_pct", Availability.NOT_APPLICABLE): (
        "This agency's total disbursement is at or below the Rs 50 lakh floor, below which "
        "one vendor's share carries no meaning."
    ),
    ("mp_utilisation_pct", Availability.NOT_PUBLISHED): (
        "No allocation is published for this work's member."
    ),
    ("completed_without_payment", Availability.NOT_PUBLISHED): (
        "The portal published no work status for this work."
    ),
}


def derive(work, sanction, completion, certification, payments, context: CorpusContext) -> FeatureSet:
    """Derive the full feature set for one work. The only derivation path.

    Nothing upstream precomputes any of these values: ingest writes raw rungs
    and this function derives, so a case opened today and a case re-derived in
    six months run through the same arithmetic.
    """
    payments = list(payments or [])
    values: dict = {}
    availability: dict = {}

    def put(key, pair):
        value, reason = pair
        values[key] = value
        availability[key] = reason

    values["work_id"] = _field(work, "work_id_canon")
    availability["work_id"] = Availability.PUBLISHED

    put("variance_sanction_to_disbursement", variance_sanction_to_disbursement(sanction, payments))
    put(
        "variance_disbursement_to_certification",
        variance_disbursement_to_certification(payments, certification),
    )
    put("sanction_lag_days", sanction_lag_days(sanction))
    put("sanction_to_first_payment_days", sanction_to_first_payment_days(sanction, payments))
    put(
        "first_payment_to_completion_days",
        first_payment_to_completion_days(payments, completion),
    )
    put("execution_days", execution_days(sanction, completion))
    put("days_since_last_payment", days_since_last_payment(payments))
    put("duplicate_similarity", duplicate_similarity(work, context))
    put("same_desc_same_agency_count", same_desc_same_agency_count(work, context))
    put("vendor_share_in_agency_pct", vendor_share_in_agency_pct(work, payments, context))
    put("completed_without_payment", completed_without_payment(work, payments))
    put("asset_image_absent", asset_image_absent(work))
    put("mp_utilisation_pct", mp_utilisation_pct(work, context))

    # Never None. Zero payments is a fact about the work, not an unmeasured
    # field; making it nullable would let a real zero masquerade as a gap.
    values["payment_count"] = len(payments)
    availability["payment_count"] = Availability.PUBLISHED

    evidence = {}
    citation = duplicate_citation(work, context)
    if citation is not None:
        evidence["duplicate_work"] = citation

    detail = {
        key: _DETAIL[(key, availability[key])]
        for key in values
        if values[key] is None and (key, availability[key]) in _DETAIL
    }
    return FeatureSet(values, availability, evidence, detail)


# --------------------------------------------------------------------------
# Ladder localisation
# --------------------------------------------------------------------------


def hop_tolerance(rulebook, hop: str) -> float:
    """The variance below which a hop is open, read off the rulebook.

    Hop 1's tolerance is `utilisation_shortfall`'s threshold, so an officer who
    edits the rule moves the ladder with it. Hop 2 has no rule - there is no
    public data to calibrate one against - and falls back to the declared
    default so the ladder can still show a state on the synthetic control. That
    open hop contributes exactly zero points, which is the demonstration
    fixture C exists to make.
    """
    from .rulebook import rule_by_field

    field = _HOP_FIELD[hop]
    rule = rule_by_field(rulebook, field) if rulebook else None
    return rule["threshold"] if rule else FUND_HOP_DEFAULT_TOLERANCE_PCT


_HOP_FIELD = {
    HOP_SANCTION_TO_DISBURSEMENT: "variance_sanction_to_disbursement",
    HOP_DISBURSEMENT_TO_CERTIFICATION: "variance_disbursement_to_certification",
}

_LAG_FIELD = {
    LAG_RECOMMEND_TO_SANCTION: "sanction_lag_days",
    LAG_SANCTION_TO_FIRST_PAYMENT: "sanction_to_first_payment_days",
    LAG_FIRST_PAYMENT_TO_COMPLETION: "first_payment_to_completion_days",
}


def locate_gap(features, rulebook=None) -> str | None:
    """The FIRST open hop, walking down the fund ladder.

    A hop that could not be computed is not a candidate: it is not "0% loss",
    it is unknown, and it is skipped over rather than treated as closed. A case
    with neither hop measurable returns None - fixture B, which has no payment
    row and no certificate.

    First rather than worst, deliberately: the money stops at the earliest open
    rung, and telling an officer the sanction never reached the vendor is more
    actionable than telling them the largest percentage was lost further down.
    """
    for hop in (HOP_SANCTION_TO_DISBURSEMENT, HOP_DISBURSEMENT_TO_CERTIFICATION):
        value = features.get(_HOP_FIELD[hop])
        if value is not None and value < hop_tolerance(rulebook, hop):
            return hop
    return None


def slowest_lag(features) -> str | None:
    """The lifecycle lag with the largest value among those that are computable.

    Ties break in ladder order: if the recommendation and the execution took
    the same number of days, the earlier stage is named, because that is where
    the clock started.

    A comparison over a set of ONE is a legitimate answer and not an error.
    Fixture B has only `recommend_to_sanction` computable - no payment row, no
    payment-side lag - and its slowest lag is that one lag. The lifecycle panel
    shows the other two as unavailable with their reasons, never as zero. If no
    lag is computable at all, this returns None.
    """
    best_lag = None
    best_value = None
    for lag in (
        LAG_RECOMMEND_TO_SANCTION,
        LAG_SANCTION_TO_FIRST_PAYMENT,
        LAG_FIRST_PAYMENT_TO_COMPLETION,
    ):
        value = features.get(_LAG_FIELD[lag])
        if value is None:
            continue
        if best_value is None or value > best_value:
            best_lag, best_value = lag, value
    return best_lag


# --------------------------------------------------------------------------
# The ladders, in the shape the frozen contract prints them
# --------------------------------------------------------------------------

HOP_ACTIONS = {
    HOP_SANCTION_TO_DISBURSEMENT: (
        "Pull the agency's payment register for this work. Confirm whether the balance is "
        "committed against an unpaid bill, unspent, or was returned. If unspent for more "
        "than one financial year, the sanction should be revalidated or surrendered rather "
        "than left standing."
    ),
    HOP_DISBURSEMENT_TO_CERTIFICATION: (
        "Obtain the utilisation certificate from the implementing agency and match the "
        "certified amount and asset description against the sanction. If no UC exists for a "
        "disbursement older than 12 months, that is a recovery proceeding, not a query."
    ),
}

_HOP_LABEL = {
    HOP_SANCTION_TO_DISBURSEMENT: "Sanction to disbursement",
    HOP_DISBURSEMENT_TO_CERTIFICATION: "Disbursement to certification",
}

_LAG_LABEL = {
    LAG_RECOMMEND_TO_SANCTION: "Recommendation to sanction",
    LAG_SANCTION_TO_FIRST_PAYMENT: "Sanction to first payment",
    LAG_FIRST_PAYMENT_TO_COMPLETION: "First payment to completion",
}


def fund_ladder(features, sanction, payments, certification, rulebook=None) -> dict:
    """The three rungs and two hops, with each hop's state and officer action."""
    sanctioned = _field(sanction, "sanctioned_amt")
    disbursed, disbursed_availability = disbursed_amount(payments)
    certified = _field(certification, "certified_amt")
    certified_availability = (
        _availability_of(certification, "certified_availability")
        if certification is not None
        else Availability.NOT_PUBLISHED
    )
    rungs = [
        {
            "key": "sanctioned_amt",
            "label": "Sanctioned",
            "amount": sanctioned,
            "availability": Availability.PUBLISHED.value
            if sanctioned is not None
            else Availability.NOT_PUBLISHED.value,
            "recommended_amt": _field(sanction, "recommended_amt"),
            "recommended_equals_sanctioned": (
                None
                if _field(sanction, "recommended_amt") is None
                else _field(sanction, "recommended_amt") == sanctioned
            ),
        },
        {
            "key": "disbursed_amt",
            "label": "Disbursed",
            "amount": disbursed,
            "availability": disbursed_availability.value,
        },
        {
            "key": "certified_amt",
            "label": "Certified",
            "amount": certified,
            "availability": certified_availability.value,
            "note": (
                "MoSPI publishes no utilisation certificate date or certified amount. "
                "See docs/domain/DOMAIN-MODEL.md (i), ablation entry 1."
            ),
        },
    ]

    hops = []
    for hop in (HOP_SANCTION_TO_DISBURSEMENT, HOP_DISBURSEMENT_TO_CERTIFICATION):
        field = _HOP_FIELD[hop]
        variance = features.get(field)
        tolerance = hop_tolerance(rulebook, hop)
        row = {
            "key": hop,
            "label": _HOP_LABEL[hop],
            "variance_pct": None if variance is None else round(variance, 2),
            "tolerance_pct": tolerance,
            "state": "unavailable"
            if variance is None
            else ("open" if variance < tolerance else "closed"),
            "hop_action": HOP_ACTIONS[hop],
        }
        if variance is None:
            row["unavailable_reason"] = features.availability[field].value
        hops.append(row)
    return {"rungs": rungs, "hops": hops}


def lifecycle_ladder(features, sanction, payments, completion) -> dict:
    """The four dates and three lags, each unavailable one carrying its reason."""
    payment_dates = _payment_dates(payments)
    first = payment_dates[0] if payment_dates else None
    last = payment_dates[-1] if payment_dates else None

    def date_row(key, label, value, reason):
        row = {
            "key": key,
            "label": label,
            "date": value,
            "availability": Availability.PUBLISHED.value if value is not None else reason.value,
        }
        if value is None:
            row["unavailable_reason"] = reason.value
        return row

    dates = [
        date_row(
            "recommended_date",
            "Recommended",
            _field(sanction, "recommended_date"),
            _availability_of(sanction, "recommended_date_availability"),
        ),
        date_row(
            "sanction_date", "Sanctioned", _field(sanction, "sanction_date"), Availability.NOT_PUBLISHED
        ),
        date_row(
            "first_payment_date",
            "First payment",
            first,
            features.availability["sanction_to_first_payment_days"],
        ),
        date_row(
            "completion_date",
            "Completed",
            _field(completion, "completion_date"),
            Availability.NOT_APPLICABLE
            if completion is None
            else _availability_of(completion, "completion_date_availability"),
        ),
    ]

    lags = []
    for lag in (
        LAG_RECOMMEND_TO_SANCTION,
        LAG_SANCTION_TO_FIRST_PAYMENT,
        LAG_FIRST_PAYMENT_TO_COMPLETION,
    ):
        field = _LAG_FIELD[lag]
        days = features.get(field)
        row = {
            "key": lag,
            "label": _LAG_LABEL[lag],
            "days": days,
            "state": "computed" if days is not None else "unavailable",
        }
        if days is None:
            row["unavailable_reason"] = features.availability[field].value
        lags.append(row)

    return {
        "dates": dates,
        "lags": lags,
        "last_payment_date": last,
        "payment_count": features["payment_count"],
    }
