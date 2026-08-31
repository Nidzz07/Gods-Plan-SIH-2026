"""Rulebook endpoint - F2's surface.

Reads through `engine/rulebook.load()` at request time, so an officer editing
`rules.yaml` sees the change on the next refresh without a restart and without
a code change. That is the feature and not a convenience: the thresholds belong
to MoSPI.

**The parsed YAML is returned as-is, with no response model, and the inherited
reason still holds.** A response model would pin the rulebook's shape in Python,
which is exactly the coupling this feature exists to avoid: add a `unit`, a
`caveat` or a `skip_caveats` block to a rule in the YAML and it should reach
the screen on its own. The trace rows in `case_detail.json` ARE modelled,
because a trace is a finding about a work and the frontend renders it column by
column; the rulebook is a document the officer owns.

Two things are added to the parsed file rather than left implicit, and neither
comes out of the YAML:

* `versions` - what is actually stored in `rulebook_versions`, with the sha256
  of each snapshot. A case is scored under a stored snapshot, never under the
  file, so a screen that showed only the file could not tell an officer that
  the cases in front of them were scored under something else.
* `file_matches_stored_version` - whether the file on disk still hashes to the
  snapshot the current cases were scored under. False is a real and useful
  answer: it means somebody has edited `rules.yaml` since the last
  `python -m app.derive_all`, and the case list is showing scores from the
  older rulebook until the build step is re-run.

**Readable by all four roles, deliberately, and that is a scoping decision
rather than an omission.** The rulebook is the document by which a work is being
judged: an officer whose district carries a flagged case, and a member whose
recommendation carries one, are both entitled to read the rule that produced it
and check the arithmetic. A rulebook only its author may read is not an
explainable system, it is an assertion. It names no state, district, agency or
member, so there is nothing here to scope by - which is why this router takes
`get_current_user` and no predicate. DOMAIN-MODEL.md (k) already says as much:
`rulebook_versions` is "all, read" for three roles and "all, write" for the
ministry.

`PUT /api/rulebook`, which creates a new version and never mutates one, is a
later phase; when it lands it is Ministry-only, and the auth added in Phase 6 is
what makes "which officer changed it" answerable at all. Nothing here writes.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..engine import derive as derive_mod
from ..engine.rulebook import RULES_PATH, load, severity_bands, validate, weight_total
from ..models import Case, RulebookVersion, User

router = APIRouter(prefix="/rulebook", tags=["rulebook"])


@router.get("")
def get_rulebook(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """The rulebook in force, its stored versions, and whether they agree.

    Validated against the derived feature dictionary before it is returned, so
    a rule naming a field `engine/derive.py` does not produce is a 500 here
    rather than a silent skip on every case - which is the same choice
    `engine/rulebook.validate` makes at load time and for the same reason.
    """
    text = RULES_PATH.read_text(encoding="utf-8")
    book = validate(load(), derive_mod.FEATURE_KEYS)
    file_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()

    versions = db.scalars(
        select(RulebookVersion).order_by(RulebookVersion.id.desc())
    ).all()
    scored_under = db.scalar(
        select(RulebookVersion)
        .join(Case, Case.rulebook_version_id == RulebookVersion.id)
        .limit(1)
    )

    high, medium = severity_bands(book)
    return {
        **book,
        "file_sha256": file_sha256,
        "rule_weight_total": weight_total(book),
        "severity_bands_resolved": {"high": high, "medium": medium},
        "cases_scored_under": (
            {"version": scored_under.version, "yaml_sha256": scored_under.yaml_sha256}
            if scored_under is not None
            else None
        ),
        "file_matches_stored_version": (
            scored_under is not None and scored_under.yaml_sha256 == file_sha256
        ),
        "versions": [
            {
                "id": version.id,
                "version": version.version,
                "yaml_sha256": version.yaml_sha256,
                "created_at": version.created_at,
                "created_by_role": version.created_by_role,
                "note": version.note,
            }
            for version in versions
        ],
    }
