"""F8's build step - raise an alert for every case that crosses the bar.

    python -m app.alerts_run

**Fifth in the sequence, after `app.derive_all` and before or after
`app.seed_users`.** It reads `cases` and writes `alerts`, so it needs the cases
to exist; it does not read `users`, so it does not care whether the accounts
have been provisioned yet. Running it before `derive_all` produces nothing and
says so rather than failing.

**Why this is a build step and not a query.** The alternative - deriving the
inbox on every request from "which cases are HIGH" - cannot carry state, and
state is the entire point of an alert. An alert accumulates the
administration's handling of a finding: who acknowledged it, when, who escalated
it and to which desk. A list recomputed per request would discard all of that on
the next refresh, and the officer would be looking at a queue that never
shortens no matter what they did to it.

**Idempotent by case, NOT by rebuild.** The other build steps drop their tables
and rewrite them, and this one deliberately must not: `alerts.status`,
`acknowledged_at` and `escalated_at` are the only rows in the database that are
not re-derivable from the corpus, because they record decisions rather than
findings. So the insert is guarded by the `uq_alert_case_kind` constraint and a
second run adds only what is new. Re-running after a re-derive tops the inbox up;
it does not reset it.

**What raises an alert.** One kind today: `severity_high` - a case whose stored
severity is HIGH. That is the band the rulebook itself defines (score >= 75 on
the capped display score), read from the case rather than recomputed here, so
the alert and the case sheet can never disagree about what HIGH means. The
labelled synthetic control is excluded, like every other published aggregate
(invariant 12).

**Nothing here scores anything.** It reads `cases.severity`, which
`engine/score.py` decided. There is no threshold in this file and there must
never be one: a second place that decided what was serious would be a second
rulebook, unversioned and unauditable (invariant 1).
"""

from __future__ import annotations

import argparse
from datetime import datetime

from sqlalchemy import func, select

from .constants import DATA_AS_OF, SEVERITY_HIGH
from .db import SessionLocal
from .engine.audit import log as audit_log
from .models import Alert, Case, RuleHit, Work

KIND_SEVERITY_HIGH = "severity_high"
EVENT_ALERT_RAISED = "ALERT_RAISED"

# Written at the corpus as-of date rather than at wall-clock now, so a rebuild
# reproduces the same rows and a demo does not show alerts "raised" at whatever
# time the laptop happened to be started. Same reason `derive_all` pins
# MATERIALISED_AT.
RAISED_AT = datetime.combine(DATA_AS_OF, datetime.min.time())


def loudest_rule(session, case_id: str) -> str | None:
    """The fired rule that contributed most to this case, or None.

    Recorded on the alert so an officer opening the inbox sees WHY before they
    open the sheet. Ties break on the rule id so a rebuild is deterministic; a
    case with no fired rule - possible for a HIGH case only if the whole score
    came from the corroboration bonus - returns None, and the alert says the
    case as a whole rather than inventing a rule.
    """
    return session.scalar(
        select(RuleHit.rule_id)
        .where(RuleHit.case_id == case_id, RuleHit.status == "fired")
        .order_by(RuleHit.contribution.desc(), RuleHit.rule_id)
        .limit(1)
    )


def message_for(case, work, rule_id: str | None) -> str:
    """The one line an officer reads in the inbox before opening anything."""
    where = work.district or "an unrecorded district"
    because = (
        f"the {rule_id.replace('_', ' ')} rule contributed most to its score"
        if rule_id
        else "its agency's pattern of conduct, with no single rule dominating"
    )
    return (
        f"{case.severity} case scoring {case.score} of 100 in {where}, on {case.coverage_pct}% "
        f"rulebook coverage. Raised because {because}. The full trace is on the case sheet."
    )


def raise_alerts(session, progress=None) -> dict:
    """Insert one alert per HIGH case that does not already have one.

    Returns counts. Commits once at the end: a partial inbox is worse than none,
    because an officer cannot tell which half they are looking at.
    """
    say = progress or (lambda _message: None)

    existing = {
        case_id
        for (case_id,) in session.execute(
            select(Alert.case_id).where(Alert.kind == KIND_SEVERITY_HIGH)
        )
    }
    say(f"{len(existing):,} alerts already raised; they keep whatever status they carry.")

    rows = session.execute(
        select(Case, Work)
        .join(Work, Work.id == Case.work_id)
        .where(Case.severity == SEVERITY_HIGH, Case.is_synthetic.is_(False))
        .order_by(Case.score.desc(), Case.case_id)
    ).all()
    say(f"{len(rows):,} HIGH cases in the corpus, the labelled control excluded.")

    raised = 0
    for case, work in rows:
        if case.case_id in existing:
            continue
        rule_id = loudest_rule(session, case.case_id)
        session.add(
            Alert(
                case_id=case.case_id,
                kind=KIND_SEVERITY_HIGH,
                severity=case.severity,
                rule_id=rule_id,
                message=message_for(case, work, rule_id),
                status="open",
                created_at=RAISED_AT,
                state_id=work.state_id,
                district=work.district,
                mp_id=work.mp_id,
            )
        )
        audit_log(
            session,
            EVENT_ALERT_RAISED,
            "ministry",
            case_id=case.case_id,
            payload={
                "kind": KIND_SEVERITY_HIGH,
                "severity": case.severity,
                "score": case.score,
                "rule_id": rule_id,
            },
            at=RAISED_AT,
        )
        raised += 1

    session.commit()

    # Alerts whose case is no longer in the corpus. Possible only after a
    # re-ingest that changed which works exist, because a re-derive over the
    # same corpus reproduces every case id (invariant 8). Counted rather than
    # deleted: an orphan is evidence that the corpus moved under the inbox, and
    # the list endpoint already inner-joins `cases`, so it reaches nobody.
    orphans = (
        session.scalar(
            select(func.count())
            .select_from(Alert)
            .where(~select(Case.case_id).where(Case.case_id == Alert.case_id).exists())
        )
        or 0
    )

    return {
        "high_cases": len(rows),
        "already_raised": len(existing),
        "raised": raised,
        "orphans": orphans,
        "total": session.scalar(select(func.count()).select_from(Alert)) or 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Raise one alert per HIGH case. Idempotent by case: a second run adds only "
            "what is new and never resets an acknowledgement."
        )
    )
    parser.parse_args()

    session = SessionLocal()
    try:
        Alert.__table__.create(session.get_bind(), checkfirst=True)
        counts = raise_alerts(session, progress=lambda message: print(message, flush=True))
    finally:
        session.close()

    print(
        f"\n  HIGH cases     {counts['high_cases']:,}"
        f"\n  already raised {counts['already_raised']:,} (left exactly as they were)"
        f"\n  newly raised   {counts['raised']:,}"
        f"\n  alerts now     {counts['total']:,}"
    )
    if counts["orphans"]:
        print(
            f"\n  {counts['orphans']:,} alert(s) point at a case id no longer in the corpus. "
            "They are left in\n  place as evidence that the corpus changed under the inbox, "
            "and they reach\n  nobody: the list endpoint joins `cases`."
        )
    if counts["high_cases"] == 0:
        print(
            "\nNo HIGH cases found. If that is a surprise, run `python -m app.derive_all` "
            "first: this step reads stored cases and derives nothing itself."
        )
    print(
        "\nNo score was computed here. Every severity above is the one engine.score.compute "
        "stored on the case (CLAUDE.md invariant 1)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
