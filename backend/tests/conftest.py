"""Shared fixtures.

Two kinds of test live in this suite and they are deliberately kept apart.

**Corpus tests** read `backend/nigrani.db` and assert that the engine
reproduces `docs/contract/fixtures.md` and the firing-count table in
`docs/data/DATA-PROFILE.md` section 6 on the real ingested rows. They are the
acceptance tests and they skip, loudly, if the corpus has not been loaded.

**Unit tests** build feature sets and rulebooks by hand. They exist to exercise
branches the corpus does not reach - a payment published as zero, an allocation
published as zero, a case that breaks the 100-point cap - because a branch
nothing exercises is exactly the declared-but-never-computed defect CLAUDE.md
invariant 3 exists to prevent.

No derived value is ever hardcoded on the way IN. The fixtures supply raw
inputs; the engine derives; a wrong derivation fails a test instead of being
handed the right answer.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import inspect

from app.constants import Availability
from app.db import DB_PATH, SessionLocal
from app.engine import derive as derive_mod
from app.engine import rulebook as rulebook_mod

FIXTURE_A = "WS/MP847/2025-2026/160261"
FIXTURE_B = "WS/MP163/2024-2025/136111"
FIXTURE_C = "WS/MP503/2025-2026/140882"


@pytest.fixture(scope="session")
def rulebook():
    """The shipped rulebook, validated against the derived feature dictionary."""
    book = rulebook_mod.load()
    return rulebook_mod.validate(book, derive_mod.FEATURE_KEYS)


@pytest.fixture(scope="session")
def db_session():
    """A session on the ingested corpus, or a skip if it has not been loaded."""
    if not DB_PATH.exists():
        pytest.skip(f"{DB_PATH} not found - run `python -m ingest.run` first.")
    session = SessionLocal()
    if not inspect(session.bind).has_table("works"):
        session.close()
        pytest.skip("corpus database has no tables - run `python -m ingest.run` first.")
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def corpus(db_session, rulebook):
    """Every sanctioned work, derived and scored through the engine."""
    from .corpus import Corpus

    return Corpus(db_session, rulebook)


@pytest.fixture(scope="session")
def ml_run(corpus):
    """All four ML tiers, fitted once and shared across the ML test modules.

    Session-scoped because the forest and the classifier are fitted here: a
    per-test fit would spend a minute proving nothing, and the fits are
    deterministic anyway (`app.constants.ML_RANDOM_SEED`), so one is enough.
    """
    from .ml_harness import MLRun

    return MLRun(corpus)


# ---------------------------------------------------------------------------
# Hand-built inputs, for the branches the corpus does not reach
# ---------------------------------------------------------------------------


def work(**overrides):
    """A minimal work row. Only the fields the engine reads are present."""
    defaults = dict(
        id=1,
        work_id_canon="WS/MP001/2025-2026/000001",
        work_id_raw="WS/MP001/2025-2026/000001",
        mp_id=1,
        agency_id=1,
        district="TESTDISTRICT",
        description="construction of a boundary wall",
        description_availability=Availability.PUBLISHED,
        status="Work Completed",
        status_availability=Availability.PUBLISHED,
        fy="2025-2026",
        asset_image_present=True,
        asset_image_availability=Availability.PUBLISHED,
        is_synthetic=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def sanction(**overrides):
    defaults = dict(
        work_id=1,
        recommended_amt=1_000_000,
        recommended_availability=Availability.PUBLISHED,
        recommended_date=date(2025, 1, 1),
        recommended_date_availability=Availability.PUBLISHED,
        sanctioned_amt=1_000_000,
        sanction_date=date(2025, 3, 1),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def payment(paid_amt=500_000, payment_date=date(2025, 6, 1), vendor_id=1, availability=None):
    return SimpleNamespace(
        work_id=1,
        vendor_id=vendor_id,
        paid_amt=paid_amt,
        paid_availability=availability
        or (Availability.PUBLISHED_ZERO if paid_amt == 0 else Availability.PUBLISHED),
        payment_date=payment_date,
        payment_date_availability=(
            Availability.PUBLISHED if payment_date is not None else Availability.NOT_PUBLISHED
        ),
        payment_status="Payment Success",
    )


def completion(completion_date=date(2025, 12, 1), completed_amt=990_000):
    return SimpleNamespace(
        work_id=1,
        completion_date=completion_date,
        completion_date_availability=(
            Availability.PUBLISHED if completion_date is not None else Availability.NOT_PUBLISHED
        ),
        completed_amt=completed_amt,
        completed_availability=Availability.PUBLISHED,
    )


def certification(certified_amt=700_000, certification_date=date(2026, 1, 1)):
    return SimpleNamespace(
        work_id=1,
        certified_amt=certified_amt,
        certified_availability=(
            Availability.PUBLISHED if certified_amt is not None else Availability.NOT_PUBLISHED
        ),
        certification_date=certification_date,
        certification_date_availability=Availability.PUBLISHED,
    )


def context(**overrides):
    """A corpus context with one agency well over the vendor floor."""
    defaults = dict(
        agency_disbursed={1: 50_000_000},
        agency_vendor_disbursed={(1, 1): 5_000_000},
        agency_name={1: "TEST DISTRICT MAGISTRATE"},
        mp_account={1: (10_000_000, Availability.PUBLISHED, 5_000_000)},
    )
    defaults.update(overrides)
    ctx = derive_mod.CorpusContext(**defaults)
    return ctx


def with_descriptions(ctx, rows):
    """Load (work_pk, work_id, agency_id, description) tuples into a context."""
    ctx.load_descriptions(rows)
    return ctx


@pytest.fixture
def features_factory():
    """Build a FeatureSet from a values dict, filling availability for the rest."""

    def build(values=None, availability=None, evidence=None):
        values = dict(values or {})
        reasons = dict(availability or {})
        for key in derive_mod.FEATURE_KEYS:
            values.setdefault(key, None)
            reasons.setdefault(
                key,
                Availability.PUBLISHED
                if values[key] is not None
                else Availability.NOT_PUBLISHED,
            )
        return derive_mod.FeatureSet(values, reasons, evidence)

    return build


# ---------------------------------------------------------------------------
# A server over a copy of the corpus, with the four demo accounts on it
# ---------------------------------------------------------------------------
#
# The copy exists because two endpoints append to `audit_log` and one test
# rebuilds four tables: a suite that grew the developer's audit trail by four
# rows per run would be writing history nobody asked for, and the
# materialisation test has to be able to rebuild without the developer losing
# their build.
#
# The accounts exist because every route under `/api` now requires a token
# (`app/auth.py`). `client` below carries a Ministry one, which is the widest
# scope and therefore the only one under which the acceptance assertions in
# `test_api.py` still describe the whole corpus. `anon_client` carries none, so
# a test can prove an endpoint is closed rather than assume it.


def sessionmaker_on(path):
    """A session factory on one SQLite file, with foreign keys enforced.

    The pragma listener is the same one `app/db.py` installs and for the same
    reason: SQLite ignores foreign keys unless asked, per connection, every
    time, and a test database that did not enforce them would be a weaker
    database than the one the API actually runs against.
    """
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker as _sessionmaker

    engine = create_engine(
        f"sqlite:///{path}", connect_args={"check_same_thread": False}, future=True
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, _sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def copy_corpus(destination):
    """`backend/nigrani.db`, copied, or a skip if it was never built."""
    import shutil

    if not DB_PATH.exists():
        pytest.skip(f"{DB_PATH} not found - run `python -m ingest.run` first.")
    shutil.copy2(DB_PATH, destination)
    return destination


def provision_accounts(factory):
    """Create the `users` table on a copied corpus and seed the test accounts.

    `checkfirst=True` rather than an unconditional create: the copy comes from
    whatever the developer last built, and a corpus ingested after this phase
    already carries the table because `ingest/run.py` creates everything in
    `Base.metadata`. Either way the accounts are inserted here, because
    `ingest.run` drops the table and `seed_users` is a separate build step.

    Returns detached snapshots rather than live ORM rows, so a test can read an
    id after the session that made it has closed.
    """
    from types import SimpleNamespace

    from app.models import User

    from . import accounts as accounts_mod

    engine = factory.kw["bind"]
    User.__table__.create(engine, checkfirst=True)

    with factory() as session:
        made = accounts_mod.build(session)
        accounts_mod.assert_populated(session, made)
        return {
            key: SimpleNamespace(
                id=user.id,
                email=user.email,
                role=user.role,
                display_name=user.display_name,
                is_active=user.is_active,
                scope_state_id=user.scope_state_id,
                scope_district=user.scope_district,
                scope_mp_id=user.scope_mp_id,
            )
            for key, user in made.items()
        }


@contextmanager
def api_client(factory, email=None):
    """A `TestClient` reading the copied corpus, signed in as `email` or nobody.

    The bearer token is obtained over HTTP through `POST /api/auth/login` rather
    than minted directly, so every test in the suite reaches the API the way a
    browser does - including the ones that are not about authentication.
    """
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def override():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    # Restored, not cleared. `app.dependency_overrides` belongs to the one
    # module-level `app` object, so a nested client that cleared it on the way
    # out would leave the session-scoped `client` above pointed back at the
    # developer's real `nigrani.db` - silently, and only for the tests that
    # happened to run afterwards.
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as test_client:
            if email is not None:
                from . import accounts as accounts_mod

                test_client.headers.update(
                    accounts_mod.headers(accounts_mod.token_for(test_client, email))
                )
            yield test_client
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous


@pytest.fixture(scope="session")
def api_session_factory(tmp_path_factory):
    engine, factory = sessionmaker_on(copy_corpus(tmp_path_factory.mktemp("api") / "nigrani.db"))
    yield factory
    engine.dispose()


@pytest.fixture(scope="session")
def api_accounts(api_session_factory):
    """The seeded test accounts, by role, over the copied corpus."""
    return provision_accounts(api_session_factory)


@pytest.fixture(scope="session")
def client(api_session_factory, api_accounts):
    """A TestClient signed in as Ministry - the widest scope, so unfiltered.

    `test_api.py`'s acceptance assertions are about the whole corpus, and the
    Ministry role is the one that still sees the whole corpus once scoping is
    enforced. That the suite passes unchanged under a real token is itself the
    claim: adding auth narrowed nobody who was entitled to the rows.
    """
    from .accounts import ROLE_MINISTRY_EMAIL

    with api_client(api_session_factory, email=ROLE_MINISTRY_EMAIL) as test_client:
        if test_client.get("/health").json()["cases"] == 0:
            pytest.skip("no cases in the corpus - run `python -m app.derive_all` first.")
        yield test_client


@pytest.fixture(scope="session")
def anon_client(api_session_factory, api_accounts):
    """A TestClient carrying no credentials at all."""
    with api_client(api_session_factory) as test_client:
        yield test_client
