"""Pre-aggregated dashboard endpoints - what Phase 8's four persona screens read.

**Nothing here aggregates the corpus.** Every figure comes out of the four
`rollup_*` tables `app/derive_all.py` builds at materialisation time, keyed and
indexed on what these endpoints filter by. Measured on the committed corpus:
the national rollup evaluated live over `v_case_facts` takes about 380 ms - it
walks 27,079 cases and aggregates 34,004 payment rows - and read out of
`rollup_state` it takes about 0.25 ms. The definition is shared (`v_case_facts`
is what every rollup is built from), so the Ministry's national view and a
District Authority's queue cannot disagree about what a case is worth.

**Staleness is refused rather than served.** The rollup tables are created by
DDL in `derive_all.py` rather than declared in `models.py`, so `ingest/run.py`'s
`drop_all` does not know about them: a re-ingest without a re-derive would
leave them behind describing a corpus that no longer exists. `_fresh_or_503`
compares the rollup's own case total against `cases` before any endpoint
answers. An aggregate that silently described the wrong corpus would be worse
than an error, because nobody would know to doubt it.

**Three honesty rules travel in the response, not in a footnote.**

* The corpus is a truncated portal sample, not the national record. Every
  response carries a `caption` saying so, and no figure here is presented as a
  national total (CLAUDE.md honesty rules).
* The labelled synthetic control is excluded from every rollup (invariant 12).
  It remains reachable as a case, where it is labelled on screen.
* `undisbursed_amt` is sanctioned minus disbursed and ONLY on cases whose fund
  hop 1 is open. A work with no expenditure row has an unavailable hop and
  contributes nothing, because counting it would report the truncation of
  MoSPI's export as undelivered money. The size of that population travels
  beside the sum as `cases_without_expenditure_row`.

**Role scoping is by GRAIN here, and that is a different question from the
case list's.** A rollup row is an aggregate over a population, so there is no
row-level predicate to add: either a role reads a grain or it does not.
`/national` is Ministry-only; `/state/{state}` requires `state == S` for a
State Nodal officer and is out of reach for the district and member roles;
`/district/{district}` requires the district to lie in `S` for a State Nodal
officer and to BE `D` for a District Authority; `/mp/{mp_id}` is the member's
own row, a member seated in `S` for a State Nodal officer, and invisible to the
District role entirely - a district officer has no business seeing a member's
aggregate account position (DOMAIN-MODEL.md (k)). The checks live in
`routers/scoping.py` and refuse with 403: a state name or a member id is
published by MoSPI, so there is nothing about its existence to conceal, which
is the opposite of the case-id situation and why that one 404s instead.

**The two case lists these endpoints embed are row-scoped as well**, through
`cases.list_query(user)`, so the district queue and a member's worst cases
carry the same predicate the ranked list does rather than a second one written
here. See `docs/api/ROLE-SCOPING-PLAN.md`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..constants import (
    DATA_AS_OF,
    FY_TERM_TO_DATE,
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
)
from ..db import get_db
from ..engine.rulebook import load as load_rulebook
from ..models import MP, Case, Constituency, FundAccount, State, User, Work
from ..schemas import (
    AccountLadder,
    AccountLadderRung,
    CaseListItem,
    DistrictAnalytics,
    MPAnalytics,
    NationalAnalytics,
    RollupRow,
    StateAnalytics,
)
from .cases import list_item, list_query
from .scoping import check_district_grain, check_mp_grain, check_state_grain

router = APIRouter(prefix="/analytics", tags=["analytics"])

SAMPLE_CAPTION = (
    "Measured over the committed MPLADS portal sample of 27,078 real sanctioned works, "
    "as of 2026-08-24. This is a truncated sample of the portal, not the national record: "
    "no figure here is a national total. The labelled synthetic control is excluded."
)

STALE = (
    "The pre-aggregated rollups do not describe the current cases. Run "
    "`python -m app.derive_all` in backend/. Serving a stale aggregate would be worse "
    "than this error, because nobody would know to doubt it."
)

MISSING = (
    "No rollups have been built. Run `python -m ingest.run` and then "
    "`python -m app.derive_all` in backend/."
)

ROLLUP_COLUMNS = (
    "cases, high_cases, medium_cases, low_cases, corroborated_cases, sanctioned_amt, "
    "undisbursed_amt, cases_without_expenditure_row, mean_coverage_pct, worst_score"
)


def _fresh_or_503(db: Session) -> None:
    """Refuse to answer from a rollup that does not describe the current cases."""
    try:
        rolled = db.execute(text("SELECT COALESCE(SUM(cases), 0) FROM rollup_state")).scalar_one()
    except Exception as exc:  # noqa: BLE001 - the table itself is absent
        raise HTTPException(status_code=503, detail=MISSING) from exc
    stored = db.scalar(
        select(func.count()).select_from(Case).where(Case.is_synthetic.is_(False))
    )
    if rolled != stored:
        raise HTTPException(status_code=503, detail=f"{STALE} (rollup {rolled}, cases {stored})")


def _state_ids(db: Session) -> dict:
    """Every state name to its id. 36 rows, so this is one query and not a join."""
    return {name: state_id for state_id, name in db.execute(select(State.id, State.name))}


def _state_name(db: Session, state_id: int | None) -> str | None:
    """One state's name by id, or None. The inverse of `_state_ids`."""
    return db.scalar(select(State.name).where(State.id == state_id)) if state_id else None


