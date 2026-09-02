"""F8 - the routed inbox, its scoping, and an escalation that sends nothing.

**The scoping test is written against a colliding district name on purpose.**
The last defect found in this codebase was an endpoint resolving a district by
name alone, on a corpus where 61 of the 634 district names carrying cases belong
to more than one state. `alerts` carries its own denormalised `state_id` and
`district`, which is exactly the shape that invites the same mistake a second
time - so the inbox is tested with two District Authorities in two different
states holding the SAME district name, and the one whose state has no alerts
must see none rather than the other state's.

**The escalation test asserts an absence.** In the shipped configuration nothing
is emailed: `delivered` is false, the transport is `dry-run`, and the message
that would have gone out comes back so an officer can see it. PROJECT-BRIEF.md
declares this and `app/notify.py` argues it; a test that only checked the status
moved to `escalated` would let a future change quietly start sending mail from a
demo.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.alerts_run import KIND_SEVERITY_HIGH, raise_alerts
from app.auth import hash_password
from app.constants import DATA_AS_OF, ROLE_DISTRICT_AUTHORITY
from app.models import Alert, AuditLog, Case, State, User, Work

from .accounts import (
    MEMBER_A_EMAIL,
    PASSWORD,
    ROLE_DISTRICT_EMAIL,
    ROLE_MINISTRY_EMAIL,
    ROLE_STATE_EMAIL,
    headers,
    token_for,
)
from .conftest import api_client

pytestmark = pytest.mark.corpus


@pytest.fixture(scope="module", autouse=True)
def alerts_raised(api_session_factory):
    """Make sure the copied corpus has an inbox to test.

    Raised here rather than assumed, so the suite does not depend on the
    developer having run `python -m app.alerts_run` before `pytest`. Same
    reasoning as `provision_accounts`: a test over an empty table passes by
    accident.
    """
    session = api_session_factory()
    try:
        Alert.__table__.create(session.get_bind(), checkfirst=True)
        if not session.scalar(select(func.count()).select_from(Alert)):
            raise_alerts(session)
        total = session.scalar(select(func.count()).select_from(Alert))
    finally:
        session.close()
    if not total:
        pytest.skip("no HIGH cases in the corpus, so there is no inbox to test")
    return total


@pytest.fixture(scope="module")
def signed_in(client):
    return {
        email: headers(token_for(client, email))
        for email in (
            ROLE_MINISTRY_EMAIL,
            ROLE_STATE_EMAIL,
            ROLE_DISTRICT_EMAIL,
            MEMBER_A_EMAIL,
        )
    }


def inbox(client, auth, **params):
    response = client.get("/api/alerts", params=params, headers=auth)
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# The build step
# ---------------------------------------------------------------------------


def test_one_alert_per_high_case_and_none_for_anything_else(api_session_factory):
    session = api_session_factory()
    try:
        high = session.scalar(
            select(func.count())
            .select_from(Case)
            .where(Case.severity == "HIGH", Case.is_synthetic.is_(False))
        )
        alerts = session.scalar(select(func.count()).select_from(Alert))
        severities = {row for (row,) in session.execute(select(Alert.severity).distinct())}
        synthetic = session.scalar(
            select(func.count())
            .select_from(Alert)
            .join(Case, Case.case_id == Alert.case_id)
            .where(Case.is_synthetic.is_(True))
        )
    finally:
        session.close()

    assert alerts == high
    assert severities == {"HIGH"}
    # Invariant 12: the labelled control is excluded from every published
    # aggregate, and an inbox is one.
    assert synthetic == 0


def test_raising_alerts_twice_adds_nothing_and_keeps_decisions(api_session_factory):
    """Idempotent by case, not by rebuild.

    `alerts.status` is the only thing in the database that is not re-derivable
    from the corpus - it records a decision rather than a finding - so a second
    run must not reset it. This is the assertion that stops somebody 'fixing'
    the run script to drop and rebuild its table the way the other build steps
    do.
    """
    session = api_session_factory()
    try:
        target = session.scalars(select(Alert).limit(1)).one()
        target.status = "acknowledged"
        target.acknowledged_at = datetime.combine(DATA_AS_OF, datetime.min.time())
        session.commit()
        marked_id = target.id

        before = session.scalar(select(func.count()).select_from(Alert))
        counts = raise_alerts(session)
        after = session.scalar(select(func.count()).select_from(Alert))
        still = session.get(Alert, marked_id)

        assert counts["raised"] == 0
        assert after == before
        assert still.status == "acknowledged", "a re-run reset an officer's acknowledgement"

        still.status = "open"
        still.acknowledged_at = None
        session.commit()
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Scoping
# ---------------------------------------------------------------------------


def test_each_role_sees_its_own_inbox(client, signed_in, api_session_factory):
    session = api_session_factory()
    try:
        total = session.scalar(select(func.count()).select_from(Alert))
        state_id = session.scalar(select(State.id).where(State.name == "Uttar Pradesh"))
        in_state = session.scalar(
            select(func.count()).select_from(Alert).where(Alert.state_id == state_id)
        )
        in_district = session.scalar(
            select(func.count())
            .select_from(Alert)
            .where(Alert.state_id == state_id, Alert.district == "JALAUN")
        )
    finally:
        session.close()

    assert inbox(client, signed_in[ROLE_MINISTRY_EMAIL])["total"] == total
    assert inbox(client, signed_in[ROLE_STATE_EMAIL])["total"] == in_state
    assert inbox(client, signed_in[ROLE_DISTRICT_EMAIL])["total"] == in_district
    assert in_district < in_state <= total, "pick scopes that actually differ"

    # And every row a narrower role sees really is theirs.
    for item in inbox(client, signed_in[ROLE_DISTRICT_EMAIL], limit=500)["items"]:
        assert item["district"] == "JALAUN"
        assert item["state"] == "Uttar Pradesh"


def test_two_districts_of_one_name_do_not_share_an_inbox(api_session_factory):
    """The district-collision class of bug, checked for a second time.

    `KAITHAL` is a district of four different states in this corpus. An inbox
    filtered on the name alone would hand a Karnataka officer Madhya Pradesh's
    alerts. Both officers are provisioned here and both inboxes are read.
    """
    # A district name held by two states where exactly one carries alerts.
    session = api_session_factory()
    try:
        rows = session.execute(
            select(Work.district, Work.state_id, State.name, func.count())
            .join(State, State.id == Work.state_id)
            .join(Case, Case.work_id == Work.id)
            .where(Work.district.is_not(None), Case.is_synthetic.is_(False))
            .group_by(Work.district, Work.state_id, State.name)
        ).all()
        by_name = {}
        for district, state_id, state_name, _count in rows:
            by_name.setdefault(district, []).append((state_id, state_name))
        alert_counts = {
            (district, state_id): count
            for district, state_id, count in session.execute(
                select(Alert.district, Alert.state_id, func.count()).group_by(
                    Alert.district, Alert.state_id
                )
            )
        }

        chosen = None
        for district, states in by_name.items():
            if len(states) < 2:
                continue
            with_alerts = [s for s in states if alert_counts.get((district, s[0]))]
            without = [s for s in states if not alert_counts.get((district, s[0]))]
            if with_alerts and without:
                chosen = (district, with_alerts[0], without[0])
                break
        if chosen is None:
            pytest.skip("no colliding district name where exactly one state carries alerts")

        district, (loud_id, loud_name), (quiet_id, quiet_name) = chosen
        expected = alert_counts[(district, loud_id)]

        for state_id, state_name in ((loud_id, loud_name), (quiet_id, quiet_name)):
            email = f"kaithal-{state_id}@test.nigrani"
            if session.scalar(select(User).where(User.email == email)) is None:
                session.add(
                    User(
                        email=email,
                        password_hash=hash_password(PASSWORD),
                        role=ROLE_DISTRICT_AUTHORITY,
                        display_name=f"{district} ({state_name}) test officer",
                        is_active=True,
                        created_at=datetime.combine(DATA_AS_OF, datetime.min.time()),
                        scope_state_id=state_id,
                        scope_district=district,
                    )
                )
        session.commit()
    finally:
        session.close()

    with api_client(api_session_factory, email=f"kaithal-{loud_id}@test.nigrani") as loud:
        theirs = loud.get("/api/alerts", params={"limit": 500}).json()
    with api_client(api_session_factory, email=f"kaithal-{quiet_id}@test.nigrani") as quiet:
        others = quiet.get("/api/alerts", params={"limit": 500}).json()

    assert theirs["total"] == expected
    assert all(item["state"] == loud_name for item in theirs["items"])
    assert others["total"] == 0, (
        f"the {quiet_name} officer for {district!r} was shown {others['total']} alerts "
        f"belonging to {loud_name}'s district of the same name"
    )


def test_an_out_of_scope_alert_id_is_a_404(client, signed_in, api_session_factory):
    session = api_session_factory()
    try:
        state_id = session.scalar(select(State.id).where(State.name == "Uttar Pradesh"))
        elsewhere = session.scalar(
            select(Alert.id).where(Alert.state_id != state_id).limit(1)
        )
    finally:
        session.close()
    if elsewhere is None:
        pytest.skip("every alert is in the district officer's own state")

    for path in (f"/api/alerts/{elsewhere}/acknowledge", f"/api/alerts/{elsewhere}/escalate"):
        response = client.post(path, headers=signed_in[ROLE_DISTRICT_EMAIL])
        assert response.status_code == 404, f"{path} -> {response.status_code}"


def test_the_member_reads_alerts_and_acts_on_none(client, signed_in, api_session_factory):
    """Read-only everywhere, the same rule that governs their cases."""
    own = inbox(client, signed_in[MEMBER_A_EMAIL], limit=500)
    if own["total"] == 0:
        pytest.skip("the seeded member holds no HIGH case")
    alert_id = own["items"][0]["id"]

    for action in ("acknowledge", "escalate"):
        refused = client.post(
            f"/api/alerts/{alert_id}/{action}", headers=signed_in[MEMBER_A_EMAIL]
        )
        assert refused.status_code == 403, f"{action} -> {refused.status_code}"


# ---------------------------------------------------------------------------
# The two decisions
# ---------------------------------------------------------------------------


def test_acknowledging_moves_the_alert_and_never_moves_it_back(client, signed_in):
    open_ones = inbox(client, signed_in[ROLE_DISTRICT_EMAIL], status="open", limit=500)
    if open_ones["total"] == 0:
        pytest.skip("no open alert in the district inbox")
    alert_id = open_ones["items"][0]["id"]
    auth = signed_in[ROLE_DISTRICT_EMAIL]

    acknowledged = client.post(f"/api/alerts/{alert_id}/acknowledge", headers=auth)
    assert acknowledged.status_code == 200, acknowledged.text
    assert acknowledged.json()["status"] == "acknowledged"
    assert acknowledged.json()["acknowledged_at"] is not None

    # Escalate it, then try to walk it back.
    assert client.post(f"/api/alerts/{alert_id}/escalate", headers=auth).status_code == 200
    backwards = client.post(f"/api/alerts/{alert_id}/acknowledge", headers=auth)
    assert backwards.status_code == 409


def test_escalation_is_a_dry_run_that_sends_nothing(client, signed_in, caplog):
    """The absence is the assertion. Nothing is emailed and the response says so."""
    open_ones = inbox(client, signed_in[ROLE_STATE_EMAIL], status="open", limit=500)
    if open_ones["total"] == 0:
        pytest.skip("no open alert in the state inbox")
    alert_id = open_ones["items"][0]["id"]

    with caplog.at_level(logging.INFO, logger="nigrani.escalation"):
        response = client.post(
            f"/api/alerts/{alert_id}/escalate", headers=signed_in[ROLE_STATE_EMAIL]
        )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["dry_run"] is True
    assert body["delivered"] is False
    assert body["transport"] == "dry-run"
    assert "No email was sent" in body["detail"]
    # The word matters: PROJECT-BRIEF.md says "queued", never "notified".
    assert "queued" in body["detail"].lower()
    assert "notified" not in body["detail"].lower()

    # The message it would have sent is real and complete.
    assert body["alert"]["case_id"] in body["subject"]
    assert body["alert"]["case_id"] in body["body"]
    assert "not a system of record" in body["body"]

    # It logged what it would have done.
    assert any("DRY RUN" in record.message for record in caplog.records)

    # A state officer escalates to the ministry.
    assert body["alert"]["status"] == "escalated"
    assert body["alert"]["escalated_to"] == "ministry"
    assert body["alert"]["escalated_at"] is not None


def test_escalation_writes_the_audit_event(client, signed_in, api_session_factory):
    open_ones = inbox(client, signed_in[ROLE_MINISTRY_EMAIL], status="open", limit=500)
    if open_ones["total"] == 0:
        pytest.skip("no open alert anywhere")
    alert_id = open_ones["items"][0]["id"]
    case_id = open_ones["items"][0]["case_id"]

    session = api_session_factory()
    try:
        before = session.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.event == "ALERT_ESCALATED")
        )
    finally:
        session.close()

    assert client.post(
        f"/api/alerts/{alert_id}/escalate", headers=signed_in[ROLE_MINISTRY_EMAIL]
    ).status_code == 200

    session = api_session_factory()
    try:
        rows = session.scalars(
            select(AuditLog)
            .where(AuditLog.event == "ALERT_ESCALATED")
            .order_by(AuditLog.id.desc())
        ).all()
        assert len(rows) == before + 1
        latest = rows[0]
        assert latest.case_id == case_id
        assert latest.actor_role == "ministry"
        payload = json.loads(latest.payload_json)
        assert payload["alert_id"] == alert_id
        assert payload["to_role"] == "ministry"
    finally:
        session.close()


def test_the_inbox_can_be_filtered_by_status(client, signed_in):
    all_of_them = inbox(client, signed_in[ROLE_MINISTRY_EMAIL], limit=500)
    escalated = inbox(client, signed_in[ROLE_MINISTRY_EMAIL], status="escalated", limit=500)
    assert escalated["total"] <= all_of_them["total"]
    assert all(item["status"] == "escalated" for item in escalated["items"])

    bad = client.get(
        "/api/alerts", params={"status": "urgent"}, headers=signed_in[ROLE_MINISTRY_EMAIL]
    )
    assert bad.status_code == 422
