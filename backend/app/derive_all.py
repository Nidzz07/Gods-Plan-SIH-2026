"""`python -m app.derive_all` - open a case for every sanctioned work, once.

    cd backend
    python -m ingest.run        # the corpus
    python -m app.derive_all    # the cases          <- this file
    python -m app.ml.run        # the badges
    python -m app.ablation.run  # the gap report

**Why this is a command and not something a router does on first request.**
The inherited LEAKPROOF routers derived their cases lazily: the first HTTP
request to reach `/api/cases` ran the engine over every shop and wrote the
results. That was tolerable at 60 shops. NIGRANI has 27,079 sanctioned works,
and deriving them costs a corpus-wide similarity matrix, a corpus-wide payment
rollup and two full scoring passes - minutes, not milliseconds. A first request
that did that would hang a browser, and a second concurrent request would run
the whole thing again against a half-written table.

So the derivation is an explicit build step and the routers only ever read.
That is also the honest arrangement for an audit trail: cases are opened by a
run somebody can name and date, not as a side effect of somebody opening a
screen.

**Idempotent by rebuild, exactly as the three commands around it are.**
`ingest/run.py` drops and recreates every table, `ml/base.rebuild` drops and
recreates `ml_findings`, `ablation/run.store` drops and recreates
`ablation_findings`. This file drops and recreates the four tables it owns -
`rulebook_versions`, `cases`, `rule_hits`, `audit_log` - in foreign-key order,
then writes them in one pass. Running it twice produces the same case count and
the same score for every case rather than doubled rows.

It is DDL and not a row removal, for the reason `ml/base.py` gives at length:
CLAUDE.md invariant 4 forbids any helper anywhere in `backend/` capable of
removing or editing a row, and the right response to an absolute is to obey it
rather than to carve out an exception for a derived table.

**The consequence, stated rather than discovered.** `audit_log` goes with the
cases it describes, so a note added through `POST /api/cases/{id}/notes` does
not survive a re-run. That is the same bargain `ingest/run.py` already makes -
a trail whose cases no longer exist is not a trail - and the command prints it
before it writes. Rebuild when the corpus or the rulebook changes; not to
refresh a screen.

**Every timestamp is `DATA_AS_OF`, never a wall clock.** `cases.opened_at` and
every `audit_log.at` written here read 2026-08-24T00:00:00, the corpus as-of
date. Two runs over the same corpus therefore produce not merely the same
scores but the same hash chain, which is what lets a test assert idempotence on
the trail rather than only on the numbers.

**No number is computed here.** The two passes call `engine.score.compute`, the
same function a recompute calls six months from now, and store what it
returned. There is no second scoring path in NIGRANI and this file does not
open one.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, time

from sqlalchemy import select, text

from .constants import (
    CORROBORATION_CITATION_LIMIT,
    DATA_AS_OF,
    RULE_STATUS_FIRED,
    SEVERITY_HIGH,
    case_id_for,
)
from .db import SessionLocal
from .engine import audit as audit_mod
from .engine import derive as derive_mod
from .engine import rulebook as rulebook_mod
from .engine.score import compute
from .models import (
    AuditLog,
    Case,
    Certification,
    Completion,
    Payment,
    RuleHit,
    RulebookVersion,
    Sanction,
    Work,
)

# The corpus as-of date at midnight. Used for `cases.opened_at`, for every
# audit row this file writes, and for the rulebook snapshot's `created_at`, so
# that a rebuild reproduces the hash chain byte for byte. A wall clock here
# would make the trail unreproducible for no gain: the cases describe a corpus
# frozen on this date, not on the date somebody happened to run the command.
MATERIALISED_AT = datetime.combine(DATA_AS_OF, time.min)

# Who the seeded first rulebook version is recorded as having been created by.
# Rulebook governance is a Ministry function (DOMAIN-MODEL.md (k)).
SEED_ROLE = "ministry"
SEED_NOTE = (
    "Seeded by python -m app.derive_all from backend/app/rules.yaml. Every case in this "
    "run was scored under this snapshot, and a recompute re-derives against it rather "
    "than against whatever rules.yaml says later (CLAUDE.md invariant 5)."
)

# Written in this order per case, so the chain is reproducible.
EVENT_CASE_OPENED = "CASE_OPENED"
EVENT_RULE_FIRED = "RULE_FIRED"
EVENT_DUPLICATE_LINKED = "DUPLICATE_LINKED"
EVENT_PATTERN_LINKED = "PATTERN_LINKED"

# Dropped and recreated in this order. Children first, parents last: SQLite
# enforces foreign keys on DROP TABLE (db.py turns the pragma on), so dropping
# `cases` while `rule_hits` or `audit_log` still reference it is an error.
REBUILT_TABLES = (RuleHit, AuditLog, Case, RulebookVersion)


# ---------------------------------------------------------------------------
# The rollup the dashboards read
# ---------------------------------------------------------------------------

# `v_case_facts` is ONE definition of what a case is worth, so the four persona
# dashboards, the case list and the ablation report cannot drift apart on a
# join or on the meaning of `undisbursed_amt`.
#
# **A view is a stored query and not a stored result, so the view alone is not
# enough here, and this file does not pretend otherwise.** Measured on the
# committed corpus, a national rollup evaluated live off `v_case_facts` takes
# roughly 380 ms - it walks 27,079 cases and aggregates 34,004 payment rows on
# every request. That is the shape of thing this build step exists to get out
# of the request path. So the view is the definition and the four `rollup_*`
# tables below are the answer: built once here with CREATE TABLE AS SELECT,
# read by the analytics endpoints in under a millisecond.
#
# The rollup tables are created by DDL here rather than declared in
# `models.py`, because `models.py` is the storage contract for what NIGRANI
# ingests and derives, and a cache of its own aggregates is neither. The cost
# of that choice is that `ingest/run.py`'s `drop_all` does not know about them,
# so a re-ingest without a re-derive would leave them behind describing a
# corpus that no longer exists. `routers/analytics.py` closes that: it compares
# the rollup's own case total against `cases` before answering and refuses to
# serve a stale aggregate.
#
# `undisbursed_amt` is deliberately narrow. It is the sanctioned amount not
# reached by a payment, and ONLY on cases whose fund hop 1 is open - a case
# with no expenditure row has an unavailable hop, contributes nothing to the
# sum, and is counted separately as `cases_without_expenditure_row`. Summing
# over works with no payment row would report the truncation of MoSPI's
# expenditure export as undelivered money, which it is not.
VIEWS = {
    "v_case_facts": """
        CREATE VIEW v_case_facts AS
        SELECT
            c.case_id            AS case_id,
            c.score              AS score,
            c.raw_score          AS raw_score,
            c.severity           AS severity,
            c.status             AS status,
            c.coverage_pct       AS coverage_pct,
            c.gap_hop            AS gap_hop,
            c.slowest_lag        AS slowest_lag,
            c.corroboration_bonus AS corroboration_bonus,
            c.opened_at          AS opened_at,
            c.is_synthetic       AS is_synthetic,
            w.id                 AS work_pk,
            w.work_id_canon      AS work_id,
            w.description        AS description,
            w.category           AS category,
            w.status             AS work_status,
            w.district           AS district,
            w.fy                 AS fy,
            st.id                AS state_id,
            st.name              AS state,
            ag.id                AS agency_id,
            ag.name_canon        AS agency,
            mp.id                AS mp_id,
            mp.name_raw          AS mp_name,
            mp.house             AS mp_house,
            sa.sanctioned_amt    AS sanctioned_amt,
            pay.disbursed_amt    AS disbursed_amt,
            CASE
                WHEN c.gap_hop = 'sanction_to_disbursement'
                THEN sa.sanctioned_amt - COALESCE(pay.disbursed_amt, 0)
            END                  AS undisbursed_amt
        FROM cases c
        JOIN works    w  ON w.id  = c.work_id
        JOIN states   st ON st.id = w.state_id
        JOIN mps      mp ON mp.id = w.mp_id
        JOIN sanctions sa ON sa.work_id = w.id
        LEFT JOIN agencies ag ON ag.id = w.agency_id
        LEFT JOIN (
            SELECT work_id, SUM(paid_amt) AS disbursed_amt
            FROM payments
            WHERE paid_amt IS NOT NULL
            GROUP BY work_id
        ) pay ON pay.work_id = w.id
    """,
}

# The shared aggregate columns, spelled once. Every rollup measures a case the
# same way; only the grouping changes.
_MEASURES = """
            COUNT(*)                                        AS cases,
            SUM(severity = 'HIGH')                          AS high_cases,
            SUM(severity = 'MEDIUM')                        AS medium_cases,
            SUM(severity = 'LOW')                           AS low_cases,
            SUM(corroboration_bonus > 0)                    AS corroborated_cases,
            SUM(sanctioned_amt)                             AS sanctioned_amt,
            SUM(COALESCE(undisbursed_amt, 0))               AS undisbursed_amt,
            SUM(gap_hop IS NULL AND disbursed_amt IS NULL)  AS cases_without_expenditure_row,
            ROUND(AVG(coverage_pct), 2)                     AS mean_coverage_pct,
            MAX(score)                                      AS worst_score
