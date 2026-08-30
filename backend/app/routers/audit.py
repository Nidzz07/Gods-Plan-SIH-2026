"""Audit endpoint - F6's surface.

Read-only, and permanently so. There are two routes here and both return rows.
No route in this file may ever offer an edit or a removal of an audit row: the
trail is the one thing in NIGRANI that an auditor is entitled to assume nobody
in this codebase can touch (CLAUDE.md invariant 4).

The trail is ordered oldest first. It is read as a narrative of what happened
to the case, and a narrative runs forwards.

**Two different integrity claims, at two URLs, because they cost different
things and prove different things.**

`GET /api/audit/{case_id}` returns `rows_intact`: every row it is about to
return has had its `row_hash` recomputed from its own stored columns and its
own stored `prev_hash`. That catches any alteration of a row's content -
somebody reaching the SQLite file and changing a note, a payload or an actor -
and it costs one sha256 per returned row.

`GET /api/audit/chain` walks the WHOLE chain and returns the id of the first
row whose link does not hold. That is the claim that catches a *removed* row,
which a per-row check cannot: a deletion leaves the surviving rows individually
valid and breaks only the links between them. It reads 84,629 rows on the
committed corpus and takes about two seconds, which is why it is its own
endpoint rather than a cost paid on every case sheet.

Neither repairs anything. A broken chain is evidence, and evidence is not
tidied away.

An empty `events` list for a case that exists is a real answer - nothing has
happened to it since it was opened. It never means the case is missing; an
unknown case id is a 404.

Role scoping (Phase 7): the case is fetched through
`routers/cases.scoped_cases` first, so an out-of-scope case id 404s before any
trail is read. The MP role additionally has `payload.text` removed from
`NOTE_ADDED` rows - an MP sees that a note was added, by which role and when,
because the text is the administration's working record (DOMAIN-MODEL.md (k)).
That redaction is the only place in the API where a response shape changes by
role, which is why `docs/api/ROLE-SCOPING-PLAN.md` calls it out separately.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..engine.audit import row_hash, verify_chain
from ..models import AuditLog
from ..schemas import AuditEventOut, AuditTrail, ChainStatus
from .cases import _case_or_404

router = APIRouter(prefix="/audit", tags=["audit"])


def _event(row: AuditLog) -> AuditEventOut:
    return AuditEventOut(
        id=row.id,
        at=row.at,
        actor_role=row.actor_role,
        actor_id=row.actor_id,
        event=row.event,
        case_id=row.case_id,
        # Stored as text so a row written today stays readable after the
        # payload shape of its event type has moved on; decoded here so the
        # client does not have to parse twice.
        payload=json.loads(row.payload_json) if row.payload_json else None,
        prev_hash=row.prev_hash,
        row_hash=row.row_hash,
    )


def _row_holds(row: AuditLog) -> bool:
    """Does this row's stored hash still follow from its stored content?"""
    return row.row_hash == row_hash(
        row.prev_hash, row.at, row.actor_role, row.actor_id, row.event, row.case_id, row.payload_json
    )


# Declared before `/{case_id}` so the literal path wins the match. Case ids are
# `NG-` plus ten hex characters and could never be the string "chain", but
# relying on that would make the routing correct by luck.
@router.get("/chain", response_model=ChainStatus)
def get_chain(db: Session = Depends(get_db)):
    """Walk the whole hash chain and name the first row whose link fails.

    Slow by nature - it reads every audit row - and that is the price of the
    only check that detects a removed row. Nothing is repaired.
    """
    chain = verify_chain(db)
    return ChainStatus(
        rows=chain["rows"], intact=chain["intact"], broken_at=chain["broken_at"]
    )


@router.get("/{case_id}", response_model=AuditTrail)
def get_trail(case_id: str, db: Session = Depends(get_db)):
    """Every event written against this case, oldest first, each hash re-checked."""
    case, _work = _case_or_404(db, case_id)

    rows = db.scalars(
        select(AuditLog).where(AuditLog.case_id == case.case_id).order_by(AuditLog.id)
    ).all()
    broken = next((row.id for row in rows if not _row_holds(row)), None)

    return AuditTrail(
        case_id=case.case_id,
        events=[_event(row) for row in rows],
        rows_intact=broken is None,
        first_broken_row=broken,
    )
