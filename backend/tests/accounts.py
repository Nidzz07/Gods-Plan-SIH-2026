"""The four demo accounts, built on a copy of the corpus, for the auth tests.

`tests/test_auth.py` and `tests/test_role_scoping.py` both need real accounts
over real rows: a `state_nodal` bound to a state with no cases would pass a
scoping test by returning nothing, which proves the filter ran and nothing
about whether it filtered correctly. So every scope here is pinned to a
populated part of the committed corpus, and `assert_populated` is what stops
that from quietly stopping being true after a re-ingest.

The scopes are the same four `app/seed_users.py` provisions for the
walkthrough, and for the same reason: what the demo shows and what the tests
prove should be the same rows.

**Passwords here are test literals and are not the demo credentials.**
`seed_users.py` generates its passwords at run time and prints them once to
stdout; nothing in this repository stores a password that unlocks a running
NIGRANI.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.constants import (
    DATA_AS_OF,
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MEMBER_OF_PARLIAMENT,
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
)
from app.models import MP, Case, State, User, Work

# docs/contract/fixtures.md. Fixture A is MP 91's work, in JALAUN, Uttar
# Pradesh; fixture B is MP 512's, in MADURAI, Tamil Nadu. Two real, populated,
# different members in different states is exactly what the hard scoping test
# needs, and using the documented fixtures means the ids are already written
# down somewhere an auditor can check.
MP_A_NAME = "BABURAM NISHAD"
MP_B_NAME = "R GIRIRAJAN"
STATE_A = "Uttar Pradesh"
STATE_B = "Tamil Nadu"
DISTRICT_A = "JALAUN"

PASSWORD = "test-account-password"
WRONG_PASSWORD = "test-account-passwore"

# The addresses, named so a test says which officer it is signing in as rather
# than repeating a literal.
ROLE_MINISTRY_EMAIL = "ministry@test.nigrani"
ROLE_STATE_EMAIL = "state@test.nigrani"
ROLE_DISTRICT_EMAIL = "district@test.nigrani"
MEMBER_A_EMAIL = "member@test.nigrani"
MEMBER_B_EMAIL = "member-b@test.nigrani"
INACTIVE_EMAIL = "inactive@test.nigrani"
ABSENT_EMAIL = "nobody@test.nigrani"


def mp_id(db: Session, name: str) -> int:
    """One member's primary key by canonical name, or a skip if the corpus moved."""
    found = db.scalar(select(MP.id).where(MP.name_canon == name))
    if found is None:
        pytest.skip(f"no MP named {name!r} in the corpus - re-run `python -m ingest.run`")
    return found


def state_id(db: Session, name: str) -> int:
    found = db.scalar(select(State.id).where(State.name == name))
    if found is None:
        pytest.skip(f"no state named {name!r} in the corpus")
    return found


def case_count(db: Session, **scope) -> int:
    """How many non-synthetic cases a scope covers. The populated-ness check."""
    query = (
        select(func.count())
        .select_from(Case)
        .join(Work, Work.id == Case.work_id)
        .where(Case.is_synthetic.is_(False))
    )
    if "state_id" in scope:
        query = query.where(Work.state_id == scope["state_id"])
    if "district" in scope:
        query = query.where(Work.district == scope["district"])
    if "mp_id" in scope:
        query = query.where(Work.mp_id == scope["mp_id"])
    return db.scalar(query) or 0


def build(db: Session) -> dict[str, User]:
    """Create the four accounts on this session's database and return them by role.

    Committed here rather than left pending, because the tests log in over HTTP
    through a different session on the same file.
    """
    state_a = state_id(db, STATE_A)
    accounts = {
        ROLE_MINISTRY: User(
            email=ROLE_MINISTRY_EMAIL,
            password_hash=hash_password(PASSWORD),
            role=ROLE_MINISTRY,
            display_name="Ministry Test Analyst",
            is_active=True,
            created_at=datetime.combine(DATA_AS_OF, datetime.min.time()),
        ),
        ROLE_STATE_NODAL: User(
            email=ROLE_STATE_EMAIL,
            password_hash=hash_password(PASSWORD),
            role=ROLE_STATE_NODAL,
            display_name="Uttar Pradesh Test Nodal Officer",
            is_active=True,
            created_at=datetime.combine(DATA_AS_OF, datetime.min.time()),
            scope_state_id=state_a,
        ),
        ROLE_DISTRICT_AUTHORITY: User(
            email=ROLE_DISTRICT_EMAIL,
            password_hash=hash_password(PASSWORD),
            role=ROLE_DISTRICT_AUTHORITY,
            display_name="Jalaun Test District Authority",
            is_active=True,
            created_at=datetime.combine(DATA_AS_OF, datetime.min.time()),
            scope_state_id=state_a,
            scope_district=DISTRICT_A,
        ),
        ROLE_MEMBER_OF_PARLIAMENT: User(
            email=MEMBER_A_EMAIL,
            password_hash=hash_password(PASSWORD),
            role=ROLE_MEMBER_OF_PARLIAMENT,
            display_name=f"Office of {MP_A_NAME} (test)",
            is_active=True,
            created_at=datetime.combine(DATA_AS_OF, datetime.min.time()),
            scope_mp_id=mp_id(db, MP_A_NAME),
        ),
    }
    # A second member, so "another MP's case" is a real member's real case
    # rather than a hypothetical id.
    accounts["member_b"] = User(
        email=MEMBER_B_EMAIL,
        password_hash=hash_password(PASSWORD),
        role=ROLE_MEMBER_OF_PARLIAMENT,
        display_name=f"Office of {MP_B_NAME} (test)",
        is_active=True,
        created_at=datetime.combine(DATA_AS_OF, datetime.min.time()),
        scope_mp_id=mp_id(db, MP_B_NAME),
    )
    # A deactivated Ministry account. Login must refuse it, and a token minted
    # before deactivation must stop working - both are tested, and neither is
    # testable without a row that is switched off.
    accounts["inactive"] = User(
        email=INACTIVE_EMAIL,
        password_hash=hash_password(PASSWORD),
        role=ROLE_MINISTRY,
        display_name="Revoked Test Analyst",
        is_active=False,
        created_at=datetime.combine(DATA_AS_OF, datetime.min.time()),
    )

    db.add_all(accounts.values())
    db.commit()
    for user in accounts.values():
        db.refresh(user)
    return accounts


def assert_populated(db: Session, accounts: dict[str, User]) -> None:
    """Every scope under test covers real cases, or these tests prove nothing.

    A filter that returns zero rows because the scope is empty looks identical
    to a filter that returns zero rows because it works. This is what keeps the
    two apart.
    """
    for role, user in accounts.items():
        if user.role == ROLE_MINISTRY:
            continue
        scope = {}
        if user.scope_mp_id is not None:
            scope["mp_id"] = user.scope_mp_id
        if user.scope_district is not None:
            scope["district"] = user.scope_district
        if user.scope_state_id is not None and not scope.get("mp_id"):
            scope["state_id"] = user.scope_state_id
        count = case_count(db, **scope)
        assert count > 0, (
            f"the {role} test account is bound to a scope with no cases ({scope}); "
            "a scoping test over an empty scope passes by accident"
        )


def token_for(client, email: str, password: str = PASSWORD) -> str:
    """Sign in over HTTP and return the bearer token. Fails loudly, never silently."""
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, f"login for {email} -> {response.text[:300]}"
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
