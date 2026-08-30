"""Tier 3 - the IsolationForest anomaly badge. Worth exactly ZERO points.

**This is a badge and nothing else.** It confirms, or fails to confirm, what
the rulebook already found. A badge reading "confirms" raises an officer's
confidence; it does not raise the number (DOMAIN-MODEL.md (h), CLAUDE.md
invariant 1). Nothing under `engine/` imports this module, `anomaly_score` is
not a key in `engine/derive.FEATURE_KEYS`, and `engine/rulebook.validate`
rejects any rule that names a field outside that list - so there is no rulebook
edit, and no hand-built feature dict, that can route this number into a score.
`tests/test_ml_anomaly.py` proves it against this module's real output rather
than against a stand-in.

**The direction of the arrow.** The score is an INPUT here: `confirms` cannot
be stated without knowing whether a rule fired. A badge is never an input to a
score. That asymmetry is the whole of the tier boundary and it is enforced by
the directory layout, not by intention.

**The feature block, and why it is the payment-side one.**

An IsolationForest takes a dense matrix and MPLADS data is not dense. Filling a
gap with a zero, a mean or a median would make a work with no expenditure row
look like a work whose expenditure was published as zero, which is the single
confusion CLAUDE.md invariant 2 exists to prevent - and it would do it silently,
inside a model, where no trace row could show it. So nothing is imputed. A work
is vectorised only when every feature in `ANOMALY_FEATURES` was actually
measured on it, and a work that is not vectorisable is `not_applicable` with
the reason and the list of features it was missing.

The block is the fund-and-payment side of the derived dictionary, and it is
jointly available on the works an expenditure row joins to. Measured on this
corpus: **3,380 of the 27,078 real sanctioned works carry a complete vector**
and 23,698 do not. That is 12.5% coverage, and it is the honest ceiling rather
than a shortfall to engineer around: `utilisation_shortfall`, `stalled_work`
and `vendor_concentration` read populations of 3,529, 3,529 and 3,392 for
exactly the same reason (DATA-PROFILE.md section 6). A work whose payments
MoSPI never published has nothing for an outlier detector to be an outlier in.

One consequence is worth naming because it is useful: all 37 of the corpus's
HIGH cases sit inside those 3,380. The tier that can say least about the corpus
can still say something about every case at the top of the queue.

**Peer groups.** `(work category, state, financial year)` - the group the
frozen contract already names in its `statistical` block. The forest is fitted
once over the whole vectorisable population, because 125 separate forests over
a median of six works each would fit noise; the peer group is what the badge
NAMES, and `ANOMALY_MIN_PEER_GROUP` is the floor below which "unusual among its
peers" has no content and the finding is `not_applicable` instead.

**Contamination is measured, not defaulted.** See
`app.constants.ANOMALY_CONTAMINATION`.
"""

from __future__ import annotations

from collections import defaultdict

from ..constants import (
    ANOMALY_CONTAMINATION,
    ANOMALY_MIN_PEER_GROUP,
    ML_KIND_ANOMALY,
    ML_RANDOM_SEED,
    Availability,
)
from .base import Finding, model_version

# The nine derived features an anomaly vector is built from, in a fixed order
# so the matrix column meanings are stable across runs and the model version
# digest changes if the list ever does.
#
# Every one is a key of `engine.derive.FEATURE_KEYS`, deliberately: the badge
# looks at exactly what the rulebook looks at, so a work the forest calls
# unusual is unusual in facts an officer can already read on the trace, not in
# some private representation. `work_id` and the two boolean features are left
# out - an id is not a measurement, and a boolean contributes a split the
# rulebook already makes deterministically and better.
ANOMALY_FEATURES = (
    "variance_sanction_to_disbursement",
    "sanction_lag_days",
    "sanction_to_first_payment_days",
    "days_since_last_payment",
    "vendor_share_in_agency_pct",
    "duplicate_similarity",
    "same_desc_same_agency_count",
    "mp_utilisation_pct",
    "payment_count",
)

METHOD = (
    "sklearn.IsolationForest over nine derived features, fitted once on every real "
    "sanctioned work carrying a complete vector; no value is imputed"
)


