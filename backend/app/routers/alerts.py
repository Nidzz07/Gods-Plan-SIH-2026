"""Alerts endpoint - F8's surface. The routed inbox, and the two decisions on it.

**Scoped exactly as cases are, and by the same predicate shape.** An alert
carries `state_id` and `district` copied from its work, and the district filter
is always `state_id == S AND district == D`, both terms. Never the district name
alone: 61 of the 634 district names carrying cases in this corpus belong to more
than one state, and filtering an inbox on the bare name would show a Uttar
Pradesh officer alerts about Rajasthan. That exact bug has already been found
once in the analytics router, on the same corpus, for the same reason - so the
predicate here is written the way `scoping.work_predicate` writes it and is
tested against a colliding district name rather than assumed safe.

**Read by three roles, written by three.** The member of parliament reads their
own alerts and cannot act on them, which is the same read-only rule that applies
to their cases: the scheme's subject does not adjudicate the scheme's findings
(DOMAIN-MODEL.md (k)). `require_write` refuses them before an alert is fetched.

**Escalation sends nothing in the shipped configuration.** It moves the alert to
another desk's queue and writes an `ALERT_ESCALATED` row, and it composes the
email it would have sent and hands it back unsent. See `app/notify.py`, which
carries the whole of that argument, and PROJECT-BRIEF.md's declared limitation
8. The response says `delivered: false` and the word is `queued`, never
`notified`.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_write
from ..constants import (
    ALERT_STATUSES,
    ESCALATES_TO,
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MEMBER_OF_PARLIAMENT,
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
)
from ..db import get_db
from ..engine.audit import log as audit_log
from ..models import Alert, Case, State, User, Work
from ..notify import send_escalation
from ..schemas import AlertOut, AlertPage, EscalationOut

router = APIRouter(prefix="/alerts", tags=["alerts"])

EVENT_ALERT_ESCALATED = "ALERT_ESCALATED"
EVENT_ALERT_ACKNOWLEDGED = "NOTE_ADDED"

# Where a case sheet lives, for the escalation message. The API does not know
# the frontend's origin, so the link is relative and the mail says what it is.
CASE_URL = "/cases/{case_id}"


def alert_predicate(user: User) -> list:
    """The `WHERE` terms this role adds to any query over `alerts`.

    The same shape as `scoping.work_predicate`, deliberately, so the two cannot
    drift apart: an alert a role can see is exactly an alert about a case that
    role can open. Written here rather than reused directly because that helper
    returns terms over `works` and these columns live on `alerts` - the columns
    are denormalised copies, and this is the one place that has to know it.
    """
    if user.role == ROLE_MINISTRY:
        return []
    if user.role == ROLE_STATE_NODAL:
        return [Alert.state_id == user.scope_state_id]
    if user.role == ROLE_DISTRICT_AUTHORITY:
        # BOTH terms. See the module docstring.
        return [Alert.state_id == user.scope_state_id, Alert.district == user.scope_district]
    if user.role == ROLE_MEMBER_OF_PARLIAMENT:
        return [Alert.mp_id == user.scope_mp_id]
    raise HTTPException(status_code=403, detail="Your role does not reach the alert queue.")


def scoped_alerts(user: User):
    """The base select every alert query starts from, already narrowed."""
    query = (
        select(Alert, Case, Work, State.name)
        .join(Case, Case.case_id == Alert.case_id)
        .join(Work, Work.id == Case.work_id)
        .join(State, State.id == Work.state_id)
    )
    for term in alert_predicate(user):
        query = query.where(term)
    return query


def _alert_or_404(db: Session, alert_id: int, user: User) -> tuple:
    """One alert through the scoped select, or 404.

    404 and not 403, for the reason the case lookup gives: a 403 would confirm
    that another district's alert id is real, which is a scoping leak spelled
    with a status code.
    """
    row = db.execute(scoped_alerts(user).where(Alert.id == alert_id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No alert {alert_id}")
    return row


def alert_out(row) -> AlertOut:
    """One joined row as the response shape."""
    alert, case, work, state_name = row
    return AlertOut(
        id=alert.id,
        case_id=alert.case_id,
        severity=alert.severity,
        rule_id=alert.rule_id,
        message=alert.message,
        status=alert.status,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        escalated_at=alert.escalated_at,
        escalated_to=alert.escalated_to,
        state=state_name,
        district=alert.district,
        score=case.score,
        work_id=work.work_id_canon,
        description=work.description,
    )


@router.get("", response_model=AlertPage)
def list_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: str | None = Query(default=None, description=" | ".join(ALERT_STATUSES)),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """This role's alert queue, open first, worst first.

    Ordered by status then score rather than by age: every alert in this corpus
    was raised by one run and carries one timestamp, so ordering by time would
    be ordering by nothing. Open alerts come before acknowledged ones because
    the queue exists to be worked down, and within a status the highest score
    is the one to open first - the same triage order the case list uses.
    """
    if status is not None and status not in ALERT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"status must be one of {', '.join(ALERT_STATUSES)}",
        )

    query = scoped_alerts(user)
    if status is not None:
        query = query.where(Alert.status == status)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    ranked = (
        query.order_by(
            # open, acknowledged, escalated, closed - the order they are worked
            # in, not alphabetical, which would put `acknowledged` first.
            func.instr("open|acknowledged|escalated|closed", Alert.status),
            Case.score.desc(),
            Alert.id,
        )
        .limit(limit)
        .offset(offset)
    )
    return AlertPage(
        total=total,
        limit=limit,
        offset=offset,
        items=[alert_out(row) for row in db.execute(ranked).all()],
    )


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_write),
):
    """Mark an alert as seen. Refused to the member of parliament.

    An acknowledgement is not a resolution and does not close anything: it
    records that a desk has the alert, which is the fact a queue needs in order
    to stop showing the same row to the same officer forever. An alert that has
    already been escalated cannot be walked back to acknowledged - escalation is
    the later state, and moving it backwards would leave the other desk holding
    something this one no longer shows.
    """
    row = _alert_or_404(db, alert_id, user)
    alert = row[0]
    if alert.status in ("escalated", "closed"):
        raise HTTPException(
            status_code=409,
            detail=(
                f"This alert is {alert.status} and acknowledging it would move it backwards. "
                "The trail records what happened in the order it happened."
            ),
        )
    if alert.status == "open":
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user.id
        audit_log(
            db,
            EVENT_ALERT_ACKNOWLEDGED,
            user.role,
            case_id=alert.case_id,
            actor_id=user.id,
            payload={"text": f"Alert {alert.id} acknowledged.", "alert_id": alert.id},
        )
        db.commit()
        db.refresh(alert)
    return alert_out(_alert_or_404(db, alert_id, user))


@router.post("/{alert_id}/escalate", response_model=EscalationOut)
def escalate(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_write),
):
    """Move an alert to the next desk, write the trail row, and compose the mail.

    The mail is not sent unless a mail host is configured, and in the shipped
    configuration there is none - so `delivered` comes back false and the
    message that would have gone out is returned verbatim. That is the honest
    shape of this feature and the response carries it rather than leaving the
    screen to guess (`app/notify.py`, PROJECT-BRIEF.md limitation 8).

    The queue move and the audit row happen BEFORE the delivery attempt and are
    committed regardless of what it returns. An escalation's substance is that
    another desk now holds the alert and the trail says so; a mail server being
    unreachable must not undo either.
    """
    row = _alert_or_404(db, alert_id, user)
    alert = row[0]
    if alert.status == "closed":
        raise HTTPException(status_code=409, detail="This alert is closed.")

    to_role = ESCALATES_TO.get(user.role)
    if to_role is None:
        raise HTTPException(status_code=403, detail="Your role cannot escalate an alert.")

    already = alert.status == "escalated"
    if not already:
        alert.status = "escalated"
        alert.escalated_at = datetime.utcnow()
        alert.escalated_to = to_role
        alert.escalated_by = user.id
        audit_log(
            db,
            EVENT_ALERT_ESCALATED,
            user.role,
            case_id=alert.case_id,
            actor_id=user.id,
            payload={
                "alert_id": alert.id,
                "to_role": to_role,
                "severity": alert.severity,
                "rule_id": alert.rule_id,
            },
        )
        db.commit()
        db.refresh(alert)

    delivery = send_escalation(
        alert,
        case_url=CASE_URL.format(case_id=alert.case_id),
        to_role=to_role,
        actor_role=user.role,
    )
    return EscalationOut(
        alert=alert_out(_alert_or_404(db, alert_id, user)),
        dry_run=delivery.dry_run,
        delivered=delivery.delivered,
        recipient=delivery.recipient,
        subject=delivery.subject,
        body=delivery.body,
        transport=delivery.transport,
        detail=(
            delivery.detail
            if not already
            else f"{delivery.detail} This alert was already escalated; nothing moved."
        ),
    )