"""

# Every rollup excludes the labelled synthetic control: invariant 12 keeps
# injected rows out of every published aggregate. The control is still
# reachable case by case, where it is labelled on screen.
ROLLUPS = {
    "rollup_state": f"""
        CREATE TABLE rollup_state AS
        SELECT state_id, state,
{_MEASURES},
            COUNT(DISTINCT district) AS districts,
            COUNT(DISTINCT agency_id) AS agencies
        FROM v_case_facts WHERE is_synthetic = 0
        GROUP BY state_id, state
    """,
    "rollup_district": f"""
        CREATE TABLE rollup_district AS
        SELECT state_id, state, district,
{_MEASURES},
            COUNT(DISTINCT agency_id) AS agencies
        FROM v_case_facts WHERE is_synthetic = 0
        GROUP BY state_id, state, district
    """,
    "rollup_agency": f"""
        CREATE TABLE rollup_agency AS
        SELECT state_id, state, district, agency_id, agency,
{_MEASURES}
        FROM v_case_facts WHERE is_synthetic = 0 AND agency_id IS NOT NULL
        GROUP BY state_id, state, district, agency_id, agency
    """,
    "rollup_mp": f"""
        CREATE TABLE rollup_mp AS
        SELECT mp_id, mp_name, mp_house, state_id, state,
{_MEASURES}
        FROM v_case_facts WHERE is_synthetic = 0
        GROUP BY mp_id, mp_name, mp_house, state_id, state
    """,
}

# Indexed on what the endpoints filter by, so a lookup is a seek rather than a
# scan of a table SQLite has no key for.
ROLLUP_INDEXES = (
    "CREATE INDEX ix_rollup_state_state ON rollup_state(state)",
    "CREATE INDEX ix_rollup_district_state ON rollup_district(state)",
    "CREATE INDEX ix_rollup_district_district ON rollup_district(district)",
    "CREATE INDEX ix_rollup_agency_district ON rollup_agency(district)",
    "CREATE INDEX ix_rollup_mp_mp_id ON rollup_mp(mp_id)",
)


def rebuild_rollups(connection) -> int:
    """Drop and recreate the case-facts view and the four rollup tables.

    Returns the number of rollup rows written. Rebuilt rather than appended to,
    the same idiom as everything else in the pipeline: a second run replaces
    its own output. A stale rollup left behind by an older build is the one way
    a dashboard could quietly disagree with the case list it links to, and
    `routers/analytics.py` refuses to serve one that does.
    """
    for name in ROLLUPS:
        connection.execute(text(f"DROP TABLE IF EXISTS {name}"))
    for name in VIEWS:
        connection.execute(text(f"DROP VIEW IF EXISTS {name}"))
    for statement in VIEWS.values():
        connection.execute(text(statement))
    written = 0
    for name, statement in ROLLUPS.items():
        connection.execute(text(statement))
        written += connection.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
    for statement in ROLLUP_INDEXES:
        connection.execute(text(statement))
    return written


# ---------------------------------------------------------------------------
# Reading the corpus
# ---------------------------------------------------------------------------


class CorpusReader:
    """Every row the derivation needs, read once.

    The same shape `ml/run.py` and `ablation/run.py` build for themselves. It
    is repeated rather than imported from `tests/corpus.py` for the reason both
    of those give: a module under `backend/` that imported from `tests/` would
    make the test harness a runtime dependency.
    """

    def __init__(self, session):
        self.session = session
        self.context = derive_mod.CorpusContext.from_session(session)
        self.works = {w.id: w for w in session.scalars(select(Work))}
        self.sanctions = {s.work_id: s for s in session.scalars(select(Sanction))}
        self.completions = {c.work_id: c for c in session.scalars(select(Completion))}
        self.certifications = {c.work_id: c for c in session.scalars(select(Certification))}
        self.payments = defaultdict(list)
        for payment in session.scalars(select(Payment)):
            self.payments[payment.work_id].append(payment)
        self.features = {
            work_pk: derive_mod.derive(
                self.works[work_pk],
                self.sanctions.get(work_pk),
                self.completions.get(work_pk),
                self.certifications.get(work_pk),
                self.payments.get(work_pk, []),
                self.context,
            )
            for work_pk in self.sanctions
        }


def corroboration_peers(reader, rulebook) -> dict:
    """Pass 1: (agency_id, fy) -> the set of work pks whose BASE severity is HIGH.

    Scored with no bonus, because whether a peer is HIGH would otherwise depend
    on its own bonus, which depends on its peers. `engine.score.corroboration`
    describes this two-pass and explains why it cannot perform it for itself.
    """
    peers = defaultdict(set)
    for work_pk, features in reader.features.items():
        if compute(features, rulebook, 0)["severity"] != SEVERITY_HIGH:
            continue
        work = reader.works[work_pk]
        peers[(work.agency_id, work.fy)].add(work_pk)
    return peers


def corroboration_for(reader, peers, work_pk) -> tuple[int, dict]:
    """The count of OTHER HIGH cases under this work's agency and FY, and the evidence.

    A case never corroborates itself, which is why fixture A's count is the 25
    the frozen contract prints and not 26.
    """
    work = reader.works[work_pk]
    others = peers[(work.agency_id, work.fy)] - {work_pk}
    cited = sorted(reader.works[peer].work_id_canon for peer in others)
    return len(others), {
        "agency": reader.context.agency_name.get(work.agency_id),
        "window": f"FY{work.fy}",
        "matched_case_ids": [case_id_for(peer) for peer in cited[:CORROBORATION_CITATION_LIMIT]],
    }


# ---------------------------------------------------------------------------
# Turning scored bodies into rows
# ---------------------------------------------------------------------------


def case_row(case_id, work, body, version_id) -> dict:
    """One `cases` mapping. Every value comes out of `compute()`."""
    return {
        "case_id": case_id,
        "work_id": work.id,
        "score": body["score"],
        "raw_score": body["raw_score"],
        "severity": body["severity"],
        "status": "open",
        "coverage_pct": body["coverage_pct"],
        "gap_hop": body["gap_hop"],
        "slowest_lag": body["slowest_lag"],
        "rulebook_version_id": version_id,
        "corroboration_bonus": body["corroboration"]["contribution"],
        "opened_at": MATERIALISED_AT,
        "is_synthetic": bool(work.is_synthetic),
    }


def rule_hit_rows(case_id, body) -> list[dict]:
    """Ten `rule_hits` mappings per case - fired, passed AND skipped.

    All ten, always. A trace that omitted the passes would not be re-derivable
    and one that omitted the skips would be a lie about what was checked.
    `raw_value` and `threshold` are stringified because the column is text: a
    float, a boolean, an integer and a null have to share it, and `recompute`
    stringifies both sides before comparing so the round trip is exact.
    """
    return [
        {
            "case_id": case_id,
            "rule_id": hit["rule_id"],
            "label": hit["label"],
            "field": hit["field"],
            "raw_value": None if hit["raw_value"] is None else str(hit["raw_value"]),
            "threshold": str(hit["threshold"]),
            "operator": hit["operator"],
            "weight": hit["weight"],
            "contribution": hit["contribution"],
            "severity": hit["severity"],
            "status": hit["status"],
            "skip_reason": hit["skip_reason"],
            "citation_json": (
                None if hit["citation"] is None else json.dumps(hit["citation"], sort_keys=True)
            ),
            "caveat": hit["caveat"],
        }
        for hit in body["rule_hits"]
    ]


def audit_payloads(case_id, work, body) -> list[tuple[str, dict]]:
    """The (event, payload) pairs one freshly opened case writes to the trail.

    Four of the ten event types in DOMAIN-MODEL.md (j) are written here; the
    other six belong to an officer's session, to a rulebook edit or to ingest.

    **`CASE_OPENED` carries the corroboration block, and that is where the
    block lives.** `cases` stores whether the bonus was awarded and not the
    count behind it, because - as `engine/score.py` puts it - the count was a
    fact about the corpus on the day rather than a fact about this work. The
    case sheet reads the block back off this row, so the number an officer sees
    is the number that was written down when the case was opened.
    """
    events = [
        (
            EVENT_CASE_OPENED,
            {
                "work_id": work.work_id_canon,
                "score": body["score"],
                "raw_score": body["raw_score"],
                "severity": body["severity"],
                "coverage_pct": body["coverage_pct"],
                "gap_hop": body["gap_hop"],
                "slowest_lag": body["slowest_lag"],
                "rulebook_version": body["rulebook_version"],
                "corroboration": body["corroboration"],
                "is_synthetic": bool(work.is_synthetic),
            },
        )
    ]
    for hit in body["rule_hits"]:
        if hit["status"] != RULE_STATUS_FIRED:
            continue
        events.append(
            (
                EVENT_RULE_FIRED,
                {
                    "rule_id": hit["rule_id"],
                    "field": hit["field"],
                    "raw_value": hit["raw_value"],
                    "operator": hit["operator"],
                    "threshold": hit["threshold"],
                    "contribution": hit["contribution"],
                },
            )
        )
        if hit["citation"] is not None:
            events.append(
                (
                    EVENT_DUPLICATE_LINKED,
                    {
                        "rule_id": hit["rule_id"],
                        "matched_work_ids": hit["citation"].get("matched_work_ids"),
                        "cluster_size": hit["citation"].get("cluster_size"),
                        "similarity": hit["citation"].get("similarity"),
                        "method": hit["citation"].get("method"),
                    },
                )
            )
    bonus = body["corroboration"]
    if bonus["applied"]:
        events.append(
            (
                EVENT_PATTERN_LINKED,
                {
                    "agency": bonus.get("agency"),
                    "window": bonus.get("window"),
                    "high_case_count": bonus.get("high_case_count"),
                    "matched_case_ids": bonus.get("matched_case_ids"),
                    "contribution": bonus.get("contribution"),
                },
            )
        )
    return events


def chain(rows) -> list[dict]:
    """Hash-chain a batch of audit events into `audit_log` mappings.

    `engine.audit.log` chains one row at a time and re-reads the tail of the
    table to find its predecessor - correct for an officer's note, and 85,000
    round trips for a build. The hash function itself is imported from that
    module rather than restated here, so a chain written by this file and a row
    appended by an endpoint are links of the same chain and `verify_chain`
    walks both without knowing which wrote what.
    """
    out = []
    previous = None
    for case_id, event, payload in rows:
        payload_json = audit_mod._canonical(payload) if payload is not None else None
        digest = audit_mod.row_hash(
            previous, MATERIALISED_AT, SEED_ROLE, None, event, case_id, payload_json
        )
        out.append(
            {
                "at": MATERIALISED_AT,
                "actor_role": SEED_ROLE,
                "actor_id": None,
                "event": event,
                "case_id": case_id,
                "payload_json": payload_json,
                "prev_hash": previous,
                "row_hash": digest,
            }
        )
        previous = digest
    return out


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------


def materialise(session, progress=None) -> dict:
    """Derive, score and store every case. Returns the counts it wrote.

    Calling this twice on the same corpus produces the same case count, the
    same score for every case and the same audit hash chain, because the four
    tables it owns are rebuilt and every timestamp it writes is `DATA_AS_OF`.
    """
    say = progress or (lambda _message: None)

    yaml_text = rulebook_mod.RULES_PATH.read_text(encoding="utf-8")
    rulebook = rulebook_mod.validate(rulebook_mod.loads(yaml_text), derive_mod.FEATURE_KEYS)

    say("reading the corpus and deriving features ...")
    reader = CorpusReader(session)

    say(f"scoring {len(reader.features):,} sanctioned works, pass 1 of 2 ...")
    peers = corroboration_peers(reader, rulebook)

    say("scoring pass 2 of 2, with the corroboration bonus resolved ...")
    cases: list[dict] = []
    hits: list[dict] = []
    events: list[tuple] = []
    for work_pk in sorted(reader.features):
        work = reader.works[work_pk]
        case_id = case_id_for(work.work_id_raw)
        count, evidence = corroboration_for(reader, peers, work_pk)
        body = compute(reader.features[work_pk], rulebook, count, evidence)
        cases.append(case_row(case_id, work, body, version_id=1))
        hits.extend(rule_hit_rows(case_id, body))
        events.extend((case_id, event, payload) for event, payload in audit_payloads(case_id, work, body))

    # Ordered by case id so the hash chain is a property of the corpus rather
    # than of the order SQLite happened to return rows in.
    cases.sort(key=lambda row: row["case_id"])
    hits.sort(key=lambda row: row["case_id"])
    events.sort(key=lambda row: row[0])
    audit_rows = chain(events)

    say("rebuilding cases, rule_hits, rulebook_versions and audit_log ...")
    session.commit()
    bind = session.get_bind()
    for model in REBUILT_TABLES:
        model.__table__.drop(bind, checkfirst=True)
    for model in reversed(REBUILT_TABLES):
        model.__table__.create(bind)

    session.add(
        RulebookVersion(
            id=1,
            version=rulebook.get("version"),
            yaml_snapshot=yaml_text,
            yaml_sha256=hashlib.sha256(yaml_text.encode("utf-8")).hexdigest(),
            created_at=MATERIALISED_AT,
            created_by_role=SEED_ROLE,
            note=SEED_NOTE,
        )
    )
    session.flush()
    session.bulk_insert_mappings(Case, cases)
    session.bulk_insert_mappings(RuleHit, hits)
    session.bulk_insert_mappings(AuditLog, audit_rows)
    session.commit()

    # The session's own bind, not the module-level engine, so a test can drive
    # the whole build against a copied database by handing in a session on it.
    say("rebuilding the case-facts view and the four rollup tables ...")
    with bind.begin() as connection:
        rollup_rows = rebuild_rollups(connection)

    return {
        "rulebook_version": rulebook.get("version"),
        "cases": len(cases),
        "rule_hits": len(hits),
        "audit_rows": len(audit_rows),
        "rollup_rows": rollup_rows,
        "bands": {
            band: sum(1 for row in cases if row["severity"] == band and not row["is_synthetic"])
            for band in ("HIGH", "MEDIUM", "LOW")
        },
        "corroborated": sum(
            1 for row in cases if row["corroboration_bonus"] and not row["is_synthetic"]
        ),
        "synthetic": sum(1 for row in cases if row["is_synthetic"]),
    }


def main() -> int:
    print(
        "python -m app.derive_all rebuilds cases, rule_hits, rulebook_versions and\n"
        "audit_log from the ingested corpus. Any note or recompute recorded against\n"
        "the current cases goes with them. Run it when the corpus or the rulebook\n"
        "changes, not to refresh a screen.\n"
    )
    session = SessionLocal()
    try:
        counts = materialise(session, progress=lambda message: print(message, flush=True))
    finally:
        session.close()

    print(
        f"\n  rulebook      {counts['rulebook_version']} snapshotted into rulebook_versions"
        f"\n  cases         {counts['cases']:,}  "
        f"({counts['bands']['HIGH']:,} HIGH, {counts['bands']['MEDIUM']:,} MEDIUM, "
        f"{counts['bands']['LOW']:,} LOW, over real works)"
        f"\n  corroborated  {counts['corroborated']:,} cases carry the agency pattern bonus"
        f"\n  synthetic     {counts['synthetic']} labelled control excluded from every band count"
        f"\n  rule_hits     {counts['rule_hits']:,}  (ten per case: fired, passed and skipped)"
        f"\n  audit_log     {counts['audit_rows']:,} rows, hash-chained"
        f"\n  rollups       {counts['rollup_rows']:,} rows across {len(ROLLUPS)} rebuilt "
        f"rollup tables, over v_case_facts"
    )
    print(
        "\nEvery score above is the sum of fired rulebook weights plus the corroboration "
        "bonus and nothing else (CLAUDE.md invariant 1). Nothing was computed in this "
        "file: it stores what engine.score.compute returned."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
