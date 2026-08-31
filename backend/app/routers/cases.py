"""Case endpoints: the ranked list, the case sheet, notes and recompute.

**Cases are not derived here.** `python -m app.derive_all` opens a case for
every sanctioned work, stores the score, the full ten-row trace and the opening
audit events, and this router reads them. The inherited LEAKPROOF routers
derived lazily on the first request, which was tolerable over 60 shops and is
not tolerable over 27,079 works: the derivation costs a corpus-wide similarity
matrix and two full scoring passes, minutes rather than milliseconds, and two
concurrent first requests would both run it against a half-written table. See
`app/derive_all.py` for the whole argument.

So the score, the severity, the coverage and every trace row this file returns
are the STORED ones - what was decided on the day, under the rulebook version
named on the case.

**What IS derived per request, and why that is not a second scoring path.**
The two ladders, the `unavailable_fields` block and the memo are presentation
of a case rather than a score for one. They are rebuilt by calling the same
`engine/derive.py` functions the build step called, over the same raw rows, so
they cannot disagree with the stored trace. Storing them would have meant
either new columns in `models.py` - which this phase does not touch - or a
second copy of numbers that already exist in `sanctions`, `payments` and
`completions`, which is the shape of defect that lets two screens print two
different figures for one work.

**The corpus context is scoped to the work's agency and member, and that is
exact rather than approximate.** Four of the fourteen derived features are
properties of the corpus around a work rather than of the work:
`duplicate_similarity` and `same_desc_same_agency_count` are blocked by agency,
`vendor_share_in_agency_pct` is a share of one agency's disbursement, and
`mp_utilisation_pct` reads one member's account row. Every one of them is
therefore fully determined by that work's agency and that work's member, so a
context built from those two produces byte-identical features to the
corpus-wide context `derive_all` used - proved for every work in the corpus by
`tests/test_api.py::test_the_scoped_context_reproduces_the_corpus_wide_one`,
not asserted here. It costs 5-60 ms instead of 5 s.

**Role scoping.** Every case-bearing query in this file goes through
`scoping.scoped_cases(user)`, which returns the base select already narrowed to
what the caller's role may reach - `Work.state_id == S` for a State Nodal
officer, `state_id == S AND district == D` for a District Authority,
`Work.mp_id == M` for a member. It is applied BEFORE the query-parameter
filters below, so `?district=` can only narrow the scope further and never
reach outside it, and an out-of-scope case id returns 404 rather than 403 so
that a status code cannot confirm the existence of another district's case.
Nothing in this file filters rows in Python after a query has run. The rules
live in `routers/scoping.py`; the endpoint-by-endpoint commitment they keep is
`docs/api/ROLE-SCOPING-PLAN.md`.

**The two writes are refused to the member of parliament**, through
`auth.require_write`, before the case is even fetched. An MP can see, and
cannot annotate, escalate, resolve or recompute: the scheme's subject does not
adjudicate the scheme's findings (DOMAIN-MODEL.md (k)).
"""

from __future__ import annotations

import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from ..constants import (
    DATA_AS_OF,
    FY_TERM_TO_DATE,
    ML_KIND_ANOMALY,
    ML_KIND_FORECAST,
    ML_KIND_GRAPH,
    Availability,
)
from ..auth import get_current_user, require_write
from ..db import get_db
from ..engine import derive as derive_mod
from ..engine import memo as memo_mod
from ..engine.audit import log, recompute as recompute_case
from ..ml.badges import attach
from ..ml.base import Finding
from ..models import (
    Agency,
    AgencyNameVariant,
    Case,
    Certification,
    Completion,
    Constituency,
    FundAccount,
    MLFinding,
    MP,
    Payment,
    RuleHit,
    RulebookVersion,
    Sanction,
    State,
    User,
    Work,
)
from ..schemas import CaseDetail, CaseListItem, CaseListPage, NoteIn, NoteOut, RecomputeOut
from .scoping import scope_works, scoped_cases

router = APIRouter(prefix="/cases", tags=["cases"])

EVENT_NOTE_ADDED = "NOTE_ADDED"
EVENT_CASE_OPENED = "CASE_OPENED"

