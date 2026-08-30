"""F6 - the append-only trail, the hash chain, and re-derivation that is real.

Three claims are under test, and the third is the one the inherited engine got
wrong.

**Append-only.** `audit_log` is insert-only: no in-place edit, no removal, and
no helper capable of either anywhere in `backend/` (CLAUDE.md invariant 4). The
grep at the bottom of this module enforces that across the WHOLE backend rather
than across two hand-listed files. The inherited suite listed
`engine/audit.py` and `routers/audit.py` and nothing else, which meant a
mutation helper added to `ingest/`, to `seed.py` or to a router nobody thought
of would have passed. That narrow scope was a documented defect and it is not
repeated here.

**Hash-chained.** `row_hash` covers the row's own content together with the
previous row's hash, so a forged row is visible and a removed row breaks every
hash after it. Both are asserted, and neither is asserted by performing the
mutation: a forged row is INSERTED, and the consequence of a removal is
computed over the stored columns. This module writes no update and no delete,
because a test suite that needed one would be evidence against the invariant it
is testing.

**Re-derived against the SNAPSHOT.** The inherited `recompute()` read the
rulebook file on disk and compared five scalars. Both halves were wrong.
NIGRANI's must re-derive against the rulebook the case was actually scored
under - `cases.rulebook_version_id` -> `rulebook_versions.yaml_snapshot`
(invariant 5) - and must compare the full trace, because an auditor's question
is never "did the number move" but "which rule moved, and why".
`test_recompute_re_derives_against_the_stored_snapshot_not_todays_rulebook`
constructs that divergence explicitly: the stored snapshot and the shipped
`rules.yaml` disagree about `execution_delay`, and a recompute that quietly
read the file instead of the snapshot would move the case from LOW to MEDIUM.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.constants import Availability, case_id_for
from app.db import Base
from app.engine import derive as derive_mod
from app.engine.audit import (
    COMPARED_FIELDS,
    EVENT_SCORE_RECOMPUTED,
    TRACE_FIELDS,
    _bonus_count,
    diff_traces,
    log,
    recompute,
    row_hash,
    snapshot_for,
    summarise,
    summarise_trace,
    verify_chain,
)
from app.engine.rulebook import load, loads
from app.engine.score import compute
from app.models import MP, AuditLog, Case, RuleHit, RulebookVersion, State, Work

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Published on every key, so the case under test skips nothing and any trace
# movement is a rulebook difference rather than an availability one.
AUDIT_FEATURES = {
    "work_id": "WS/MP001/2025-2026/000001",
    "variance_sanction_to_disbursement": -40.01,
    "variance_disbursement_to_certification": None,
    "sanction_lag_days": 333,
    "sanction_to_first_payment_days": 9,
    "first_payment_to_completion_days": 100,
    "execution_days": 481,
    "days_since_last_payment": 100,
    "duplicate_similarity": 0.4,
    "same_desc_same_agency_count": 1,
    "vendor_share_in_agency_pct": 17.35,
    "completed_without_payment": False,
    "asset_image_absent": False,
    "mp_utilisation_pct": 73.8,
    "payment_count": 1,
}

WORK_ID = "WS/MP001/2025-2026/000001"
CASE_ID = case_id_for(WORK_ID)


def features():
    values = dict(AUDIT_FEATURES)
    availability = {
        key: (Availability.PUBLISHED if values[key] is not None else Availability.NOT_PUBLISHED)
        for key in derive_mod.FEATURE_KEYS
    }
    return derive_mod.FeatureSet(values, availability)


@pytest.fixture
def audit_db():
    """A throwaway database with the real schema and foreign keys enforced."""
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, future=True)()
    session.add(State(id=1, name="TEST STATE"))
    session.add(
        MP(id=1, name_raw="Shri Test Member", name_canon="TEST MEMBER", house="lok_sabha", state_id=1)
    )
    session.add(
        Work(
            id=1,
            work_id_canon=WORK_ID,
            work_id_raw=WORK_ID,
            mp_id=1,
            state_id=1,
            fy="2025-2026",
            source_file="test",
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()


def store_version(session, yaml_text, version="v1.0.0", version_id=1):
    import hashlib

    session.add(
        RulebookVersion(
            id=version_id,
            version=version,
            yaml_snapshot=yaml_text,
            yaml_sha256=hashlib.sha256(yaml_text.encode()).hexdigest(),
            created_at=datetime(2026, 8, 24, 9, 0),
            created_by_role="ministry",
        )
    )
    session.commit()


def store_case(session, body, version_id=1):
    """Persist a scored body as a Case plus its ten RuleHit rows.

    Written through the same stringification `summarise_trace` reads back, so
    a stored trace and a freshly derived one are compared on equal terms.
    """
    session.add(
        Case(
            case_id=CASE_ID,
            work_id=1,
            score=body["score"],
            raw_score=body["raw_score"],
            severity=body["severity"],
            status="open",
            coverage_pct=body["coverage_pct"],
            gap_hop=body["gap_hop"],
            slowest_lag=body["slowest_lag"],
            rulebook_version_id=version_id,
            corroboration_bonus=body["corroboration"]["contribution"],
            opened_at=datetime(2026, 8, 24, 9, 30),
        )
    )
    for hit in body["rule_hits"]:
        session.add(
            RuleHit(
                case_id=CASE_ID,
                rule_id=hit["rule_id"],
                label=hit["label"],
                field=hit["field"],
                raw_value=None if hit["raw_value"] is None else str(hit["raw_value"]),
                threshold=str(hit["threshold"]),
                operator=hit["operator"],
                weight=hit["weight"],
                contribution=hit["contribution"],
                severity=hit["severity"],
                status=hit["status"],
                skip_reason=hit["skip_reason"],
                caveat=hit["caveat"],
            )
        )
    session.commit()
    return session.get(Case, CASE_ID)


# ---------------------------------------------------------------------------
# Append-only, and the chain that proves it
# ---------------------------------------------------------------------------


def test_log_appends_one_row_carrying_its_payload(audit_db):
    log(audit_db, "CASE_OPENED", "ministry", case_id=CASE_ID, payload={"score": 58})
    audit_db.commit()

    rows = audit_db.scalars(select(AuditLog)).all()
    assert len(rows) == 1
    assert rows[0].event == "CASE_OPENED"
    assert rows[0].actor_role == "ministry"
    assert rows[0].case_id == CASE_ID
    assert json.loads(rows[0].payload_json) == {"score": 58}
    assert rows[0].prev_hash is None


def test_logging_again_leaves_the_earlier_row_exactly_as_it_was(audit_db):
    log(audit_db, "CASE_OPENED", "ministry", case_id=CASE_ID)
    audit_db.commit()
    first = audit_db.scalars(select(AuditLog)).one()
    before = (first.id, first.at, first.event, first.prev_hash, first.row_hash)

    log(audit_db, "NOTE_ADDED", "district_authority", case_id=CASE_ID, payload={"note": "seen"})
    audit_db.commit()

    rows = audit_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert len(rows) == 2
    assert (rows[0].id, rows[0].at, rows[0].event, rows[0].prev_hash, rows[0].row_hash) == before


def test_each_row_links_to_the_hash_of_the_one_before(audit_db):
    for event in ("CASE_OPENED", "RULE_FIRED", "NOTE_ADDED"):
        log(audit_db, event, "ministry", case_id=CASE_ID)
    audit_db.commit()

    rows = audit_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert rows[0].prev_hash is None
    for earlier, later in zip(rows, rows[1:]):
        assert later.prev_hash == earlier.row_hash


def test_a_row_hash_is_recomputable_from_the_stored_columns_alone(audit_db):
    """An auditor walks the chain without trusting this module to have run."""
    log(audit_db, "CASE_OPENED", "ministry", case_id=CASE_ID, payload={"score": 58})
    audit_db.commit()
    row = audit_db.scalars(select(AuditLog)).one()
    assert row.row_hash == row_hash(
        row.prev_hash, row.at, row.actor_role, row.actor_id, row.event, row.case_id, row.payload_json
    )


def test_verify_chain_reports_an_untouched_trail_as_intact(audit_db):
    for event in ("CASE_OPENED", "RULE_FIRED", "PATTERN_LINKED"):
        log(audit_db, event, "ministry", case_id=CASE_ID)
    audit_db.commit()
    assert verify_chain(audit_db) == {"rows": 3, "intact": True, "broken_at": None}


def test_verify_chain_names_the_first_row_whose_hash_does_not_hold(audit_db):
    """A forged row is INSERTED rather than an honest row edited.

    The distinction matters: this suite must not itself contain a way to alter
    a written row, or it would be evidence against invariant 4. Inserting a row
    whose `row_hash` does not cover its own contents is exactly what someone
    reaching the SQLite file with a generic client would leave behind, and it
    is what `verify_chain` has to catch.
    """
    log(audit_db, "CASE_OPENED", "ministry", case_id=CASE_ID)
    audit_db.commit()
    genuine = audit_db.scalars(select(AuditLog)).one()

    audit_db.add(
        AuditLog(
            at=datetime(2026, 8, 24, 10, 0),
            actor_role="ministry",
            event="NOTE_ADDED",
            case_id=CASE_ID,
            payload_json='{"note":"inserted by hand"}',
            prev_hash=genuine.row_hash,
            row_hash="0" * 64,
        )
    )
    audit_db.commit()

    outcome = verify_chain(audit_db)
    assert outcome["rows"] == 2
    assert outcome["intact"] is False
    assert outcome["broken_at"] == genuine.id + 1


def test_removing_a_row_would_break_every_hash_after_it(audit_db):
    """Asserted arithmetically, because the suite writes no delete.

    If row 2 vanished, row 3's stored `prev_hash` would no longer be row 1's
    hash, and re-deriving row 3's own hash over the shortened chain gives a
    different digest from the one stored. That is the property that makes the
    chain worth having, and it is computable from the stored columns without
    removing anything.
    """
    for event in ("CASE_OPENED", "RULE_FIRED", "NOTE_ADDED"):
        log(audit_db, event, "ministry", case_id=CASE_ID)
    audit_db.commit()
    first, second, third = audit_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()

    assert third.prev_hash == second.row_hash
    assert third.prev_hash != first.row_hash
    without_the_second = row_hash(
        first.row_hash, third.at, third.actor_role, third.actor_id, third.event,
        third.case_id, third.payload_json,
    )
    assert without_the_second != third.row_hash


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------


def test_summarise_reads_a_stored_case_and_a_fresh_body_the_same_way(audit_db, rulebook):
    body = compute(features(), rulebook, 0)
    store_version(audit_db, Path(BACKEND_DIR / "app" / "rules.yaml").read_text(encoding="utf-8"))
    case = store_case(audit_db, body)

    stored = summarise(case)
    fresh = summarise(body)
    assert set(stored) == set(COMPARED_FIELDS)
    # `rulebook_version` is the one field a Case row does not carry under that
    # name; recompute fills it from the snapshot. Everything else must agree.
    assert {k: v for k, v in stored.items() if k != "rulebook_version"} == {
        k: v for k, v in fresh.items() if k != "rulebook_version"
    }


def test_summarise_trace_stringifies_both_sides_so_sqlite_text_compares_equal(
    audit_db, rulebook
):
    body = compute(features(), rulebook, 0)
    store_version(audit_db, Path(BACKEND_DIR / "app" / "rules.yaml").read_text(encoding="utf-8"))
    store_case(audit_db, body)
    stored_hits = audit_db.scalars(select(RuleHit).where(RuleHit.case_id == CASE_ID)).all()

    assert summarise_trace(stored_hits) == summarise_trace(body["rule_hits"])
    assert set(summarise_trace(body["rule_hits"])[0]) == set(TRACE_FIELDS)


def test_diff_traces_is_empty_when_the_trace_re_derives(rulebook):
    trace = summarise_trace(compute(features(), rulebook, 0)["rule_hits"])
    assert diff_traces(trace, trace) == []


def test_diff_traces_names_the_rule_and_every_field_that_moved(rulebook):
    """"duplicate_work moved from fired to passed", not "the score changed by 18"."""
    before = summarise_trace(compute(features(), rulebook, 0)["rule_hits"])
    after = [dict(row) for row in before]
    moved = next(row for row in after if row["rule_id"] == "execution_delay")
    moved["status"] = "passed"
    moved["contribution"] = "0"

    differences = diff_traces(before, after)
    assert {(d["rule_id"], d["field"]) for d in differences} == {
        ("execution_delay", "status"),
        ("execution_delay", "contribution"),
    }
    status = next(d for d in differences if d["field"] == "status")
    assert (status["stored"], status["recomputed"]) == ("fired", "passed")


def test_diff_traces_reports_a_rule_present_on_only_one_side(rulebook):
    before = summarise_trace(compute(features(), rulebook, 0)["rule_hits"])
    after = [row for row in before if row["rule_id"] != "stalled_work"]
    differences = diff_traces(before, after)
    assert differences == [
        {"rule_id": "stalled_work", "field": None, "stored": "present", "recomputed": None}
    ]


def test_a_score_that_did_not_move_while_two_rules_swapped_is_not_identical(rulebook):
    """The exact case a five-field scalar comparison would have called clean."""
    before = summarise_trace(compute(features(), rulebook, 0)["rule_hits"])
    after = [dict(row) for row in before]
    for row in after:
        if row["rule_id"] == "sanction_delay":
            row["status"], row["contribution"] = "passed", "0"
        if row["rule_id"] == "stalled_work":
            row["status"], row["contribution"] = "fired", "16"
    assert diff_traces(before, after) != []


# ---------------------------------------------------------------------------
# Invariant 5 - the snapshot, not today's file
# ---------------------------------------------------------------------------


def diverged_rulebook_text() -> str:
    """The shipped rulebook with `execution_delay` raised out of reach.

    481 execution days fire the rule at the shipped threshold of 365 and pass
    it at 999, so a case scored under this snapshot is 20 points and one
    severity band away from the same case scored under `rules.yaml` today.
    That gap is what makes the invariant-5 test non-vacuous.

    The declared version moves with the threshold, because an edit CREATES a
    version and never mutates one (DOMAIN-MODEL.md section e). A snapshot that
    kept the shipped version string while carrying a different threshold would
    be the "same version, edited file" state `rulebook_versions.yaml_sha256`
    exists to make detectable, and building the fixture that way would be
    modelling the defect rather than the behaviour.
    """
    text = (BACKEND_DIR / "app" / "rules.yaml").read_text(encoding="utf-8")
    text = text.replace('version: "v1.0.0"', 'version: "v0.9.0"', 1)
    return text.replace("    threshold: 365\n", "    threshold: 999\n", 1)


def test_the_diverged_snapshot_really_does_disagree_with_todays_rulebook(rulebook):
    """Guard on the guard: if these ever agreed, the test below proves nothing."""
    diverged = loads(diverged_rulebook_text())
    today = compute(features(), rulebook, 0)
    stored = compute(features(), diverged, 0)
    assert today["score"] == 58 and today["severity"] == "MEDIUM"
    assert stored["score"] == 38 and stored["severity"] == "LOW"


def test_snapshot_for_returns_the_version_the_case_was_scored_under(audit_db, rulebook):
    text = diverged_rulebook_text()
    store_version(audit_db, text, version="v0.9.0")
    case = store_case(audit_db, compute(features(), loads(text), 0))
    assert snapshot_for(audit_db, case) == ("v0.9.0", text)


def test_snapshot_for_refuses_to_fall_back_to_the_current_rules_file(audit_db, rulebook):
    """A missing version row is an error, never a silent read of today's file.

    Falling back would re-derive the case against a rulebook it was never
    scored under, which is the whole defect invariant 5 names.
    """
    store_version(audit_db, "version: v1.0.0\nrules: []\n")
    case = store_case(audit_db, compute(features(), rulebook, 0))
    case.rulebook_version_id = 99
    audit_db.flush()
    with pytest.raises(LookupError, match="invariant 5"):
        snapshot_for(audit_db, case)


def test_recompute_re_derives_against_the_stored_snapshot_not_todays_rulebook(audit_db):
    """THE invariant-5 test. Stored and current rulebooks are made to disagree.

    The case was scored under a snapshot where `execution_delay` reads 999, so
    the rule passed and the case is 38 / LOW. Today's `rules.yaml` reads 365,
    under which the same features give 58 / MEDIUM. A recompute that read the
    file would report the case as having moved by 20 points and one band. It
    must report it as unchanged, because nothing about the case changed - only
    the rulebook did, and that rulebook is not this case's.
    """
    text = diverged_rulebook_text()
    store_version(audit_db, text, version="v0.9.0")
    stored_body = compute(features(), loads(text), 0)
    case = store_case(audit_db, stored_body)

    outcome = recompute(audit_db, case, features)
    audit_db.commit()

    assert outcome["rulebook_version"] == "v0.9.0"
    assert outcome["identical"] is True
    assert outcome["trace_diff"] == []
    assert outcome["recomputed"]["score"] == 38
    assert outcome["recomputed"]["severity"] == "LOW"
    execution = next(
        row for row in outcome["recomputed_trace"] if row["rule_id"] == "execution_delay"
    )
    assert (execution["threshold"], execution["status"]) == ("999", "passed")
    # And the shipped file, which was NOT read, still says 365.
    assert load()["rules"][1]["threshold"] == 365


def test_recompute_reports_a_trace_that_moved_rule_by_rule(audit_db, rulebook):
    """Stored under today's rulebook, pointed at a diverged snapshot.

    This is the drift a recompute exists to surface: the trace on file and the
    trace the snapshot produces disagree, and the report names which rule and
    which field rather than only that a number moved.
    """
    store_version(audit_db, diverged_rulebook_text(), version="v0.9.0")
    case = store_case(audit_db, compute(features(), rulebook, 0))

    outcome = recompute(audit_db, case, features)
    audit_db.commit()

    assert outcome["identical"] is False
    assert outcome["stored"]["score"] == 58
    assert outcome["recomputed"]["score"] == 38
    assert outcome["stored"]["severity"] == "MEDIUM"
    assert outcome["recomputed"]["severity"] == "LOW"
    moved = {(d["rule_id"], d["field"]) for d in outcome["trace_diff"]}
    assert moved == {
        ("execution_delay", "threshold"),
        ("execution_delay", "status"),
        ("execution_delay", "contribution"),
    }


def test_recompute_leaves_the_stored_case_exactly_as_it_was(audit_db, rulebook):
    """An observation, not a correction. The disagreement IS the finding."""
    store_version(audit_db, diverged_rulebook_text(), version="v0.9.0")
    case = store_case(audit_db, compute(features(), rulebook, 0))
    before = (case.score, case.raw_score, case.severity, case.coverage_pct)

    recompute(audit_db, case, features)
    audit_db.commit()

    stored = audit_db.get(Case, CASE_ID)
    assert (stored.score, stored.raw_score, stored.severity, stored.coverage_pct) == before
    hits = audit_db.scalars(select(RuleHit).where(RuleHit.case_id == CASE_ID)).all()
    execution = next(hit for hit in hits if hit.rule_id == "execution_delay")
    assert (execution.status, execution.contribution, execution.threshold) == ("fired", 20, "365")


def test_recompute_writes_one_event_carrying_both_traces_not_only_the_number(
    audit_db, rulebook
):
    """SCORE_RECOMPUTED is what makes invariant 5 auditable rather than asserted."""
    store_version(audit_db, diverged_rulebook_text(), version="v0.9.0")
    case = store_case(audit_db, compute(features(), rulebook, 0))

    recompute(audit_db, case, features, actor_role="state_nodal", actor_id=7)
    audit_db.commit()

    row = audit_db.scalars(select(AuditLog)).one()
    assert row.event == EVENT_SCORE_RECOMPUTED
    assert (row.actor_role, row.actor_id, row.case_id) == ("state_nodal", 7, CASE_ID)
    payload = json.loads(row.payload_json)
    assert len(payload["stored_trace"]) == 10
    assert len(payload["recomputed_trace"]) == 10
    assert payload["trace_diff"]
    assert verify_chain(audit_db)["intact"] is True


@pytest.mark.parametrize("bonus,expected", [(0, 0), (10, 3)])
def test_the_bonus_count_reproduces_the_award_the_case_carries(bonus, expected):
    from types import SimpleNamespace

    assert _bonus_count(SimpleNamespace(corroboration_bonus=bonus)) == expected


def test_a_recompute_reproduces_the_bonus_the_case_was_given(audit_db, rulebook):
    store_version(audit_db, (BACKEND_DIR / "app" / "rules.yaml").read_text(encoding="utf-8"))
    case = store_case(audit_db, compute(features(), rulebook, 25))
    assert case.corroboration_bonus == 10

    outcome = recompute(audit_db, case, features)
    audit_db.commit()
    assert outcome["identical"] is True
    assert outcome["recomputed"]["raw_score"] == 68


# ---------------------------------------------------------------------------
# Invariant 4 - the grep, across ALL of backend/
# ---------------------------------------------------------------------------

# Assembled from fragments, and joined with str.join rather than with `+`: the
# compiler folds adjacent string literals into one constant, which would put
# the whole pattern back into this file and trip the grep on the test that
# exists to perform it.
_DELETE_CALL = "".join((".dele", "te("))
_DELETE_SQL = "".join(("DELE", "TE FROM"))
_BULK = "".join(("synchronize_", "session"))
_UPDATE_SQL = re.compile("".join((r"UPD", r"ATE\s+\w+\s+", "SET", r"\b")), re.IGNORECASE)
# `from sqlalchemy import ...` naming a row-mutation construct. A dict's own
# .update() is legitimate and common, so the import line is what is watched
# rather than the call shape.
_MUTATION_IMPORT = re.compile(
    "".join((r"sqlalchemy[\w.]* import [^\n]*\b(", "upd", "ate|", "dele", r"te)\b"))
)

# Everything under backend/ except third-party code, build artefacts and the
# corpus itself. `.venv` is not ours; `__pycache__` is generated.
SKIPPED_DIRECTORIES = {".venv", "__pycache__", ".pytest_cache", "node_modules"}
SCANNED_SUFFIXES = {".py", ".yaml", ".yml", ".ini"}


def backend_sources():
    return [
        path
        for path in BACKEND_DIR.rglob("*")
        if path.suffix in SCANNED_SUFFIXES
        and path.is_file()
        and not SKIPPED_DIRECTORIES & set(path.relative_to(BACKEND_DIR).parts)
    ]


def test_the_grep_actually_reaches_the_whole_backend():
    """The defect being guarded against is a grep with too small a scope.

    The inherited test named `engine/audit.py` and `routers/audit.py` and
    stopped there, so a mutation helper anywhere else would have passed
    unnoticed. This asserts the walk reaches ingest, seed, the routers, the
    rulebook YAML and this suite itself before the grep below is trusted.
    """
    scanned = {path.relative_to(BACKEND_DIR).as_posix() for path in backend_sources()}
    for required in (
        "app/engine/audit.py",
        "app/engine/score.py",
        "app/models.py",
        "app/rules.yaml",
        "app/routers/audit.py",
        "app/routers/cases.py",
        "ingest/run.py",
        "seed.py",
        "tests/test_audit.py",
    ):
        assert required in scanned, required
    assert len(scanned) > 20


@pytest.mark.parametrize("path", backend_sources(), ids=lambda p: p.name)
def test_no_file_in_the_backend_can_edit_or_remove_an_audit_row(path):
    """CLAUDE.md invariant 4, enforced over every file rather than over two.

    `audit_log` is insert-only, and the invariant is written as an absolute:
    no helper capable of an update or a delete anywhere in `backend/`. The
    patterns match construct shapes rather than the bare words, because two
    comments in `ingest/run.py` say in prose that no update and no delete is
    issued - and a test that failed on a file promising to obey it would be a
    test nobody could keep.
    """
    source = path.read_text(encoding="utf-8", errors="ignore")
    assert _DELETE_CALL not in source
    assert _DELETE_SQL.lower() not in source.lower()
    assert _BULK not in source
    assert _UPDATE_SQL.search(source) is None
    assert _MUTATION_IMPORT.search(source) is None
