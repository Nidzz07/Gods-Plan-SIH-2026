"""F3 + F5 - composite score, reasoning trace, coverage.

`compute()` is the single derivation path: features in, a scored case with its
full trace out. Nothing upstream precomputes a score, so a case opened today
and a case re-derived in six months run through this same function.

**Invariant 1, structurally and not merely by convention.** The score is the
sum of fired rulebook weights plus the corroboration bonus, and nothing else.
This module cannot reach an anomaly score, a z-score, a delay forecast or a
graph centrality figure even if one were sitting in the feature dict, because
it reads the features only through `rulebook.evaluate`, which reads only the
fields the rulebook names, and `rulebook.validate` rejects any rule naming a
field outside `derive.FEATURE_KEYS`. There is no ML key on that list. Phase 4
can add every badge it likes to the case body; none of them can reach the
addition performed here.

`duplicate_similarity` IS on that list and is the single declared exception
(DOMAIN-MODEL.md section h). It earns its 18 points by citing its evidence on
the trace row - matched work ids, the shared description, the similarity
components and the method - so an officer opens the records and judges rather
than trusting the number. `compute()` refuses to return a fired
`duplicate_work` hit with no citation.

**The cap is not renormalisation.** 144 points of rule weight plus a 10-point
bonus means 154 is arithmetically reachable, and the display caps at 100. The
raw total is stored beside it and every `contribution` stays the rule's full
undivided weight, because an officer re-deriving the trace on paper must be
able to add the printed weights and reach the printed raw total. Dividing them
by 1.54 would make the printed arithmetic wrong.

**A skipped rule's weight is never redistributed.** It contributes zero and
pulls `coverage_pct` down. A case at 65% coverage scoring 50 is a different
object from a case at 100% coverage scoring 50, and nothing here may let them
look alike.
"""

from __future__ import annotations

