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

Role scoping (Phase 7): `/national` becomes Ministry-only, `/state/{state}`
requires `state == S` for a State Nodal officer, `/district/{district}`
requires `district == D` for a District Authority, and `/mp/{mp_id}` is
invisible to the District role entirely - a district officer has no business
seeing a member's aggregate account position (DOMAIN-MODEL.md (k)). See
`docs/api/ROLE-SCOPING-PLAN.md`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..constants import DATA_AS_OF, FY_TERM_TO_DATE
from ..db import get_db
from ..engine.rulebook import load as load_rulebook
from ..models import MP, Case, Constituency, FundAccount, State, Work
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
    top: int = Query(default=10, ge=1, le=32, description="how many states in the HIGH ranking"),
):
    """State-level rollups: case counts by band, value at risk, worst states."""
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
def state_analytics(state: str, db: Session = Depends(get_db)):
    """The districts inside one state, ranked by HIGH count."""
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
    limit: int = Query(default=50, ge=1, le=500, description="cases in the queue"),
):
    """One district's case queue, plus which agencies the cases sit under.

    The agency summary is the district's answer to "who is this happening
    under" - the same question the F4 corroboration bonus asks per case, asked
    over the district instead of over one work.
    """
    _fresh_or_503(db)
    summary_rows = _rows(
        db,
        f"SELECT state, district, agencies, {ROLLUP_COLUMNS} FROM rollup_district "
        "WHERE district = :district",
        district=district,
    )
    if not summary_rows:
        raise HTTPException(status_code=404, detail=f"No cases in district {district!r}")
    agencies = _rows(
        db,
        f"SELECT state, district, agency, agency_id, {ROLLUP_COLUMNS} FROM rollup_agency "
        "WHERE district = :district ORDER BY high_cases DESC, cases DESC, agency",
        district=district,
    )
    queue = db.execute(
        list_query(db)
        .where(Work.district == district, Case.is_synthetic.is_(False))
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
    """
    mp = db.get(MP, mp_id)
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
        list_query(db)
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
