"""F6 - the append-only audit trail, and true re-derivation.

Insert is the only operation this module performs. There is no helper here to
edit a row and none to remove one, and there must never be one anywhere in
`backend/` (CLAUDE.md invariant 4). A trail that can be rewritten proves
nothing, and the whole claim NIGRANI makes to an auditor is that a score can be
re-derived months later from what was written on the day.

Every row is hash-chained: `row_hash` is the sha256 of the row's own content
together with the previous row's hash, so removing or altering a row breaks
every hash after it. That makes a tamper visible even to someone who reaches
the SQLite file directly with a generic client.

**The defect this port fixes.** The inherited `recompute()` compared a stored
case against a fresh derivation read from the rulebook file ON DISK, and it
compared five scalar fields. Both halves were wrong for NIGRANI. A recompute
must re-derive against the rulebook SNAPSHOT the case was scored under, stored
in `rulebook_versions.yaml_snapshot` and reached through
`cases.rulebook_version_id` (invariant 5), because otherwise an officer editing
a threshold in March silently rewrites what a case in January is claimed to
have said. And it must compare the FULL trace - every rule id, raw value,
threshold, operator, weight, contribution, status and skip reason - because an
auditor's question is never "did the number move", it is "which rule moved, and
why". A case whose score is unchanged while two rules swapped their
contributions has changed, and a five-field comparison would call it identical.

`recompute()` is an observation, not a correction. It records what it found
next to what was stored and leaves the stored case exactly as it was. If the
two disagree, the disagreement IS the finding; overwriting the old score would
destroy the evidence that anything moved.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sqlalchemy import select

from ..models import AuditLog, RuleHit, RulebookVersion

# Event vocabulary lives in app.constants.AUDIT_EVENTS; these are the ones this
# module writes for itself.
EVENT_SCORE_RECOMPUTED = "SCORE_RECOMPUTED"

# The scalar fields quoted in the recompute summary. They are a HEADLINE over
# the trace comparison, never a substitute for it: `recompute()` compares the
# full trace and reports these alongside so an officer sees the number first.
COMPARED_FIELDS = (
    "score",
    "raw_score",
    "severity",
    "coverage_pct",
    "gap_hop",
    "slowest_lag",
    "rulebook_version",
)

# The trace columns compared row by row. Everything that could change a score,
# and everything that explains why it did not.
TRACE_FIELDS = (
    "rule_id",
    "field",
    "raw_value",
    "operator",
    "threshold",
    "weight",
    "contribution",
    "severity",
    "status",
    "skip_reason",
)


def _canonical(payload) -> str:
    """Stable JSON for hashing: sorted keys, no incidental whitespace."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def row_hash(prev_hash, at, actor_role, actor_id, event, case_id, payload_json) -> str:
    """sha256 over this row's content plus the previous row's hash.

    Recomputable by hand from the stored columns, which is the point: an
    auditor can walk the chain with a shell one-liner and does not have to
    trust this function to have run.
    """
    return hashlib.sha256(
        _canonical(
            {
                "prev_hash": prev_hash,
                "at": at,
                "actor_role": actor_role,
                "actor_id": actor_id,
                "event": event,
                "case_id": case_id,
                "payload_json": payload_json,
            }
        ).encode()
    ).hexdigest()


def log(session, event, actor_role, case_id=None, actor_id=None, payload=None, at=None):
    """Append one event to the trail. The caller commits.

    The payload is JSON-encoded rather than spread across columns so that an
    event written today stays readable after the payload shape of its event
    type has moved on. An old row must never need a migration to be understood.

    The flush is load-bearing. Sessions here are built with `autoflush=False`,
    so a row that has been added but not yet committed is invisible to the
    SELECT below - and scoring one case writes CASE_OPENED, RULE_FIRED,
    DUPLICATE_LINKED and PATTERN_LINKED before anyone commits (DOMAIN-MODEL.md
    section j). Without the flush every row in such a batch would read the same
    predecessor, take `prev_hash = None`, and the chain would silently not
    form. Flushing is not committing: the caller still owns the transaction and
    can still roll the whole batch back.
    """
    session.flush()
    previous = session.scalar(select(AuditLog).order_by(AuditLog.id.desc()).limit(1))
    at = at or datetime.utcnow()
    payload_json = _canonical(payload) if payload is not None else None
    prev = previous.row_hash if previous is not None else None
    row = AuditLog(
        at=at,
        actor_role=actor_role,
        actor_id=actor_id,
        event=event,
        case_id=case_id,
        payload_json=payload_json,
        prev_hash=prev,
        row_hash=row_hash(prev, at, actor_role, actor_id, event, case_id, payload_json),
    )
    session.add(row)
    return row


def verify_chain(session) -> dict:
    """Walk the chain and report the first row whose hash does not hold.

    Returns {"rows": n, "intact": bool, "broken_at": id|None}. Nothing is
    repaired: a broken chain is evidence, and evidence is not tidied up.
    """
    prev = None
    broken = None
    count = 0
    for row in session.scalars(select(AuditLog).order_by(AuditLog.id)):
        count += 1
        expected = row_hash(
            prev, row.at, row.actor_role, row.actor_id, row.event, row.case_id, row.payload_json
        )
        if broken is None and (row.prev_hash != prev or row.row_hash != expected):
            broken = row.id
        prev = row.row_hash
    return {"rows": count, "intact": broken is None, "broken_at": broken}


