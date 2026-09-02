"""Editing the rulebook: a new version, never a mutation, and never a rescore.

Three claims are under test here and they are the ones the feature would be
worthless without.

**An edit creates a version.** `rulebook_versions` gains a row; the row that was
there keeps its snapshot byte for byte. CLAUDE.md invariant 5 is what makes a
score reproducible months later - a case re-derives against the snapshot it was
scored under - and it is only true if an edit cannot reach backwards.

**An edit rescores nothing.** Not one stored case moves, and every case goes on
pointing at the version it was scored under. This is the claim an officer is
most likely to assume the opposite of, so it is asserted over the whole corpus
rather than over one case.

**An edit is a threshold edit.** It may not add a rule, remove one, or change
what a rule measures. The boundary is enforced rather than documented.

**The file is restored after every test in this module.** `rules.yaml` is a real
file in the working tree and these tests really rewrite it; a test that left it
edited would silently change what every later test in the session scores
against, and would leave the developer's tree dirty.
"""

from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import func, select

from app.engine.rulebook import RULES_PATH, loads
from app.models import AuditLog, Case, RulebookVersion
from app.rulebook_edit import RuleEdit, RulebookEditError, apply_edits, next_version

from .accounts import (
    MEMBER_A_EMAIL,
    ROLE_DISTRICT_EMAIL,
    ROLE_MINISTRY_EMAIL,
    ROLE_STATE_EMAIL,
    headers,
    token_for,
)
from .conftest import api_client

pytestmark = pytest.mark.corpus


@pytest.fixture(autouse=True)
def restore_rules_file():
    """Put `rules.yaml` back exactly as it was, whatever the test did to it."""
    # Read and written as BYTES, so a restore puts back exactly what was there
    # rather than what `read_text` normalised it to. On Windows a text-mode
    # round trip turns every LF into CRLF and leaves the tree dirty after a run
    # that changed nothing.
    original = RULES_PATH.read_bytes()
    try:
        yield original.decode("utf-8")
    finally:
        RULES_PATH.write_bytes(original)


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


def edit(client, auth, **body):
    body.setdefault("note", "test edit")
    return client.post("/api/rulebook", json=body, headers=auth)


# ---------------------------------------------------------------------------
# The unit the endpoint is built on
# ---------------------------------------------------------------------------


def test_an_edit_rewrites_one_scalar_and_keeps_every_comment():
    """The reason this is a text edit and not a YAML round-trip.

    `rules.yaml` is roughly two thirds comment, and those comments carry the
    firing count behind every threshold (invariant 6) and the reasoning behind
    every weight. A `safe_dump` round-trip would delete all of them on the first
    edit anyone made.
    """
    original = RULES_PATH.read_text(encoding="utf-8")
    text, changes = apply_edits(original, [RuleEdit("execution_delay", threshold=400)])

    comments_before = sum(1 for line in original.splitlines() if line.strip().startswith("#"))
    comments_after = sum(1 for line in text.splitlines() if line.strip().startswith("#"))
    assert comments_after == comments_before > 50
    assert len(text.splitlines()) == len(original.splitlines())

    differing = [
        (a, b)
        for a, b in zip(original.splitlines(), text.splitlines())
        if a != b
    ]
    assert differing == [("    threshold: 365", "    threshold: 400")]
    assert changes == [
        {"rule_id": "execution_delay", "key": "threshold", "from": 365, "to": 400}
    ]


def test_an_edit_may_not_invent_a_rule():
    original = RULES_PATH.read_text(encoding="utf-8")
    with pytest.raises(RulebookEditError) as raised:
        apply_edits(original, [RuleEdit("a_rule_nobody_wrote", threshold=1)])
    assert "may not create one" in str(raised.value)


def test_a_float_threshold_keeps_its_precision():
    original = RULES_PATH.read_text(encoding="utf-8")
    text, _ = apply_edits(original, [RuleEdit("duplicate_work", threshold=0.93)])
    assert loads(text)["rules"][2]["threshold"] == 0.93


def test_the_version_bump_is_minor():
    assert next_version("v1.0.0") == "v1.1.0"
    assert next_version("v1.9.0") == "v1.10.0"
    assert next_version("") == "v1.1.0"


# ---------------------------------------------------------------------------
# Who may edit
# ---------------------------------------------------------------------------


def test_only_the_ministry_may_edit_the_rulebook(client, signed_in):
    """403 for the other three, and the rulebook stays readable to all four.

    The asymmetry is the point of the scoping row: everyone judged by a rule is
    entitled to read it, and entitled not to be the one who can move it under
    themselves (DOMAIN-MODEL.md (k)).
    """
    for email in (ROLE_STATE_EMAIL, ROLE_DISTRICT_EMAIL, MEMBER_A_EMAIL):
        refused = edit(
            client, signed_in[email], rules=[{"rule_id": "execution_delay", "threshold": 400}]
        )
        assert refused.status_code == 403, f"{email} -> {refused.status_code}"
        # And they can still READ it.
        assert client.get("/api/rulebook", headers=signed_in[email]).status_code == 200

    # The file was not touched by any of the refusals.
    assert loads(RULES_PATH.read_text(encoding="utf-8"))["version"] == "v1.0.0"