from ..constants import (
    CORROBORATION_MIN_HIGH_CASES,
    CORROBORATION_WEIGHT,
    RULE_STATUS_FIRED,
    RULE_STATUS_SKIPPED,
    SCORE_CAP,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from .derive import locate_gap, slowest_lag
from .memo import build_memo
from .rulebook import RulebookError, evaluate, severity_bands, weight_total


class MissingCitationError(RulebookError):
    """A fired rule that owed its evidence and did not produce it.

    Currently only `duplicate_work`, the one rule fed by a similarity model. A
    fired hit with a null citation is a failed test, not a degraded row
    (DOMAIN-MODEL.md section h): the citation is the entire reason that rule is
    allowed to contribute points at all.
    """


# Rules that may not fire without evidence attached.
CITATION_REQUIRED = ("duplicate_work",)


def compute(features, rulebook, corroboration_count=0, corroboration_evidence=None) -> dict:
    """Score one work against the rulebook. Returns the whole case body.

    `corroboration_count` is the number of OTHER cases under this work's agency
    that already sit in the HIGH band in the same financial year. It is
    supplied by the caller, already narrowed to the window, exactly as the
    inherited engine took a complaint count - see `corroboration()` below for
    why the count is passed in rather than derived here.
    """
    rule_hits = evaluate(features, rulebook)
    _attach_evidence(rule_hits, features)

    total_weight = weight_total(rulebook)
    fired_total = sum(hit["contribution"] for hit in rule_hits if hit["status"] == RULE_STATUS_FIRED)
    bonus = corroboration(rulebook, corroboration_count, corroboration_evidence)

    raw_score = fired_total + bonus["contribution"]
    # Stored, never discarded: an auditor must be able to see that a case
    # displaying 100 was a 118 and not a bare crossing of the band.
    score = min(raw_score, SCORE_CAP)

    return {
        "score": score,
        "raw_score": raw_score,
        "score_cap": SCORE_CAP,
        "severity": severity(score, rulebook),
        "coverage_pct": coverage_pct(rule_hits, total_weight),
        "coverage_basis": (
            f"{total_weight - _skipped_weight(rule_hits)} of {total_weight} rulebook weight "
            "points were evaluable. Skipped weight is never redistributed."
        ),
        "gap_hop": locate_gap(features, rulebook),
        "slowest_lag": slowest_lag(features),
        "rulebook_version": rulebook.get("version"),
        "rule_hits": rule_hits,
        "corroboration": bonus,
        "unavailable_fields": features.unavailable_fields()
        if hasattr(features, "unavailable_fields")
        else [],
        "memo": None,
    }


def compute_with_memo(
    features, rulebook, corroboration_count=0, corroboration_evidence=None, facts=None
) -> dict:
    """`compute()`, plus the plain-language memo.

    Kept as a separate entry point so the memo template is provably not on the
    path that produces a number: `compute()` never imports prose, and a memo
    that failed to render could not change a score even in principle.
    """
    body = compute(features, rulebook, corroboration_count, corroboration_evidence)
    body["memo"] = build_memo(features, body, facts)
    return body


def _attach_evidence(rule_hits, features) -> None:
    """Move the cited records from the feature set onto the rows that fired."""
    evidence = getattr(features, "evidence", None) or {}
    for hit in rule_hits:
        if hit["status"] != RULE_STATUS_FIRED:
            continue
        citation = evidence.get(hit["rule_id"])
        if citation is not None:
            hit["citation"] = citation
        elif hit["rule_id"] in CITATION_REQUIRED:
            raise MissingCitationError(
                f"rule {hit['rule_id']!r} fired without a citation. It reads a model output "
                "and is admissible only because the trace row cites its evidence "
                "(DOMAIN-MODEL.md section h)."
            )


def corroboration(rulebook, count, evidence=None) -> dict:
    """F4's agency pattern-of-conduct bonus, read off the rulebook.

    **The count is supplied, not derived here, and that is a real constraint.**
    Whether a peer case is HIGH depends on its own score, and its score would
    depend on its own bonus, so deriving the count inside the scorer would be
    circular. The caller resolves it with two passes: score every case with no
    bonus, take the HIGH set from those base severities, then score again with
    the count. A case never corroborates itself - the count is of OTHER cases -
    which is what makes fixture A's 25 the number the contract prints rather
    than 26. On the profiled corpus this awards the bonus to 191 of 27,078
    cases.

    All or nothing: the bonus contributes zero or its full weight and is never
    scaled by how far past the minimum the count sits.
    """
    config = rulebook.get("corroboration") or {}
    minimum = config.get("min_high_cases", CORROBORATION_MIN_HIGH_CASES)
    weight = config.get("weight", CORROBORATION_WEIGHT)
    count = count or 0
    applied = count >= minimum
    block = {
        "rule_id": config.get("id", "agency_pattern_bonus"),
        "applied": applied,
        "weight": weight,
        "contribution": weight if applied else 0,
        "min_high_cases": minimum,
        "window": config.get("window", "FY"),
        "high_case_count": count,
        "agency": None,
        "matched_case_ids": [],
    }
    if evidence:
        block.update(evidence)
        block["high_case_count"] = count
    return block


def _skipped_weight(rule_hits) -> int:
    return sum(hit["weight"] for hit in rule_hits if hit["status"] == RULE_STATUS_SKIPPED)


def coverage_pct(rule_hits, total_weight) -> int:
    """The share of rulebook WEIGHT that could actually be evaluated.

    Measured by weight rather than by rule count, because the rules are not
    equally consequential: losing `utilisation_shortfall` costs 22 points of
    evidence and losing `account_underutilisation` costs 8, and a percentage
    that called those the same loss would be a worse description of the case
    than no percentage at all. Fixture B skips 22 + 16 + 12 = 50 points and
    reads (144 - 50) / 144 = 65%.

    The skipped weight is NOT redistributed to the rules that did run. Doing so
    would quietly inflate a case built on less evidence, which is the single
    failure mode F5 exists to prevent.
    """
    if not rule_hits or not total_weight:
        return 100
    return round((total_weight - _skipped_weight(rule_hits)) / total_weight * 100)


def severity(score, rulebook) -> str:
    """HIGH / MEDIUM / LOW, banded on the DISPLAYED score.

    Band edges come from `rules.yaml`, with the same hardcoded fallback the
    inherited engine used: high 75, medium 50 - the values the shipped rulebook
    carries and the values `app.constants` defines. Banded on the capped score
    because an officer's triage decision follows the number printed on the case
    sheet.
    """
    high, medium = severity_bands(rulebook)
    if score >= high:
        return SEVERITY_HIGH
    if score >= medium:
        return SEVERITY_MEDIUM
    return SEVERITY_LOW
