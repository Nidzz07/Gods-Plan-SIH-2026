"""The tier boundaries themselves: the arrows only point one way, and a null has a reason.

Two things are asserted here, and neither needs the corpus.

**The dependency direction.** `engine/` may not import `ml/`, and neither
`engine/` nor `ml/` may import `ablation/`. That is the structural half of
CLAUDE.md invariant 1: `score.py` cannot reach an anomaly score, a delay
forecast, a graph centrality figure or a data-gap measurement, because the
packages they live in are not reachable from the package it lives in. A comment
promising the same thing would be worth nothing the first time somebody added
an import.

The two arrows are the same claim about two tiers, so they are asserted in one
file. Splitting them would let one of them be forgotten - which is precisely
the defect `tests/test_audit.py` records against the inherited suite's
two-file grep.

**The finding contract.** A finding carries a value or the reason it has none,
never both and never neither, so a badge that could not be computed cannot
reach a screen as a zero (invariant 2).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.constants import (
    ML_KIND_ANOMALY,
    ML_KIND_DUPLICATE,
    ML_KIND_FORECAST,
    ML_KIND_GRAPH,
    ML_KINDS,
    Availability,
)
from app.ml.base import Finding, model_version, rebuild

APP = Path(__file__).resolve().parent.parent / "app"
ENGINE = APP / "engine"
ML = APP / "ml"
ABLATION = APP / "ablation"


def _imported_modules(path: Path) -> set[str]:
    """Every module name this file imports, absolute and relative alike."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # `from ..ml import x` parses as level=2, module='ml'. The dots are
            # what a naive string search misses, which is why this walks the
            # syntax tree rather than grepping.
            names.add("." * (node.level or 0) + (node.module or ""))
            if node.module is None or node.level:
                names.update(f"{node.module or ''}.{alias.name}" for alias in node.names)
    return names


@pytest.mark.parametrize("path", sorted(ENGINE.glob("*.py")), ids=lambda p: p.name)
def test_no_engine_module_imports_the_ml_package(path):
    """The scoring path cannot reach the ML tier, and this is what says so.

    `engine/score.py`, `engine/rulebook.py`, `engine/audit.py` and
    `engine/memo.py` are on the path that produces a number. `engine/derive.py`
    is on the path that produces the inputs to that number. None of them may
    import `app.ml`, directly or relatively - and if this test ever fails, the
    fix is to move the code, not to relax the test.
    """
    for name in _imported_modules(path):
        stripped = name.lstrip(".")
        assert not (stripped == "ml" or stripped.startswith("ml.")), (
            f"{path.name} imports {name!r}. Nothing under engine/ may import the ML "
            "package: the score is the rulebook plus the corroboration bonus and "
            "nothing else (CLAUDE.md invariant 1), and the directory boundary is what "
            "makes that structural rather than promised."
        )
        assert not stripped.startswith("app.ml"), f"{path.name} imports {name!r}."


@pytest.mark.parametrize("path", sorted(ML.glob("*.py")), ids=lambda p: p.name)
def test_no_ml_module_imports_the_scoring_modules(path):
    """`ml/` may read `derive` and `rulebook`; it may not read the scorer.

    Reading `engine.derive.normalise_description` and
    `engine.rulebook.rule_by_field` is the point of the one-way arrow: the ML
    tier and the rulebook must not drift apart on a normalisation or a
    threshold. Reaching into `score.py`, `audit.py` or `memo.py` is different -
    those produce the number, the audit trail and the officer-facing prose, and
    a model output has no business in any of them.

    `ml/run.py` is the one exception and it is a deliberate one: it is an entry
    point, not a model, and it scores the corpus in order to hand the anomaly
    badge the fired-rule counts it needs to say `confirms`. The score is an
    INPUT to a badge there; no badge is ever an input to a score.
    """
    forbidden = {"score", "audit", "memo"}
    if path.name == "run.py":
        forbidden = {"audit", "memo"}
    for name in _imported_modules(path):
        tail = name.lstrip(".").split(".")[-1]
        assert tail not in forbidden, (
            f"{path.name} imports {name!r}. A badge may read the rulebook and the derived "
            "features; it may not reach the scorer, the audit trail or the memo."
        )


