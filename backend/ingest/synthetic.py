"""Fixture C: the labelled synthetic certification control.

`docs/contract/fixtures.md` explains why this row has to exist. No real MPLADS
row can ever populate the certification rung, because MoSPI publishes no
utilisation certificate date and no certified amount. Without an injected row,
`variance_disbursement_to_certification` would have a derivation function that
never once ran on real data - exactly the declared-but-never-computed failure
CLAUDE.md invariant 3 exists to prevent.

Two rules govern everything below.

**It is labelled** (invariant 12). The work, its sanction, its payments, its
completion and its certification all carry `is_synthetic = true`, and so do the
member, the office and the vendor they hang on. A synthetic sanction inside a
real member's account rollup, or a synthetic payment inside a real agency's
vendor-concentration figure, would be exactly the silent mixing the invariant
forbids. The control therefore references a real state and a real constituency
- neither is an actor NIGRANI makes findings about - and synthetic actors for
everything else, each named so that nobody reading a screen can mistake it.

**Its id is reserved** (fixtures.md caveat 3). `WS/MP503/2025-2026/140882` must
not collide with a real portal id. If the portal ever publishes it, the control
is not inserted and the collision is written to `ingest_rejects` with reason
`case_id_collision` - never a silent overwrite of the real work.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.constants import (
    Availability,
    STATUS_WORK_COMPLETED,
    SYNTHETIC_CONTROL_WORK_ID,
    RejectReason,
    canonical_work_id,
    case_id_for,
)
from app.models import (
    MP,
    Agency,
    Certification,
    Completion,
    Constituency,
    Payment,
    Sanction,
    State,
    Vendor,
    Work,
)

# Every figure here is the one worked in docs/contract/fixtures.md. It is not
# tuned: the fixture's score of 42 is whatever this input set produces under
# the rulebook, and changing a number here changes that score.
SYNTHETIC_CONTROL = {
    "work_id_raw": SYNTHETIC_CONTROL_WORK_ID,
    "state": "Maharashtra",
    "district": "NASHIK",
    "constituency": "NASHIK",
    "category": "Normal/Others",
    "description": "construction of community hall at ward no 7",
    "status": STATUS_WORK_COMPLETED,
    "fy": "2025-2026",
    "asset_image_present": True,
    "recommended_amt": 4_000_000,
    "sanctioned_amt": 4_000_000,
    "recommended_date": date(2025, 1, 14),
    "sanction_date": date(2025, 4, 8),
    "completion_date": date(2026, 8, 2),
    "completed_amt": 3_880_000,
    "certified_amt": 2_910_000,
    "certification_date": date(2026, 8, 18),
    # Four payments summing to 38,80,000, first 2025-05-20, last 2026-02-11.
    # The intermediate dates and the split are the fixture's own; only the
    # first date, the last date, the count and the total are load-bearing.
    "payments": [
        (date(2025, 5, 20), 1_200_000),
        (date(2025, 9, 12), 1_000_000),
        (date(2025, 12, 4), 900_000),
        (date(2026, 2, 11), 780_000),
    ],
    "payment_count": 4,
    # Named so that no screen, export or trace can show it without saying so.
    "mp_name": "SYNTHETIC CONTROL MEMBER (fixture C)",
    "agency_name": "SYNTHETIC CONTROL AGENCY, NASHIK (fixture C)",
    "vendor_name": "SYNTHETIC CONTROL VENDOR (fixture C)",
}


def insert_synthetic_control(session, rejects) -> dict:
    """Insert fixture C, unless its reserved work id already exists.

    Returns a dict for the load report: the work id, the derived case id,
    whether the row was inserted, and why not if it was not.
    """
    canon = canonical_work_id(SYNTHETIC_CONTROL["work_id_raw"])
    case_id = case_id_for(SYNTHETIC_CONTROL["work_id_raw"])

    collision = session.scalar(select(Work).where(Work.work_id_canon == canon))
    if collision is not None:
        reason = (
            f"{canon} is reserved for the synthetic certification control but was "
            f"published by the portal in {collision.source_file}. The real work is "
            "kept; the control is not inserted."
        )
        rejects.add(
            source_file="docs/contract/fixtures.md (fixture C)",
            row_number=1,
            raw_row={"work_id": canon, "case_id": case_id},
            reason=RejectReason.CASE_ID_COLLISION,
            detail=reason,
        )
        return {
            "work_id": canon,
            "case_id": case_id,
            "inserted": False,
            "reason": reason,
        }

    state = session.scalar(select(State).where(State.name == SYNTHETIC_CONTROL["state"]))
    if state is None:
        state = State(name=SYNTHETIC_CONTROL["state"])
        session.add(state)
        session.flush()

    constituency = session.scalar(
        select(Constituency).where(
            Constituency.state_id == state.id,
            Constituency.name == SYNTHETIC_CONTROL["constituency"],
        )
    )

    mp = MP(
        name_raw=SYNTHETIC_CONTROL["mp_name"],
        name_canon=SYNTHETIC_CONTROL["mp_name"].upper(),
        house="lok_sabha",
        state_id=state.id,
        constituency_id=constituency.id if constituency is not None else None,
        term_start=2024,
        term_end=2029,
        is_synthetic=True,
    )
    agency = Agency(
        name_canon=SYNTHETIC_CONTROL["agency_name"].upper(),
        district=SYNTHETIC_CONTROL["district"],
        state_id=state.id,
        variant_count=1,
        merge_confidence=None,
        is_synthetic=True,
    )
    vendor = Vendor(
        name_canon=SYNTHETIC_CONTROL["vendor_name"].upper(),
        name_raw=SYNTHETIC_CONTROL["vendor_name"],
        agency_span=1,
        is_synthetic=True,
    )
    session.add_all([mp, agency, vendor])
    session.flush()

    work = Work(
        work_id_canon=canon,
        work_id_raw=SYNTHETIC_CONTROL["work_id_raw"],
        mp_id=mp.id,
        agency_id=agency.id,
        state_id=state.id,
        district=SYNTHETIC_CONTROL["district"],
        category=SYNTHETIC_CONTROL["category"],
        description=SYNTHETIC_CONTROL["description"],
        description_availability=Availability.PUBLISHED,
        status=SYNTHETIC_CONTROL["status"],
        status_availability=Availability.PUBLISHED,
        fy=SYNTHETIC_CONTROL["fy"],
        asset_image_present=SYNTHETIC_CONTROL["asset_image_present"],
        asset_image_availability=Availability.PUBLISHED,
        is_synthetic=True,
        source_file="docs/contract/fixtures.md (fixture C)",
    )
    session.add(work)
    session.flush()

    session.add(
        Sanction(
            work_id=work.id,
            recommended_amt=SYNTHETIC_CONTROL["recommended_amt"],
            recommended_availability=Availability.PUBLISHED,
            recommended_date=SYNTHETIC_CONTROL["recommended_date"],
            recommended_date_availability=Availability.PUBLISHED,
            sanctioned_amt=SYNTHETIC_CONTROL["sanctioned_amt"],
            sanction_date=SYNTHETIC_CONTROL["sanction_date"],
            is_synthetic=True,
        )
    )
    session.add(
        Completion(
            work_id=work.id,
            completion_date=SYNTHETIC_CONTROL["completion_date"],
            completion_date_availability=Availability.PUBLISHED,
            completed_amt=SYNTHETIC_CONTROL["completed_amt"],
            completed_availability=Availability.PUBLISHED,
            is_synthetic=True,
        )
    )
    for payment_date, amount in SYNTHETIC_CONTROL["payments"]:
        session.add(
            Payment(
                work_id=work.id,
                vendor_id=vendor.id,
                paid_amt=amount,
                paid_availability=Availability.PUBLISHED,
                payment_date=payment_date,
                payment_date_availability=Availability.PUBLISHED,
                payment_status="Payment Success",
                is_synthetic=True,
            )
        )
    # The only row this table will ever hold on public MPLADS data.
    session.add(
        Certification(
            work_id=work.id,
            certified_amt=SYNTHETIC_CONTROL["certified_amt"],
            certified_availability=Availability.PUBLISHED,
            certification_date=SYNTHETIC_CONTROL["certification_date"],
            certification_date_availability=Availability.PUBLISHED,
            is_synthetic=True,
        )
    )
    session.flush()

    return {"work_id": canon, "case_id": case_id, "inserted": True, "reason": None}