def test_an_anonymous_caller_cannot_edit_the_rulebook(anon_client):
    assert anon_client.post("/api/rulebook", json={"note": "x", "rules": []}).status_code == 401


# ---------------------------------------------------------------------------
# What an edit does, and what it leaves alone
# ---------------------------------------------------------------------------


def test_an_edit_adds_a_version_and_mutates_none(client, signed_in, api_session_factory):
    session = api_session_factory()
    try:
        before = {
            row.id: (row.version, row.yaml_sha256, row.yaml_snapshot)
            for row in session.scalars(select(RulebookVersion))
        }
        before_versions = {version for version, _sha, _text in before.values()}
    finally:
        session.close()

    response = edit(
        client,
        signed_in[ROLE_MINISTRY_EMAIL],
        note="raise the execution-delay threshold for the pilot",
        rules=[{"rule_id": "execution_delay", "threshold": 400}],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    # The file is restored between tests, so `previous_version` is always the
    # shipped one - but the NEW string skips any version already stored, since
    # `rulebook_versions.version` is unique and earlier tests in this module
    # have banked some. Asserting the exact digits would be asserting the order
    # the tests happened to run in.
    assert body["previous_version"] == "v1.0.0"
    assert body["version"] not in before_versions
    assert body["version"].startswith("v1.")
    assert body["cases_rescored"] == 0
    assert body["changes"] == [
        {"rule_id": "execution_delay", "key": "threshold", "from": 365, "to": 400}
    ]

    session = api_session_factory()
    try:
        after = {
            row.id: (row.version, row.yaml_sha256, row.yaml_snapshot)
            for row in session.scalars(select(RulebookVersion))
        }
    finally:
        session.close()

    assert len(after) == len(before) + 1
    for version_id, snapshot in before.items():
        assert after[version_id] == snapshot, "an existing snapshot was mutated"

    # The new row's snapshot is the file that is now on disk.
    text = RULES_PATH.read_text(encoding="utf-8")
    assert after[body["rulebook_version_id"]][2] == text
    assert hashlib.sha256(text.encode()).hexdigest() == body["yaml_sha256"]


def test_an_edit_rescores_nothing(client, signed_in, api_session_factory):
    """Every stored case keeps its score AND its rulebook pointer (invariant 5)."""
    session = api_session_factory()
    try:
        before = {
            case_id: (score, version_id)
            for case_id, score, version_id in session.execute(
                select(Case.case_id, Case.score, Case.rulebook_version_id)
            )
        }
    finally:
        session.close()
    assert before, "no cases to check"

    response = edit(
        client,
        signed_in[ROLE_MINISTRY_EMAIL],
        note="halve the duplicate weight",
        rules=[{"rule_id": "duplicate_work", "weight": 9}],
    )
    assert response.status_code == 201, response.text

    session = api_session_factory()
    try:
        after = {
            case_id: (score, version_id)
            for case_id, score, version_id in session.execute(
                select(Case.case_id, Case.score, Case.rulebook_version_id)
            )
        }
    finally:
        session.close()

    assert after == before, "an edit moved a stored case"


def test_an_edit_writes_one_rulebook_updated_event(client, signed_in, api_session_factory):
    session = api_session_factory()
    try:
        before = session.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.event == "RULEBOOK_UPDATED")
        )
    finally:
        session.close()

    assert edit(
        client,
        signed_in[ROLE_MINISTRY_EMAIL],
        note="widen the stalled-work window",
        rules=[{"rule_id": "stalled_work", "threshold": 300}],
    ).status_code == 201

    session = api_session_factory()
    try:
        rows = session.scalars(
            select(AuditLog)
            .where(AuditLog.event == "RULEBOOK_UPDATED")
            .order_by(AuditLog.id.desc())
        ).all()
        assert len(rows) == before + 1
        latest = rows[0]
        assert latest.actor_role == "ministry"
        assert latest.actor_id is not None
        import json

        payload = json.loads(latest.payload_json)
        assert payload["cases_rescored"] == 0
        assert payload["changes"] == [
            {"rule_id": "stalled_work", "key": "threshold", "from": 270, "to": 300}
        ]
    finally:
        session.close()


def test_an_edit_that_changes_nothing_is_refused(client, signed_in):
    same = edit(
        client,
        signed_in[ROLE_MINISTRY_EMAIL],
        note="no change at all",
        rules=[{"rule_id": "execution_delay", "threshold": 365}],
    )
    assert same.status_code == 422
    assert "already holds" in same.json()["detail"]

    empty = edit(client, signed_in[ROLE_MINISTRY_EMAIL], note="nothing", rules=[])
    assert empty.status_code == 422