# Highest score first - that IS the triage order. Ties break on the uncapped
# raw score, so a case that scored 118 and displays 100 outranks one that
# scored exactly 100; then on coverage, because between two cases on the same
# number the one we could evaluate more fully is the one whose score we can
# stand behind; then on case id, so the order is total and a page boundary
# never drops or repeats a row.
RANKED_BY = "score desc, raw_score desc, coverage_pct desc, case_id"

NOT_MATERIALISED = (
    "No cases have been derived yet. Run `python -m app.derive_all` in backend/ "
    "after `python -m ingest.run`. Cases are a build step, not a side effect of "
    "the first request (app/derive_all.py)."
)


# ---------------------------------------------------------------------------
# Reading the corpus, through the caller's scope
# ---------------------------------------------------------------------------
#
# `scoped_cases` and `scope_works` live in `routers/scoping.py`. They are
# imported rather than restated here so that the audit question - "where is the
# predicate?" - has one answer for the whole package.


def list_query(user: User) -> Select:
    """The ranked list, as one join rather than a row-at-a-time lookup.

    Every column a triage row shows is selected here, so a page of 50 costs one
    query. The obvious alternative - fetch the cases, then look up each work's
    state, agency, member and sanctioned amount - is 200 round trips for the
    same page, and it gets worse as the page grows.

    `agencies` is an OUTER join: `works.agency_id` is null where the portal
    published a blank implementing agency, and those cases are still cases.

    Scoped to `user` before it is returned, so every caller of this helper -
    the ranked list, the district queue, a member's worst cases - inherits the
    predicate without having to remember it.
    """
    query = (
        select(
            Case.case_id,
            Work.work_id_canon,
            Work.description,
            Work.category,
            State.name.label("state"),
            Work.district,
            Agency.name_canon.label("agency"),
            MP.name_canon.label("mp_name"),
            Case.score,
            Case.raw_score,
            Case.severity,
            Case.status,
            Case.coverage_pct,
            Case.gap_hop,
            Case.slowest_lag,
            Case.corroboration_bonus,
            Sanction.sanctioned_amt,
            Case.opened_at,
            Case.is_synthetic,
        )
        .join(Work, Work.id == Case.work_id)
        .join(State, State.id == Work.state_id)
        .join(MP, MP.id == Work.mp_id)
        .join(Sanction, Sanction.work_id == Work.id)
        .outerjoin(Agency, Agency.id == Work.agency_id)
    )
    # The role predicate, on the select rather than on its results, and before
    # any endpoint's own filters (CLAUDE.md invariant 10).
    return scope_works(query, user)


def list_item(row) -> CaseListItem:
    """One `list_query` row as a triage row. Field names match, so this is a map."""
    return CaseListItem(
        case_id=row.case_id,
        work_id=row.work_id_canon,
        description=row.description,
        category=row.category,
        state=row.state,
        district=row.district,
        agency=row.agency,
        mp_name=row.mp_name,
        score=row.score,
        raw_score=row.raw_score,
        severity=row.severity,
        status=row.status,
        coverage_pct=row.coverage_pct,
        gap_hop=row.gap_hop,
        slowest_lag=row.slowest_lag,
        corroboration_bonus=row.corroboration_bonus,
        sanctioned_amt=row.sanctioned_amt,
        opened_at=row.opened_at,
        is_synthetic=bool(row.is_synthetic),
    )


