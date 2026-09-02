"""A district is a state and a name, never a name.

The regression file for a scoping defect that was live in
`/api/analytics/district/{district}`: the endpoint resolved the district with
`WHERE works.district = :district LIMIT 1`, unordered, and then filtered its
rollups on the bare name as well. A district name does not identify a district
in this corpus - 61 of the 634 names carrying cases belong to more than one
state - so the endpoint picked one arbitrarily and got three things wrong at
once, in two different directions:

* **It refused a legitimate officer.** A District Authority scoped to Uttar
  Pradesh's ALWAR had their own district resolved to Rajasthan's, so the grain
  check compared Rajasthan's state id against theirs and refused them with the
  sentence "Your scope is 'ALWAR' and it is not 'ALWAR'".
* **It answered the Ministry with a sum of two districts.** `rollup_district
  WHERE district = 'ALWAR'` returns both rows, and the summary added them - one
  row of figures describing no district that exists.
* **It mixed two districts' agencies and, for the Ministry, two districts'
  cases**, a thousand kilometres apart, into one queue.

These tests are written as URL edits over real accounts on the real corpus,
like the rest of `test_role_scoping.py`, because that is the shape of the bug:
two officers ask the SAME url and must get two different, correct answers, and
neither must be able to reach the other's rows by any spelling.

Every count asserted here is computed by a query written out in this file
rather than borrowed from the code under test.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.auth import hash_password
from app.constants import DATA_AS_OF, ROLE_DISTRICT_AUTHORITY
from app.models import Case, State, User, Work

from .accounts import PASSWORD, ROLE_MINISTRY_EMAIL, headers, token_for
from .conftest import api_client

pytestmark = pytest.mark.corpus

# The name the defect was found on. Rajasthan and Uttar Pradesh both carry a
# district called this, and the case counts are lopsided enough (70 against 1)
# that a test getting the wrong one cannot pass by coincidence.
PREFERRED = "ALWAR"


def _collisions(session) -> dict[str, list[tuple[int, str, int]]]:
    """Every district name carried by more than one state, with per-state counts.

    `{name: [(state_id, state_name, cases), ...]}`, non-synthetic cases only,
    which is the population every rollup in this product is built over
    (invariant 12). Written out here rather than read from `rollup_district` so
    that a rollup built by the code under test cannot make this test agree with
    it.
    """
    rows = session.execute(
        select(Work.state_id, State.name, Work.district, func.count())
        .join(State, State.id == Work.state_id)
        .join(Case, Case.work_id == Work.id)
        .where(Work.district.is_not(None), Case.is_synthetic.is_(False))
        .group_by(Work.state_id, State.name, Work.district)
    ).all()

    by_name: dict[str, list[tuple[int, str, int]]] = {}
    for state_id, state_name, district, count in rows:
        by_name.setdefault(district, []).append((state_id, state_name, count))
    return {name: sorted(v, key=lambda r: r[1]) for name, v in by_name.items() if len(v) > 1}


@pytest.fixture(scope="module")
def collision(api_session_factory):
    """One colliding district name and the two states that carry it.

    Skips rather than fails if the corpus ever stops containing a collision:
    that would mean the bug is unreproducible on this data, not that the fix
    regressed, and the two are different findings.
    """
    session = api_session_factory()
    try:
        found = _collisions(session)
    finally:
        session.close()

    if not found:
        pytest.skip("no district name in this corpus belongs to two states")

    name = PREFERRED if PREFERRED in found else max(found, key=lambda k: len(found[k]))
    # The two states with the most lopsided counts, so a wrong answer cannot
    # coincide with a right one.
    carriers = sorted(found[name], key=lambda row: -row[2])
    return name, carriers[0], carriers[1]


@pytest.fixture(scope="module")
def two_district_officers(api_session_factory, collision):
    """A District Authority in each of the two states, both scoped to that name.

    This is the pair the product could not previously represent: two officers,
    two different districts, one district NAME. Whichever of them the old
    resolution happened to pick, the other was locked out of their own queue.
    """
    district, (state_a_id, state_a_name, _), (state_b_id, state_b_name, _) = collision

    session = api_session_factory()
    try:
        emails = {}
        for state_id, state_name in ((state_a_id, state_a_name), (state_b_id, state_b_name)):
            email = f"collision-{state_id}@test.nigrani"
            emails[state_name] = email
            if session.scalar(select(User).where(User.email == email)) is not None:
                continue
            session.add(
                User(
                    email=email,
                    password_hash=hash_password(PASSWORD),
                    role=ROLE_DISTRICT_AUTHORITY,
                    display_name=f"{district} ({state_name}) Test District Authority",
                    is_active=True,
                    created_at=datetime.combine(DATA_AS_OF, datetime.min.time()),
                    scope_state_id=state_id,
                    scope_district=district,
                )
            )
        session.commit()
    finally:
        session.close()
    return emails


def carriers_of(collision):
    """The two `(state_id, state_name, cases)` carriers out of a `collision`."""
    _, first, second = collision
    return (first, second)


def _district_payload(client, district, **params):
    response = client.get(f"/api/analytics/district/{district}", params=params)
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# The failure this file exists for
# ---------------------------------------------------------------------------


def test_each_officer_reads_their_own_state_s_district_of_the_shared_name(
    api_session_factory, collision, two_district_officers
):
    """Both officers ask the same URL and each gets their own district.

    This is the exact scenario that used to 403 for whichever officer lost the
    arbitrary resolution: the URL carries only the name, and the state has to
    come from the caller's own row for both answers to be right at once.
    """
    district, (_, state_a, cases_a), (_, state_b, cases_b) = collision
    assert cases_a != cases_b, "pick a lopsided collision or this proves nothing"

    for state_name, expected in ((state_a, cases_a), (state_b, cases_b)):
        with api_client(api_session_factory, email=two_district_officers[state_name]) as officer:
            payload = _district_payload(officer, district)
            assert payload["district"] == district
            assert payload["state"] == state_name, (
                f"the officer for {state_name} was answered with {payload['state']}'s "
                f"district of the same name"
            )
            assert payload["summary"]["cases"] == expected, (
                f"{state_name}/{district} has {expected} cases; the endpoint reported "
                f"{payload['summary']['cases']}"
            )
            # The summed answer the bug used to produce, named explicitly so a
            # regression cannot pass by matching one of the two real counts.
            assert payload["summary"]["cases"] != cases_a + cases_b


def test_neither_officer_can_reach_the_other_state_s_district_of_that_name(
    api_session_factory, collision, two_district_officers
):
    """Same URL, two callers, and no row appears in both answers.

    The queue, the agency list and the summary are checked together, because
    the old code got the queue right for a scoped role - `list_query` already
    carried the predicate - while getting the summary and the agencies wrong.
    A test that only read `cases` would have missed two thirds of the defect.
    """
    district, (_, state_a, _), (_, state_b, _) = collision

    seen = {}
    for state_name in (state_a, state_b):
        with api_client(api_session_factory, email=two_district_officers[state_name]) as officer:
            payload = _district_payload(officer, district, limit=500)
            seen[state_name] = payload
            assert all(row["state"] == state_name for row in payload["agencies"]), (
                f"the agency list for {state_name}/{district} carries another state's agencies"
            )
            assert all(item["district"] == district for item in payload["cases"])

    ids_a = {item["case_id"] for item in seen[state_a]["cases"]}
    ids_b = {item["case_id"] for item in seen[state_b]["cases"]}
    assert ids_a and ids_b, "both districts must carry cases for this to prove anything"
    assert ids_a.isdisjoint(ids_b), (
        f"{len(ids_a & ids_b)} case(s) appear in both states' queues for {district!r}"
    )

    # The agency IDS are deliberately NOT asserted disjoint, and the reason is a
    # fact about the corpus rather than about the endpoint. `DISTRICT COLLECTOR
    # ALWAR` is one canonical agency with works attributed to Rajasthan and to
    # Uttar Pradesh - 70 agencies in this corpus span more than one state, most
    # of them looking like a mis-stated state on a handful of rows - so the same
    # agency legitimately appears in both districts' lists.
    #
    # What must be right is the FIGURE each officer is given for it. Before the
    # fix both officers received both rollup rows, so a shared agency was
    # reported to each of them with the other district's count beside its own.
    # The expected counts are computed here from `works` rather than read back
    # from `rollup_agency`, which is the table the bug was reading wrongly.
    session = api_session_factory()
    try:
        expected = {}
        for state_id, agency_id, count in session.execute(
            select(Work.state_id, Work.agency_id, func.count())
            .join(Case, Case.work_id == Work.id)
            .where(Work.district == district, Case.is_synthetic.is_(False))
            .group_by(Work.state_id, Work.agency_id)
        ).all():
            expected[(state_id, agency_id)] = count
    finally:
        session.close()

    for state_id, state_name, _ in (carriers_of(collision)):
        if state_name not in seen:
            continue
        rows = {row["agency_id"]: row["cases"] for row in seen[state_name]["agencies"]}
        want = {
            agency_id: count
            for (sid, agency_id), count in expected.items()
            if sid == state_id
        }
        assert rows == want, (
            f"{state_name}/{district}: agency counts {rows} do not match this state's own "
            f"{want} - the other state's rollup rows are being mixed in"
        )


def test_an_officer_is_refused_a_district_that_is_not_theirs(
    api_session_factory, collision, two_district_officers
):
    """And the refusal does not contradict itself.

    The old message read "Your scope is 'ALWAR' and it is not 'ALWAR'". Whatever
    a refusal says now, it must not name the caller's own district as the thing
    they may not have.
    """
    district, (_, state_a, _), _ = collision
    with api_client(api_session_factory, email=two_district_officers[state_a]) as officer:
        response = officer.get("/api/analytics/district/NOWHERE-AT-ALL")
        assert response.status_code == 403, response.text
        detail = response.json()["detail"]
        assert "NOWHERE-AT-ALL" in detail
        assert f"{district!r} and it is not {district!r}" not in detail


# ---------------------------------------------------------------------------
# The Ministry, which is the one role with no state of its own
# ---------------------------------------------------------------------------


def test_the_ministry_is_asked_which_state_rather_than_handed_a_sum(client, collision):
    """An ambiguous name without `?state=` is a 400 naming the candidates.

    Refusing is the point. The old behaviour answered, and the answer was two
    districts added together into a row describing neither.
    """
    district, (_, state_a, cases_a), (_, state_b, cases_b) = collision

    response = client.get(f"/api/analytics/district/{district}")
    assert response.status_code == 400, response.text
    detail = response.json()["detail"]
    assert state_a in detail and state_b in detail, detail
    assert "state" in detail.lower()


def test_the_ministry_reads_one_state_s_district_at_a_time(client, collision):
    district, (_, state_a, cases_a), (_, state_b, cases_b) = collision

    for state_name, expected in ((state_a, cases_a), (state_b, cases_b)):
        payload = _district_payload(client, district, state=state_name)
        assert payload["state"] == state_name
        assert payload["summary"]["cases"] == expected
        assert payload["summary"]["cases"] != cases_a + cases_b
        assert all(row["state"] == state_name for row in payload["agencies"])


def test_the_ministry_asking_for_a_state_that_does_not_carry_the_name_gets_a_404(
    client, collision, api_session_factory
):
    district, _, _ = collision
    session = api_session_factory()
    try:
        carriers = {name for _, name, _ in _collisions(session)[district]}
        elsewhere = session.scalar(
            select(State.name).where(State.name.not_in(carriers)).order_by(State.name)
        )
    finally:
        session.close()
    if elsewhere is None:
        pytest.skip("every state in the corpus carries this district name")

    response = client.get(f"/api/analytics/district/{district}", params={"state": elsewhere})
    assert response.status_code == 404, response.text


# ---------------------------------------------------------------------------
# The whole corpus, not just the one name the bug was found on
# ---------------------------------------------------------------------------


def test_every_colliding_district_name_resolves_to_exactly_one_state(
    client, api_session_factory
):
    """All 61, audited. The fix is not allowed to work only for ALWAR.

    For each colliding name and each state that carries it, the Ministry asking
    with `?state=` must get that state's own figures - never the other's, and
    never the sum. This is the assertion that would have failed on every one of
    the 61 before the fix, and it runs over all of them rather than over a
    sample.
    """
    session = api_session_factory()
    try:
        collisions = _collisions(session)
    finally:
        session.close()

    if not collisions:
        pytest.skip("no district name in this corpus belongs to two states")

    wrong = []
    for district, carriers in sorted(collisions.items()):
        total = sum(count for _, _, count in carriers)

        # Asked without a state, every one of them must be refused rather than
        # answered with a sum - and the refusal must name the candidates, or the
        # caller has been told to add a parameter without being told what to put
        # in it.
        response = client.get(f"/api/analytics/district/{district}")
        if response.status_code != 400:
            wrong.append(
                f"{district!r}: answered {response.status_code} with no state given; "
                f"an ambiguous name must be refused"
            )
        else:
            detail = response.json()["detail"]
            missing = [name for _, name, _ in carriers if name not in detail]
            if missing:
                wrong.append(f"{district!r}: refusal does not name {missing}")

        for _, state_name, expected in carriers:
            payload = _district_payload(client, district, state=state_name)
            if payload["state"] != state_name or payload["summary"]["cases"] != expected:
                wrong.append(
                    f"{district!r}/{state_name}: expected {expected} cases, got "
                    f"{payload['summary']['cases']} for state {payload['state']!r}"
                )
            elif payload["summary"]["cases"] == total and len(carriers) > 1:
                wrong.append(f"{district!r}/{state_name}: reported the sum across states")
            if any(row["state"] != state_name for row in payload["agencies"]):
                wrong.append(f"{district!r}/{state_name}: agency list carries another state")

    assert not wrong, f"{len(wrong)} discrepancies:\n" + "\n".join(wrong[:20])
    assert len(collisions) >= 2, "this audit is only meaningful over several collisions"


def test_an_unambiguous_district_needs_no_state_parameter(client, api_session_factory):
    """The other 573 names still answer on the name alone.

    The fix must not turn a working call into a required-parameter error for
    every district that was never ambiguous - which includes JALAUN, the
    district the four demo accounts are provisioned against.
    """
    session = api_session_factory()
    try:
        ambiguous = set(_collisions(session))
        unambiguous = [
            (district, state_name, count)
            for district, state_name, count in session.execute(
                select(Work.district, State.name, func.count())
                .join(State, State.id == Work.state_id)
                .join(Case, Case.work_id == Work.id)
                .where(Work.district.is_not(None), Case.is_synthetic.is_(False))
                .group_by(Work.district, State.name)
            ).all()
            if district not in ambiguous
        ]
    finally:
        session.close()

    assert unambiguous, "the corpus has no unambiguous district to check"
    for district, state_name, expected in sorted(unambiguous)[:25]:
        payload = _district_payload(client, district)
        assert payload["state"] == state_name, district
        assert payload["summary"]["cases"] == expected, district