def test_an_edit_may_not_change_what_a_rule_measures(client, signed_in):
    """`field` and `operator` are not in the request shape at all.

    Pydantic refuses the extra key rather than ignoring it, so an operator
    smuggled into the body is a 422 and not a silent no-op that leaves the
    caller believing the rule now compares differently.
    """
    response = client.post(
        "/api/rulebook",
        json={
            "note": "try to change the operator",
            "rules": [{"rule_id": "execution_delay", "operator": "lt"}],
        },
        headers=signed_in[ROLE_MINISTRY_EMAIL],
    )
    assert response.status_code == 422


def test_the_read_endpoint_reports_the_drift_an_edit_creates(client, signed_in):
    """After an edit the file and the scored cases disagree, and the API says where."""
    before = client.get("/api/rulebook", headers=signed_in[ROLE_MINISTRY_EMAIL]).json()
    assert before["file_matches_stored_version"] is True
    assert before["rules_edited_since_scoring"] == []

    assert edit(
        client,
        signed_in[ROLE_MINISTRY_EMAIL],
        note="move two rules",
        rules=[
            {"rule_id": "sanction_delay", "threshold": 200},
            {"rule_id": "split_sanction", "weight": 11},
        ],
    ).status_code == 201

    after = client.get("/api/rulebook", headers=signed_in[ROLE_MINISTRY_EMAIL]).json()
    assert after["file_matches_stored_version"] is False
    assert sorted(after["rules_edited_since_scoring"]) == ["sanction_delay", "split_sanction"]
    assert after["version"] != before["version"]
    # The cases are still scored under the version they were scored under.
    assert after["cases_scored_under"]["version"] == "v1.0.0"


# ---------------------------------------------------------------------------
# The claim invariant 5 exists for
# ---------------------------------------------------------------------------


def test_a_recompute_follows_the_snapshot_the_case_points_at(
    client, signed_in, api_session_factory
):
    """Constructed explicitly: the same case, recomputed against two rulebooks.

    Against its own snapshot the recompute reproduces the stored trace. Pointed
    at a snapshot whose threshold moved, the SAME case recomputes to a different
    trace. That difference is the whole of invariant 5: which rulebook a case is
    re-derived against is decided by the case's stored pointer, never by the
    file on disk - so an officer editing a threshold in March cannot silently
    restate what a case in January was found to say.
    """
    from app.engine.audit import recompute as recompute_case
    from app.routers.cases import features_for
    from app.models import Work

    auth = signed_in[ROLE_MINISTRY_EMAIL]

    # A case whose trace has a fired `sanction_delay` row, so moving that
    # threshold is guaranteed to move this case's arithmetic.
    session = api_session_factory()
    try:
        from app.models import RuleHit

        case_id = session.scalar(
            select(RuleHit.case_id)
            .where(RuleHit.rule_id == "sanction_delay", RuleHit.status == "fired")
            .limit(1)
        )
    finally:
        session.close()
    assert case_id, "no case fires sanction_delay; pick another rule"

    # 1. Against its own snapshot: identical.
    first = client.post(f"/api/cases/{case_id}/recompute", headers=auth)
    assert first.status_code == 200, first.text
    assert first.json()["identical"] is True
    assert first.json()["rulebook_version"] == "v1.0.0"

    # 2. Edit the rulebook so `sanction_delay` can no longer fire on anything.
    made = edit(
        client,
        auth,
        note="raise sanction_delay far beyond any observed lag",
        rules=[{"rule_id": "sanction_delay", "threshold": 100000}],
    )
    assert made.status_code == 201, made.text
    new_version_string = made.json()["version"]

    # 3. The case still recomputes identical, because it still points at v1.
    unchanged = client.post(f"/api/cases/{case_id}/recompute", headers=auth)
    assert unchanged.status_code == 200
    assert unchanged.json()["identical"] is True, (
        "editing the file changed what a case re-derives to - the recompute is reading "
        "rules.yaml instead of the case's own snapshot (invariant 5)"
    )

    # 4. Point the case at the NEW snapshot and recompute again. Now it moves.
    session = api_session_factory()
    try:
        new_version = session.scalar(
            select(RulebookVersion).order_by(RulebookVersion.id.desc()).limit(1)
        )
        case = session.get(Case, case_id)
        original_version_id = case.rulebook_version_id
        case.rulebook_version_id = new_version.id
        session.commit()

        work = session.get(Work, case.work_id)
        outcome = recompute_case(
            session, case, lambda: features_for(session, work), actor_role="ministry"
        )
        session.commit()
    finally:
        session.close()

    assert outcome["rulebook_version"] == new_version_string
    assert outcome["rulebook_version"] != "v1.0.0"
    assert outcome["identical"] is False, (
        "the same case recomputed against a rulebook whose threshold moved produced an "
        "identical trace, which means the snapshot is not reaching the evaluation"
    )
    moved = {row["rule_id"] for row in outcome["trace_diff"]}
    assert "sanction_delay" in moved

    # And the stored case is STILL untouched - a recompute observes, it does not
    # correct (engine/audit.py).
    session = api_session_factory()
    try:
        case = session.get(Case, case_id)
        assert case.score == first.json()["stored"]["score"]
        # Put the pointer back so the rest of the module sees the corpus it expects.
        case.rulebook_version_id = original_version_id
        session.commit()
    finally:
        session.close()