def peer_group_key(work) -> tuple:
    """(category, state_id, fy) - the group the frozen contract names."""
    return (
        getattr(work, "category", None),
        getattr(work, "state_id", None),
        getattr(work, "fy", None),
    )


def peer_group_label(work, state_names=None) -> str:
    """The group in the words the contract prints it in."""
    state_names = state_names or {}
    category = getattr(work, "category", None) or "uncategorised"
    state = state_names.get(getattr(work, "state_id", None)) or "an unnamed state"
    return f"{category} works sanctioned in {state}, FY{getattr(work, 'fy', None)}"


def vector(features) -> list[float] | None:
    """The nine readings as floats, or None if any one of them was not measured.

    None is the whole point. There is no imputation branch, because a filled
    gap inside a fitted model is a gap nobody downstream can see.
    """
    row = []
    for key in ANOMALY_FEATURES:
        value = features.get(key)
        if value is None:
            return None
        row.append(float(value))
    return row


def missing_features(features) -> list[str]:
    """Which of the nine were not measured. Goes onto the finding as the reason."""
    return [key for key in ANOMALY_FEATURES if features.get(key) is None]


class AnomalyModel:
    """A fitted forest, plus everything needed to explain one of its readings."""

    def __init__(self, forest, order, groups, version, contamination, trained_on):
        self.forest = forest
        # The work pks the matrix rows correspond to, in matrix order.
        self.order = order
        # peer group key -> number of vectorisable REAL works in it.
        self.groups = groups
        self.version = version
        self.contamination = contamination
        self.trained_on = trained_on
        self._scores: dict[int, float] = {}

    def score_for(self, work_pk) -> float | None:
        return self._scores.get(work_pk)

    def flagged(self, work_pk) -> bool | None:
        score = self._scores.get(work_pk)
        return None if score is None else score > 0.0


def fit(features_by_pk, works_by_pk):
    """Fit the forest on every REAL work with a complete vector.

    The labelled synthetic control is excluded from the fit (CLAUDE.md
    invariant 12): it is one injected row and it must not enter a population
    that a badge is measured against. It is still eligible to be scored, if it
    ever carries a complete vector - on the current corpus it does not, and
    `tests/test_ml_anomaly.py` pins that.
    """
    import numpy as np
    from sklearn.ensemble import IsolationForest

    order, matrix = [], []
    groups: dict[tuple, int] = defaultdict(int)
    for work_pk in sorted(features_by_pk):
        work = works_by_pk.get(work_pk)
        if work is None or getattr(work, "is_synthetic", False):
            continue
        row = vector(features_by_pk[work_pk])
        if row is None:
            continue
        order.append(work_pk)
        matrix.append(row)
        groups[peer_group_key(work)] += 1

    version = model_version(
        "iso1",
        method=METHOD,
        features=list(ANOMALY_FEATURES),
        contamination=ANOMALY_CONTAMINATION,
        seed=ML_RANDOM_SEED,
        min_peer_group=ANOMALY_MIN_PEER_GROUP,
        trained_on=len(order),
    )
    forest = IsolationForest(
        contamination=ANOMALY_CONTAMINATION,
        random_state=ML_RANDOM_SEED,
        n_estimators=200,
    )
    if order:
        forest.fit(np.asarray(matrix, dtype=float))
    return AnomalyModel(
        forest=forest,
        order=order,
        groups=dict(groups),
        version=version,
        contamination=ANOMALY_CONTAMINATION,
        trained_on=len(order),
    )


def score(model: AnomalyModel, features_by_pk, works_by_pk) -> AnomalyModel:
    """Read every vectorisable work through the fitted forest.

    `anomaly_score` is the forest's decision function NEGATED, so that larger
    means more unusual and the sign carries the verdict: a score above zero is
    a work the forest places outside the bulk of the population, and a score
    below zero is one it places inside. That identity is exact rather than
    conventional - scikit-learn's `predict` returns -1 exactly where the
    decision function is negative - so the number on the badge and the flag on
    the badge can never disagree.
    """
    import numpy as np

    order, matrix = [], []
    for work_pk in sorted(features_by_pk):
        row = vector(features_by_pk[work_pk])
        if row is None:
            continue
        order.append(work_pk)
        matrix.append(row)
    if order:
        margins = model.forest.decision_function(np.asarray(matrix, dtype=float))
        model._scores = {pk: float(-margin) for pk, margin in zip(order, margins)}
    return model


