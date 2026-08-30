"""F2 - the versioned YAML rulebook, loaded and evaluated.

`app/rules.yaml` is read from disk on EVERY call to `load()`. There is no
cache, deliberately: an officer edits the rulebook in the UI, the file changes,
and the next evaluation uses it without a restart. The thresholds belong to
MoSPI, not to this module, and no value in the YAML is mirrored into a Python
constant.

`evaluate()` returns one trace row per rule, in rulebook order, with a
three-valued status:

    fired    the condition was met                  contributes the rule's weight
    passed   the condition was checked and held     contributes 0
    skipped  the input could not be read at all     contributes 0, coverage falls

**The extension over the inherited two-valued grammar.**  LEAKPROOF's rulebook
knew only "skipped" against "not skipped": a `None` reading produced a skipped
row and the row said nothing about *why* the reading was missing. NIGRANI
cannot afford that, because on MPLADS data the reason is the finding. A rule
skipped because MoSPI publishes no utilisation certificate is a reporting gap
that belongs in the ablation report; a rule skipped because the work has not
been reported complete is a fact about the work's stage; a rule skipped because
the portal published the value zero is a fact about the row. CLAUDE.md
invariant 2 requires those three to stay distinguishable end to end, so a
skipped row here carries `skip_reason`, drawn from the same
`app.constants.Availability` vocabulary the storage layer uses. There is no
second enum, and there is no default: a `None` value whose reason nobody
recorded raises rather than guessing, because guessing is precisely how a
reporting gap starts masquerading as a clean record.

Operators: lt, lte, gt, gte, eq, ne. Six, and no more. `ne` is new against the
inherited five. There is no AND, no OR and no nesting - see DOMAIN-MODEL.md
section (g) for why that is a decision rather than an omission.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..constants import (
    RULE_STATUS_FIRED,
    RULE_STATUS_PASSED,
    RULE_STATUS_SKIPPED,
    SEVERITY_HIGH_MIN,
    SEVERITY_MEDIUM_MIN,
    SKIP_REASONS,
    Availability,
)

# app/rules.yaml - the officer-editable file, one directory up from engine/.
RULES_PATH = Path(__file__).resolve().parent.parent / "rules.yaml"

# The comparisons the rulebook may express. Deliberately small: a rule an
# officer can read is worth more than an expression language they cannot.
OPERATORS = {
    "lt": lambda value, threshold: value < threshold,
    "lte": lambda value, threshold: value <= threshold,
    "gt": lambda value, threshold: value > threshold,
    "gte": lambda value, threshold: value >= threshold,
    "eq": lambda value, threshold: value == threshold,
    "ne": lambda value, threshold: value != threshold,
}

# A caveat may travel on every evaluated row, or only on a fired one. A note
# explaining how to READ a number ("this ratio is term-to-date") belongs on the
# pass as much as on the fire; a warning not to OVER-read a flag ("the export
# is truncated") only makes sense once the flag is raised.
CAVEAT_ALWAYS = "always"
CAVEAT_WHEN_FIRED = "fired"


class RulebookError(ValueError):
    """A rulebook that cannot be evaluated as written.

    Raised at load time, never swallowed into a skipped row: a rule naming a
    field that does not exist is a mistake in the rulebook, and silently
    skipping it would hide the mistake behind a lower coverage figure.
    """


class MissingAvailabilityError(RulebookError):
    """A feature read as None with no recorded reason for being None.

    This is the invariant-2 tripwire. `derive.py` records an availability for
    every feature it produces; a None arriving without one means some other
    code path built a feature set by hand and left the reason out, and the
    honest response is to fail loudly rather than to invent `not_published`.
    """


def load(path=None) -> dict:
    """Parse rules.yaml into a dict. No caching - see the module docstring."""
    path = Path(path) if path else RULES_PATH
    with open(path, "r", encoding="utf-8") as handle:
        return loads(handle.read())


def loads(text: str) -> dict:
    """Parse a rulebook from a YAML string.

    Used by `audit.recompute`, which must re-derive against the snapshot stored
    in `rulebook_versions` for the case rather than against today's file
    (CLAUDE.md invariant 5).
    """
    rulebook = yaml.safe_load(text)
    if not isinstance(rulebook, dict):
        raise RulebookError("rules.yaml did not parse to a mapping.")
    return rulebook


def validate(rulebook: dict, known_fields) -> dict:
    """Check a rulebook before anything is scored against it.

    Four things are checked, all of them load-time errors rather than runtime
    skips: every rule names a field the derived feature dictionary actually
    defines (DOMAIN-MODEL.md section f), every operator is one of the six,
    every rule id is unique, and the declared weights still total what
    `coverage_pct` is measured against.
    """
    rules = rulebook.get("rules") or []
    if not rules:
        raise RulebookError("rulebook declares no rules.")

    seen = set()
    known = set(known_fields)
    for rule in rules:
        for key in ("id", "label", "field", "operator", "threshold", "severity", "weight"):
            if key not in rule:
                raise RulebookError(f"rule {rule.get('id', '<unnamed>')!r} is missing {key!r}.")
        if rule["id"] in seen:
            raise RulebookError(f"rule id {rule['id']!r} appears twice.")
        seen.add(rule["id"])
        if rule["operator"] not in OPERATORS:
            raise RulebookError(
                f"rule {rule['id']!r} uses unknown operator {rule['operator']!r}. "
                f"Supported: {', '.join(sorted(OPERATORS))}."
            )
        if rule["field"] not in known:
            raise RulebookError(
                f"rule {rule['id']!r} reads {rule['field']!r}, which is not in the derived "
                "feature dictionary (DOMAIN-MODEL.md section f). A rule naming an unknown "
                "field is a load-time error, not a silent skip."
            )
        for reason in (rule.get("skip_caveats") or {}):
            if reason not in SKIP_REASONS:
                raise RulebookError(
                    f"rule {rule['id']!r} declares a skip caveat for {reason!r}, which is not "
                    f"one of {', '.join(SKIP_REASONS)}."
                )
    return rulebook


def weight_total(rulebook: dict) -> int:
    """Total declared weight. `coverage_pct` is measured against this."""
    return sum(rule["weight"] for rule in rulebook.get("rules") or [])


def severity_bands(rulebook: dict) -> tuple[int, int]:
    """(high, medium) cut-offs, with the fallback the inherited engine used.

    Fallbacks are 75 and 50, the same numbers `rules.yaml` carries and the same
    ones `app.constants` defines, so a rulebook that omits the block bands
    exactly as the shipped one does.
    """
    bands = rulebook.get("severity_bands") or {}
    return (
        int(bands.get("high", SEVERITY_HIGH_MIN)),
        int(bands.get("medium", SEVERITY_MEDIUM_MIN)),
    )


def rule_by_field(rulebook: dict, field: str) -> dict | None:
    """The rule reading a given feature, or None. Used for hop tolerances."""
    for rule in rulebook.get("rules") or []:
        if rule["field"] == field:
            return rule
    return None


def evaluate(features, rulebook: dict) -> list[dict]:
    """Evaluate every rule against one feature set. Returns the full trace.

    Every rule produces a row, including the ones that passed and the ones that
    could not be checked. A trace that omitted the passes would not be
    re-derivable, and one that omitted the skips would be a lie.

    `features` is normally a `derive.FeatureSet`, which carries an availability
    for every key. A plain dict works too, as long as none of the values a rule
    reads is None - see `MissingAvailabilityError`.
    """
    return [_evaluate_rule(rule, features) for rule in rulebook.get("rules") or []]


def _reason_for(features, field: str) -> str:
    """Why this feature is None, taken from the feature set, never guessed."""
    availability = getattr(features, "availability", None) or {}
    reason = availability.get(field)
    if reason is None:
        raise MissingAvailabilityError(
            f"feature {field!r} is None and no availability was recorded for it. "
            "CLAUDE.md invariant 2 requires the reason a value is missing to survive "
            "into the trace; defaulting it here would let a reporting gap read as a "
            "clean record."
        )
    value = reason.value if isinstance(reason, Availability) else str(reason)
    if value not in SKIP_REASONS:
        raise MissingAvailabilityError(
            f"feature {field!r} is None but its availability reads {value!r}. A rule that "
            "read a value is never skipped, so `published` cannot be a skip reason."
        )
    return value


def _evaluate_rule(rule: dict, features) -> dict:
    field = rule["field"]
    value = features.get(field)

    hit = {
        "rule_id": rule["id"],
        "label": rule["label"],
        "field": field,
        "raw_value": None,
        "operator": rule["operator"],
        "threshold": rule["threshold"],
        "weight": rule["weight"],
        "contribution": 0,
        "severity": rule["severity"],
        "status": RULE_STATUS_SKIPPED,
        "skip_reason": None,
        "citation": None,
        "caveat": None,
    }

    if value is None:
        hit["skip_reason"] = _reason_for(features, field)
        hit["caveat"] = (rule.get("skip_caveats") or {}).get(hit["skip_reason"])
        return hit

    # The comparison runs on the value as measured, never on the rounded value
    # the trace displays. Rounding first moves 11 works across the
    # duplicate_work threshold on this corpus, which would put the engine out
    # of step with DATA-PROFILE.md section 6 for no reason an officer could see.
    fired = OPERATORS[rule["operator"]](value, rule["threshold"])
    hit["raw_value"] = _display_value(value)
    hit["status"] = RULE_STATUS_FIRED if fired else RULE_STATUS_PASSED
    hit["contribution"] = rule["weight"] if fired else 0

    caveat = rule.get("caveat")
    if caveat and (rule.get("caveat_when", CAVEAT_ALWAYS) == CAVEAT_ALWAYS or fired):
        hit["caveat"] = caveat
    return hit


def _display_value(value):
    """The value as the trace quotes it: two decimals on a measured float.

    Booleans and counts pass through untouched, so the trace row carries a JSON
    type the frozen contract can represent (`docs/contract/case_detail.json`
    prints -40.01, 333, false and null in the same column).
    """
    if isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value, 2)
    return value
