"""Authentication: who a token belongs to, and what refusing one looks like.

This file is about IDENTITY. `tests/test_role_scoping.py` is about which rows
an identity reaches, and the split is deliberate: a bug that lets a bad password
through and a bug that hands a district officer another district's rows are
different failures and should fail different tests.

Runs against the shared copied corpus and the seeded accounts in
`tests/accounts.py`, which pins every scope to a populated part of the real
data - see that module for why an empty scope would make these tests vacuous.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.auth import DEV_SECRET, hash_password, issue_token, secret_key, verify_password
from app.constants import (
    JWT_ALGORITHM,
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MEMBER_OF_PARLIAMENT,
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
    TOKEN_TTL_HOURS,
)

from .accounts import (
    ABSENT_EMAIL,
    DISTRICT_A,
    INACTIVE_EMAIL,
    MEMBER_A_EMAIL,
    MP_A_NAME,
    PASSWORD,
    ROLE_DISTRICT_EMAIL,
    ROLE_MINISTRY_EMAIL,
    ROLE_STATE_EMAIL,
    STATE_A,
    WRONG_PASSWORD,
    headers,
    token_for,
)

pytestmark = pytest.mark.corpus


def login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ---------------------------------------------------------------------------
# Hashing - the part that has nothing to do with HTTP
# ---------------------------------------------------------------------------


def test_a_password_is_stored_as_a_bcrypt_digest_and_never_as_itself():
    """The digest must not be the password, must not be reversible, must verify."""
    digest = hash_password(PASSWORD)
    assert digest != PASSWORD
    assert PASSWORD not in digest
    assert digest.startswith("$2"), "a bcrypt digest, not some other encoding"
    assert verify_password(PASSWORD, digest)
    assert not verify_password(WRONG_PASSWORD, digest)


def test_two_hashes_of_one_password_differ_and_both_verify():
    """bcrypt salts. Identical stored digests would leak that two officers share a password."""
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert first != second
    assert verify_password(PASSWORD, first) and verify_password(PASSWORD, second)


def test_an_unparseable_stored_digest_is_a_refusal_and_not_a_crash():
    """A hand-edited `password_hash` must not 500 the login endpoint."""
    assert verify_password(PASSWORD, "this was never a bcrypt digest") is False


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------


def test_login_succeeds_with_the_right_credentials_and_returns_the_identity(client):
    """One round trip: the token, when it expires, and who it is for."""
    response = login(client, ROLE_MINISTRY_EMAIL)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in_hours"] == TOKEN_TTL_HOURS
    assert body["user"]["email"] == ROLE_MINISTRY_EMAIL
    assert body["user"]["role"] == ROLE_MINISTRY
    assert body["user"]["can_write"] is True
    # No password, no digest, and nothing else from the row that is not identity.
    assert "password" not in response.text and "password_hash" not in response.text


def test_login_fails_on_a_wrong_password(client):
    assert login(client, ROLE_MINISTRY_EMAIL, WRONG_PASSWORD).status_code == 401


def test_login_fails_for_an_address_that_holds_no_account(client):
    assert login(client, ABSENT_EMAIL).status_code == 401


def test_login_fails_for_a_deactivated_account(client):
    """A revoked officer is refused. The row survives, because the trail points at it."""
    assert login(client, INACTIVE_EMAIL).status_code == 401


def test_the_three_failures_are_indistinguishable(client):
    """Wrong password, unknown address and revoked account give one answer.

    Three distinguishable messages would turn the login form into a way of
    asking which officers hold accounts (`app/auth.py`).
    """
    answers = {
        login(client, ROLE_MINISTRY_EMAIL, WRONG_PASSWORD).json()["detail"],
        login(client, ABSENT_EMAIL).json()["detail"],
        login(client, INACTIVE_EMAIL).json()["detail"],
    }
    assert len(answers) == 1, f"the failures are distinguishable: {answers}"


def test_the_login_address_is_not_case_sensitive(client):
    """`Ministry@Test.NIGRANI` is the same officer as `ministry@test.nigrani`."""
    assert login(client, ROLE_MINISTRY_EMAIL.upper()).status_code == 200


def test_an_empty_password_is_rejected_by_the_shape_before_it_reaches_bcrypt(client):
    """422, not 401: the request never became a credential attempt."""
    assert client.post(
        "/api/auth/login", json={"email": ROLE_MINISTRY_EMAIL, "password": ""}
    ).status_code == 422


# ---------------------------------------------------------------------------
# The token itself
# ---------------------------------------------------------------------------


def test_a_valid_token_admits_its_holder(client):
    token = token_for(client, ROLE_STATE_EMAIL)
    response = client.get("/api/auth/me", headers=headers(token))
    assert response.status_code == 200
    assert response.json()["email"] == ROLE_STATE_EMAIL


def test_a_request_with_no_token_is_401(anon_client):
    response = anon_client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_a_malformed_token_is_401_and_not_a_500(client):
    for bad in ("not-a-jwt", "a.b.c", ""):
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {bad}"})
        assert response.status_code == 401, f"{bad!r} -> {response.status_code}"


def test_a_token_signed_with_another_key_is_401(client):
    """The signature is checked, not just the shape."""
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "a key this server does not hold",
        algorithm=JWT_ALGORITHM,
    )
    assert client.get("/api/auth/me", headers=headers(forged)).status_code == 401


def test_an_expired_token_is_401(client, api_accounts):
    """Minted in the past, refused now. The expiry is enforced, not decorative."""
    expired = jwt.encode(
        {
            "sub": str(api_accounts[ROLE_MINISTRY].id),
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        secret_key(),
        algorithm=JWT_ALGORITHM,
    )
    assert client.get("/api/auth/me", headers=headers(expired)).status_code == 401


def test_a_well_formed_token_for_a_user_that_does_not_exist_is_401(client):
    """A valid signature over a nonexistent subject is still nobody."""
    orphan = jwt.encode(
        {"sub": "99999999", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        secret_key(),
        algorithm=JWT_ALGORITHM,
    )
    assert client.get("/api/auth/me", headers=headers(orphan)).status_code == 401


def test_a_token_for_a_deactivated_account_stops_working(client, api_accounts):
    """The row decides, not the token.

    A token minted while the account was live must stop being accepted the
    moment the account is switched off - which is only true because
    `get_current_user` loads the row rather than trusting the claims
    (`app/auth.py`). It is also the only revocation this prototype has, and
    that limitation is declared in that module rather than implied away here.
    """
    from types import SimpleNamespace

    inactive = api_accounts["inactive"]
    token, _ = issue_token(SimpleNamespace(id=inactive.id, role=inactive.role, email=inactive.email))
    assert client.get("/api/auth/me", headers=headers(token)).status_code == 401


def test_the_expiry_the_response_prints_is_the_expiry_in_the_token(client):
    """Two places computing "now plus twelve hours" is two places that can disagree."""
    body = login(client, ROLE_MINISTRY_EMAIL).json()
    claimed = jwt.decode(body["access_token"], secret_key(), algorithms=[JWT_ALGORITHM])["exp"]
    printed = datetime.fromisoformat(body["expires_at"])
    assert abs(claimed - printed.timestamp()) < 1
    hours = (printed - datetime.now(timezone.utc)).total_seconds() / 3600
    assert TOKEN_TTL_HOURS - 0.1 < hours <= TOKEN_TTL_HOURS


def test_the_development_signing_key_announces_itself(monkeypatch):
    """The committed fallback must not read as a secret to whoever finds it.

    A random-looking constant in a repository invites the belief that it is
    safe. This one says what it is in its own value, and the environment
    variable overrides it.
    """
    monkeypatch.delenv("NIGRANI_JWT_SECRET", raising=False)
    assert secret_key() == DEV_SECRET
    assert "not-a-secret" in DEV_SECRET
    monkeypatch.setenv("NIGRANI_JWT_SECRET", "an-operator-supplied-key")
    assert secret_key() == "an-operator-supplied-key"


# ---------------------------------------------------------------------------
# GET /api/auth/me - the role and the scope, resolved to names
# ---------------------------------------------------------------------------


def test_me_reports_the_ministry_scope_as_unrestricted(client):
    body = client.get("/api/auth/me", headers=headers(token_for(client, ROLE_MINISTRY_EMAIL))).json()
    assert body["role"] == ROLE_MINISTRY
    assert body["can_write"] is True
    assert body["scope"] == {
        "state": None,
        "state_id": None,
        "district": None,
        "mp_id": None,
        "mp_name": None,
        "describes": "every work in the committed sample, unrestricted",
    }


def test_me_reports_a_state_nodal_scope_as_one_named_state(client, api_accounts):
    body = client.get("/api/auth/me", headers=headers(token_for(client, ROLE_STATE_EMAIL))).json()
    assert body["role"] == ROLE_STATE_NODAL
    assert body["can_write"] is True
    assert body["scope"]["state"] == STATE_A
    assert body["scope"]["state_id"] == api_accounts[ROLE_STATE_NODAL].scope_state_id
    assert body["scope"]["district"] is None and body["scope"]["mp_id"] is None
    assert body["scope"]["describes"] == f"the works in {STATE_A}"


def test_me_reports_a_district_scope_as_a_district_inside_its_state(client):
    """A district name alone would be ambiguous - see the `User` model docstring."""
    body = client.get("/api/auth/me", headers=headers(token_for(client, ROLE_DISTRICT_EMAIL))).json()
    assert body["role"] == ROLE_DISTRICT_AUTHORITY
    assert body["scope"]["district"] == DISTRICT_A
    assert body["scope"]["state"] == STATE_A, "the state travels with the district"
    assert body["scope"]["describes"] == f"the works in {DISTRICT_A}, {STATE_A}"


def test_me_reports_a_member_scope_as_one_named_member_and_read_only(client, api_accounts):
    body = client.get("/api/auth/me", headers=headers(token_for(client, MEMBER_A_EMAIL))).json()
    assert body["role"] == ROLE_MEMBER_OF_PARLIAMENT
    assert body["scope"]["mp_id"] == api_accounts[ROLE_MEMBER_OF_PARLIAMENT].scope_mp_id
    assert body["scope"]["mp_name"] == MP_A_NAME
    assert body["scope"]["state"] is None and body["scope"]["district"] is None
    # DOMAIN-MODEL.md (k): the scheme's subject does not adjudicate the
    # scheme's findings. The server refuses the write regardless; this key is
    # what lets a screen not offer a button that would be refused.
    assert body["can_write"] is False


def test_every_role_returns_the_same_scope_key_set(client):
    """One shape for four roles, so a screen renders one component."""
    shapes = [
        set(
            client.get("/api/auth/me", headers=headers(token_for(client, email))).json()["scope"]
        )
        for email in (ROLE_MINISTRY_EMAIL, ROLE_STATE_EMAIL, ROLE_DISTRICT_EMAIL, MEMBER_A_EMAIL)
    ]
    assert all(shape == shapes[0] for shape in shapes)
    assert shapes[0] == {"state", "state_id", "district", "mp_id", "mp_name", "describes"}


def test_me_reads_the_row_rather_than_the_token_claims(client, api_accounts):
    """A token carrying a lie about its own role does not get that role.

    The claims carry `role` for a human reading a decoded token in a console.
    Nothing on the server reads it back - if it did, minting a token with
    `role: ministry` would be an escalation anyone holding the signing key
    could perform, and the key has a committed development fallback.
    """
    member = api_accounts[ROLE_MEMBER_OF_PARLIAMENT]
    lying = jwt.encode(
        {
            "sub": str(member.id),
            "role": ROLE_MINISTRY,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        secret_key(),
        algorithm=JWT_ALGORITHM,
    )
    body = client.get("/api/auth/me", headers=headers(lying)).json()
    assert body["role"] == ROLE_MEMBER_OF_PARLIAMENT
    assert body["can_write"] is False


def test_there_is_no_registration_endpoint(client):
    """Accounts are provisioned by `python -m app.seed_users`, not by their holders.

    A declared limitation rather than an oversight: an officer's district is
    granted to them, not chosen by them (`routers/auth.py`).
    """
    for path in ("/api/auth/register", "/api/auth/signup", "/api/auth/users"):
        assert client.post(path, json={}).status_code == 404, path
