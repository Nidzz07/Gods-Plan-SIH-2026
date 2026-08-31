"""FastAPI application entrypoint.

    cd backend && uvicorn app.main:app --reload --port 8000

App, CORS, `/health`, and the seven routers. Every route lives under `/api`; the
prefix is applied here rather than repeated in each router, so the contract in
PROJECT-BRIEF.md has exactly one place it can drift from.

**This app reads. It does not build.** Cases are opened by
`python -m app.derive_all`, badges by `python -m app.ml.run`, the gap report by
`python -m app.ablation.run`, and the corpus by `python -m ingest.run`. Nothing
here derives a case on the first request the way the inherited LEAKPROOF
routers did - the reasoning is in `app/derive_all.py`, and the short version is
that 27,079 works is not 60 shops.

The two writes the API does perform, notes and recompute, only ever append to
`audit_log`. No endpoint anywhere in this application edits or removes a row of
the trail, and no helper capable of doing so exists in `backend/` (CLAUDE.md
invariant 4).

**Everything under `/api` requires a token. `/health` does not.** `/health` is
liveness plus four row counts and it is what a load balancer, a judge and a
developer all reach for first; putting it behind a login would mean an outage
and a bad password looked the same from outside. It reveals corpus totals that
`docs/data/DATA-PROFILE.md` already publishes, and no row about any state,
district or member. Every other route is scoped or role-gated - see
`docs/api/ROLE-SCOPING-PLAN.md`, and `tests/test_role_scoping.py`, which walks
this application's own route table rather than trusting a list.

**`create_all` is deliberately not called here.** The inherited app created
missing tables on import, which is convenient and, on this project, wrong: an
empty `cases` table created silently at startup is exactly the state that lets
a screen show "0 cases" as though it were a finding. `/health` reports the row
counts instead, so a service that is up over an unbuilt database says so.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from fastapi import Depends

from .constants import DATA_AS_OF
from .db import get_db
from .models import AblationFinding, Case, MLFinding, RulebookVersion, Work
from .routers import ablation, analytics, audit, auth, cases, rulebook, works
from .schemas import Health

app = FastAPI(
    title="NIGRANI",
    description=(
        "Anomaly, fraud and inefficiency detection for MPLADS, the Members of Parliament "
        "Local Area Development Scheme. Every flag is a rulebook arithmetic an officer can "
        "re-derive on paper and an auditor can reproduce months later against the rulebook "
        "snapshot the case was scored under."
    ),
    version="0.6.0",
)

# Vite dev server only. No wildcard: the demo runs on one known origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=Health)
def health(db: Session = Depends(get_db)):
    """Liveness, plus whether the four build steps have actually run.

    A green service over an empty database is the most misleading answer this
    API could give, so the counts travel with the status. `status` reads `ok`
    only when there are cases to serve; `awaiting_build` is a working service
    that has nothing to say yet, which is a different thing from a broken one.
    """
    if not inspect(db.get_bind()).has_table("cases"):
        return Health(
            status="awaiting_ingest",
            service="nigrani",
            version=app.version,
            data_as_of=DATA_AS_OF,
            corpus_works=0,
            cases=0,
            rulebook_version=None,
            ml_findings=0,
            ablation_findings=0,
        )

    case_count = db.scalar(select(func.count()).select_from(Case)) or 0
    version = db.scalar(select(RulebookVersion).order_by(RulebookVersion.id.desc()).limit(1))
    return Health(
        status="ok" if case_count else "awaiting_build",
        service="nigrani",
        version=app.version,
        data_as_of=DATA_AS_OF,
        corpus_works=db.scalar(select(func.count()).select_from(Work)) or 0,
        cases=case_count,
        rulebook_version=version.version if version is not None else None,
        ml_findings=db.scalar(select(func.count()).select_from(MLFinding)) or 0,
        ablation_findings=db.scalar(select(func.count()).select_from(AblationFinding)) or 0,
    )


# Declared first so the sign-in route reads first in the generated OpenAPI
# page: it is the one route a caller can reach before they have anything.
app.include_router(auth.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(works.router, prefix="/api")
app.include_router(rulebook.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(ablation.router, prefix="/api")