def _assert_does_not_import(path: Path, package: str, why: str) -> None:
    """Fail if this file imports `package`, absolutely or relatively.

    Shared by the three direction tests below so the AST walk is written once.
    `from ..ablation import measure` parses as level=2, module='ablation', and
    the dots are what a naive string search misses.
    """
    for name in _imported_modules(path):
        stripped = name.lstrip(".")
        assert not (stripped == package or stripped.startswith(f"{package}.")), (
            f"{path.name} imports {name!r}. {why}"
        )
        assert not stripped.startswith(f"app.{package}"), f"{path.name} imports {name!r}."


@pytest.mark.parametrize("path", sorted(ENGINE.glob("*.py")), ids=lambda p: p.name)
def test_no_engine_module_imports_the_ablation_package(path):
    """The scoring path cannot reach the data-gap tier either.

    `ablation/` measures what the rulebook could NOT evaluate. Nothing it
    produces is a point, a threshold or an input to one, and the directory
    boundary is what makes that structural rather than promised - the same
    guarantee `engine/` already has against `ml/`.
    """
    _assert_does_not_import(
        path,
        "ablation",
        "Nothing under engine/ may import the ablation package: the score is the "
        "rulebook plus the corroboration bonus and nothing else (CLAUDE.md invariant 1). "
        "If this fails, the fix is to move the code, not to relax the test.",
    )


@pytest.mark.parametrize("path", sorted(ML.glob("*.py")), ids=lambda p: p.name)
def test_no_ml_module_imports_the_ablation_package(path):
    """Tiers 3 and 4 have no business in the gap measurement either.

    A badge says whether a model confirms what the rulebook found. What the
    rulebook could not evaluate at all is a different question, answered in a
    different package, and a badge that reached into it would blur the two.
    """
    _assert_does_not_import(
        path,
        "ablation",
        "A badge may read the rulebook and the derived features; it may not reach the "
        "data-gap measurement.",
    )


@pytest.mark.parametrize("path", sorted(ABLATION.glob("*.py")), ids=lambda p: p.name)
def test_no_ablation_module_imports_the_ml_package(path):
    """And the arrow between ablation and ml points nowhere at all.

    `ablation/` reads `engine/` - deliberately, and including
    `engine.score.coverage_pct`, because a second copy of the coverage formula
    would eventually disagree with the first. That import is READ-ONLY and it
    is the point of the one-way arrow: the gap measurement and the case screen
    must not drift apart on what coverage means.

    `ml/` is different. A duplicate cluster, an anomaly badge and a delay
    forecast are model outputs; a skipped rule is a fact about MoSPI's export.
    Nothing in the measurement should depend on a fit, because a report to a
    ministry that moved when a forest was refitted would not be a measurement.
    """
    _assert_does_not_import(
        path,
        "ml",
        "The data-gap measurement is arithmetic over the recorded trace. It reads "
        "engine/ and it does not read model output: a figure in the MoSPI report must "
        "not move because a model was refitted.",
    )


def test_the_boundary_walk_reaches_all_three_packages():
    """The defect guarded against is a boundary test with too small a scope."""
    for package, path in (("engine", ENGINE), ("ml", ML), ("ablation", ABLATION)):
        modules = {p.name for p in path.glob("*.py")}
        assert "__init__.py" in modules, package
        assert len(modules) > 1, f"{package} has no modules to check"
    assert {"score.py", "derive.py", "rulebook.py"} <= {p.name for p in ENGINE.glob("*.py")}
    assert {"measure.py", "rank.py", "report.py", "run.py"} <= {
        p.name for p in ABLATION.glob("*.py")
    }


def test_the_four_kinds_are_the_four_the_data_model_declares():
    assert ML_KINDS == (ML_KIND_DUPLICATE, ML_KIND_ANOMALY, ML_KIND_FORECAST, ML_KIND_GRAPH)


# ---------------------------------------------------------------------------
# The finding contract - invariant 2, one layer up
# ---------------------------------------------------------------------------


def test_a_published_finding_must_carry_a_value():
    with pytest.raises(ValueError, match="published with no value"):
        Finding(
            work_pk=1,
            kind=ML_KIND_ANOMALY,
            value=None,
            availability=Availability.PUBLISHED,
        )


