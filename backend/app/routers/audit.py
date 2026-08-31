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

**Role scoping.** The case is fetched through `routers/cases._case_or_404`
first, so an out-of-scope case id 404s before any trail is read - the trail is
scoped by the case it belongs to, and there is no second predicate to keep in
step with the first.

The member of parliament additionally has `payload.text` removed from
`NOTE_ADDED` rows. An MP sees that a note was added, by which role and when;
the text is the administration's working record (DOMAIN-MODEL.md (k)). The row
is otherwise untouched, `row_hash` included, so the redaction is visible as a
redaction rather than passed off as the whole row: a reader who recomputes the
hash of what they were given will find it does not match, which is the honest
outcome. It is the only place in this API where a response shape changes by
role, which is why `docs/api/ROLE-SCOPING-PLAN.md` calls it out separately.

`GET /api/audit/chain` is Ministry-only. Every other endpoint here is scoped by
a case; the chain walk is over all 84,629 rows of the trail at once, which is a
corpus-wide artefact and not a finding about anyone's district.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..constants import ROLE_MEMBER_OF_PARLIAMENT, ROLE_MINISTRY
from ..db import get_db
from ..engine.audit import row_hash, verify_chain
from ..models import AuditLog, User
from ..schemas import AuditEventOut, AuditTrail, ChainStatus
from .cases import EVENT_NOTE_ADDED, _case_or_404

router = APIRouter(prefix="/audit", tags=["audit"])


# What replaces a note's text for a member of parliament. A key that says it
# was removed, rather than a missing key or an empty string: a frontend
# rendering `undefined` and a note that was genuinely blank are both wrong
# answers to "what did the officer write".
REDACTED = {
    "redacted": True,
    "reason": (
        "The text of an officer's note is the administration's working record and is not "
        "shown to the member (DOMAIN-MODEL.md (k)). That the note exists, its author's role "
        "and its timestamp are shown."
    ),
}


def _event(row: AuditLog, redact_note_text: bool = False) -> AuditEventOut:
    payload = json.loads(row.payload_json) if row.payload_json else None
    if redact_note_text and row.event == EVENT_NOTE_ADDED and payload is not None:
        payload = {key: value for key, value in payload.items() if key != "text"} | REDACTED
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
        payload=payload,
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
def get_chain(
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(ROLE_MINISTRY)),
):
    """Walk the whole hash chain and name the first row whose link fails.

    Slow by nature - it reads every audit row - and that is the price of the
    only check that detects a removed row. Nothing is repaired.

    Ministry-only: this walks the entire trail rather than one case's, so there
    is no case to scope it by, and the integrity of the whole log is a question
    for the ministry that owns it.
    """
    chain = verify_chain(db)
    return ChainStatus(
        rows=chain["rows"], intact=chain["intact"], broken_at=chain["broken_at"]
    )


@router.get("/{case_id}", response_model=AuditTrail)
def get_trail(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Every event written against this case, oldest first, each hash re-checked.

    Scoped by the case: an id outside the caller's scope 404s in
    `_case_or_404` before a single audit row is read.
    """
    case, _work = _case_or_404(db, case_id, user)

    rows = db.scalars(
        select(AuditLog).where(AuditLog.case_id == case.case_id).order_by(AuditLog.id)
    ).all()
    # Checked against the STORED row, before any redaction, so the integrity
    # claim is about what the database holds rather than about what this
    # response happens to print.
    broken = next((row.id for row in rows if not _row_holds(row)), None)
    redact = user.role == ROLE_MEMBER_OF_PARLIAMENT

    return AuditTrail(
        case_id=case.case_id,
        events=[_event(row, redact_note_text=redact) for row in rows],
        rows_intact=broken is None,
        first_broken_row=broken,
    )