def _district_states(db: Session, district: str) -> list[tuple[int, str]]:
    """EVERY state carrying a district of this name with at least one case.

    A LIST, and the plural in the name is the whole bug fix. This returned one
    arbitrary row before - `WHERE district = :district LIMIT 1`, unordered - and
    a district name does not identify a district in this corpus. 61 of the 634
    district names carrying cases appear in more than one state: 53 in two, four
    in three, one in four, and `AGRA`, `PILIBHIT` and `SHAHJAHANPUR` in five
    each. `ALWAR` is a district of Rajasthan with 70 cases AND a district of
    Uttar Pradesh with one.

    What the arbitrary pick cost, in the three places it reached:

      * The grain check compared the WRONG state's id against the caller's, so a
        District Authority legitimately scoped to Uttar Pradesh/ALWAR was
        refused their own district with the self-contradicting sentence "Your
        scope is 'ALWAR' and it is not 'ALWAR'".
      * The rollup queries selected on the name alone, so a Ministry analyst
        reading ALWAR got Rajasthan's 70 cases and Uttar Pradesh's one SUMMED
        into a single row describing no district that exists.
      * The agency list likewise mixed the implementing agencies of two
        different districts a thousand kilometres apart.

    Ordered by state name so the disambiguation message a caller gets back is
    stable rather than depending on row order.
    """
    return [
        (row[0], row[1])
        for row in db.execute(
            select(Work.state_id, State.name)
            .join(State, State.id == Work.state_id)
            .join(Case, Case.work_id == Work.id)
            .where(Work.district == district)
            .group_by(Work.state_id, State.name)
            .order_by(State.name)
        ).all()
    ]