def test_an_unavailable_finding_must_not_carry_a_value():
    """A reason and a reading may never disagree.

    This is the shape of the failure invariant 2 exists to catch: a badge that
    said `not_applicable` while carrying 0.0 would put a reason on the screen
    and a number in the aggregate.
    """
    with pytest.raises(ValueError, match="carries a value"):
        Finding(
            work_pk=1,
            kind=ML_KIND_ANOMALY,
            value=0.0,
            availability=Availability.NOT_APPLICABLE,
        )


def test_an_unknown_kind_is_refused():
    with pytest.raises(ValueError, match="unknown ml_findings kind"):
        Finding(work_pk=1, kind="hunch", value=None, availability=Availability.NOT_APPLICABLE)


def test_the_reason_travels_into_the_row_because_the_table_has_no_column_for_it():
    """`ml_findings` has no availability companion, so the payload carries it."""
    import json

    row = Finding(
        work_pk=7,
        kind=ML_KIND_FORECAST,
        value=None,
        availability=Availability.NOT_APPLICABLE,
        payload={"detail": "the outcome is observed, not predicted"},
    ).as_row()
    payload = json.loads(row["payload_json"])
    assert payload["availability"] == "not_applicable"
    assert payload["detail"] == "the outcome is observed, not predicted"
    assert row["value"] is None
    assert row["contributes_to_score"] is False


def test_model_version_changes_when_anything_that_determines_the_output_changes():
    """Two fits over the same population under the same parameters agree."""
    base = model_version("iso1", features=["a", "b"], seed=1, trained_on=100)
    assert base == model_version("iso1", trained_on=100, seed=1, features=["a", "b"])
    assert base != model_version("iso1", features=["a", "b"], seed=1, trained_on=101)
    assert base != model_version("iso1", features=["a", "c"], seed=1, trained_on=100)
    assert base.startswith("iso1-")


# ---------------------------------------------------------------------------
# Persistence - a derived cache, rebuilt rather than appended to
# ---------------------------------------------------------------------------


@pytest.fixture
def scratch_session(tmp_path):
    """A throwaway database with the real schema. Never the ingested corpus."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    from app import models  # noqa: F401  - registers the tables on Base

    engine = create_engine(f"sqlite:///{tmp_path / 'scratch.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _seed_one_work(session):
    from app import models

    state = models.State(name="TESTSTATE")
    session.add(state)
    session.flush()
    mp = models.MP(
        name_raw="Test Member", name_canon="TEST MEMBER", house="lok_sabha", state_id=state.id
    )
    session.add(mp)
    session.flush()
    work = models.Work(
        work_id_canon="WS/MP001/2025-2026/000001",
        work_id_raw="WS/MP001/2025-2026/000001",
        mp_id=mp.id,
        state_id=state.id,
        fy="2025-2026",
        source_file="test",
    )
    session.add(work)
    session.commit()
    return work.id


def test_rebuild_is_idempotent_and_does_not_double_on_a_second_run(scratch_session):
    """Idempotent by rebuild, the way `ingest/run.py` is.

    The table is dropped and recreated rather than having its rows deleted.
    CLAUDE.md invariant 4 forbids any helper anywhere in `backend/` capable of
    removing a row, and `tests/test_audit.py` enforces that over every file
    rather than over `audit.py` alone. The right response to an absolute is to
    obey it, not to carve out an exception for a table that happens to be a
    cache - so the whole table goes and comes back, the way the corpus does.
    """
    from app.models import MLFinding

    work_pk = _seed_one_work(scratch_session)
    findings = [
        Finding(
            work_pk=work_pk,
            kind=kind,
            value=0.5,
            availability=Availability.PUBLISHED,
            model_version=f"{kind}-test",
        )
        for kind in (ML_KIND_GRAPH, ML_KIND_ANOMALY)
    ]
    assert rebuild(scratch_session, findings) == 2
    assert rebuild(scratch_session, findings) == 2
    assert scratch_session.query(MLFinding).count() == 2
    # And the work rows the findings point at survive the rebuild.
    from app.models import Work

    assert scratch_session.query(Work).count() == 1


def test_rebuild_refuses_a_finding_of_an_unknown_kind(scratch_session):
    """The kind vocabulary is closed - `models.py` declares four."""
    work_pk = _seed_one_work(scratch_session)

    class Rogue:
        kind = "hunch"

        def as_row(self):  # pragma: no cover - never reached
            return {}

    with pytest.raises(ValueError, match="unknown ml_findings kind"):
        rebuild(scratch_session, [Rogue()])
    del work_pk
