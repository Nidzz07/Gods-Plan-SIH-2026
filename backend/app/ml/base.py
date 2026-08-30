"""What every ML module in this package shares: a finding, and a version.

Three things live here so the four modules cannot spell them differently.

**`Finding`** is one `ml_findings` row before it becomes one. It carries a
value OR the reason the value is missing, never neither and never both, because
a badge that could not be computed is `not_applicable` and not zero (CLAUDE.md
invariant 2). The reason travels in `payload_json` under `availability`, since
`ml_findings` has no availability companion column of its own and this phase
does not touch `models.py`.

**`model_version`** is a digest of everything that determines the output: the
method, the parameters, the threshold read from the rulebook, and the size of
the population the model saw. A forecast whose model version an auditor cannot
trace back to a fit is a number nobody can check, which is the same objection
invariant 5 raises against a recompute that reads today's rules.yaml.

**`rebuild`** rewrites `ml_findings` from scratch. It drops and recreates the
table and then inserts, which is exactly the idiom `ingest/run.py` uses on the
whole corpus - idempotent by rebuild, not by append, so a second run does not
double its own output.

It is deliberately DDL and not a row delete. CLAUDE.md invariant 4 forbids any
helper anywhere in `backend/` capable of updating or removing a row, and
`tests/test_audit.py` enforces that by walking every file under `backend/` for
the construct shapes rather than for `audit_log` by name. That test is written
as an absolute on purpose, and the right response to it is to obey it rather
than to carve out an exception for a table that happens to be a cache. The
whole table goes and comes back, the way the corpus does.

One consequence is worth stating: `rebuild` takes EVERY kind at once. Rebuilding
one kind at a time would drop the other three, so the signature does not offer
the option.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from ..constants import ML_KINDS, Availability


@dataclass(frozen=True)
class Finding:
    """One model output about one work, on its way to `ml_findings`.

    `work_pk` is `works.id`, the integer primary key the table's foreign key
    points at - not the portal work id, which lives in the payload where a
    reader needs it.

    `value` is None exactly when `availability` is not `published`. A finding
    that carries both, or neither, is a bug and `__post_init__` says so rather
    than writing a row an officer would have to guess at.
    """

    work_pk: int
    kind: str
    value: float | None
    availability: Availability
    payload: dict = field(default_factory=dict)
    model_version: str = ""
    contributes_to_score: bool = False

    def __post_init__(self) -> None:
        if self.kind not in ML_KINDS:
            raise ValueError(f"unknown ml_findings kind {self.kind!r}; expected one of {ML_KINDS}")
        published = self.availability == Availability.PUBLISHED
        if published and self.value is None:
            raise ValueError(
                f"{self.kind} finding for work {self.work_pk} is marked published with no value. "
                "A badge that could not be computed carries the reason it could not "
                "(CLAUDE.md invariant 2), never a bare null."
            )
        if not published and self.value is not None:
            raise ValueError(
                f"{self.kind} finding for work {self.work_pk} carries a value of {self.value!r} "
                f"under availability {self.availability.value!r}. A value that was measured is "
                "`published`; anything else would let a reason and a reading disagree."
            )

    def as_row(self) -> dict:
        """The column values for one `ml_findings` insert.

        The availability rides inside `payload_json` because `ml_findings` has
        no companion column, and it is written FIRST in the dict so that a
        human opening the JSON in a database client reads the reason before
        the detail.
        """
        payload = {"availability": self.availability.value, **self.payload}
        return {
            "work_id": self.work_pk,
            "kind": self.kind,
            "value": self.value,
            "payload_json": json.dumps(payload, sort_keys=True, default=str),
            "model_version": self.model_version,
            "contributes_to_score": self.contributes_to_score,
        }


def by_work(findings) -> dict:
    """Index findings by work pk. Lives here rather than beside the badge
    blocks, because indexing a list of findings is a property of a finding and
    not of the case body they end up in."""
    return {finding.work_pk: finding for finding in findings}


def model_version(prefix: str, **parts) -> str:
    """`<prefix>-<12 hex>`, digesting everything that determines the output.

    Two fits that saw the same population under the same parameters produce the
    same string; changing a threshold, a feature list, a random seed or the
    number of training rows changes it. That is what lets a stored badge be
    traced to the fit that produced it months later, rather than to "the model,
    whichever one that was".
    """
    canonical = json.dumps(parts, sort_keys=True, default=str).encode()
    return f"{prefix}-{hashlib.sha256(canonical).hexdigest()[:12]}"


def rebuild(session, findings) -> int:
    """Drop `ml_findings`, recreate it, and write every finding. Returns the count.

    Idempotent by rebuild, the way `ingest/run.py` is: the table goes and comes
    back, so a second run does not double its own output and a missing table is
    not a special case. See the module docstring for why this is DDL rather
    than a row delete.

    Takes every kind at once. A per-kind call would drop the other three.
    """
    from ..models import MLFinding

    rows = []
    for finding in findings:
        if finding.kind not in ML_KINDS:
            raise ValueError(
                f"unknown ml_findings kind {finding.kind!r}; expected one of {ML_KINDS}"
            )
        rows.append(finding.as_row())

    session.commit()
    bind = session.get_bind()
    MLFinding.__table__.drop(bind, checkfirst=True)
    MLFinding.__table__.create(bind)
    if rows:
        session.bulk_insert_mappings(MLFinding, rows)
    session.commit()
    return len(rows)