def findings(model: AnomalyModel, features_by_pk, works_by_pk, fired_counts=None, state_names=None):
    """One `anomaly` finding per work, badges and skips alike.

    `fired_counts` maps work pk to the number of rulebook rules that FIRED on
    that case, and it is what lets the badge say `confirms`. It travels one way
    only: the score is read here, and nothing computed here is readable from
    the scoring path. Omit it and `confirms` is None - "not stated" - rather
    than False, because a badge that had no finding to confirm has not failed
    to confirm one.

    Three states, and they are the three CLAUDE.md invariant 2 requires:

      published       the vector was complete and the peer group large enough
      not_applicable  the vector was incomplete, or the peer group too thin
      not_published   never used here. Every input this module reads is a
                      derived feature that already carries its own reason, and
                      restating "MoSPI did not publish it" one layer up would
                      duplicate a finding rather than add one.
    """
    fired_counts = fired_counts or {}
    state_names = state_names or {}
    out = []
    for work_pk in sorted(features_by_pk):
        work = works_by_pk.get(work_pk)
        features = features_by_pk[work_pk]
        group = peer_group_key(work) if work is not None else None
        group_size = model.groups.get(group, 0)
        label = peer_group_label(work, state_names) if work is not None else None
        payload = {"peer_group": label, "peer_group_size": group_size, "method": METHOD}

        missing = missing_features(features)
        if missing:
            payload["detail"] = (
                "No anomaly score: this work is missing "
                f"{len(missing)} of the {len(ANOMALY_FEATURES)} readings a vector needs "
                f"({', '.join(missing)}). Nothing is imputed, so the work is not compared "
                "rather than compared against filled-in values."
            )
            payload["missing_features"] = missing
            out.append(_skip(work_pk, payload, model.version))
            continue

        if group_size < ANOMALY_MIN_PEER_GROUP:
            payload["detail"] = (
                f"No anomaly score: this work's peer group holds {group_size} comparable "
                f"works, below the floor of {ANOMALY_MIN_PEER_GROUP}. Below that, "
                '"unusual among its peers" carries no content.'
            )
            out.append(_skip(work_pk, payload, model.version))
            continue

        value = model.score_for(work_pk)
        if value is None:
            payload["detail"] = "This work was not read through the fitted forest."
            out.append(_skip(work_pk, payload, model.version))
            continue

        flagged = value > 0.0
        fired = fired_counts.get(work_pk)
        confirms = None if fired is None else bool(flagged and fired > 0)
        payload.update(
            {
                "flagged": flagged,
                "confirms": confirms,
                "rules_fired": fired,
                "contamination": model.contamination,
                "trained_on": model.trained_on,
                "features": {key: features.get(key) for key in ANOMALY_FEATURES},
                "reading": (
                    "Badge only. Contributes zero points to the score "
                    "(CLAUDE.md invariant 1). A positive score means the forest places "
                    "this work outside the bulk of its comparable population; it is a "
                    "reason to read the trace, never a finding of its own."
                ),
            }
        )
        out.append(
            Finding(
                work_pk=work_pk,
                kind=ML_KIND_ANOMALY,
                value=round(value, 6),
                availability=Availability.PUBLISHED,
                payload=payload,
                model_version=model.version,
                contributes_to_score=False,
            )
        )
    return out


def _skip(work_pk, payload, version) -> Finding:
    payload.setdefault("flagged", None)
    payload.setdefault("confirms", None)
    return Finding(
        work_pk=work_pk,
        kind=ML_KIND_ANOMALY,
        value=None,
        availability=Availability.NOT_APPLICABLE,
        payload=payload,
        model_version=version,
        contributes_to_score=False,
    )


def run(features_by_pk, works_by_pk, fired_counts=None, state_names=None):
    """Fit, score and describe in one call. Returns (model, findings)."""
    model = score(fit(features_by_pk, works_by_pk), features_by_pk, works_by_pk)
    return model, findings(model, features_by_pk, works_by_pk, fired_counts, state_names)
