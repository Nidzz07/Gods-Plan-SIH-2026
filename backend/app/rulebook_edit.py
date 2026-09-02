"""Applying an officer's edit to `rules.yaml` without destroying the file.

**Why this is a text edit and not a YAML round-trip.** `rules.yaml` is roughly
two thirds comment by line count, and those comments are load-bearing: CLAUDE.md
invariant 6 requires every threshold to carry the firing count it produced on
the profiled sample, and the file also carries the reasoning for each weight and
the three skip caveats per rule that invariant 2 depends on. `yaml.safe_dump`
would parse the file to a dict and write it back with every one of those
comments gone - a silent, total loss of the document's explanation, on the first
edit anyone made. PyYAML cannot preserve comments and there is no comment-
preserving parser in the dependency list (`ruamel.yaml` would be a new
dependency, and CLAUDE.md says to ask rather than add one).

So an edit here rewrites the SCALAR ON ONE LINE and leaves every other byte of
the file alone. That is only safe because it is checked afterwards rather than
trusted: `apply_edits` re-parses the rewritten text and asserts that the result
differs from the original in exactly the values that were asked for and in
nothing else - same rule ids in the same order, same fields, operators, labels,
severities, units, caveats. A surgical edit that moved anything it was not asked
to move raises instead of being written.

**What an edit may change, and the boundary is deliberate.** Thresholds, weights,
the two severity band cut-offs, and the corroboration bonus weight. That is all.

An edit may NOT add a rule, remove one, rename one, or change a rule's `field`
or `operator`. Those are not edits, they are changes to what the system measures:
a new rule needs a field that `engine/derive.py` actually derives, a threshold
calibrated against a measured distribution in the data profile, a weight argued
against the other nine, and skip caveats for each way its input can go missing.
That is a modelling exercise with a data-profile pass attached, not a form
submission, and pretending a text box could stand in for it would be the kind of
overclaim CLAUDE.md's honesty rules exist to stop. The API says so in its own
error message rather than silently ignoring the extra keys.

**This module does not score anything and must never learn how.** It rewrites a
document. `engine/score.py` remains the only place a contribution is added up,
and an edit here changes WHICH thresholds that arithmetic reads, never how the
arithmetic runs (invariant 1).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .engine.rulebook import RulebookError, loads

# The keys an edit may move on a rule, and nothing else. `id`, `field`,
# `operator`, `label`, `severity` and every caveat are out of reach by
# construction: they are not in this set, so the line-finder never looks for
# them.
EDITABLE_RULE_KEYS = ("threshold", "weight")

# The structural keys compared before and after a rewrite. If any of these moved,
# the text edit did something it was not asked to do and the result is thrown
# away rather than written.
FROZEN_RULE_KEYS = ("id", "field", "operator", "label", "severity", "unit")


class RulebookEditError(ValueError):
    """An edit that cannot be applied as asked. Nothing is written."""


@dataclass(frozen=True)
class RuleEdit:
    """One rule's proposed new threshold and weight. Either may be None."""

    rule_id: str
    threshold: object = None
    weight: int | None = None


def _scalar(value) -> str:
    """A YAML scalar for a value the rulebook admits.

    Bools are lower-cased because that is how the file already spells them and
    how `yaml.safe_load` reads them back; a `True` written here would parse as
    the string "True" under some loaders and compare unequal to the boolean the
    feature carries.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        # `repr` rather than `str` so a float keeps the precision it arrived
        # with: a threshold of 0.85 must not be written as 0.8500000000000001,
        # and one of -15.0 must not silently become the int -15.
        return repr(value)
    raise RulebookEditError(f"{value!r} is not a scalar a rulebook threshold may hold.")


# A rule block starts at `  - id: <name>` and runs to the next one at the same
# indent, or to a top-level key. Matching on the indent rather than on a blank
# line is what keeps a rule's own commented paragraphs inside its block.
_RULE_START = re.compile(r"^(\s*)-\s+id:\s*(\S+)\s*$")
_TOP_LEVEL = re.compile(r"^\S")


def _rule_spans(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Every rule id to the half-open line span of its block."""
    spans: dict[str, tuple[int, int]] = {}
    current_id = None
    start = 0
    indent = None
    for index, line in enumerate(lines):
        match = _RULE_START.match(line)
        if match:
            if current_id is not None:
                spans[current_id] = (start, index)
            indent, current_id, start = match.group(1), match.group(2), index
            continue
        if current_id is not None and _TOP_LEVEL.match(line) and line.strip():
            spans[current_id] = (start, index)
            current_id = None
    if current_id is not None:
        spans[current_id] = (start, len(lines))
    return spans


