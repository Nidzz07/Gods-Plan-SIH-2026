"""Escalation delivery. **Dry run by default, and that is not a placeholder.**

READ THIS BEFORE DESCRIBING ESCALATION TO ANYONE.

An escalation in NIGRANI moves an alert to another desk's queue and writes an
`ALERT_ESCALATED` row to the append-only trail. Those two things always happen
and they are the substance of the feature. Sending an email is an OPTIONAL extra
that is **switched off unless a mail host is configured**, and in the shipped
configuration nothing is sent to anybody.

This module contains a real `smtplib` send. It is real so that a deployment can
turn it on by setting environment variables rather than by writing code, and it
is off so that a demo cannot accidentally mail a stranger. What it does in the
default configuration is compose the exact message it would have sent and return
it, and write it to the log, and report `delivered: false`.

**The honesty rule this file exists to keep.** PROJECT-BRIEF.md declares, in the
limitations an officer and a judge both see: escalation delivers to an in-app
queue and an audit event, and does not send email or SMS - "say 'queued for the
State Nodal Authority', not 'notified'". Every string this module hands back
says `queued` where nothing was sent. Do not reword the API response, the UI
copy or a slide to imply a delivery that a dry run did not make. If the SMTP
path is ever switched on for a real deployment, the response says `delivered:
true` and the wording may change with it - and not before.

**To make it live**, all four must be set, and the absence of any one of them
keeps the dry run:

    NIGRANI_SMTP_HOST      the mail server's hostname
    NIGRANI_SMTP_PORT      its port (default 587)
    NIGRANI_SMTP_FROM      the envelope sender
    NIGRANI_ESCALATION_TO  where escalations are addressed

Optionally `NIGRANI_SMTP_USER` and `NIGRANI_SMTP_PASSWORD` for authentication,
and `NIGRANI_SMTP_STARTTLS=0` to disable STARTTLS on a host that does not offer
it. A password is read from the environment and never from a file in this
repository.
"""

from __future__ import annotations

import logging
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

logger = logging.getLogger("nigrani.escalation")

# The four that decide whether anything can be sent at all.
ENV_HOST = "NIGRANI_SMTP_HOST"
ENV_PORT = "NIGRANI_SMTP_PORT"
ENV_FROM = "NIGRANI_SMTP_FROM"
ENV_TO = "NIGRANI_ESCALATION_TO"
ENV_USER = "NIGRANI_SMTP_USER"
ENV_PASSWORD = "NIGRANI_SMTP_PASSWORD"
ENV_STARTTLS = "NIGRANI_SMTP_STARTTLS"

# What the response says when nothing was sent. Worded to match the declared
# limitation exactly rather than approximately.
DRY_RUN_DETAIL = (
    "Queued for the {role} and written to the audit trail. No email was sent: NIGRANI runs "
    "escalation in dry-run mode unless a mail host is configured, and this deployment has "
    "none. The message that would have been sent is included above verbatim."
)

SENT_DETAIL = "Queued for the {role}, written to the audit trail, and emailed to {recipient}."

TRANSPORT_DRY_RUN = "dry-run"
TRANSPORT_SMTP = "smtp"

# Where a dry run addresses its message, so the composed text is complete rather
# than carrying an empty To: line. It is a documentation address on a domain
# reserved for examples; it is never contacted, because nothing is sent.
UNCONFIGURED_RECIPIENT = "escalations@nigrani.invalid (no recipient configured)"


@dataclass(frozen=True)
class Delivery:
    """What happened, in enough detail that the screen cannot overstate it."""

    dry_run: bool
    delivered: bool
    recipient: str
    subject: str
    body: str
    transport: str
    detail: str


def configured() -> bool:
    """True only when every setting a real send needs is present."""
    return all(os.environ.get(name) for name in (ENV_HOST, ENV_PORT, ENV_FROM, ENV_TO))


