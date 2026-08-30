"""Assembling the ML blocks of a case body, without touching its numbers.

`attach()` takes the body `engine/score.compute()` returned and returns a NEW
dict carrying the badge blocks. It never mutates the body it was given, and it
never writes to `score`, `raw_score`, `severity`, `coverage_pct`, `rule_hits`
or `corroboration` - `SCORED_KEYS` names them and the function refuses to emit
a body in which any of them changed.

That refusal is not decoration. It is the last link in the chain that makes
CLAUDE.md invariant 1 structural rather than promised: `engine/` cannot import
`ml/`, no ML key is in `engine/derive.FEATURE_KEYS`, and the one place the two
tiers meet in the same dict asserts that the scored half came through
untouched. `tests/test_ml_integration.py` drives the whole pipeline over
fixtures A, B and C and checks the same thing end to end.

**Key names follow `docs/contract/case_detail.json`.** `statistical` and
`forecast` are the two blocks the frozen contract already declares, keys and
all, currently carrying nulls and a note saying feature F7 has not been built.
This module fills those keys with the shapes the contract declares.

`concentration` has NO key in the frozen contract. It is emitted here under
that name because the tier-4 graph has to go somewhere, and adding a key to
`case_detail.json` is not this phase's to make: the contract and
`app/schemas.py` move together or not at all (invariant 9), and `schemas.py` is
still the inherited LEAKPROOF shape - it speaks of shops and complaints and
mirrors nothing in the contract yet. Both are rewritten together when the API
is built, and that is the moment `concentration` becomes contractual.
"""

from __future__ import annotations

from ..constants import ML_KIND_ANOMALY, ML_KIND_FORECAST, ML_KIND_GRAPH, Availability
from .base import by_work  # noqa: F401  - re-exported; it is defined beside Finding

# The keys `attach()` may not change. Everything a score is made of.
SCORED_KEYS = (
    "score",
    "raw_score",
    "score_cap",
    "severity",
    "coverage_pct",
    "coverage_basis",
    "rule_hits",
    "corroboration",
)

ZERO_NOTE = (
    "Badge only. Contributes zero points to the score (CLAUDE.md invariant 1). "
    "The statistical and graph tiers confirm, or fail to confirm, what the rulebook "
    "already found; they never move the number."
)


class ScoreMutatedError(RuntimeError):
    """A badge changed something a badge may not change.

    Raised rather than corrected. If this is ever hit, something on the ML side
    reached a scored key, and quietly restoring the old value would hide the
    breach instead of stopping it.
    """


def statistical_block(finding, peer_group=None) -> dict:
    """The contract's `statistical` block, from one `anomaly` finding.

    `z_score` stays null. The frozen contract declares the key and no document
    in the repository defines WHAT the z-score is a z-score of - which quantity,
    over which peer statistic - so filling it would mean inventing a measure and
    printing it beside measured ones. `z_peer_group` is filled, because the
    peer group is defined and the anomaly badge uses it.
    """
    payload = getattr(finding, "payload", None) or {}
    available = finding is not None and finding.availability == Availability.PUBLISHED
    return {
        "z_score": None,
        "z_peer_group": payload.get("peer_group") or peer_group,
        "anomaly_score": finding.value if available else None,
        "anomaly_model_version": getattr(finding, "model_version", None),
        "anomaly_flagged": payload.get("flagged"),
        "confirms": payload.get("confirms"),
        "contribution": 0,
        "availability": (
            finding.availability.value if finding is not None else Availability.NOT_APPLICABLE.value
        ),
        "detail": payload.get("detail"),
        "peer_group_size": payload.get("peer_group_size"),
        "note": ZERO_NOTE,
    }


def forecast_block(finding) -> dict:
    """The contract's `forecast` block, from one `forecast` finding."""
    payload = getattr(finding, "payload", None) or {}
    available = finding is not None and finding.availability == Availability.PUBLISHED
    return {
        "delay_risk": finding.value if available else None,
        "risk_percentile": payload.get("risk_percentile"),
        "horizon_days": payload.get("horizon_days"),
        "horizon_meaning": payload.get("horizon_meaning"),
        "model_version": getattr(finding, "model_version", None),
        "contribution": 0,
        "availability": (
            finding.availability.value if finding is not None else Availability.NOT_APPLICABLE.value
        ),
        "outcome": payload.get("outcome"),
        "elapsed_days": payload.get("elapsed_days"),
        "detail": payload.get("detail"),
        "holdout": payload.get("holdout"),
        "note": payload.get("reading"),
    }


def concentration_block(finding) -> dict:
    """The tier-4 graph block. No contract key yet - see the module docstring."""
    payload = getattr(finding, "payload", None) or {}
    available = finding is not None and finding.availability == Availability.PUBLISHED
    return {
        "hhi": finding.value if available else None,
        "agency": payload.get("agency"),
        "vendor_count": payload.get("vendor_count"),
        "top_vendor": payload.get("top_vendor"),
        "top_vendor_share_pct": payload.get("top_vendor_share_pct"),
        "shared_vendor_exposure_pct": payload.get("shared_vendor_exposure_pct"),
        "widest_vendor_span": payload.get("widest_vendor_span"),
        "component_agencies": payload.get("component_agencies"),
        "work_vendors": payload.get("work_vendors"),
        "model_version": getattr(finding, "model_version", None),
        "contribution": 0,
        "availability": (
            finding.availability.value if finding is not None else Availability.NOT_APPLICABLE.value
        ),
        "detail": payload.get("detail"),
        "note": ZERO_NOTE,
    }


def attach(body: dict, anomaly=None, forecast=None, concentration=None) -> dict:
    """Return `body` with the three badge blocks added and nothing else changed.

    The three arguments are `base.Finding` objects for ONE work, or None where
    that module produced nothing for it. A missing finding is rendered as a
    `not_applicable` block rather than omitted, so the case body's shape does
    not change depending on how much the ML tier could say.
    """
    before = {key: body.get(key) for key in SCORED_KEYS}
    out = dict(body)
    out["statistical"] = statistical_block(anomaly)
    out["forecast"] = forecast_block(forecast)
    out["concentration"] = concentration_block(concentration)

    changed = [key for key in SCORED_KEYS if out.get(key) != before[key]]
    if changed:
        raise ScoreMutatedError(
            f"attaching ML badges changed {', '.join(changed)}. The statistical and graph "
            "tiers are worth zero points and may not reach a scored key "
            "(CLAUDE.md invariant 1)."
        )
    return out


def kinds_are_badges(findings) -> bool:
    """True when every finding in the list is worth zero points.

    The three badge kinds must all carry `contributes_to_score = False`. Only
    `duplicate` may carry True, and only because `duplicate_work` reads a
    similarity number and cites the records behind it (DOMAIN-MODEL.md (h)).
    """
    badge_kinds = (ML_KIND_ANOMALY, ML_KIND_FORECAST, ML_KIND_GRAPH)
    return all(
        not finding.contributes_to_score
        for finding in findings
        if finding.kind in badge_kinds
    )