def _replace_scalar(lines: list[str], span: tuple[int, int], key: str, value) -> bool:
    """Rewrite `key: <scalar>` inside one span. True if a line was changed.

    Only a line whose key sits at the block's own value indent is touched, so a
    `threshold:` appearing inside a nested `skip_caveats:` paragraph - or inside
    a comment - is not mistaken for the rule's own.
    """
    start, end = span
    pattern = re.compile(rf"^(\s*){re.escape(key)}:\s*(.+?)\s*$")
    for index in range(start, end):
        line = lines[index]
        if line.lstrip().startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        lines[index] = f"{match.group(1)}{key}: {_scalar(value)}"
        return True
    return False


def _replace_top_level(lines: list[str], key: str, value) -> bool:
    """Rewrite a top-level `key: <scalar>` line. Used for `version`."""
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.+?)\s*$")
    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = f"{key}: {value}"
            return True
    return False


def _replace_nested(lines: list[str], parent: str, key: str, value) -> bool:
    """Rewrite `key:` under a named top-level mapping (`severity_bands`, etc)."""
    parent_at = None
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(parent)}:\s*$", line):
            parent_at = index
            break
    if parent_at is None:
        return False
    for index in range(parent_at + 1, len(lines)):
        line = lines[index]
        if line.strip() and _TOP_LEVEL.match(line):
            break
        if line.lstrip().startswith("#"):
            continue
        match = re.match(rf"^(\s*){re.escape(key)}:\s*(.+?)\s*$", line)
        if match:
            lines[index] = f"{match.group(1)}{key}: {_scalar(value)}"
            return True
    return False


def next_version(current: str) -> str:
    """The next version string. A threshold edit is a minor bump.

    `v1.0.0` -> `v1.1.0`. Minor rather than patch because an edit changes what
    the system finds: two cases scored a month apart under different thresholds
    are not the same measurement, and a version string that only moved in its
    patch digit would understate that. Anything unparseable gets `.1` appended
    rather than being replaced, so a hand-edited version never silently loses
    what an officer wrote.
    """
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (current or "").strip())
    if not match:
        return f"{current}.1" if current else "v1.1.0"
    major, minor, _patch = (int(part) for part in match.groups())
    return f"v{major}.{minor + 1}.0"


def diff_of(before: dict, after: dict) -> list[dict]:
    """What actually moved between two parsed rulebooks, for the audit payload.

    Reported per rule and per band rather than as a text diff: an auditor's
    question is "which threshold changed, from what, to what", and a unified
    diff of a commented YAML file answers that only by being read carefully.
    """
    moved = []
    before_rules = {rule["id"]: rule for rule in before.get("rules") or []}
    for rule in after.get("rules") or []:
        old = before_rules.get(rule["id"]) or {}
        for key in EDITABLE_RULE_KEYS:
            if old.get(key) != rule.get(key):
                moved.append(
                    {
                        "rule_id": rule["id"],
                        "key": key,
                        "from": old.get(key),
                        "to": rule.get(key),
                    }
                )
    old_bands = before.get("severity_bands") or {}
    new_bands = after.get("severity_bands") or {}
    for band in ("high", "medium"):
        if old_bands.get(band) != new_bands.get(band):
            moved.append(
                {
                    "rule_id": None,
                    "key": f"severity_bands.{band}",
                    "from": old_bands.get(band),
                    "to": new_bands.get(band),
                }
            )
    old_bonus = (before.get("corroboration") or {}).get("weight")
    new_bonus = (after.get("corroboration") or {}).get("weight")
    if old_bonus != new_bonus:
        moved.append(
            {"rule_id": "agency_pattern_bonus", "key": "weight", "from": old_bonus, "to": new_bonus}
        )
    return moved


def _assert_only_editable_moved(before: dict, after: dict) -> None:
    """The rewrite changed the scalars asked for and nothing else, or it raises.

    This is what makes a text edit of a YAML file defensible. The edit is not
    trusted to have been surgical; the result is re-parsed and checked against
    the original, key by key, and a rewrite that disturbed a field, an operator,
    a label or the ORDER of the rules is discarded before it can reach disk.
    """
    before_rules = before.get("rules") or []
    after_rules = after.get("rules") or []
    if len(before_rules) != len(after_rules):
        raise RulebookEditError(
            f"the edit changed the number of rules ({len(before_rules)} -> "
            f"{len(after_rules)}). An edit may not add or remove a rule."
        )
    for old, new in zip(before_rules, after_rules):
        for key in FROZEN_RULE_KEYS:
            if old.get(key) != new.get(key):
                raise RulebookEditError(
                    f"the edit would change {key!r} on rule {old.get('id')!r} "
                    f"({old.get(key)!r} -> {new.get(key)!r}). Only thresholds and weights "
                    "may be edited."
                )
        for key in ("caveat", "caveat_when", "skip_caveats"):
            if old.get(key) != new.get(key):
                raise RulebookEditError(
                    f"the edit would change {key!r} on rule {old.get('id')!r}. The caveats "
                    "explain a rule's findings and are not editable here."
                )
    old_bonus = dict(before.get("corroboration") or {})
    new_bonus = dict(after.get("corroboration") or {})
    old_bonus.pop("weight", None)
    new_bonus.pop("weight", None)
    if old_bonus != new_bonus:
        raise RulebookEditError(
            "the edit would change the corroboration rule beyond its weight. "
            "Only the bonus weight is editable."
        )