def compose(alert, case_url: str, to_role: str, actor_role: str) -> tuple[str, str]:
    """The subject and body of the escalation message.

    Composed the same way whether or not it will be sent, so a dry run shows the
    real thing rather than a summary of it. Deliberately plain text: this is an
    administrative notice, and an HTML mail with a logo in it would be the kind
    of dressing that makes a prototype look like a product it is not.
    """
    subject = f"[NIGRANI] {alert.severity} case {alert.case_id} escalated to the {to_role}"
    where = ", ".join(part for part in (alert.district, _state_name(alert)) if part)
    body = (
        f"An MPLADS case has been escalated to the {to_role.replace('_', ' ')}.\n"
        f"\n"
        f"  Case      {alert.case_id}\n"
        f"  Severity  {alert.severity}\n"
        f"  Where     {where or 'not recorded'}\n"
        f"  Raised by rule  {alert.rule_id or 'the case as a whole'}\n"
        f"  Escalated by    the {actor_role.replace('_', ' ')}\n"
        f"\n"
        f"{alert.message}\n"
        f"\n"
        f"Open the case sheet: {case_url}\n"
        f"\n"
        f"This case was scored by a versioned rulebook, and every rule it fired, the value "
        f"read and the points contributed are on that sheet. The score is arithmetic that "
        f"can be re-derived on paper; nothing in it comes from a model.\n"
        f"\n"
        f"NIGRANI operates over a truncated sample of the MPLADS portal, not the national "
        f"record. This is a demonstration system and not a system of record.\n"
    )
    return subject, body


def _state_name(alert) -> str | None:
    """The alert's state name if the relationship is loaded, else None."""
    case = getattr(alert, "case", None)
    work = getattr(case, "work", None) if case is not None else None
    state = getattr(work, "state", None) if work is not None else None
    return getattr(state, "name", None)


def send_escalation(alert, case_url: str, to_role: str, actor_role: str) -> Delivery:
    """Deliver an escalation, or say precisely what would have been delivered.

    Never raises on a mail failure. An escalation's substance is the queue move
    and the audit row, both of which have already happened by the time this is
    called; a mail server being down must not roll those back or hand the
    officer a 500 for an action that succeeded. A failure is reported as
    `delivered: false` with the reason, which is the same shape as a dry run and
    is read the same way by the screen.
    """
    subject, body = compose(alert, case_url, to_role, actor_role)

    if not configured():
        recipient = os.environ.get(ENV_TO) or UNCONFIGURED_RECIPIENT
        logger.info(
            "escalation DRY RUN: alert=%s case=%s to_role=%s recipient=%s subject=%r",
            alert.id,
            alert.case_id,
            to_role,
            recipient,
            subject,
        )
        logger.debug("escalation DRY RUN body:\n%s", body)
        return Delivery(
            dry_run=True,
            delivered=False,
            recipient=recipient,
            subject=subject,
            body=body,
            transport=TRANSPORT_DRY_RUN,
            detail=DRY_RUN_DETAIL.format(role=to_role.replace("_", " ")),
        )

    recipient = os.environ[ENV_TO]
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.environ[ENV_FROM]
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(os.environ[ENV_HOST], int(os.environ[ENV_PORT]), timeout=20) as server:
            if os.environ.get(ENV_STARTTLS, "1") != "0":
                server.starttls()
            if os.environ.get(ENV_USER):
                server.login(os.environ[ENV_USER], os.environ.get(ENV_PASSWORD, ""))
            server.send_message(message)
    except Exception as exc:  # noqa: BLE001 - see the docstring: never raise
        logger.warning("escalation email failed for alert %s: %s", alert.id, exc)
        return Delivery(
            dry_run=False,
            delivered=False,
            recipient=recipient,
            subject=subject,
            body=body,
            transport=TRANSPORT_SMTP,
            detail=(
                f"Queued for the {to_role.replace('_', ' ')} and written to the audit trail. "
                f"The email could not be sent ({exc.__class__.__name__}), so treat this as "
                f"queued and not delivered."
            ),
        )

    logger.info("escalation sent: alert=%s case=%s to=%s", alert.id, alert.case_id, recipient)
    return Delivery(
        dry_run=False,
        delivered=True,
        recipient=recipient,
        subject=subject,
        body=body,
        transport=TRANSPORT_SMTP,
        detail=SENT_DETAIL.format(role=to_role.replace("_", " "), recipient=recipient),
    )