def _resolve_district_state(
    db: Session, user: User, district: str, state: str | None
) -> tuple[int | None, str | None]:
    """Which state's district of this name the caller is asking about.

    **The state comes from the caller's own row wherever the role has one, and
    never from the client.** A State Nodal officer and a District Authority are
    both bound to a state id in `users` (models.User, `ck_user_scope_matches_role`),
    so for them the second term of the predicate is already known server-side
    and a client-supplied one could only ever be redundant or a lie. That is
    also why the route did not need to change shape: for three of the four roles
    there was never a missing parameter, only a query that failed to use one it
    already had.

    The Ministry is the one role with no state of its own, so it is the one role
    that may pass `?state=`. When it does not, an unambiguous name resolves on
    its own and an ambiguous one is refused with the candidates named - because
    the alternative, summing several districts that share a name into one row,
    is the correctness half of this bug and answering it silently is worse than
    asking the caller which one they meant.

    Returns `(state_id, state_name)`, or `(None, None)` to mean "not in this
    caller's reach", which `check_district_grain` turns into the 403.
    """
    if user.role == ROLE_DISTRICT_AUTHORITY:
        # Their own state, unconditionally. Whether the district NAME is theirs
        # is the grain check's question, and whether it holds cases is the 404's;
        # neither is answered by looking the name up across the corpus.
        return user.scope_state_id, _state_name(db, user.scope_state_id)

    if user.role == ROLE_STATE_NODAL:
        carriers = {state_id for state_id, _ in _district_states(db, district)}
        if user.scope_state_id not in carriers:
            # Not a district of their state. Refused as a grain (403) with the
            # state that DOES carry the name left unsaid: naming it would tell
            # an officer of one state about the districts of another, which the
            # old message did.
            return None, None
        return user.scope_state_id, _state_name(db, user.scope_state_id)

    if user.role != ROLE_MINISTRY:
        # Any other role is refused by the grain check on the role alone.
        return None, None

    candidates = _district_states(db, district)
    if state is not None:
        wanted = _state_ids(db).get(state)
        match = next(((sid, name) for sid, name in candidates if sid == wanted), None)
        if match is None:
            raise HTTPException(
                status_code=404, detail=f"No cases in district {district!r} in state {state!r}"
            )
        return match
    if not candidates:
        raise HTTPException(status_code=404, detail=f"No cases in district {district!r}")
    if len(candidates) > 1:
        names = ", ".join(name for _, name in candidates)
        raise HTTPException(
            status_code=400,
            detail=(
                f"{district!r} names a district in more than one state ({names}). "
                f"Add ?state= to say which. Answering without it would sum districts that "
                f"share a name into one row describing none of them."
            ),
        )
    return candidates[0]


def _rows(db: Session, sql: str, **params) -> list[RollupRow]:
    return [RollupRow(**dict(row._mapping)) for row in db.execute(text(sql), params).all()]


def _totalled(rows: list[RollupRow], **identity) -> RollupRow:
    """One RollupRow summing a list of them. Coverage is weighted by case count.

    A plain mean of the per-row means would weight a district with four cases
    the same as one with seven thousand, and print a coverage figure that
    describes no population at all.
    """
    cases = sum(row.cases for row in rows)
    weighted = sum((row.mean_coverage_pct or 0) * row.cases for row in rows)
    return RollupRow(
        **identity,
        cases=cases,
        high_cases=sum(row.high_cases for row in rows),
        medium_cases=sum(row.medium_cases for row in rows),
        low_cases=sum(row.low_cases for row in rows),
        corroborated_cases=sum(row.corroborated_cases for row in rows),
        sanctioned_amt=sum(row.sanctioned_amt or 0 for row in rows),
        undisbursed_amt=sum(row.undisbursed_amt or 0 for row in rows),
        cases_without_expenditure_row=sum(row.cases_without_expenditure_row for row in rows),
        mean_coverage_pct=round(weighted / cases, 2) if cases else None,
        worst_score=max((row.worst_score or 0 for row in rows), default=None),
    )


@router.get("/national", response_model=NationalAnalytics)
def national(
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(ROLE_MINISTRY)),
    top: int = Query(default=10, ge=1, le=32, description="how many states in the HIGH ranking"),
):
    """State-level rollups: case counts by band, value at risk, worst states.

    Ministry-only. Every other role reads its own grain: a state nodal officer's
    equivalent view is `/state/{their state}`, and a national ranking of states
    is not a narrower version of that - it is a different question.
    """
    _fresh_or_503(db)
    states = _rows(
        db, f"SELECT state, districts, agencies, {ROLLUP_COLUMNS} FROM rollup_state ORDER BY state"
    )
    total = _totalled(states)
    return NationalAnalytics(
        caption=SAMPLE_CAPTION,
        data_as_of=DATA_AS_OF,
        rulebook_version=load_rulebook().get("version", ""),
        total_cases=total.cases,
        high_cases=total.high_cases,
        medium_cases=total.medium_cases,
        low_cases=total.low_cases,
        corroborated_cases=total.corroborated_cases,
        sanctioned_amt=total.sanctioned_amt or 0,
        undisbursed_amt=total.undisbursed_amt or 0,
        cases_without_expenditure_row=total.cases_without_expenditure_row,
        mean_coverage_pct=total.mean_coverage_pct or 0.0,
        states=states,
        # Ranked on HIGH count, then on the value the open hops leave
        # undelivered. Two states with one HIGH case each are not equally
        # urgent if one of them has Rs 12 crore sitting behind an open hop.
        top_states_by_high=sorted(
            states, key=lambda row: (-row.high_cases, -(row.undisbursed_amt or 0), row.state or "")
        )[:top],
    )


