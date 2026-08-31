"""Provision the four demo accounts, one per role.

    cd backend && python -m app.seed_users

**Where this sits in the build sequence: last.**

    python -m ingest.run        drops and recreates every table
    python -m app.ml.run        }
    python -m app.ablation.run  } any order
    python -m app.derive_all    }
    python -m app.seed_users    <- here

After `derive_all`, because the scopes are chosen from the DERIVED corpus and
not from a list written down here. A `state_nodal` account bound to a state
with no cases, or a member bound to one with no works, would give the
walkthrough a login that opens onto an empty screen - and an empty screen is
indistinguishable from a broken one. So the state, the district and the member
below are picked by counting cases, and the script refuses to write an account
whose scope has none.

After `ingest.run` for the harder reason: `ingest.run` calls `drop_all`, and
`users` is one of the tables it drops. Accounts do not survive a re-ingest and
are not meant to; this script is re-run, and it is idempotent - an existing
address is updated in place with a fresh password rather than duplicated.

**Passwords are generated here and printed once.** Nothing in this repository
stores a password that unlocks a running NIGRANI, and nothing writes one to a
file. Hand the printed block to whoever is driving the demo; if it is lost, run
this again and every password is replaced.

**This is a demo provisioning script, and the honest description of it is that
it stands in for an identity provider.** PROJECT-BRIEF.md says the role
switcher is a dropdown over seeded accounts. This is where those accounts come
from. It is also the only way to create one: there is no registration endpoint,
because an officer's district is granted to them rather than chosen by them.
"""

from __future__ import annotations

import secrets
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .constants import (
    DATA_AS_OF,
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MEMBER_OF_PARLIAMENT,
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
)
from .auth import hash_password
from .db import SessionLocal, engine
from .models import MP, Case, State, User, Work

# The demo domain. Not a real one, and it is not meant to look like one: these
# addresses are logins for a prototype, and an address at a live government
# domain would be a credential that appeared to belong to somebody.
DOMAIN = "demo.nigrani.local"

# Long enough that the demo is not trivially guessable by anyone watching the
# screen, short enough to be typed at a podium. Generated per run.
PASSWORD_BYTES = 9


def _password() -> str:
    return secrets.token_urlsafe(PASSWORD_BYTES)


def _scored(db: Session):
    """The base count query: real cases only, joined to their work.

    The labelled synthetic control is excluded (invariant 12) so a scope cannot
    be chosen on the strength of an injected row.
    """
    return (
        select(func.count())
        .select_from(Case)
        .join(Work, Work.id == Case.work_id)
        .where(Case.is_synthetic.is_(False))
    )


def busiest_state(db: Session):
    """The state with the most real cases, and its id. HIGH count breaks a tie."""
    return db.execute(
        select(State.id, State.name, func.count().label("cases"))
        .select_from(Case)
        .join(Work, Work.id == Case.work_id)
        .join(State, State.id == Work.state_id)
        .where(Case.is_synthetic.is_(False))
        .group_by(State.id)
        .order_by(func.count().desc(), State.name)
        .limit(1)
    ).first()


def busiest_district(db: Session, state_id: int):
    """The district of `state_id` carrying the most HIGH cases.

    HIGH first rather than volume first: the district screen is a triage queue,
    and a queue with nothing in the top band demonstrates the product less well
    than a smaller one that has something to work on.
    """
    return db.execute(
        select(
            Work.district,
            func.count().label("cases"),
            func.sum(func.iif(Case.severity == "HIGH", 1, 0)).label("high"),
        )
        .select_from(Case)
        .join(Work, Work.id == Case.work_id)
        .where(
            Case.is_synthetic.is_(False),
            Work.state_id == state_id,
            Work.district.is_not(None),
        )
        .group_by(Work.district)
        .order_by(func.sum(func.iif(Case.severity == "HIGH", 1, 0)).desc(), func.count().desc())
        .limit(1)
    ).first()


def busiest_member(db: Session, district: str, state_id: int):
    """A member recommending into that district, ranked by HIGH cases.

    Chosen inside the district on purpose: the walkthrough then shows the same
    works from three angles - the ministry's national ranking, the district
    officer's queue, and the member's own portfolio - which is what makes the
    scoping visible rather than merely asserted.

    The counts returned are the counts INSIDE that district, and they are the
    ranking criterion and nothing else. What the account will actually reach is
    every case of that member's, in every district and every state, which is a
    larger number - `member_totals` measures it, and the printed report states
    that one, because a credentials block that understated a scope would be
    telling the demo operator something false about what they are handing over.
    """
    return db.execute(
        select(
            MP.id,
            MP.name_canon,
            func.count().label("cases"),
            func.sum(func.iif(Case.severity == "HIGH", 1, 0)).label("high"),
        )
        .select_from(Case)
        .join(Work, Work.id == Case.work_id)
        .join(MP, MP.id == Work.mp_id)
        .where(
            Case.is_synthetic.is_(False),
            Work.state_id == state_id,
            Work.district == district,
            MP.is_synthetic.is_(False),
        )
        .group_by(MP.id)
        .order_by(func.sum(func.iif(Case.severity == "HIGH", 1, 0)).desc(), func.count().desc())
        .limit(1)
    ).first()


def member_totals(db: Session, mp_id: int):
    """Every case belonging to this member, which is what their token reaches.

    Their works are not confined to the district they were selected from: a
    member recommends across their whole constituency or state, and the scope
    is `works.mp_id == M` with no geography in it at all.
    """
    return db.execute(
        select(
            func.count().label("cases"),
            func.sum(func.iif(Case.severity == "HIGH", 1, 0)).label("high"),
            func.count(func.distinct(Work.district)).label("districts"),
        )
        .select_from(Case)
        .join(Work, Work.id == Case.work_id)
        .where(Case.is_synthetic.is_(False), Work.mp_id == mp_id)
    ).one()


