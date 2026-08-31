"""The role predicate, in one place, applied to selects rather than to results.

CLAUDE.md invariant 10: *role scoping is enforced server-side, in the query.
Never by hiding rows in the UI. A District Authority token must not be able to
fetch another district's cases by editing a URL.*

`docs/api/ROLE-SCOPING-PLAN.md` is the endpoint-by-endpoint commitment Phase 5
made and this module keeps. `docs/domain/DOMAIN-MODEL.md` (k) is the authority
for what each role may see.

**Everything here returns a `Select` or raises.** Nothing filters a list after
`.all()`. A list comprehension over fetched rows would be scoping in the
application, and the row would already have left the database - which is the
failure invariant 10 names, not a stylistic preference. The whole module is
`.where(...)` calls and role checks, and it is short on purpose: a scoping rule
that is hard to read is a scoping rule nobody audits.

**Two status codes, and which one applies is a question about secrecy.**

* An out-of-scope **row id** - a case, a work - returns **404**. A 403 would
  confirm that another district's case id is real, which is a scoping leak
  spelled with a status code. The caller learns exactly what they would learn
  about an id that does not exist.
* An out-of-scope **grain** - `/analytics/state/{state}`, `/analytics/mp/{id}` -
  returns **403**. State names and member ids are published by MoSPI; there is
  nothing to conceal about their existence, and a 404 would tell an officer
  their own state has no data rather than that they asked the wrong question.

**The scopes**, with `S` the user's state, `D` their district, `M` their member:

| Role | Predicate on `works` | May write |
| --- | --- | --- |
| `ministry` | none | yes |
| `state_nodal` | `state_id == S` | yes |
| `district_authority` | `state_id == S AND district == D` | yes |
| `member_of_parliament` | `mp_id == M` | **no** |

The district predicate carries the state and the corpus is why: `AGRA`,
`KAITHAL`, `PILIBHIT` and `SHAHJAHANPUR` each name a district in five different
states in `works`. `district == D` alone would hand a Uttar Pradesh officer the
Madhya Pradesh district of the same name (see `models.User`).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import Select, select

from ..constants import (
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MEMBER_OF_PARLIAMENT,
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
)
from ..models import Case, User, Work

OUT_OF_GRAIN = (
    "Your role does not reach this view. See docs/domain/DOMAIN-MODEL.md (k) for the "
    "scoping matrix."
)


def work_predicate(user: User) -> list:
    """The `WHERE` terms this user's role adds to any query over `works`.

    Empty for the Ministry, which is the widest scope and therefore no
    predicate at all rather than a predicate that happens to match everything.

    Returns terms rather than applying them so that both the case select and
    the bare work select can use the same rule without one of them being
    written twice.
    """
    if user.role == ROLE_MINISTRY:
        return []
    if user.role == ROLE_STATE_NODAL:
        return [Work.state_id == user.scope_state_id]
    if user.role == ROLE_DISTRICT_AUTHORITY:
        # Both terms, always. See the module docstring: district names repeat
        # across states in this corpus.
        return [Work.state_id == user.scope_state_id, Work.district == user.scope_district]
    if user.role == ROLE_MEMBER_OF_PARLIAMENT:
        return [Work.mp_id == user.scope_mp_id]
    # Unreachable through the API - `users.role` carries a CHECK constraint
    # naming the four - and deliberately not a permissive default. A fifth role
    # arriving through a hand-edited row sees nothing rather than everything.
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=OUT_OF_GRAIN)


def scope_works(query: Select, user: User) -> Select:
    """Add the role predicate to a select that already joins `works`."""
    for term in work_predicate(user):
        query = query.where(term)
    return query


def scoped_cases(user: User) -> Select:
    """The base select every case query in the API starts from.

    Cases joined to their work, narrowed to what this role may reach. Endpoints
    add their own filters AFTER this, so a query parameter can only narrow the
    scope further and never widen it.
    """
    return scope_works(select(Case, Work).join(Work, Work.id == Case.work_id), user)


# ---------------------------------------------------------------------------
# Grain checks - which aggregate views a role may ask for at all
# ---------------------------------------------------------------------------


def _refuse(detail: str):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def check_state_grain(user: User, state: str, state_of: dict) -> None:
    """May this user read the district breakdown of `state`?

    Ministry: any. State Nodal: their own. District Authority and Member: not
    at all - neither works at this grain, and both have a narrower view that
    answers their own question (ROLE-SCOPING-PLAN.md).

    `state_of` maps state name to id, supplied by the caller because the
    router already has to resolve the name to answer at all.
    """
    if user.role == ROLE_MINISTRY:
        return
    if user.role == ROLE_STATE_NODAL:
        if state_of.get(state) != user.scope_state_id:
            _refuse(
                f"Your scope is one state and it is not {state!r}. "
                "A state nodal officer reads their own state only."
            )
        return
    _refuse(
        f"{OUT_OF_GRAIN} The state view is for the ministry and the state nodal authority; "
        f"your role is {user.role}."
    )


def check_district_grain(user: User, district: str, state_of_district: str | None,
                         state_id_of_district: int | None) -> None:
    """May this user read `district`'s queue?

    Ministry: any. State Nodal: districts inside their state - which is why the
    district's own state is resolved and compared, rather than the name being
    trusted to be unique. District Authority: their own district, in their own
    state. Member: not at all; their works reach them through their own list.
    """
    if user.role == ROLE_MINISTRY:
        return
    if user.role == ROLE_STATE_NODAL:
        if state_id_of_district != user.scope_state_id:
            _refuse(
                f"{district!r} is not a district of your state"
                + (f" - it is in {state_of_district}." if state_of_district else ".")
            )
        return
    if user.role == ROLE_DISTRICT_AUTHORITY:
        if district != user.scope_district or state_id_of_district != user.scope_state_id:
            _refuse(
                f"Your scope is {user.scope_district!r} and it is not {district!r}. "
                "A district authority reads their own district only."
            )
        return
    _refuse(
        f"{OUT_OF_GRAIN} The district view is for the ministry, the state nodal authority "
        f"and the district authority; your role is {user.role}."
    )


def check_mp_grain(user: User, mp_id: int, mp_state_id: int | None) -> None:
    """May this user read member `mp_id`'s account and portfolio?

    Ministry: any. State Nodal: members seated in their state, matching
    `fund_accounts` in DOMAIN-MODEL.md (k). Member: their own row only.

    **District Authority: never, for any member, including their own district's.**
    That is a deliberate row of the matrix rather than an omission: a district
    officer has no business seeing a member's aggregate account position, it is
    not evidence about any work in their district, and the one derived value
    they do need - `mp_utilisation_pct` - reaches them through the case trace
    where it is already scoped to that case's member.
    """
    if user.role == ROLE_MINISTRY:
        return
    if user.role == ROLE_STATE_NODAL:
        if mp_state_id != user.scope_state_id:
            _refuse("That member is not seated in your state.")
        return
    if user.role == ROLE_MEMBER_OF_PARLIAMENT:
        if mp_id != user.scope_mp_id:
            _refuse(
                "Your scope is one member's own record. A member reads their own account "
                "and their own works, and no other member's."
            )
        return
    _refuse(
        "A district authority does not read a member's account position: it is not evidence "
        "about any work in the district, and the one derived value the district needs, "
        "mp_utilisation_pct, travels with each case's own trace (DOMAIN-MODEL.md (k))."
    )
