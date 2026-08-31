"""Sign in, and read back who you are and what you can reach.

Two endpoints, and the second one exists because of the first. A token proves
identity; it does not, on its own, tell a screen which of the four persona
dashboards to render or which state name to put in the heading. `/me` answers
that from the row rather than from the token, so an account whose scope was
corrected reports the corrected scope on the next request.

**There is no registration endpoint and there is not going to be one.**
Accounts are created by `python -m app.seed_users`, which is how a government
deployment provisions access: an officer's district is granted to them, not
chosen by them. It is a declared limitation rather than an oversight - this
prototype has no password reset, no account recovery and no way for anyone but
the operator running that script to add a user, and PROJECT-BRIEF.md already
says the login is a demo over seeded accounts rather than an identity provider.

**`/login` does not say why it refused.** A wrong password, an unknown address
and a deactivated account all return the same 401 with the same sentence. Three
distinguishable answers would turn the login form into a way of asking which
officers hold accounts (`app/auth.py`).

Neither endpoint is scoped, which is not an exception to CLAUDE.md invariant 10:
`/login` runs before there is a caller to scope, and `/me` returns exactly one
row - the caller's own - which is the narrowest scope there is.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CREDENTIALS_REJECTED, authenticate, get_current_user, issue_token
from ..constants import TOKEN_TTL_HOURS, WRITE_ROLES
from ..db import get_db
from ..models import MP, State, User
from ..schemas import LoginIn, MeOut, ScopeOut, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


def scope_of(db: Session, user: User) -> ScopeOut:
    """This account's scope, with the ids resolved to the names a screen prints.

    Two lookups at most, and only for the roles that carry them. The Ministry
    role does none, because "everything" needs no join to describe.
    """
    state_name = (
        db.scalar(select(State.name).where(State.id == user.scope_state_id))
        if user.scope_state_id is not None
        else None
    )
    mp_name = (
        db.scalar(select(MP.name_canon).where(MP.id == user.scope_mp_id))
        if user.scope_mp_id is not None
        else None
    )

    if user.scope_mp_id is not None:
        describes = f"the works recommended by {mp_name or f'MP {user.scope_mp_id}'}"
    elif user.scope_district is not None:
        describes = f"the works in {user.scope_district}, {state_name}"
    elif user.scope_state_id is not None:
        describes = f"the works in {state_name}"
    else:
        describes = "every work in the committed sample, unrestricted"

    return ScopeOut(
        state=state_name,
        state_id=user.scope_state_id,
        district=user.scope_district,
        mp_id=user.scope_mp_id,
        mp_name=mp_name,
        describes=describes,
    )


def identity(db: Session, user: User) -> MeOut:
    """One user row as the identity block both endpoints return."""
    return MeOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        can_write=user.role in WRITE_ROLES,
        scope=scope_of(db, user),
    )


@router.post("/login", response_model=TokenOut)
def login(credentials: LoginIn, db: Session = Depends(get_db)):
    """Email and password for a signed token, or one 401 for every failure.

    The identity block comes back with the token so the screen that follows a
    login has the role and the scope in hand without a second request.
    """
    user = authenticate(db, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=CREDENTIALS_REJECTED,
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_at = issue_token(user)
    return TokenOut(
        access_token=token,
        expires_at=expires_at,
        expires_in_hours=TOKEN_TTL_HOURS,
        user=identity(db, user),
    )


@router.get("/me", response_model=MeOut)
def me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The caller, their role, and the rows their role reaches.

    Read from the `users` row rather than from the token's claims. A token
    minted twelve hours ago carries the role its holder had then; this endpoint
    reports the role they have now, which is the one every query will be scoped
    by.
    """
    return identity(db, user)