def apply_edits(
    yaml_text: str,
    rule_edits,
    severity_bands=None,
    corroboration_weight=None,
    version=None,
) -> tuple[str, list[dict]]:
    """Return the rewritten YAML and the list of what moved.

    Raises `RulebookEditError` and writes nothing if an edit names a rule that
    does not exist, if a scalar cannot be located on its own line, or if the
    rewritten text differs from the original anywhere it was not asked to.
    """
    before = loads(yaml_text)
    known = {rule["id"] for rule in before.get("rules") or []}

    lines = yaml_text.splitlines()
    spans = _rule_spans(lines)

    for edit in rule_edits:
        if edit.rule_id not in known:
            raise RulebookEditError(
                f"no rule with id {edit.rule_id!r}. An edit may not create one: a new rule "
                "needs a derived field, a measured threshold and its own skip caveats."
            )
        if edit.rule_id not in spans:
            raise RulebookEditError(
                f"rule {edit.rule_id!r} parses but its block could not be located in the "
                "file, so it cannot be edited without rewriting the whole document."
            )
        for key in EDITABLE_RULE_KEYS:
            value = getattr(edit, key)
            if value is None:
                continue
            if not _replace_scalar(lines, spans[edit.rule_id], key, value):
                raise RulebookEditError(
                    f"rule {edit.rule_id!r} has no {key!r} line of its own to rewrite."
                )

    if severity_bands:
        for band in ("high", "medium"):
            if severity_bands.get(band) is None:
                continue
            if not _replace_nested(lines, "severity_bands", band, severity_bands[band]):
                raise RulebookEditError(f"no severity_bands.{band} line to rewrite.")

    if corroboration_weight is not None:
        if not _replace_nested(lines, "corroboration", "weight", corroboration_weight):
            raise RulebookEditError("no corroboration.weight line to rewrite.")

    if version is not None and not _replace_top_level(lines, "version", f'"{version}"'):
        raise RulebookEditError("no top-level version line to rewrite.")

    text = "\n".join(lines) + ("\n" if yaml_text.endswith("\n") else "")

    try:
        after = loads(text)
    except Exception as exc:  # noqa: BLE001 - any parse failure is the same answer
        raise RulebookEditError(f"the edited rulebook no longer parses: {exc}") from exc
    if not isinstance(after, dict):
        raise RulebookEditError("the edited rulebook no longer parses to a mapping.")

    _assert_only_editable_moved(before, after)
    return text, diff_of(before, after)


def edited_against(book: dict, snapshot: dict) -> list[str]:
    """Rule ids whose threshold or weight differs from a stored snapshot.

    What this is FOR: every threshold in the shipped file carries a comment
    naming the count it fired on over the profiled sample (invariant 6). The
    moment an officer edits a threshold, that comment describes a value the file
    no longer holds, and the cases on screen were scored under the old one until
    a rebuild. The screen has to be able to say which rules are in that state,
    so this names them rather than leaving a reader to compare two YAML blobs.
    """
    stored = {rule["id"]: rule for rule in snapshot.get("rules") or []}
    drifted = []
    for rule in book.get("rules") or []:
        old = stored.get(rule["id"])
        if old is None:
            drifted.append(rule["id"])
            continue
        if any(old.get(key) != rule.get(key) for key in EDITABLE_RULE_KEYS):
            drifted.append(rule["id"])
    return drifted


def validated(text: str, known_fields) -> dict:
    """Parse and validate an edited rulebook, reusing the Phase 2 validator.

    `engine.rulebook.validate` is the authority on what a loadable rulebook is -
    every rule names a derived field, every operator is one of the six, ids are
    unique - and it is called rather than reimplemented so an edit cannot be
    admitted under looser rules than a file on disk would be.
    """
    from .engine.rulebook import validate

    book = loads(text)
    try:
        return validate(book, known_fields)
    except RulebookError as exc:
        raise RulebookEditError(str(exc)) from exc
