"""Password hashing, JWT issuance, and the dependencies every scoped route uses.

Three things live here and nothing else: how a password becomes a stored
digest, how an authenticated identity becomes a token and back, and how a route
asks for the caller. The rows a role may READ are decided in
`routers/scoping.py`, because that is a question about queries rather than
about identity, and keeping the two apart is what lets the scoping tests read
as statements about data.

**What this is, said plainly.** NIGRANI's login is a demo over seeded accounts,
not an identity provider (PROJECT-BRIEF.md, "Honest scoping"). The hashing is
real bcrypt and the server-side scoping in `routers/scoping.py` is real - a
token genuinely cannot reach another district's rows. What is NOT here, and is
not claimed anywhere: no refresh flow, no revocation list, no session store, no
rate limiting on failed logins, no password reset, no MFA, no self-service
registration. A token is valid until it expires and there is no way to end it
early. That is a scoping decision for a hackathon prototype and it is declared
rather than hidden.

**Token contents.** `sub` is the user's numeric id and nothing else identifying.
The role and the scope are NOT read from the token when a request is served:
`get_current_user` loads the row and reads them from the database, so
deactivating an account or correcting a scope takes effect on the next request
rather than at the next expiry. The token proves who; the row decides what.

**Why the errors are shaped the way they are.** A failed login says
"Incorrect email or password" for a wrong password, an unknown address and a
deactivated account alike. Three distinguishable messages would let anyone with
the login form enumerate which officers hold accounts.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from .constants import JWT_ALGORITHM, JWT_SECRET_ENV, ROLES, TOKEN_TTL_HOURS, WRITE_ROLES
from .db import get_db
from .models import User

# The signing secret, from the environment.
#
# THE FALLBACK IS A DEVELOPMENT VALUE AND IT IS IN THE REPOSITORY. Anyone
# holding this file can mint a Ministry token against a server that did not set
# NIGRANI_JWT_SECRET. That is stated here rather than disguised behind a
# generated-looking string, because a secret that looks random and is committed
# is worse than one that announces itself: the first invites the belief that it
# is safe. A deployment sets the variable. The demo does not have to, and the
# demo is what this is.
DEV_SECRET = "nigrani-development-signing-key-not-a-secret"

# bcrypt, via passlib. `deprecated="auto"` means a digest written under an older
# scheme is still verifiable and is re-hashed on next use if the scheme list
# ever grows; today there is one scheme and the setting costs nothing.
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# `auto_error=False` so a missing header reaches `get_current_user` as `None`
# and this module raises the 401 with its own message. FastAPI's default is a
# bare "Not authenticated", and an officer reading a browser console deserves
# to be told which header the server wanted.
_bearer = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

CREDENTIALS_REJECTED = "Incorrect email or password"
NOT_AUTHENTICATED = "Not authenticated. Send `Authorization: Bearer <token>` from /api/auth/login."
TOKEN_REJECTED = "Token is invalid or has expired. Sign in again at /api/auth/login."
ACCOUNT_GONE = "The account this token was issued for no longer exists or is inactive."


def secret_key() -> str:
    """The signing secret, read per call so a test can set the variable."""
    return os.environ.get(JWT_SECRET_ENV) or DEV_SECRET


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------


def hash_password(plaintext: str) -> str:
    """A bcrypt digest. The only way a password enters `users.password_hash`."""
    return _pwd.hash(plaintext)


def verify_password(plaintext: str, password_hash: str) -> bool:
    """Constant-time comparison, delegated to passlib rather than written here."""
    try:
        return _pwd.verify(plaintext, password_hash)
    except ValueError:
        # A stored digest bcrypt cannot parse - a hand-edited row, or a column
        # carrying something that was never a hash. It is not a match, and it
        # is not a 500 either.
        return False


# Hashed once at import, against a password nothing knows, purely so
# `authenticate` spends the same bcrypt time on an unknown address as on a
# known one.
_ABSENT_USER_DIGEST = hash_password("no user holds this password")


def authenticate(db: Session, email: str, password: str) -> User | None:
    """The user behind these credentials, or None. One answer for every failure.

    Unknown address, wrong password and deactivated account are one return
    value on purpose - see the module docstring. The password is verified even
    when the address is unknown, against a throwaway digest, so the response
    time does not tell a caller which addresses hold accounts.
    """
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        verify_password(password, _ABSENT_USER_DIGEST)
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


def issue_token(user: User, ttl_hours: int = TOKEN_TTL_HOURS) -> tuple[str, datetime]:
    """A signed access token for this user, and the moment it stops working.

    The expiry is returned rather than left for the caller to recompute: the
    login response prints it, and two places computing "now plus twelve hours"
    is two places that can disagree by a second.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    claims = {
        "sub": str(user.id),
        # Carried for a human reading a decoded token in a console, never read
        # back by this server: `get_current_user` reads the row instead, so a
        # scope correction takes effect on the next request (module docstring).
        "role": user.role,
        "email": user.email,
        "exp": expires_at,
    }
    return jwt.encode(claims, secret_key(), algorithm=JWT_ALGORITHM), expires_at


def decode_token(token: str) -> dict:
    """The claims, or a 401. Signature and expiry are both checked by `jose`."""
    try:
        return jwt.decode(token, secret_key(), algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=TOKEN_REJECTED,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user(token: str | None = Depends(_bearer), db: Session = Depends(get_db)) -> User:
    """The authenticated caller, loaded from the database. 401 otherwise.

    Every scoped endpoint depends on this, and it is the only door. An endpoint
    that forgot it would be open, which is why `tests/test_role_scoping.py`
    walks the route table of the running application and asserts that every
    route under `/api` carries it, rather than listing the endpoints by hand.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=NOT_AUTHENTICATED,
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = decode_token(token)
    subject = claims.get("sub")
    user = db.get(User, int(subject)) if isinstance(subject, str) and subject.isdigit() else None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ACCOUNT_GONE,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*allowed: str):
    """A dependency admitting only these roles. Identity, not data.

    This is the coarse gate: `GET /api/ablation/report` is Ministry-only
    whatever rows it would return. It is deliberately NOT how a case list is
    scoped - that is a question about which rows, answered in
    `routers/scoping.py` by a WHERE clause. Using a role gate where a predicate
    belongs is how an endpoint ends up returning every district's rows to
    whoever is allowed through the door.

    403, not 404: the endpoint's existence is not a secret, and the caller is
    authenticated, so there is nothing to conceal by pretending it is absent.
    An out-of-scope case id is the opposite case and returns 404 - see
    `routers/scoping.py`.
    """
    unknown = set(allowed) - set(ROLES)
    assert not unknown, f"require_role names roles that do not exist: {sorted(unknown)}"

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This endpoint is restricted to {', '.join(sorted(allowed))}. "
                    f"Your role is {user.role}."
                ),
            )
        return user

    return dependency


def require_write(user: User = Depends(get_current_user)) -> User:
    """A caller allowed to write. The member of parliament never is.

    DOMAIN-MODEL.md (k): "An MP can see, and cannot annotate, escalate, resolve
    or recompute. The scheme's subject does not adjudicate the scheme's
    findings." A dependency of its own rather than `require_role(*WRITE_ROLES)`
    spelled at each call site, so the rule is stated once and the reason travels
    with it.
    """
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "The member of parliament role is read-only. The scheme's subject does not "
                "adjudicate the scheme's findings (DOMAIN-MODEL.md (k))."
            ),
        )
    return user
