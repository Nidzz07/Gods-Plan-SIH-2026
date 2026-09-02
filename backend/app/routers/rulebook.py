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

`POST /api/rulebook` is the write side, and it is Ministry-only. It CREATES a
version and never mutates one (invariant 5): the edit is snapshotted into
`rulebook_versions` with its own sha256, the file on disk is rewritten, and
every case already in the database goes on referencing the snapshot it was
scored under until somebody explicitly recomputes it. That is the same
"observation, not correction" rule `engine/audit.recompute` follows, applied one
level up - an edit records a new intention, it does not retroactively restate
what was found last month.

**Nothing here rescores anything, and the response says so as a number.** An
officer who has just changed a threshold may reasonably assume the corpus moved
with it. It did not. `cases_rescored` is in the response body, always zero, so
the screen can print it rather than leaving the assumption to form in silence.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..constants import ROLE_MINISTRY
from ..db import get_db
from ..engine import derive as derive_mod
from ..engine.audit import log as audit_log
from ..engine.rulebook import RULES_PATH, load, loads, severity_bands, validate, weight_total
from ..models import Case, RulebookVersion, User
from ..rulebook_edit import (
    RuleEdit,
    RulebookEditError,
    apply_edits,
    edited_against,
    next_version,
    validated,
)
from ..schemas import RulebookChange, RulebookEditIn, RulebookEditOut

router = APIRouter(prefix="/rulebook", tags=["rulebook"])

EVENT_RULEBOOK_UPDATED = "RULEBOOK_UPDATED"

RECOMPUTE_HINT = (
    "No case was rescored. Existing cases keep the rulebook snapshot they were scored "
    "under until each is recomputed individually from its own case sheet, or until "
    "`python -m app.derive_all` rebuilds the corpus against this file."
)


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
        # Which rules the file and the cases now disagree about, by id.
        #
        # `file_matches_stored_version` already says THAT they disagree; this
        # says WHERE, and the difference matters on screen. Every threshold in
        # the shipped file carries a comment naming the count it fired on over
        # the profiled sample (invariant 6), so the moment one is edited that
        # comment describes a value the file no longer holds and the cases in
        # front of the officer were scored under the old one. Naming the rules
        # lets the editor mark those rows instead of showing one banner over a
        # table of ten and leaving the reader to diff two YAML blobs.
        "rules_edited_since_scoring": (
            edited_against(book, loads(scored_under.yaml_snapshot))
            if scored_under is not None
            else []
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


@router.post("", response_model=RulebookEditOut, status_code=201)
def edit_rulebook(
    edit: RulebookEditIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(ROLE_MINISTRY)),
):
    """Apply a threshold/weight edit, snapshot it as a NEW version, rescore nothing.

    Ministry-only. DOMAIN-MODEL.md (k) has `rulebook_versions` as "all, **write**"
    for the ministry and "all, read" for the other three, and that asymmetry is
    the whole reason the rulebook is readable by everyone: an officer judged by
    a rule is entitled to read it, and entitled NOT to be the one who can move
    it under themselves.

    **The order of operations is not arbitrary.** The edit is applied in memory
    and validated against the derived feature dictionary first, so a rulebook
    that would not load never reaches the disk. The version row and the audit
    event are added next, inside the open transaction. Only then is the file
    rewritten, and if that write fails the transaction rolls back and the
    original text is restored - so the file and `rulebook_versions` cannot end
    up describing different rulebooks through a half-completed edit.

    **What this endpoint does NOT do**, said here because both would be
    reasonable guesses:

    * It does not rescore. Not one case. `cases_rescored` is in the response,
      always zero, and the stored cases keep pointing at the snapshot they were
      scored under (invariant 5). A recompute is a separate, deliberate,
      per-case action that re-derives against the case's OWN snapshot.
    * It does not change how a score is computed. It moves numbers in a
      document that `engine/score.py` reads. No model output becomes a scoring
      input because a threshold moved (invariant 1); the four tiers are exactly
      where they were.
    """
    original = RULES_PATH.read_text(encoding="utf-8")

    if not edit.rules and edit.severity_bands is None and edit.corroboration_weight is None:
        raise HTTPException(status_code=422, detail="The edit changes nothing.")

    current = loads(original)
    previous_version = str(current.get("version") or "")

    # Unique across `rulebook_versions`, so a corpus rebuilt under a version
    # string that already exists cannot collide with it silently.
    taken = {row for (row,) in db.execute(select(RulebookVersion.version))}
    version = next_version(previous_version)
    while version in taken:
        version = next_version(version)

    try:
        text, changes = apply_edits(
            original,
            [
                RuleEdit(rule_id=rule.rule_id, threshold=rule.threshold, weight=rule.weight)
                for rule in edit.rules
            ],
            severity_bands=edit.severity_bands.model_dump() if edit.severity_bands else None,
            corroboration_weight=edit.corroboration_weight,
            version=version,
        )
        # The same validator a file on disk is held to, so an edit cannot be
        # admitted under looser rules than a hand-written rulebook would be.
        validated(text, derive_mod.FEATURE_KEYS)
    except RulebookEditError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not changes:
        raise HTTPException(
            status_code=422,
            detail="Every value in the edit already holds. Nothing would change.",
        )

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    row = RulebookVersion(
        version=version,
        yaml_snapshot=text,
        yaml_sha256=digest,
        created_at=datetime.utcnow(),
        created_by_role=user.role,
        note=edit.note.strip(),
    )
    db.add(row)

    audit_log(
        db,
        EVENT_RULEBOOK_UPDATED,
        user.role,
        actor_id=user.id,
        payload={
            "version": version,
            "previous_version": previous_version,
            "yaml_sha256": digest,
            "note": edit.note.strip(),
            "changes": changes,
            # Recorded on the event itself so an auditor reading the trail sees
            # that the edit rescored nothing, without having to know that from
            # elsewhere.
            "cases_rescored": 0,
        },
    )

    try:
        _write_atomically(text)
    except OSError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"the rulebook could not be written: {exc}"
        ) from exc

    try:
        db.commit()
    except Exception:
        # The file is already on disk at this point, so put it back rather than
        # leaving a rulebook nothing snapshotted.
        RULES_PATH.write_text(original, encoding="utf-8")
        raise

    db.refresh(row)
    return RulebookEditOut(
        version=version,
        previous_version=previous_version,
        yaml_sha256=digest,
        rulebook_version_id=row.id,
        changes=[RulebookChange(**change) for change in changes],
        cases_rescored=0,
        note=row.note,
        recompute_hint=RECOMPUTE_HINT,
    )


def _write_atomically(text: str) -> None:
    """Write `rules.yaml` through a temporary file in the same directory.

    `rules.yaml` is the only source of score in the product and it is read from
    disk on every evaluation. A partial write - the process dying mid-`write` -
    would leave the file unparseable and every subsequent evaluation raising, so
    the new text lands beside it first and is moved into place in one operation.
    Same directory, because a rename across filesystems is not atomic.
    """
    temporary = RULES_PATH.with_suffix(".yaml.tmp")
    # newline="" so the bytes written are exactly the bytes composed. Without
    # it Python translates every line feed to the platform separator, which on
    # Windows silently rewrites all 250 lines of the file on the first edit -
    # a whole-file diff in version control, and a stored snapshot that no
    # longer matches the file it was taken from byte for byte.
    with open(temporary, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    temporary.replace(RULES_PATH)
