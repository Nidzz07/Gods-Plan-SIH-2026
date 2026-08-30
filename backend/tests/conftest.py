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
