"""Work endpoint - the published record, before NIGRANI concluded anything.

Deliberately independent of `cases`. Three things need this:

* **Browsing.** `works` holds 65,270 rows - the union of every work id in the
  four work-level exports - while a case exists only for the 27,079 that carry
  a sanction (DOMAIN-MODEL.md (a)). A recommendation that was never sanctioned
  has no fund journey and no case, and it still has to be reachable.
* **The duplicate citation.** A fired `duplicate_work` row cites matched work
  ids so an officer can open them and judge. Some of those may sit outside
  whatever list the officer came from, and following a citation must not
  depend on a case having been derived for the work at the other end.
* **Separating evidence from finding.** What this endpoint returns is what
  MoSPI published. What `/api/cases/{id}` returns is what NIGRANI concluded
  from it. Keeping them at two URLs is what lets a screen show the first
  without implying the second.

`case_id` is present when a case has been opened for the work and null
otherwise. Null means "not a sanctioned work, or the build step has not run",
never "no findings".

Role scoping (Phase 7) filters the work select itself -
`Work.state_id == S`, `Work.district == D`, `Work.mp_id == M` - and returns 404
rather than 403 for a work out of scope. See `docs/api/ROLE-SCOPING-PLAN.md`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..constants import canonical_work_id
from ..db import get_db
from ..models import (
    MP,
    Agency,
    Case,
    Certification,
    Completion,
    Payment,
    Sanction,
    State,
    Vendor,
    Work,
)
from ..schemas import WorkDetail
from .cases import _mp_ref, _work_ref

router = APIRouter(prefix="/works", tags=["works"])


@router.get("/{work_id:path}", response_model=WorkDetail)
def get_work(work_id: str, db: Session = Depends(get_db)):
    """One work as published: rungs, dates, payments and the source file.

    The path is declared `:path` because a portal work id contains slashes -
    `WS/MP847/2025-2026/160261` - and the id is canonicalised before the lookup
    (uppercased, all whitespace including embedded tabs removed), so a caller
    who copies an id straight off the portal, tabs and all, still finds the row.
    """
    canon = canonical_work_id(work_id)
    work = db.scalar(select(Work).where(Work.work_id_canon == canon))
    if work is None:
        raise HTTPException(status_code=404, detail=f"No work {work_id}")

    sanction = db.scalar(select(Sanction).where(Sanction.work_id == work.id))
    completion = db.scalar(select(Completion).where(Completion.work_id == work.id))
    certification = db.scalar(select(Certification).where(Certification.work_id == work.id))
    payments = db.execute(
        select(Payment, Vendor.name_canon)
        .outerjoin(Vendor, Vendor.id == Payment.vendor_id)
        .where(Payment.work_id == work.id)
        .order_by(Payment.payment_date, Payment.id)
    ).all()

    agency_name = (
        db.scalar(select(Agency.name_canon).where(Agency.id == work.agency_id))
        if work.agency_id is not None
        else None
    )
    state_name = db.scalar(select(State.name).where(State.id == work.state_id))

    return WorkDetail(
        work=_work_ref(db, work, state_name, agency_name),
        mp=_mp_ref(db, db.get(MP, work.mp_id)),
        case_id=db.scalar(select(Case.case_id).where(Case.work_id == work.id)),
        recommended_amt=getattr(sanction, "recommended_amt", None),
        recommended_availability=(
            sanction.recommended_availability.value if sanction is not None else "not_applicable"
        ),
        recommended_date=getattr(sanction, "recommended_date", None),
        sanctioned_amt=getattr(sanction, "sanctioned_amt", None),
        sanction_date=getattr(sanction, "sanction_date", None),
        completion_date=getattr(completion, "completion_date", None),
        completed_amt=getattr(completion, "completed_amt", None),
        # Null on every real row. MoSPI publishes no utilisation certificate
        # date and no certified amount; the one populated row in the whole
        # table is the labelled synthetic control (DOMAIN-MODEL.md (i)).
        certified_amt=getattr(certification, "certified_amt", None),
        certification_date=getattr(certification, "certification_date", None),
        payments=[
            {
                "vendor": vendor_name,
                "paid_amt": payment.paid_amt,
                "paid_availability": payment.paid_availability.value,
                "payment_date": payment.payment_date,
                "payment_status": payment.payment_status,
            }
            for payment, vendor_name in payments
        ],
        source_file=work.source_file,
    )