def summarise(case_or_body) -> dict:
    """The comparable headline of a case, from a stored row or a fresh derivation."""
    if isinstance(case_or_body, dict):
        return {field: case_or_body.get(field) for field in COMPARED_FIELDS}
    return {field: getattr(case_or_body, field, None) for field in COMPARED_FIELDS}


def summarise_trace(rule_hits) -> list[dict]:
    """The comparable form of a full trace, from stored rows or fresh dicts.

    Stored `rule_hits.raw_value` and `threshold` are text columns, so both
    sides are rendered through the same stringification before comparison. A
    stored `-40.01` and a fresh `-40.01` must compare equal without the
    comparison depending on which side came out of SQLite.
    """
    rows = []
    for hit in rule_hits or []:
        source = hit if isinstance(hit, dict) else None
        row = {}
        for field in TRACE_FIELDS:
            value = source.get(field) if source is not None else getattr(hit, field, None)
            row[field] = None if value is None else str(value)
        rows.append(row)
    return sorted(rows, key=lambda row: row["rule_id"] or "")


def snapshot_for(session, case) -> tuple[str, str]:
    """The rulebook a case was SCORED UNDER, not the one on disk today.

    Returns (version, yaml_snapshot) read through `cases.rulebook_version_id`.
    Raises if the version row is gone, because scoring against today's file
    instead is the exact defect this port exists to fix (invariant 5).
    """
    version = session.get(RulebookVersion, case.rulebook_version_id)
    if version is None:
        raise LookupError(
            f"case {case.case_id} references rulebook version id "
            f"{case.rulebook_version_id}, which no longer exists. A recompute cannot fall "
            "back to the current rules.yaml: that would re-derive the case against a "
            "rulebook it was never scored under (CLAUDE.md invariant 5)."
        )
    return version.version, version.yaml_snapshot


def recompute(session, case, derive_features, actor_role="ministry", actor_id=None):
    """Re-derive one stored case against its own rulebook snapshot and record it.

    `derive_features` is a zero-argument callable returning the `FeatureSet` for
    the case's work. It is injected rather than looked up here so that this
    module needs no knowledge of the corpus context, and so a test can drive a
    recompute without a loaded database.

    Returns {stored, recomputed, identical, trace_diff, rulebook_version}, and
    writes exactly one SCORE_RECOMPUTED row carrying the before and after
    trace - not merely the before and after number. The stored case is left
    untouched whatever the comparison says.
    """
    from .rulebook import loads
    from .score import compute

    version, yaml_snapshot = snapshot_for(session, case)
    rulebook = loads(yaml_snapshot)

    fresh = compute(derive_features(), rulebook, _bonus_count(case))
    stored_hits = session.scalars(
        select(RuleHit).where(RuleHit.case_id == case.case_id)
    ).all()

    stored_summary = summarise(case)
    stored_summary["rulebook_version"] = version
    fresh_summary = summarise(fresh)

    stored_trace = summarise_trace(stored_hits)
    fresh_trace = summarise_trace(fresh["rule_hits"])
    trace_diff = diff_traces(stored_trace, fresh_trace)

    outcome = {
        "stored": stored_summary,
        "recomputed": fresh_summary,
        "identical": stored_summary == fresh_summary and not trace_diff,
        "trace_diff": trace_diff,
        "stored_trace": stored_trace,
        "recomputed_trace": fresh_trace,
        "rulebook_version": version,
    }
    log(
        session,
        EVENT_SCORE_RECOMPUTED,
        actor_role,
        case_id=case.case_id,
        actor_id=actor_id,
        payload=outcome,
    )
    return outcome


def _bonus_count(case) -> int:
    """The corroboration count implied by a stored case.

    A stored case records whether the bonus was awarded, not the count behind
    it, so a recompute reproduces the award it was given rather than re-running
    the corpus-wide two-pass. The count behind the original award is in the
    PATTERN_LINKED audit row for the case, where it belongs: it was a fact
    about the corpus on the day, not about this work.
    """
    from ..constants import CORROBORATION_MIN_HIGH_CASES

    return CORROBORATION_MIN_HIGH_CASES if case.corroboration_bonus else 0


def diff_traces(stored_trace, fresh_trace) -> list[dict]:
    """Which rules moved, and in what. Empty list means the trace re-derived.

    Reported per rule and per field, so an auditor reads "duplicate_work's
    threshold moved from 0.85 to 0.92 and its status from fired to passed"
    rather than "the score changed by 18".
    """
    stored_by_rule = {row["rule_id"]: row for row in stored_trace}
    fresh_by_rule = {row["rule_id"]: row for row in fresh_trace}
    differences = []
    for rule_id in sorted(set(stored_by_rule) | set(fresh_by_rule)):
        before = stored_by_rule.get(rule_id)
        after = fresh_by_rule.get(rule_id)
        if before is None or after is None:
            differences.append(
                {
                    "rule_id": rule_id,
                    "field": None,
                    "stored": None if before is None else "present",
                    "recomputed": None if after is None else "present",
                }
            )
            continue
        for field in TRACE_FIELDS:
            if before[field] != after[field]:
                differences.append(
                    {
                        "rule_id": rule_id,
                        "field": field,
                        "stored": before[field],
                        "recomputed": after[field],
                    }
                )
    return differences