def upsert(db: Session, email: str, password: str, **fields) -> User:
    """Create the account, or replace the password and scope of an existing one.

    Idempotent by address. Re-running this script does not accumulate accounts,
    and it does not leave an old password working either.
    """
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, created_at=datetime.combine(DATA_AS_OF, datetime.min.time()))
        db.add(user)
    user.password_hash = hash_password(password)
    user.is_active = True
    for name, value in fields.items():
        setattr(user, name, value)
    return user


def plan(db: Session) -> list[dict]:
    """The four accounts to write, with their scopes chosen from the corpus.

    Raises rather than writing an account onto an empty scope: a login that
    opens onto an empty screen is worse than no login, because nobody watching
    can tell it apart from a broken one.
    """
    if not db.scalar(_scored(db)):
        raise SystemExit(
            "No cases have been derived. Run `python -m ingest.run` and then "
            "`python -m app.derive_all` in backend/ before seeding accounts - the "
            "scopes below are chosen from the derived corpus."
        )

    state = busiest_state(db)
    district = busiest_district(db, state.id)
    member = busiest_member(db, district.district, state.id)
    if district is None or member is None:
        raise SystemExit(
            f"Could not find a populated district and member inside {state.name}. "
            "The corpus may have been re-ingested without a re-derive."
        )

    whole_portfolio = member_totals(db, member.id)

    return [
        {
            "email": f"ministry@{DOMAIN}",
            "role": ROLE_MINISTRY,
            "display_name": "MoSPI DIID Analyst (demo)",
            "covers": "every case in the committed sample",
            "cases": db.scalar(_scored(db)),
        },
        {
            "email": f"nodal.{state.name.lower().replace(' ', '')}@{DOMAIN}",
            "role": ROLE_STATE_NODAL,
            "display_name": f"{state.name} State Nodal Authority (demo)",
            "scope_state_id": state.id,
            "covers": state.name,
            "cases": state.cases,
        },
        {
            "email": f"dm.{district.district.lower()}@{DOMAIN}",
            "role": ROLE_DISTRICT_AUTHORITY,
            "display_name": f"District Magistrate, {district.district.title()} (demo)",
            "scope_state_id": state.id,
            "scope_district": district.district,
            "covers": f"{district.district}, {state.name}",
            "cases": district.cases,
            "high": district.high,
        },
        {
            "email": f"office.mp{member.id}@{DOMAIN}",
            "role": ROLE_MEMBER_OF_PARLIAMENT,
            "display_name": f"Office of {member.name_canon.title()} (demo)",
            "scope_mp_id": member.id,
            # The member's OWN totals, not the district slice they were
            # ranked on. Their scope carries no geography.
            "covers": f"{member.name_canon} (mp_id {member.id}), all districts",
            "cases": whole_portfolio.cases,
            "high": whole_portfolio.high,
            "note": (
                f"selected as the busiest member in {district.district}; their own scope "
                f"spans {whole_portfolio.districts} districts"
            ),
        },
    ]


def seed(db: Session) -> list[dict]:
    """Write the four accounts and return them, each with its plaintext password.

    The password is returned rather than stored anywhere, so the caller - and
    only the caller - can print it once.
    """
    # `users` is created here with `checkfirst` rather than assumed: a database
    # ingested before this table existed does not carry it, and `ingest.run`
    # creates everything in `Base.metadata` for one ingested after.
    User.__table__.create(engine, checkfirst=True)

    written = []
    for entry in plan(db):
        password = _password()
        fields = {
            key: value
            for key, value in entry.items()
            if key.startswith("scope_") or key in ("role", "display_name")
        }
        # Every scope column is written on every account, so re-seeding a
        # changed corpus clears a scope that no longer applies instead of
        # leaving it behind on a role that must not carry it.
        for column in ("scope_state_id", "scope_district", "scope_mp_id"):
            fields.setdefault(column, None)
        user = upsert(db, entry["email"], password, **fields)
        written.append({**entry, "password": password, "user": user})

    db.commit()
    for entry in written:
        db.refresh(entry["user"])
    return written


def report(written: list[dict]) -> str:
    """The credentials block, for stdout and nowhere else."""
    lines = [
        "",
        "NIGRANI demo accounts - four roles, four scopes.",
        "",
        "  These passwords are printed ONCE and are stored nowhere. Re-running",
        "  `python -m app.seed_users` replaces every one of them.",
        "",
        "  The login is a demo over seeded accounts, not an identity provider",
        "  (PROJECT-BRIEF.md). What IS real is the scoping: each token below",
        "  reaches only the rows its row in the matrix allows, enforced in the",
        "  query (docs/domain/DOMAIN-MODEL.md (k)).",
        "",
    ]
    for entry in written:
        counted = f"{entry['cases']:,} cases"
        if entry.get("high") is not None:
            counted += f", {entry['high']:,} HIGH"
        lines += [
            f"  {entry['role']}",
            f"    email    {entry['email']}",
            f"    password {entry['password']}",
            f"    sees     {entry['covers']}  ({counted})",
        ]
        if entry.get("note"):
            lines.append(f"    note     {entry['note']}")
        lines.append("")
    lines += [
        "  The member of parliament account is READ-ONLY: it can open a case and",
        "  cannot annotate, recompute, resolve or escalate one. The scheme's",
        "  subject does not adjudicate the scheme's findings.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    with SessionLocal() as db:
        print(report(seed(db)))


if __name__ == "__main__":
    main()
