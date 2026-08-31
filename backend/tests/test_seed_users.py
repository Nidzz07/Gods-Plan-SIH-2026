"""The demo account provisioning script.

Small file, three claims worth holding: the scopes it picks are populated, the
credentials it prints are the credentials that work, and running it twice does
not accumulate accounts or leave an old password valid.

Runs over a copy of the corpus, like the rest of the API suite - this script
writes to `users`, and a test that grew the developer's account list by four
rows per run would be provisioning access nobody asked for.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.constants import (
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MEMBER_OF_PARLIAMENT,
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
    ROLES,
)
from app.models import Case, User, Work
from app.seed_users import report, seed

from .conftest import api_client, copy_corpus, sessionmaker_on

pytestmark = pytest.mark.corpus


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    """A fresh corpus copy with the four demo accounts written onto it.

    `app.seed_users` reads `SessionLocal` and `engine` from `app.db` at module
    scope, so both are pointed at the copy for the duration - the alternative
    is a script that takes a session it never has a reason to take outside a
    test, which is a worse shape for the sake of a fixture.
    """
    import app.seed_users as seed_users

    engine, factory = sessionmaker_on(copy_corpus(tmp_path / "nigrani.db"))
    monkeypatch.setattr(seed_users, "engine", engine)
    monkeypatch.setattr(seed_users, "SessionLocal", factory)
    try:
        with factory() as db:
            written = seed(db)
        yield factory, written
    finally:
        engine.dispose()


def test_it_writes_one_account_per_role(seeded):
    factory, written = seeded
    assert {entry["role"] for entry in written} == set(ROLES)
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 4


def test_every_scope_it_chooses_covers_real_cases(seeded):
    """The whole reason it runs after `derive_all`.

    A login that opens onto an empty screen is indistinguishable from a broken
    one, so the script picks its state, district and member by counting derived
    cases. This asserts the counts it printed are the counts the database holds.
    """
    factory, written = seeded
    with factory() as db:
        for entry in written:
            user = db.get(User, entry["user"].id)
            query = (
                select(func.count())
                .select_from(Case)
                .join(Work, Work.id == Case.work_id)
                .where(Case.is_synthetic.is_(False))
            )
            if user.scope_mp_id is not None:
                query = query.where(Work.mp_id == user.scope_mp_id)
            else:
                if user.scope_state_id is not None:
                    query = query.where(Work.state_id == user.scope_state_id)
                if user.scope_district is not None:
                    query = query.where(Work.district == user.scope_district)
            count = db.scalar(query)
            assert count > 0, f"the {entry['role']} account opens onto nothing"
            assert count == entry["cases"], (
                f"the {entry['role']} account was advertised as covering "
                f"{entry['cases']} cases and covers {count}"
            )


def test_the_member_scope_is_advertised_as_the_whole_portfolio(seeded):
    """It is selected from one district; it reaches every district it recommends into.

    The member is picked as the busiest inside the demo district so that the
    walkthrough shows one set of works from three angles. Their scope carries
    no geography, so the printed figure has to be their own total - a
    credentials block that understated a scope would tell the operator
    something false about what they are handing over.
    """
    factory, written = seeded
    entry = next(e for e in written if e["role"] == ROLE_MEMBER_OF_PARLIAMENT)
    with factory() as db:
        user = db.get(User, entry["user"].id)
        districts = db.scalar(
            select(func.count(func.distinct(Work.district)))
            .select_from(Case)
            .join(Work, Work.id == Case.work_id)
            .where(Case.is_synthetic.is_(False), Work.mp_id == user.scope_mp_id)
        )
    assert districts >= 1
    assert str(districts) in entry["note"]


def test_the_scope_columns_match_the_role_each_account_carries(seeded):
    """The `users` CHECK constraint accepted them, and this says what shape that is."""
    factory, written = seeded
    with factory() as db:
        by_role = {u.role: u for u in db.scalars(select(User))}

    ministry = by_role[ROLE_MINISTRY]
    assert (ministry.scope_state_id, ministry.scope_district, ministry.scope_mp_id) == (
        None,
        None,
        None,
    )
    state = by_role[ROLE_STATE_NODAL]
    assert state.scope_state_id and not state.scope_district and not state.scope_mp_id

    district = by_role[ROLE_DISTRICT_AUTHORITY]
    assert district.scope_state_id and district.scope_district
    assert district.scope_mp_id is None, "a district authority carries no member scope"

    member = by_role[ROLE_MEMBER_OF_PARLIAMENT]
    assert member.scope_mp_id
    assert member.scope_state_id is None and member.scope_district is None


def test_no_plaintext_password_reaches_the_database(seeded):
    """`users.password_hash` is a bcrypt digest and never the password itself."""
    factory, written = seeded
    with factory() as db:
        stored = {u.email: u.password_hash for u in db.scalars(select(User))}
    for entry in written:
        digest = stored[entry["email"]]
        assert digest.startswith("$2")
        assert entry["password"] not in digest


def test_the_printed_credentials_are_the_credentials_that_work(seeded):
    """Every account it advertises signs in, and reads back the scope it printed."""
    factory, written = seeded
    with api_client(factory) as client:
        for entry in written:
            response = client.post(
                "/api/auth/login",
                json={"email": entry["email"], "password": entry["password"]},
            )
            assert response.status_code == 200, f"{entry['email']} -> {response.text[:200]}"
            body = response.json()
            assert body["user"]["role"] == entry["role"]
            assert body["user"]["can_write"] is (entry["role"] != ROLE_MEMBER_OF_PARLIAMENT)


def test_running_it_twice_replaces_the_passwords_and_adds_no_accounts(seeded):
    """Idempotent by address, and the old password stops working.

    `ingest.run` drops `users`, so re-running this script is the ordinary way
    to get accounts back after a rebuild. Accumulating a second set of four, or
    leaving a previous password valid, would both be quiet defects.
    """
    factory, first = seeded
    with factory() as db:
        second = seed(db)
        assert db.scalar(select(func.count()).select_from(User)) == 4

    with api_client(factory) as client:
        for old, new in zip(first, second, strict=True):
            assert old["email"] == new["email"]
            assert old["password"] != new["password"]
            stale = client.post(
                "/api/auth/login", json={"email": old["email"], "password": old["password"]}
            )
            assert stale.status_code == 401, "the previous password still works"
            fresh = client.post(
                "/api/auth/login", json={"email": new["email"], "password": new["password"]}
            )
            assert fresh.status_code == 200


def test_the_printed_block_names_the_scoping_decisions_it_is_handing_over(seeded):
    """The credentials go to a demo operator, so the caveats travel with them.

    CLAUDE.md's honesty rules: the login is a demo over seeded accounts, and
    the member role is read-only. Both are on the same screen as the passwords
    rather than in a document nobody opens at a podium.
    """
    _factory, written = seeded
    printed = report(written)
    assert "not an identity provider" in printed
    assert "READ-ONLY" in printed
    assert "stored nowhere" in printed
    for entry in written:
        assert entry["email"] in printed
        assert entry["password"] in printed