@router.get("/state/{state}", response_model=StateAnalytics)
def state_analytics(
    state: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """The districts inside one state, ranked by HIGH count.

    The grain check runs against the resolved state id rather than the name, so
    a caller cannot reach their own state's rollup under a different spelling,
    nor another state's under theirs.
    """
    check_state_grain(user, state, _state_ids(db))
    _fresh_or_503(db)
    districts = _rows(
        db,
        f"SELECT state, district, agencies, {ROLLUP_COLUMNS} FROM rollup_district "
        "WHERE state = :state ORDER BY high_cases DESC, cases DESC, district",
        state=state,
    )
    if not districts:
        raise HTTPException(status_code=404, detail=f"No cases in state {state!r}")
    return StateAnalytics(
        caption=SAMPLE_CAPTION,
        data_as_of=DATA_AS_OF,
        state=state,
        summary=_totalled(districts, state=state),
        districts=districts,
    )


@router.get("/district/{district}", response_model=DistrictAnalytics)
def district_analytics(
    district: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=500, description="cases in the queue"),
    state: str | None = Query(
        default=None,
        description=(
            "Which state's district of this name. Meaningful for the ministry only: "
            "every other role is bound to a state and it is read from their own row, "
            "never from here."
        ),
    ),
):
    """One district's case queue, plus which agencies the cases sit under.

    The agency summary is the district's answer to "who is this happening
    under" - the same question the F4 corroboration bonus asks per case, asked
    over the district instead of over one work.

    **A DISTRICT IS A STATE AND A NAME, never a name.** 61 of the 634 district
    names carrying cases in this corpus belong to more than one state, so every
    query below takes both terms. Which state is decided in
    `_resolve_district_state` and comes from the caller's own row for the two
    roles that are bound to one - the client cannot choose it, and for the
    Ministry, which is bound to none, an ambiguous name is refused rather than
    silently answered with one of the candidates.

    The rollups are keyed on `state_id` rather than on the state's name here,
    for the same reason the predicate on `works` is: two spellings of one state
    would otherwise be two states.
    """
    district_state_id, district_state_name = _resolve_district_state(db, user, district, state)
    check_district_grain(user, district, district_state_name, district_state_id)
    _fresh_or_503(db)
    summary_rows = _rows(
        db,
        f"SELECT state, district, agencies, {ROLLUP_COLUMNS} FROM rollup_district "
        "WHERE state_id = :state_id AND district = :district",
        state_id=district_state_id,
        district=district,
    )
    if not summary_rows:
        raise HTTPException(
            status_code=404,
            detail=f"No cases in district {district!r} in {district_state_name}",
        )
    agencies = _rows(
        db,
        f"SELECT state, district, agency, agency_id, {ROLLUP_COLUMNS} FROM rollup_agency "
        "WHERE state_id = :state_id AND district = :district "
        "ORDER BY high_cases DESC, cases DESC, agency",
        state_id=district_state_id,
        district=district,
    )
    queue = db.execute(
        list_query(user)
        # Both terms here too. `list_query` already carries the role predicate,
        # so this was safe for the two scoped roles and wrong for the Ministry,
        # whose queue mixed the cases of every district sharing the name.
        .where(
            Work.state_id == district_state_id,
            Work.district == district,
            Case.is_synthetic.is_(False),
        )
        .order_by(Case.score.desc(), Case.raw_score.desc(), Case.coverage_pct.desc(), Case.case_id)
        .limit(limit)
    ).all()
    return DistrictAnalytics(
        caption=SAMPLE_CAPTION,
        data_as_of=DATA_AS_OF,
        district=district,
        state=summary_rows[0].state,
        summary=_totalled(summary_rows, state=summary_rows[0].state, district=district),
        agencies=agencies,
        cases=[list_item(row) for row in queue],
    )


