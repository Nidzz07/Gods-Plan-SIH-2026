"""Role scoping: which rows a token reaches, and which it must not.

This is the file CLAUDE.md invariant 10 is about - *role scoping is enforced
server-side, in the query. Never by hiding rows in the UI. A District Authority
token must not be able to fetch another district's cases by editing a URL.* The
tests here are written as URL edits, because that is the attack: every one of
them asks the server for something the caller has no business seeing and
asserts the server refuses, rather than asserting that a well-behaved client
would not have asked.

`tests/test_auth.py` covers identity. This file assumes identity works and asks
what an identity can read.

**Every scope is pinned to a populated part of the real corpus.** A filter that
returns nothing because the scope is empty is indistinguishable from a filter
that returns nothing because it works, so `tests/accounts.assert_populated`
refuses to build an account over an empty scope, and the counts below are
compared against a query that is written out here rather than borrowed from the
code under test.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.constants import (
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MEMBER_OF_PARLIAMENT,
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
)
from app.models import MP, Case, State, Work

from .accounts import (
    DISTRICT_A,
    MEMBER_A_EMAIL,
    MEMBER_B_EMAIL,
    MP_A_NAME,
    MP_B_NAME,
    ROLE_DISTRICT_EMAIL,
    ROLE_MINISTRY_EMAIL,
    ROLE_STATE_EMAIL,
    STATE_A,
    STATE_B,
    headers,
    token_for,
)
from .conftest import FIXTURE_A, FIXTURE_B

pytestmark = pytest.mark.corpus

# Every endpoint that must refuse an anonymous caller. `/health` is absent on
# purpose - it is liveness plus counts the data profile publishes, and putting
# it behind a login would make an outage and a bad password look the same from
# outside (app/main.py).
SCOPED_PATHS = [
    "/api/cases",
    "/api/cases/NG-0000000000",
    "/api/works/WS/MP847/2025-2026/160261",
    "/api/rulebook",
    "/api/audit/chain",
    "/api/audit/NG-0000000000",
    "/api/analytics/national",
    "/api/analytics/state/Uttar%20Pradesh",
    "/api/analytics/district/JALAUN",
    "/api/analytics/mp/1",
    "/api/ablation/report",
    "/api/auth/me",
]


@pytest.fixture(scope="module")
def signed_in(client):
    """A bearer header per account, obtained over HTTP the way a browser would."""
    return {
        email: headers(token_for(client, email))
        for email in (
            ROLE_MINISTRY_EMAIL,
            ROLE_STATE_EMAIL,
            ROLE_DISTRICT_EMAIL,
            MEMBER_A_EMAIL,
            MEMBER_B_EMAIL,
        )
    }


def case_ids(client, auth, **params):
    """One page of the ranked list, as case ids."""
    response = client.get("/api/cases", params=params, headers=auth)
    assert response.status_code == 200, response.text
    return [item["case_id"] for item in response.json()["items"]]


def total(client, auth, **params):
    response = client.get("/api/cases", params={"limit": 1, **params}, headers=auth)
    assert response.status_code == 200, response.text
    return response.json()["total"]


def expected_total(db, **scope):
    """The count, written out here rather than borrowed from the code under test."""
    query = (
        select(func.count())
        .select_from(Case)
        .join(Work, Work.id == Case.work_id)
        .where(Case.is_synthetic.is_(False))
    )
    for column, value in (
        (Work.state_id, scope.get("state_id")),
        (Work.district, scope.get("district")),
        (Work.mp_id, scope.get("mp_id")),
    ):
        if value is not None:
            query = query.where(column == value)
    return db.scalar(query)


# ---------------------------------------------------------------------------
# Nothing is open by default
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", SCOPED_PATHS)
def test_an_unauthenticated_request_is_401_and_never_a_default_open_answer(anon_client, path):
    """No token, no rows. Not a filtered response, not an empty one - a refusal."""
    response = anon_client.get(path)
    assert response.status_code == 401, f"{path} -> {response.status_code} {response.text[:200]}"


def test_every_api_route_carries_the_authentication_dependency():
    """Walk the route table rather than trusting the list above.

    A list of endpoints goes stale the moment somebody adds one; the
    application's own routing table does not. `/api/auth/login` is the single
    exemption, and it is named here so that adding a second one has to be a
    deliberate edit to this test.
    """
    from app.main import app

    def dependency_names(dependant):
        found = set()
        for child in dependant.dependencies:
            found.add(getattr(child.call, "__name__", str(child.call)))
            found |= dependency_names(child)
        return found

    open_routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api") or getattr(route, "dependant", None) is None:
            continue
        names = dependency_names(route.dependant)
        if "get_current_user" not in names:
            open_routes.append(path)

    assert open_routes == ["/api/auth/login"], f"routes with no authentication: {open_routes}"


# ---------------------------------------------------------------------------
# The list, per role, against a count computed independently
# ---------------------------------------------------------------------------


def test_the_ministry_sees_every_case(client, signed_in, db_session):
    """The widest scope: no predicate at all, not a predicate that matches everything."""
    assert total(client, signed_in[ROLE_MINISTRY_EMAIL]) == expected_total(db_session)


def test_a_state_nodal_token_sees_only_its_own_state(client, signed_in, db_session, api_accounts):
    scope_state = api_accounts[ROLE_STATE_NODAL].scope_state_id
    seen = total(client, signed_in[ROLE_STATE_EMAIL])
    assert seen == expected_total(db_session, state_id=scope_state)
    assert 0 < seen < expected_total(db_session), "narrower than the corpus, and not empty"

    listed = client.get(
        "/api/cases", params={"limit": 200}, headers=signed_in[ROLE_STATE_EMAIL]
    ).json()["items"]
    assert listed and all(item["state"] == STATE_A for item in listed)


def test_a_district_token_sees_only_its_own_district(client, signed_in, db_session, api_accounts):
    account = api_accounts[ROLE_DISTRICT_AUTHORITY]
    seen = total(client, signed_in[ROLE_DISTRICT_EMAIL])
    assert seen == expected_total(
        db_session, state_id=account.scope_state_id, district=account.scope_district
    )
    assert 0 < seen

    listed = client.get(
        "/api/cases", params={"limit": 200}, headers=signed_in[ROLE_DISTRICT_EMAIL]
    ).json()["items"]
    assert listed and all(
        (item["district"], item["state"]) == (DISTRICT_A, STATE_A) for item in listed
    )


def test_a_member_token_sees_only_its_own_members_cases(
    client, signed_in, db_session, api_accounts
):
    account = api_accounts[ROLE_MEMBER_OF_PARLIAMENT]
    seen = total(client, signed_in[MEMBER_A_EMAIL])
    assert seen == expected_total(db_session, mp_id=account.scope_mp_id)
    assert 0 < seen

    listed = client.get(
        "/api/cases", params={"limit": 200}, headers=signed_in[MEMBER_A_EMAIL]
    ).json()["items"]
    assert listed and all(item["mp_name"] == MP_A_NAME for item in listed)


def test_the_four_scopes_are_strictly_nested_and_none_is_the_corpus(client, signed_in):
    """Ministry > state > district, and the member's scope is not empty either.

    Stated as one assertion because the interesting failure is a scope that is
    accidentally as wide as the one above it - which each test above would pass
    individually if the predicate were dropped for exactly one role.
    """
    ministry = total(client, signed_in[ROLE_MINISTRY_EMAIL])
    state = total(client, signed_in[ROLE_STATE_EMAIL])
    district = total(client, signed_in[ROLE_DISTRICT_EMAIL])
    member = total(client, signed_in[MEMBER_A_EMAIL])
    assert ministry > state > district > 0
    assert 0 < member < ministry


def test_a_query_parameter_cannot_widen_a_scope(client, signed_in):
    """`?state=` and `?district=` narrow. They never reach outside the token.

    This is the URL edit invariant 10 names, made concretely: a district
    officer asking for another state by query parameter gets an empty page,
    because the role predicate is already on the select before the parameter is
    applied.
    """
    assert case_ids(client, signed_in[ROLE_DISTRICT_EMAIL], state=STATE_B) == []
    assert case_ids(client, signed_in[ROLE_STATE_EMAIL], state=STATE_B) == []
    # And a district officer naming their own district gains nothing and loses
    # nothing - the parameter is redundant, not additive.
    assert total(client, signed_in[ROLE_DISTRICT_EMAIL], district=DISTRICT_A) == total(
        client, signed_in[ROLE_DISTRICT_EMAIL]
    )


def test_a_state_officer_cannot_reach_a_same_named_district_in_another_state(
    client, signed_in, db_session, api_accounts
):
    """District names repeat across five states in this corpus. The predicate carries the state.

    `AGRA`, `KAITHAL`, `PILIBHIT` and `SHAHJAHANPUR` each name a district in
    five different states of `works`. A scope written as `district == D` alone
    would hand an officer the other five, which is why `models.User` binds a
    district authority to a state as well.
    """
    shared = db_session.execute(
        select(Work.district)
        .join(Case, Case.work_id == Work.id)
        .where(Work.district.is_not(None))
        .group_by(Work.district)
        .having(func.count(func.distinct(Work.state_id)) > 1)
        .limit(1)
    ).scalar()
    if shared is None:
        pytest.skip("no district name spans two states in this corpus")

    states_with_it = {
        row[0]
        for row in db_session.execute(
            select(State.name)
            .join(Work, Work.state_id == State.id)
            .join(Case, Case.work_id == Work.id)
            .where(Work.district == shared)
            .distinct()
        )
    }
    assert len(states_with_it) > 1

    listed = client.get(
        "/api/cases",
        params={"district": shared, "limit": 200},
        headers=signed_in[ROLE_STATE_EMAIL],
    ).json()["items"]
    # Whatever comes back is that officer's own state's rows, and never the
    # other four states' district of the same name.
    assert all(item["state"] == STATE_A for item in listed)


# ---------------------------------------------------------------------------
# THE hard test: one member, another member's case, fetched by id
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def two_members(db_session):
    """Fixture A's member and fixture B's member, with one case id each.

    Two real, different, populated members in different states. The case ids
    are read out of the corpus rather than transcribed, so the test cannot pass
    against an id that stopped belonging to the member it names.
    """
    out = {}
    for name in (MP_A_NAME, MP_B_NAME):
        row = db_session.execute(
            select(MP.id, Case.case_id, Work.work_id_canon)
            .join(Work, Work.mp_id == MP.id)
            .join(Case, Case.work_id == Work.id)
            .where(MP.name_canon == name, Case.is_synthetic.is_(False))
            .order_by(Case.case_id)
            .limit(1)
        ).first()
        if row is None:
            pytest.skip(f"{name} has no case in this corpus")
        out[name] = {"mp_id": row[0], "case_id": row[1], "work_id": row[2]}
    assert out[MP_A_NAME]["mp_id"] != out[MP_B_NAME]["mp_id"]
    assert out[MP_A_NAME]["case_id"] != out[MP_B_NAME]["case_id"]
    return out


def test_a_member_cannot_fetch_another_members_case_by_guessing_the_id(
    client, signed_in, two_members
):
    """The single most damaging leak this system could have, asserted directly.

    Member A signs in and asks for member B's case by its real id - the URL
    edit, not a filtered list. The refusal must come from the query: the case
    is fetched through the scoped select, so it is not found at all, rather
    than found and then withheld.

    404 and not 403, deliberately. A 403 would confirm that the id is real,
    which is a scoping leak spelled with a status code - the caller learns
    exactly what they would learn about an id that was never issued.
    """
    a, b = two_members[MP_A_NAME], two_members[MP_B_NAME]

    # Each member can read their own case, so the ids are good and the refusal
    # below is about scope rather than about a broken id.
    assert client.get(f"/api/cases/{a['case_id']}", headers=signed_in[MEMBER_A_EMAIL]).status_code == 200
    assert client.get(f"/api/cases/{b['case_id']}", headers=signed_in[MEMBER_B_EMAIL]).status_code == 200

    # And neither can read the other's.
    crossed = client.get(f"/api/cases/{b['case_id']}", headers=signed_in[MEMBER_A_EMAIL])
    assert crossed.status_code == 404, crossed.text
    assert b["case_id"] not in crossed.text or "No case" in crossed.text

    back = client.get(f"/api/cases/{a['case_id']}", headers=signed_in[MEMBER_B_EMAIL])
    assert back.status_code == 404, back.text


def test_the_refusal_is_indistinguishable_from_an_id_that_was_never_issued(
    client, signed_in, two_members
):
    """A real out-of-scope id and an invented id give the same answer.

    If they differed, the difference would be a way of asking whether another
    member's case exists.
    """
    real_but_foreign = client.get(
        f"/api/cases/{two_members[MP_B_NAME]['case_id']}", headers=signed_in[MEMBER_A_EMAIL]
    )
    invented = client.get("/api/cases/NG-DEADBEEF01", headers=signed_in[MEMBER_A_EMAIL])
    assert real_but_foreign.status_code == invented.status_code == 404


def test_a_member_cannot_reach_another_members_case_through_the_audit_trail(
    client, signed_in, two_members
):
    """The trail is scoped by its case, so the second door is the same door."""
    response = client.get(
        f"/api/audit/{two_members[MP_B_NAME]['case_id']}", headers=signed_in[MEMBER_A_EMAIL]
    )
    assert response.status_code == 404


def test_a_member_cannot_reach_another_members_work(client, signed_in, two_members):
    """`works` is a wider table than `cases` and is scoped by the same predicate."""
    own = client.get(
        f"/api/works/{two_members[MP_A_NAME]['work_id']}", headers=signed_in[MEMBER_A_EMAIL]
    )
    assert own.status_code == 200
    foreign = client.get(
        f"/api/works/{two_members[MP_B_NAME]['work_id']}", headers=signed_in[MEMBER_A_EMAIL]
    )
    assert foreign.status_code == 404


def test_a_district_officer_cannot_fetch_a_case_outside_their_district(client, signed_in):
    """The same URL edit, one role up. Fixture B is in MADURAI, Tamil Nadu."""
    from app.constants import case_id_for

    outside = case_id_for(FIXTURE_B)
    assert client.get(f"/api/cases/{outside}", headers=signed_in[ROLE_DISTRICT_EMAIL]).status_code == 404
    # And fixture A, which IS in JALAUN, is readable - so the 404 above is
    # scope and not a broken lookup.
    assert client.get(
        f"/api/cases/{case_id_for(FIXTURE_A)}", headers=signed_in[ROLE_DISTRICT_EMAIL]
    ).status_code == 200


# ---------------------------------------------------------------------------
# Analytics: refused by grain
# ---------------------------------------------------------------------------


def test_the_national_view_is_ministry_only(client, signed_in):
    assert client.get("/api/analytics/national", headers=signed_in[ROLE_MINISTRY_EMAIL]).status_code == 200
    for email in (ROLE_STATE_EMAIL, ROLE_DISTRICT_EMAIL, MEMBER_A_EMAIL):
        response = client.get("/api/analytics/national", headers=signed_in[email])
        assert response.status_code == 403, f"{email} -> {response.status_code}"


def test_a_state_officer_reads_their_own_state_and_no_other(client, signed_in):
    assert client.get(f"/api/analytics/state/{STATE_A}", headers=signed_in[ROLE_STATE_EMAIL]).status_code == 200
    assert client.get(f"/api/analytics/state/{STATE_B}", headers=signed_in[ROLE_STATE_EMAIL]).status_code == 403


def test_the_state_view_is_out_of_reach_for_the_district_and_member_roles(client, signed_in):
    for email in (ROLE_DISTRICT_EMAIL, MEMBER_A_EMAIL):
        assert client.get(f"/api/analytics/state/{STATE_A}", headers=signed_in[email]).status_code == 403


def test_a_district_officer_reads_their_own_district_queue_and_no_other(
    client, signed_in, db_session
):
    own = client.get(f"/api/analytics/district/{DISTRICT_A}", headers=signed_in[ROLE_DISTRICT_EMAIL])
    assert own.status_code == 200
    # And every case in the queue it returns is theirs.
    assert all(item["district"] == DISTRICT_A for item in own.json()["cases"])

    other = db_session.execute(
        select(Work.district)
        .join(Case, Case.work_id == Work.id)
        .where(Work.district.is_not(None), Work.district != DISTRICT_A)
        .limit(1)
    ).scalar()
    assert client.get(
        f"/api/analytics/district/{other}", headers=signed_in[ROLE_DISTRICT_EMAIL]
    ).status_code == 403


def test_a_member_reads_their_own_account_and_never_another_members(
    client, signed_in, two_members
):
    """`/api/analytics/mp/{id}` for a different member must be refused.

    A member's aggregate account position - allocation, utilisation, percentile
    against their peers - is exactly the figure MPLADS criticism lands on. One
    member reading another's would be the second most damaging leak in this
    system after reading their cases, and it is the same edit to the same kind
    of URL.
    """
    a, b = two_members[MP_A_NAME], two_members[MP_B_NAME]

    own = client.get(f"/api/analytics/mp/{a['mp_id']}", headers=signed_in[MEMBER_A_EMAIL])
    assert own.status_code == 200
    assert own.json()["mp"]["name"] == MP_A_NAME

    foreign = client.get(f"/api/analytics/mp/{b['mp_id']}", headers=signed_in[MEMBER_A_EMAIL])
    assert foreign.status_code == 403, foreign.text
    # Nothing about the other member leaked into the refusal.
    assert MP_B_NAME not in foreign.text


def test_a_district_officer_reads_no_members_account_at_all(client, signed_in, two_members):
    """A deliberate row of the matrix, not an omission.

    DOMAIN-MODEL.md (k): a district officer has no business seeing a member's
    aggregate account position; it is not evidence about any work in their
    district, and the one derived value they need, `mp_utilisation_pct`,
    reaches them through the case trace where it is scoped to that case's
    member.
    """
    for member in two_members.values():
        response = client.get(
            f"/api/analytics/mp/{member['mp_id']}", headers=signed_in[ROLE_DISTRICT_EMAIL]
        )
        assert response.status_code == 403, response.text


def test_a_state_officer_reads_members_seated_in_their_state_only(client, signed_in, two_members):
    """Matching `fund_accounts` in the matrix: MPs seated in S."""
    seated = client.get(
        f"/api/analytics/mp/{two_members[MP_A_NAME]['mp_id']}", headers=signed_in[ROLE_STATE_EMAIL]
    )
    assert seated.status_code == 200
    elsewhere = client.get(
        f"/api/analytics/mp/{two_members[MP_B_NAME]['mp_id']}", headers=signed_in[ROLE_STATE_EMAIL]
    )
    assert elsewhere.status_code == 403


def test_a_member_id_that_does_not_exist_does_not_leak_through_the_grain_check(client, signed_in):
    """A refused role is refused before it learns whether the id is real."""
    assert client.get("/api/analytics/mp/99999999", headers=signed_in[MEMBER_A_EMAIL]).status_code == 403
    assert client.get("/api/analytics/mp/99999999", headers=signed_in[ROLE_MINISTRY_EMAIL]).status_code == 404


# ---------------------------------------------------------------------------
# Writes, and the member's read-only role
# ---------------------------------------------------------------------------


def test_a_member_cannot_add_a_note_even_to_their_own_case(client, signed_in, two_members):
    """Read-only means read-only, on their own rows as much as anyone's.

    The scheme's subject does not adjudicate the scheme's findings
    (DOMAIN-MODEL.md (k)). 403 rather than 404 here because the case IS in
    scope: what is refused is the verb, not the row, and pretending the case
    was missing would be a worse answer than the true one.
    """
    response = client.post(
        f"/api/cases/{two_members[MP_A_NAME]['case_id']}/notes",
        json={"text": "A member should not be able to write this."},
        headers=signed_in[MEMBER_A_EMAIL],
    )
    assert response.status_code == 403, response.text


def test_a_member_cannot_recompute_even_their_own_case(client, signed_in, two_members):
    response = client.post(
        f"/api/cases/{two_members[MP_A_NAME]['case_id']}/recompute",
        headers=signed_in[MEMBER_A_EMAIL],
    )
    assert response.status_code == 403


def test_a_district_officers_note_cannot_reach_a_case_outside_their_district(client, signed_in):
    """404 before the write, so an out-of-scope note never reaches `audit_log`.

    404 and not 403 because here the ROW is out of reach, which is the opposite
    of the case above: the verb is allowed and the case is not theirs.
    """
    from app.constants import case_id_for

    response = client.post(
        f"/api/cases/{case_id_for(FIXTURE_B)}/notes",
        json={"text": "This must not be written."},
        headers=signed_in[ROLE_DISTRICT_EMAIL],
    )
    assert response.status_code == 404


def test_a_note_records_the_authenticated_officer_and_not_a_declared_role(client, signed_in):
    """The actor line comes from the token, together with the user id.

    Until Phase 6 the caller declared which role was writing and an append-only
    row recorded what was declared.
    """
    from app.constants import case_id_for

    written = client.post(
        f"/api/cases/{case_id_for(FIXTURE_A)}/notes",
        # A declared role in the body is ignored; there is no such field.
        json={"text": "Payment register requested.", "actor_role": "ministry"},
        headers=signed_in[ROLE_DISTRICT_EMAIL],
    )
    assert written.status_code == 201, written.text
    event = written.json()["event"]
    assert event["actor_role"] == ROLE_DISTRICT_AUTHORITY
    assert event["actor_id"] is not None


# ---------------------------------------------------------------------------
# The two role-gated documents, and the one that is not gated
# ---------------------------------------------------------------------------


def test_the_gap_report_is_ministry_only(client, signed_in):
    """A recommendation to MoSPI about MoSPI's own publishing.

    DOMAIN-MODEL.md (k) has no row for `ablation_findings` - the table did not
    exist when the matrix was written - so this is the call this phase made,
    and the matrix now records it (`routers/ablation.py`).
    """
    assert client.get("/api/ablation/report", headers=signed_in[ROLE_MINISTRY_EMAIL]).status_code == 200
    for email in (ROLE_STATE_EMAIL, ROLE_DISTRICT_EMAIL, MEMBER_A_EMAIL):
        assert client.get("/api/ablation/report", headers=signed_in[email]).status_code == 403


def test_the_whole_chain_walk_is_ministry_only(client, signed_in):
    """Every other audit read is scoped by a case. This one is over the whole trail."""
    assert client.get("/api/audit/chain", headers=signed_in[ROLE_MINISTRY_EMAIL]).status_code == 200
    for email in (ROLE_STATE_EMAIL, ROLE_DISTRICT_EMAIL, MEMBER_A_EMAIL):
        assert client.get("/api/audit/chain", headers=signed_in[email]).status_code == 403


def test_the_rulebook_is_readable_by_all_four_roles(client, signed_in):
    """Everyone judged by a rule is entitled to read it.

    A rulebook only its author may read is not an explainable system, it is an
    assertion. It names no state, district, agency or member, so there is
    nothing here to scope by (DOMAIN-MODEL.md (k): "all, read").
    """
    for email in (ROLE_MINISTRY_EMAIL, ROLE_STATE_EMAIL, ROLE_DISTRICT_EMAIL, MEMBER_A_EMAIL):
        response = client.get("/api/rulebook", headers=signed_in[email])
        assert response.status_code == 200, f"{email} -> {response.status_code}"
        assert response.json()["version"]


# ---------------------------------------------------------------------------
# The one redaction, and what it does NOT touch
# ---------------------------------------------------------------------------


def test_a_member_sees_that_a_note_exists_and_not_what_it_says(client, signed_in, two_members):
    """The only place in this API where a response shape changes by role.

    An MP sees that a note was added, by which role, and when. The text is the
    administration's working record (DOMAIN-MODEL.md (k)).
    """
    case_id = two_members[MP_A_NAME]["case_id"]
    secret = "Vendor register impounded pending inspection."
    posted = client.post(
        f"/api/cases/{case_id}/notes",
        json={"text": secret},
        headers=signed_in[ROLE_MINISTRY_EMAIL],
    )
    assert posted.status_code == 201, posted.text

    as_member = client.get(f"/api/audit/{case_id}", headers=signed_in[MEMBER_A_EMAIL])
    assert as_member.status_code == 200
    assert secret not in as_member.text, "the note text reached the member"

    notes = [event for event in as_member.json()["events"] if event["event"] == "NOTE_ADDED"]
    assert notes, "the member should see that a note happened"
    for note in notes:
        assert note["payload"]["redacted"] is True
        assert "text" not in note["payload"]
        # What the member IS entitled to: that it happened, by whom, and when.
        assert note["actor_role"] and note["at"]

    as_ministry = client.get(f"/api/audit/{case_id}", headers=signed_in[ROLE_MINISTRY_EMAIL])
    assert secret in as_ministry.text


def test_the_redaction_does_not_alter_any_other_event(client, signed_in, two_members):
    """Only `NOTE_ADDED` payloads change. The scoring events are identical."""
    case_id = two_members[MP_A_NAME]["case_id"]
    member = client.get(f"/api/audit/{case_id}", headers=signed_in[MEMBER_A_EMAIL]).json()
    ministry = client.get(f"/api/audit/{case_id}", headers=signed_in[ROLE_MINISTRY_EMAIL]).json()

    assert [event["id"] for event in member["events"]] == [
        event["id"] for event in ministry["events"]
    ], "the member sees every row, redacted or not - no row is hidden"

    for mine, theirs in zip(member["events"], ministry["events"], strict=True):
        if mine["event"] == "NOTE_ADDED":
            continue
        assert mine == theirs


def test_the_integrity_claim_is_about_the_stored_row_and_not_the_printed_one(
    client, signed_in, two_members
):
    """`rows_intact` must not be computed over the redacted payload.

    The hash is checked against what the database holds, before anything is
    removed, so the claim stays a claim about the trail rather than about this
    particular response. A reader who recomputes the hash of a redacted row
    will find it does not match, which is the honest outcome: the redaction is
    visible as a redaction rather than passed off as the whole row.
    """
    case_id = two_members[MP_A_NAME]["case_id"]
    member = client.get(f"/api/audit/{case_id}", headers=signed_in[MEMBER_A_EMAIL]).json()
    ministry = client.get(f"/api/audit/{case_id}", headers=signed_in[ROLE_MINISTRY_EMAIL]).json()
    assert member["rows_intact"] is ministry["rows_intact"] is True
    assert member["first_broken_row"] == ministry["first_broken_row"] is None


def test_only_the_member_role_is_redacted(client, signed_in, two_members):
    """A district or state officer reading the same case reads the note in full."""
    case_id = two_members[MP_A_NAME]["case_id"]
    trail = client.get(f"/api/audit/{case_id}", headers=signed_in[ROLE_STATE_EMAIL])
    assert trail.status_code == 200
    notes = [event for event in trail.json()["events"] if event["event"] == "NOTE_ADDED"]
    assert notes and all("text" in note["payload"] for note in notes)


# ---------------------------------------------------------------------------
# Scoping happens in the query, not after it
# ---------------------------------------------------------------------------


def test_the_scoped_select_is_narrowed_before_it_runs(db_session, api_accounts):
    """Invariant 10 asserted against the SQL, not against a response body.

    Every test above could in principle be satisfied by fetching everything and
    dropping rows in Python, which is precisely the failure the invariant names:
    the row would already have left the database. This one compiles the select
    each role's list starts from and asserts the predicate is in its WHERE
    clause.
    """
    from app.routers.scoping import scoped_cases

    def where_clause(user):
        return str(scoped_cases(user).compile(compile_kwargs={"literal_binds": True}))

    ministry = where_clause(api_accounts[ROLE_MINISTRY])
    assert "WHERE" not in ministry, "the widest scope adds no predicate at all"

    state_sql = where_clause(api_accounts[ROLE_STATE_NODAL])
    assert f"works.state_id = {api_accounts[ROLE_STATE_NODAL].scope_state_id}" in state_sql

    district = api_accounts[ROLE_DISTRICT_AUTHORITY]
    district_sql = where_clause(district)
    assert f"works.state_id = {district.scope_state_id}" in district_sql
    assert f"works.district = '{district.scope_district}'" in district_sql, (
        "a district authority is bound to a state AND a district - district names "
        "repeat across five states in this corpus"
    )

    member = api_accounts[ROLE_MEMBER_OF_PARLIAMENT]
    assert f"works.mp_id = {member.scope_mp_id}" in where_clause(member)


def test_an_unknown_role_sees_nothing_rather_than_everything(api_accounts):
    """A hand-edited `users.role` must fail closed.

    The column carries a CHECK constraint naming the four, so this is
    unreachable through the API. It is asserted anyway because the alternative
    implementation - a chain of `if` clauses ending in an unfiltered select - is
    the one that fails open, and the difference is invisible until it matters.
    """
    from types import SimpleNamespace

    from fastapi import HTTPException

    from app.routers.scoping import work_predicate

    with pytest.raises(HTTPException) as raised:
        work_predicate(SimpleNamespace(role="auditor_general", scope_state_id=None))
    assert raised.value.status_code == 403