def _case_or_404(db: Session, case_id: str, user: User) -> tuple[Case, Work]:
    """One case, through the scoped select. 404 when it is not in scope.

    404 rather than 403 on purpose: a 403 would confirm that another district's
    case id is real, which is a scoping leak spelled with a status code. A case
    outside the caller's scope is indistinguishable from a case id that was
    never issued, which is exactly as much as the caller is entitled to learn.
    """
    row = db.execute(scoped_cases(user).where(Case.case_id == case_id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No case {case_id}")
    return row[0], row[1]


# ---------------------------------------------------------------------------
# Reading a case's raw rows and rebuilding its feature set
# ---------------------------------------------------------------------------


def case_context(db: Session, work: Work) -> derive_mod.CorpusContext:
    """A `CorpusContext` covering exactly this work's agency and member.

    Exact, not approximate - see the module docstring. Three queries: the
    agency's payments (for the vendor share), the agency's sanctioned works
    with their descriptions (for the similarity block and the cluster count),
    and the member's term-to-date account row.
    """
    context = derive_mod.CorpusContext()

    if work.agency_id is not None:
        context.agency_name[work.agency_id] = db.scalar(
            select(Agency.name_canon).where(Agency.id == work.agency_id)
        )
        agency_total = 0
        vendor_total: dict = defaultdict(int)
        rows = db.execute(
            select(Payment.vendor_id, Payment.paid_amt)
            .join(Work, Work.id == Payment.work_id)
            .where(Work.agency_id == work.agency_id, Payment.paid_amt.is_not(None))
        )
        for vendor_id, paid in rows:
            agency_total += paid
            if vendor_id is not None:
                vendor_total[(work.agency_id, vendor_id)] += paid
        # Absent rather than zero when the agency has never paid anyone:
        # `derive.vendor_share_in_agency_pct` reads a missing key as
        # `not_published`, and a stored 0 would read as a published zero.
        context.agency_disbursed = {work.agency_id: agency_total} if agency_total else {}
        context.agency_vendor_disbursed = dict(vendor_total)

        # Sanctioned works only - the population a case can be opened for
        # (DOMAIN-MODEL.md (a)) - which is the same population `derive_all`
        # blocked on, so the similarity ranking and the cited peers match.
        context.load_descriptions(
            db.execute(
                select(Work.id, Work.work_id_canon, Work.agency_id, Work.description)
                .join(Sanction, Sanction.work_id == Work.id)
                .where(Work.agency_id == work.agency_id)
            ).all()
        )

    account = db.execute(
        select(
            FundAccount.allocated_amt,
            FundAccount.allocated_availability,
            FundAccount.sanctioned_amt,
        ).where(FundAccount.mp_id == work.mp_id, FundAccount.fy == FY_TERM_TO_DATE)
    ).first()
    if account is not None:
        context.mp_account[work.mp_id] = tuple(account)
    return context


def case_rows(db: Session, work: Work) -> dict:
    """The raw rows one case is derived and narrated from."""
    return {
        "sanction": db.scalar(select(Sanction).where(Sanction.work_id == work.id)),
        "completion": db.scalar(select(Completion).where(Completion.work_id == work.id)),
        "certification": db.scalar(select(Certification).where(Certification.work_id == work.id)),
        "payments": list(db.scalars(select(Payment).where(Payment.work_id == work.id))),
    }


def features_for(db: Session, work: Work, rows=None) -> derive_mod.FeatureSet:
    """The derived feature set for one work, through the one derivation path."""
    rows = rows or case_rows(db, work)
    return derive_mod.derive(
        work,
        rows["sanction"],
        rows["completion"],
        rows["certification"],
        rows["payments"],
        case_context(db, work),
    )


# ---------------------------------------------------------------------------
# Stored rows back into the shapes the contract prints
# ---------------------------------------------------------------------------


def _typed(text: str | None):
    """A stored trace value, back in the type it was measured in.

    `rule_hits.raw_value` and `rule_hits.threshold` are text columns because one
    column has to carry a percentage, a whole count, a boolean and a null. The
    frozen contract prints -40.01, 333, false and null with their JSON types, so
    the round trip is completed here rather than pushed onto the frontend.

    This is a rendering step and nothing more: the comparison a recompute makes
    stringifies both sides through `engine.audit.summarise_trace`, so what is
    stored stays the thing that is compared.
    """
    if text is None:
        return None
    if text == "True":
        return True
    if text == "False":
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def trace_rows(db: Session, case_id: str) -> list[dict]:
    """The stored ten-row trace, in rulebook order, as the contract prints it."""
    hits = db.scalars(
        select(RuleHit).where(RuleHit.case_id == case_id).order_by(RuleHit.id)
    ).all()
    return [
        {
            "rule_id": hit.rule_id,
            "label": hit.label,
            "field": hit.field,
            "raw_value": _typed(hit.raw_value),
            "operator": hit.operator,
            "threshold": _typed(hit.threshold),
            "weight": hit.weight,
            "contribution": hit.contribution,
            "severity": hit.severity,
            "status": hit.status,
            "skip_reason": hit.skip_reason,
            "citation": json.loads(hit.citation_json) if hit.citation_json else None,
            "caveat": hit.caveat,
        }
        for hit in hits
    ]


def corroboration_block(db: Session, case: Case) -> dict:
    """The F4 block, read off the case's own CASE_OPENED audit row.

    `cases` stores whether the bonus was awarded and not the count behind it,
    because - as `engine/score.py` puts it - the count was a fact about the
    corpus on the day rather than a fact about this work. `derive_all` writes
    the whole block into the opening event for exactly this read, so the number
    an officer sees is the number that was written down when the case was
    opened, hash-chained, rather than a figure recomputed against a corpus that
    has moved on.

    Falls back to a block built from the stored bonus if the opening event is
    missing, so a case is still renderable rather than a 500.
    """
    from ..models import AuditLog

    payload = db.scalar(
        select(AuditLog.payload_json)
        .where(AuditLog.case_id == case.case_id, AuditLog.event == EVENT_CASE_OPENED)
        .order_by(AuditLog.id)
        .limit(1)
    )
    if payload:
        block = (json.loads(payload) or {}).get("corroboration")
        if block:
            return block
    return {
        "rule_id": "agency_pattern_bonus",
        "applied": bool(case.corroboration_bonus),
        "weight": case.corroboration_bonus or 0,
        "contribution": case.corroboration_bonus or 0,
        "min_high_cases": 3,
        "window": f"FY{case.work.fy}",
        "agency": None,
        "high_case_count": 0,
        "matched_case_ids": [],
    }


def ml_findings_for(db: Session, work_pk: int) -> dict:
    """The stored badge rows for one work, back as `ml.base.Finding` objects.

    Rebuilt as real `Finding`s rather than as loose dicts so that the same
    validation `ml/run.py` wrote them under holds on the way out: a value
    without a `published` availability, or an availability with no value, is a
    contradiction and `Finding.__post_init__` refuses it in both directions.
    """
    out: dict = {}
    rows = db.scalars(select(MLFinding).where(MLFinding.work_id == work_pk)).all()
    for row in rows:
        payload = json.loads(row.payload_json) if row.payload_json else {}
        availability = Availability(payload.pop("availability", Availability.PUBLISHED.value))
        out[row.kind] = Finding(
            work_pk=row.work_id,
            kind=row.kind,
            value=row.value,
            availability=availability,
            payload=payload,
            model_version=row.model_version,
            contributes_to_score=bool(row.contributes_to_score),
        )
    return out


def _work_ref(db: Session, work: Work, state_name: str, agency_name: str | None) -> dict:
    raw = None
    if work.agency_id is not None:
        raw = db.scalar(
            select(AgencyNameVariant.name_raw)
            .where(AgencyNameVariant.agency_id == work.agency_id)
            .order_by(AgencyNameVariant.score.desc(), AgencyNameVariant.id)
            .limit(1)
        )
    return {
        "id": work.id,
        "work_id": work.work_id_canon,
        "work_id_raw": work.work_id_raw,
        "category": work.category,
        "description": work.description,
        "state": state_name,
        "district": work.district,
        "agency": agency_name,
        "agency_name_raw": raw,
        "status": work.status,
        "asset_image_present": work.asset_image_present,
        "fy": work.fy,
        "is_synthetic": bool(work.is_synthetic),
    }


def _mp_ref(db: Session, mp: MP) -> dict:
    constituency = None
    if mp.constituency_id is not None:
        constituency = db.scalar(
            select(Constituency.name).where(Constituency.id == mp.constituency_id)
        )
    term = None
    if mp.term_start is not None and mp.term_end is not None:
        term = f"{mp.term_start}-{mp.term_end}"
    return {
        "id": mp.id,
        "name": mp.name_canon,
        "house": mp.house,
        "constituency": constituency,
        "state": db.scalar(select(State.name).where(State.id == mp.state_id)),
        "term": term,
    }


def build_case_detail(db: Session, case: Case, work: Work) -> dict:
    """Assemble one case sheet from stored rows plus re-derived presentation."""
    rows = case_rows(db, work)
    features = features_for(db, work, rows)
    agency_name = (
        db.scalar(select(Agency.name_canon).where(Agency.id == work.agency_id))
        if work.agency_id is not None
        else None
    )
    version = db.get(RulebookVersion, case.rulebook_version_id)
    hits = trace_rows(db, case.case_id)
    corroboration = corroboration_block(db, case)

    # The body shape `engine/score.compute` returns, rebuilt from the stored
    # decision. `memo.build_memo` and `badges.attach` both read it, and both
    # are given exactly what they were given at build time.
    body = {
        "score": case.score,
        "raw_score": case.raw_score,
        "score_cap": 100,
        "severity": case.severity,
        "coverage_pct": case.coverage_pct,
        "coverage_basis": (
            f"{sum(hit['weight'] for hit in hits if hit['status'] != 'skipped')} of "
            f"{sum(hit['weight'] for hit in hits)} rulebook weight points were evaluable. "
            "Skipped weight is never redistributed."
        ),
        "rulebook_version": version.version if version else None,
        "rule_hits": hits,
        "corroboration": corroboration,
    }

    facts = memo_mod.case_facts(
        work, rows["sanction"], rows["payments"], rows["completion"], agency_name=agency_name
    )
    badges = ml_findings_for(db, work.id)
    badged = attach(
        body,
        anomaly=badges.get(ML_KIND_ANOMALY),
        forecast=badges.get(ML_KIND_FORECAST),
        concentration=badges.get(ML_KIND_GRAPH),
    )

    return {
        "case_id": case.case_id,
        "work": _work_ref(db, work, db.scalar(select(State.name).where(State.id == work.state_id)), agency_name),
        "mp": _mp_ref(db, db.get(MP, work.mp_id)),
        "score": case.score,
        "raw_score": case.raw_score,
        "score_cap": body["score_cap"],
        "severity": case.severity,
        "status": case.status,
        "opened_at": case.opened_at,
        "data_as_of": DATA_AS_OF,
        "fund_ladder": derive_mod.fund_ladder(
            features, rows["sanction"], rows["payments"], rows["certification"]
        ),
        "lifecycle_ladder": derive_mod.lifecycle_ladder(
            features, rows["sanction"], rows["payments"], rows["completion"]
        ),
        "gap_hop": case.gap_hop,
        "slowest_lag": case.slowest_lag,
        "coverage_pct": case.coverage_pct,
        "coverage_basis": body["coverage_basis"],
        "unavailable_fields": features.unavailable_fields(),
        "rulebook_version": version.version if version else "",
        "rulebook_version_sha256": version.yaml_sha256 if version else "",
        "rule_hits": hits,
        "corroboration": corroboration,
        "statistical": badged["statistical"],
        "forecast": badged["forecast"],
        "concentration": badged["concentration"],
        "memo": memo_mod.build_memo(features, body, facts),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=CaseListPage)
def list_cases(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    severity: str | None = Query(default=None, description="HIGH, MEDIUM or LOW"),
    state: str | None = Query(default=None),
    district: str | None = Query(default=None),
    agency: str | None = Query(default=None, description="canonical agency name"),
    status: str | None = Query(default=None, description="open, under_review, escalated, resolved"),
    include_synthetic: bool = Query(
        default=False,
        description=(
            "Include the labelled synthetic control. Excluded by default: invariant 12 "
            "keeps injected rows out of every published aggregate."
        ),
    ),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """The ranked case list. Highest score first - that IS the triage order.

    Filters narrow; they never widen. The role predicate is already on the
    select `list_query` returns, applied before any of the filters below, so
    `?district=` cannot reach outside the caller's own scope - it can only
    select a subset of what that scope already allows. A District Authority
    passing another district's name gets an empty page, not that district.
    """
    query = list_query(user)
    if severity:
        query = query.where(Case.severity == severity.upper())
    if state:
        query = query.where(State.name == state)
    if district:
        query = query.where(Work.district == district)
    if agency:
        query = query.where(Agency.name_canon == agency)
    if status:
        query = query.where(Case.status == status)
    if not include_synthetic:
        query = query.where(Case.is_synthetic.is_(False))

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    ranked = (
        query.order_by(
            Case.score.desc(), Case.raw_score.desc(), Case.coverage_pct.desc(), Case.case_id
        )
        .limit(limit)
        .offset(offset)
    )
    return CaseListPage(
        total=total or 0,
        limit=limit,
        offset=offset,
        ranked_by=RANKED_BY,
        items=[list_item(row) for row in db.execute(ranked).all()],
    )


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """One case sheet: both ladders, the trace, coverage, badges and the memo.

    The same object for every role that can reach it. What a role changes is
    which cases it can reach, never which keys a case carries - so a District
    Authority reading a case in their district gets exactly what the Ministry
    gets (DOMAIN-MODEL.md (k), `schemas.py`).
    """
    case, work = _case_or_404(db, case_id, user)
    return CaseDetail(**build_case_detail(db, case, work))


@router.post("/{case_id}/notes", response_model=NoteOut, status_code=201)
def add_note(
    case_id: str,
    note: NoteIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_write),
):
    """An officer's note. It lands in the audit trail and nowhere else.

    There is no notes table: a note IS an audit event (DOMAIN-MODEL.md (j)),
    hash-chained like every other row, so a note cannot be edited or removed
    after the fact any more than a score can.

    The actor comes from the token. Until Phase 6 the caller declared which role
    was writing and the trail recorded what was declared, which made the actor
    line on an append-only row a client-supplied string; it is now the
    authenticated role and the authenticated user id, so the trail records who
    wrote a note rather than who said they did.

    Refused outright to the member of parliament by `require_write`, before the
    case is fetched - so an out-of-scope note cannot reach `audit_log` and a
    member's attempt does not even confirm whether the case exists.
    """
    case, _work = _case_or_404(db, case_id, user)

    text = note.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="A note needs text")

    row = log(
        db,
        EVENT_NOTE_ADDED,
        user.role,
        case_id=case.case_id,
        actor_id=user.id,
        payload={"text": text},
    )
    db.commit()
    db.refresh(row)
    return NoteOut(
        case_id=case.case_id,
        event={
            "id": row.id,
            "at": row.at,
            "actor_role": row.actor_role,
            "actor_id": row.actor_id,
            "event": row.event,
            "case_id": row.case_id,
            "payload": json.loads(row.payload_json) if row.payload_json else None,
            "prev_hash": row.prev_hash,
            "row_hash": row.row_hash,
        },
    )


@router.post("/{case_id}/recompute", response_model=RecomputeOut)
def recompute(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_write),
):
    """Re-derive this case against its OWN rulebook snapshot and report what moved.

    Wired straight to `engine.audit.recompute`, which reads the snapshot stored
    in `rulebook_versions` through `cases.rulebook_version_id` and compares the
    full trace rather than the scalar score (CLAUDE.md invariant 5). This router
    supplies only the callable that re-derives the features; it does not
    reimplement any part of the comparison.

    The stored case is left exactly as it was. If the two disagree, the
    disagreement is the finding.

    Refused to the member of parliament, and the resulting `SCORE_RECOMPUTED`
    row carries the officer who asked for it rather than a default role.
    """
    case, work = _case_or_404(db, case_id, user)
    outcome = recompute_case(
        db, case, lambda: features_for(db, work), actor_role=user.role, actor_id=user.id
    )
    db.commit()
    return RecomputeOut(
        case_id=case.case_id,
        rulebook_version=outcome["rulebook_version"],
        identical=outcome["identical"],
        stored=outcome["stored"],
        recomputed=outcome["recomputed"],
        trace_diff=outcome["trace_diff"],
        stored_trace=outcome["stored_trace"],
        recomputed_trace=outcome["recomputed_trace"],
    )