@router.get("/mp/{mp_id}", response_model=MPAnalytics)
def mp_analytics(
    mp_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=200, description="worst cases to list"),
):
    """One member's account ladder, work portfolio and utilisation percentile.

    The account ladder is `fund_accounts`, one row per FY plus the
    `term_to_date` sentinel that carries the published allocation - the portal
    publishes one cumulative allocation per member and no per-year breakdown,
    so the utilisation ratio is computable only on the sentinel row and every
    per-FY row carries a null allocation with reason `not_published`
    (DOMAIN-MODEL.md (d)).

    The percentile is over members holding both an allocation and a sanction,
    computed live from `fund_accounts` - 419 rows, not 27,079 - and the peer
    group is named in the response rather than left for the reader to assume it
    is national.

    A member reads their own row and no other. The district authority reads none
    at all, including their own district's members: a member's aggregate account
    position is not evidence about any work in a district, and the one derived
    value the district needs, `mp_utilisation_pct`, travels with each case's own
    trace (DOMAIN-MODEL.md (k)).
    """
    mp = db.get(MP, mp_id)
    # The grain check needs the member's own state, so the row is fetched
    # first - but the check runs before the 404, so a refused role learns
    # nothing about whether the id exists.
    check_mp_grain(user, mp_id, mp.state_id if mp is not None else None)
    if mp is None:
        raise HTTPException(status_code=404, detail=f"No MP {mp_id}")
    _fresh_or_503(db)

    accounts = db.scalars(
        select(FundAccount).where(FundAccount.mp_id == mp_id).order_by(FundAccount.fy)
    ).all()
    ladders = [
        AccountLadder(
            fy=account.fy,
            mp_utilisation_pct=account.mp_utilisation_pct,
            rungs=[
                AccountLadderRung(
                    key="allocated_amt",
                    label="Allocated",
                    amount=account.allocated_amt,
                    availability=account.allocated_availability.value,
                ),
                AccountLadderRung(
                    key="sanctioned_amt",
                    label="Sanctioned",
                    amount=account.sanctioned_amt,
                    availability="published",
                ),
                AccountLadderRung(
                    key="disbursed_amt",
                    label="Disbursed",
                    amount=account.disbursed_amt,
                    availability=account.disbursed_availability.value,
                ),
            ],
        )
        for account in accounts
    ]

    peers = [
        value
        for (value,) in db.execute(
            select(FundAccount.mp_utilisation_pct).where(
                FundAccount.fy == FY_TERM_TO_DATE,
                FundAccount.mp_utilisation_pct.is_not(None),
                FundAccount.sanctioned_amt > 0,
            )
        )
    ]
    own = next(
        (
            account.mp_utilisation_pct
            for account in accounts
            if account.fy == FY_TERM_TO_DATE and account.mp_utilisation_pct is not None
        ),
        None,
    )
    percentile = (
        round(100.0 * sum(1 for value in peers if value <= own) / len(peers), 1)
        if own is not None and peers
        else None
    )

    portfolio = _rows(
        db, f"SELECT mp_id, mp_name, state, {ROLLUP_COLUMNS} FROM rollup_mp WHERE mp_id = :mp_id",
        mp_id=mp_id,
    )
    worst = db.execute(
        list_query(user)
        .where(Work.mp_id == mp_id, Case.is_synthetic.is_(False))
        .order_by(Case.score.desc(), Case.raw_score.desc(), Case.coverage_pct.desc(), Case.case_id)
        .limit(limit)
    ).all()

    return MPAnalytics(
        caption=SAMPLE_CAPTION,
        data_as_of=DATA_AS_OF,
        mp={
            "id": mp.id,
            "name": mp.name_canon,
            "house": mp.house,
            "constituency": (
                db.scalar(select(Constituency.name).where(Constituency.id == mp.constituency_id))
                if mp.constituency_id is not None
                else None
            ),
            "state": db.scalar(select(State.name).where(State.id == mp.state_id)),
            "term": (
                f"{mp.term_start}-{mp.term_end}"
                if mp.term_start is not None and mp.term_end is not None
                else None
            ),
        },
        account=ladders,
        utilisation_percentile=percentile,
        utilisation_peer_group=(
            "members holding both a published allocation and at least one sanction, "
            "term-to-date, in the committed sample"
        ),
        utilisation_peers=len(peers),
        portfolio=portfolio[0] if portfolio else None,
        worst_cases=[list_item(row) for row in worst],
    )
