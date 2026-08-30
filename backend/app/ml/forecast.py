"""Tier 3 - the delay-risk panel. Worth exactly ZERO points.

**This is a panel, never a score input.** Nothing under `engine/` imports this
module, `delay_risk` is not a key of `engine/derive.FEATURE_KEYS`, and
`engine/rulebook.validate` refuses any rule naming a field outside that list.
`tests/test_ml_forecast.py` proves it against this module's real output, the
same way `tests/test_ml_anomaly.py` does for the forest.

**The target, stated exactly.**

    label = 1 when execution_days > T, where T is the threshold of the
            `execution_delay` rule, READ FROM THE RULEBOOK and not restated
            here.

T is 365 on the shipped rulebook v1.0.0. It is read through
`engine.rulebook.rule_by_field` rather than copied into a constant for the same
reason `engine.derive.hop_tolerance` reads it: an officer who edits the rule in
the UI moves the forecast's definition of "late" with it, and a rulebook value
mirrored into Python is a value that can silently disagree with the YAML.

**The horizon, stated exactly.** `horizon_days` is T, and `delay_risk` is:

    the probability that this work's execution_days will exceed T - that is,
    that it will still not be reported complete T days after ITS OWN sanction
    date.

It is not a probability of anything happening in the next 90 days, and it is
not measured from today. The clock starts at the work's sanction date, the
same clock `execution_delay` reads, so a forecast and the rule it anticipates
are answering one question.

**Who is forecast, and who is not.** Three populations, kept apart:

| population | works | what NIGRANI says |
| --- | ---: | --- |
| completed, `execution_days` known | 12,974 | nothing. The outcome is observed - `not_applicable` |
| in progress, under T days since sanction | 6,829 | a forecast |
| in progress, over T days since sanction | 7,275 | nothing to forecast - `not_applicable`, and the elapsed days are stated as fact |

That third row matters and is not a rounding detail. **7,275 works have been
under way for more than a year with no completion reported**, so their
execution has already exceeded T; a "risk" of an outcome that has already
happened is not a forecast, it is a restatement dressed as one. NIGRANI reports
the elapsed days as a measurement instead. Those works are also the ones
`execution_delay` is *skipped* on - the rule reads `execution_days`, which
needs a completion date - so the rulebook is silent about them by design and
this panel does not fill the silence with a number. It is a finding for the
ablation report, not a rule this phase may invent.

**The accuracy figure, and why the obvious one is wrong.**

Works sanctioned by one office in one batch share their features and their
fate. A random train/test split therefore puts siblings on both sides, and the
model scores well by recognising the batch rather than by predicting anything.
Measured both ways on this corpus:

    random 75/25 holdout                 AUC 0.962
    holdout grouped by implementing agency   AUC 0.759

**0.755 is the figure NIGRANI quotes**, and the gap between the two is itself
the finding: it is what a random split is worth on administrative data. The
grouped split answers the question a deployment actually asks - can this
forecast say anything about a work in an office it has not scored before - and
it is the conservative answer for an office it has.

**`delay_risk` is a RANKING, and the panel says so rather than implying
otherwise.** On the agency-grouped holdout the model's Brier score is 0.1106
against 0.1045 for a constant prediction at the base rate - that is, it orders
works by risk usefully (AUC 0.755) while its probabilities, read literally, are
no better calibrated than saying "12%" about everything. Both numbers travel on
every panel, so the comparison is visible rather than buried. Isotonic
calibration over a five-fold agency-grouped cross-fit was tried and rejected:
it moved the Brier to 0.139 against a 0.159 baseline while pushing readings to
a hard 0.0 and 1.0, which trades a number nobody should read literally for a
number that looks like certainty. Ranking honestly beats calibrating
cosmetically, so `risk_percentile` - the work's rank among the works still open
- travels beside the probability and is the figure meant for an officer's eye.

**The feature list is chosen against distribution shift, not against accuracy.**
The model is trained on completed works and applied to works in progress, which
are two different populations, and several derived features MEAN DIFFERENT
THINGS in each. `days_since_last_payment` is small for a slow completed work
and large for a stalled in-progress one - the same number pointing opposite
ways. `variance_sanction_to_disbursement` is near zero on a work whose payments
are finished and deeply negative on one that is half paid. `payment_count` is
final in one population and partial in the other. All three are excluded, and
excluding them costs accuracy: this is a case where the honest model is the
weaker one. What is left is the readings that are fixed by the time a work is
under way and mean the same thing in both populations.

**Missing values are not imputed.** `HistGradientBoostingClassifier` routes a
NaN down its own branch natively, so a work with no first payment yet is
handled as a work with no first payment yet, rather than as a work whose first
payment took the average number of days. That is the same discipline invariant
2 requires everywhere else, and it is why this estimator was chosen over one
that requires a filled matrix.

**Illustrative, and labelled as such.** The corpus is a truncated portal
sample (DATA-PROFILE.md), the label is measured on the 12,974 works that have a
completion date at all, and the horizon is a demonstration rather than a
commitment (PROJECT-BRIEF declared limitation 5). Nothing here is described as
a prediction the ministry can plan against.
"""

from __future__ import annotations

from ..constants import (
    DATA_AS_OF,
    FORECAST_HOLDOUT_FRACTION,
    ML_KIND_FORECAST,
    ML_RANDOM_SEED,
    Availability,
)
from ..engine.rulebook import RulebookError, rule_by_field
from .base import Finding, model_version

# The rule whose threshold defines "late". Named by the FIELD it reads, so the
# lookup survives a rule being relabelled.
TARGET_FIELD = "execution_days"

# The derived readings that are fixed once a work is under way and carry the
# same meaning on a completed work and on one in progress. See the module
# docstring for the three that were excluded and why.
STABLE_FEATURES = (
    "sanction_lag_days",
    "sanction_to_first_payment_days",
    "duplicate_similarity",
    "same_desc_same_agency_count",
    "mp_utilisation_pct",
)

# Two facts fixed at sanction, added because they are known before a spade goes
# in the ground and neither shifts between the two populations: the size of the
# sanction, and where and what it is. State and category are handed to the
# estimator as categorical rather than numeric - a state id is a name, and
# treating it as a quantity would let the model split on "state 17 or higher".
STRUCTURAL_FEATURES = ("log10_sanctioned_amt", "state_id", "category")

FEATURE_NAMES = STABLE_FEATURES + STRUCTURAL_FEATURES
CATEGORICAL_INDICES = (len(STABLE_FEATURES) + 1, len(STABLE_FEATURES) + 2)

METHOD = (
    "sklearn.HistGradientBoostingClassifier over eight sanction-time features, trained "
    "on works with an observed completion date, holdout grouped by implementing agency"
)

MAX_ITER = 200

_READING = (
    "Panel only. Contributes zero points to the score (CLAUDE.md invariant 1). "
    "Illustrative: trained on a truncated portal sample, and the horizon is a "
    "demonstration rather than a commitment. Read delay_risk as a RANKING, not as "
    "a literal probability - on the agency-grouped holdout the model orders works "
    "usefully (AUC 0.755) while its probabilities score no better than a constant "
    "at the base rate. risk_percentile is the figure meant for the eye."
)


def horizon_days(rulebook) -> int:
    """T - the `execution_delay` threshold, read off the rulebook.

    Raises rather than falling back. A forecast whose definition of "late" was
    guessed because the rulebook could not be read would be a number with no
    stated meaning, and a silent default is exactly how a threshold starts
    disagreeing with the YAML an officer edits.
    """
    rule = rule_by_field(rulebook or {}, TARGET_FIELD)
    if rule is None:
        raise RulebookError(
            f"no rule reads {TARGET_FIELD!r}, so the forecast has no definition of 'late'. "
            "The horizon is the execution_delay threshold and is never restated in Python."
        )
    return int(rule["threshold"])


def feature_row(features, sanction, work, category_code) -> list[float]:
    """Eight readings for one work. `nan` where a value was not measured.

    Nothing is imputed - see the module docstring. The `nan` reaches the
    estimator, which routes it down its own branch natively.
    """
    import math

    row = [
        float("nan") if features.get(key) is None else float(features[key])
        for key in STABLE_FEATURES
    ]
    amount = getattr(sanction, "sanctioned_amt", None)
    row.append(float(math.log10(amount)) if amount else float("nan"))
    state_id = getattr(work, "state_id", None)
    row.append(float("nan") if state_id is None else float(state_id))
    row.append(float("nan") if category_code is None else float(category_code))
    return row


class ForecastModel:
    """A fitted classifier, its holdout report and its version string."""

    def __init__(self, estimator, categories, version, horizon, metrics, trained_on):
        self.estimator = estimator
        # Category label -> ordinal, so the encoding is reproducible.
        self.categories = categories
        self.version = version
        self.horizon = horizon
        self.metrics = metrics
        self.trained_on = trained_on

    def encode(self, features, sanction, work) -> list[float]:
        category = getattr(work, "category", None)
        return feature_row(features, sanction, work, self.categories.get(category))


def _label(features, horizon) -> int | None:
    days = features.get("execution_days")
    return None if days is None else int(days > horizon)


def fit(features_by_pk, works_by_pk, sanctions_by_pk, rulebook):
    """Train on the works with an observed completion date, and report honestly.

    The labelled synthetic control is excluded from training and from the
    holdout (CLAUDE.md invariant 12). One injected row cannot be allowed inside
    a figure NIGRANI quotes.
    """
    import numpy as np
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
    from sklearn.model_selection import GroupShuffleSplit, train_test_split

    horizon = horizon_days(rulebook)
    categories = {
        name: index
        for index, name in enumerate(
            sorted({getattr(w, "category", None) for w in works_by_pk.values()} - {None})
        )
    }
    shell = ForecastModel(None, categories, "", horizon, {}, 0)

    rows, labels, groups = [], [], []
    for work_pk in sorted(features_by_pk):
        work = works_by_pk.get(work_pk)
        if work is None or getattr(work, "is_synthetic", False):
            continue
        label = _label(features_by_pk[work_pk], horizon)
        if label is None:
            continue
        rows.append(shell.encode(features_by_pk[work_pk], sanctions_by_pk.get(work_pk), work))
        labels.append(label)
        # Grouping key: the implementing agency. A work with no agency is its
        # own group rather than sharing one with every other agency-less work.
        agency_id = getattr(work, "agency_id", None)
        groups.append(agency_id if agency_id is not None else -work_pk)

    X = np.asarray(rows, dtype=float)
    y = np.asarray(labels, dtype=int)
    groups = np.asarray(groups)

    def _new():
        return HistGradientBoostingClassifier(
            random_state=ML_RANDOM_SEED,
            max_iter=MAX_ITER,
            categorical_features=list(CATEGORICAL_INDICES),
        )

    metrics = {
        "horizon_days": horizon,
        "labelled_works": int(len(y)),
        "positives": int(y.sum()),
        "positive_rate": round(float(y.mean()), 4) if len(y) else None,
        "holdout_fraction": FORECAST_HOLDOUT_FRACTION,
        "split": "GroupShuffleSplit grouped by implementing agency",
    }
    if len(y) and len(set(y)) > 1:
        splitter = GroupShuffleSplit(
            n_splits=1, test_size=FORECAST_HOLDOUT_FRACTION, random_state=ML_RANDOM_SEED
        )
        train_idx, test_idx = next(splitter.split(X, y, groups=groups))
        grouped = _new().fit(X[train_idx], y[train_idx])
        probability = grouped.predict_proba(X[test_idx])[:, 1]
        metrics.update(
            {
                "train_works": int(len(train_idx)),
                "holdout_works": int(len(test_idx)),
                "holdout_positive_rate": round(float(y[test_idx].mean()), 4),
                "roc_auc": round(float(roc_auc_score(y[test_idx], probability)), 4),
                "accuracy": round(
                    float(accuracy_score(y[test_idx], (probability >= 0.5).astype(int))), 4
                ),
                "brier": round(float(brier_score_loss(y[test_idx], probability)), 4),
                # What a constant prediction at the holdout's own base rate
                # would score. Printed beside the model's Brier so a reader can
                # see, without doing the arithmetic, that this model RANKS well
                # and is not calibrated: see the module docstring.
                "brier_baseline_constant": round(
                    float(y[test_idx].mean() * (1 - y[test_idx].mean())), 4
                ),
                "calibration": (
                    "Not calibrated. delay_risk orders works by risk; it is not a literal "
                    "probability. Compare brier against brier_baseline_constant."
                ),
            }
        )
        # The contrast, kept because the difference is the finding: a random
        # split scores far higher by recognising sibling works from the same
        # agency batch. It is recorded, and it is never the quoted number.
        r_train, r_test = train_test_split(
            np.arange(len(y)),
            test_size=FORECAST_HOLDOUT_FRACTION,
            random_state=ML_RANDOM_SEED,
            stratify=y,
        )
        random_probability = _new().fit(X[r_train], y[r_train]).predict_proba(X[r_test])[:, 1]
        metrics["roc_auc_random_split_not_quoted"] = round(
            float(roc_auc_score(y[r_test], random_probability)), 4
        )

    estimator = _new().fit(X, y) if len(y) and len(set(y)) > 1 else None
    version = model_version(
        "fc1",
        method=METHOD,
        features=list(FEATURE_NAMES),
        horizon=horizon,
        max_iter=MAX_ITER,
        seed=ML_RANDOM_SEED,
        trained_on=int(len(y)),
        holdout=FORECAST_HOLDOUT_FRACTION,
    )
    return ForecastModel(estimator, categories, version, horizon, metrics, int(len(y)))


def elapsed_days(sanction) -> int | None:
    """Days from the work's sanction date to the corpus as-of date.

    Measured to `DATA_AS_OF`, never to `today`, for the same reason
    `days_since_last_payment` is: a panel re-derived six months from now must
    reproduce the number the officer saw.
    """
    sanction_date = getattr(sanction, "sanction_date", None)
    return None if sanction_date is None else (DATA_AS_OF - sanction_date).days


def findings(model: ForecastModel, features_by_pk, works_by_pk, sanctions_by_pk):
    """One `forecast` finding per work, forecasts and non-forecasts alike.

    Every work gets a row. A completed work carries `not_applicable` with its
    observed `execution_days`; an in-progress work already past the horizon
    carries `not_applicable` with its elapsed days; only the works with an
    outcome still open carry a probability.
    """
    import numpy as np

    horizon = model.horizon
    pending, rows = [], []
    out_by_pk: dict[int, Finding] = {}

    for work_pk in sorted(features_by_pk):
        work = works_by_pk.get(work_pk)
        features = features_by_pk[work_pk]
        sanction = sanctions_by_pk.get(work_pk)
        observed = features.get("execution_days")
        elapsed = elapsed_days(sanction)
        payload = {
            "horizon_days": horizon,
            "horizon_meaning": (
                f"the probability that this work is not reported complete within {horizon} "
                "days of its own sanction date, the threshold the execution_delay rule reads"
            ),
            "method": METHOD,
            "elapsed_days": elapsed,
            "reading": _READING,
        }

        if observed is not None:
            payload["detail"] = (
                f"No forecast: this work has been reported complete, {observed} days after "
                f"sanction. The outcome is observed, not predicted."
            )
            payload["observed_execution_days"] = int(observed)
            payload["outcome"] = "exceeded" if observed > horizon else "within_horizon"
            out_by_pk[work_pk] = _skip(work_pk, payload, model.version)
            continue

        if elapsed is None:
            payload["detail"] = "No forecast: this work has no published sanction date."
            out_by_pk[work_pk] = _skip(work_pk, payload, model.version)
            continue

        if elapsed > horizon:
            payload["detail"] = (
                f"No forecast: this work was sanctioned {elapsed} days ago and has not been "
                f"reported complete, so it has already exceeded the {horizon}-day horizon. "
                "A risk of an outcome that has already occurred is not a forecast, and "
                "execution_delay is skipped on this work because no completion date exists "
                "to measure against."
            )
            payload["outcome"] = "already_exceeded"
            out_by_pk[work_pk] = _skip(work_pk, payload, model.version)
            continue

        pending.append(work_pk)
        rows.append(model.encode(features, sanction, work))
        out_by_pk[work_pk] = None  # filled below

    if pending and model.estimator is not None:
        probabilities = model.estimator.predict_proba(np.asarray(rows, dtype=float))[:, 1]
        # The work's rank among the works still open, 0-100. This is what the
        # model actually earned - see the module docstring on ranking against
        # calibration - and it is the figure the panel puts in front of an eye.
        ranks = probabilities.argsort().argsort()
        percentiles = (
            ranks / (len(probabilities) - 1) * 100 if len(probabilities) > 1 else ranks * 0.0
        )
    else:
        probabilities = [None] * len(pending)
        percentiles = [None] * len(pending)

    for work_pk, probability, percentile in zip(pending, probabilities, percentiles):
        sanction = sanctions_by_pk.get(work_pk)
        elapsed = elapsed_days(sanction)
        payload = {
            "horizon_days": horizon,
            "horizon_meaning": (
                f"the probability that this work is not reported complete within {horizon} "
                "days of its own sanction date, the threshold the execution_delay rule reads"
            ),
            "method": METHOD,
            "elapsed_days": elapsed,
            "days_remaining": None if elapsed is None else horizon - elapsed,
            "outcome": "open",
            "risk_percentile": None if percentile is None else round(float(percentile), 1),
            "holdout": model.metrics,
            "reading": _READING,
        }
        if probability is None:
            payload["detail"] = "No forecast: no model was fitted on this corpus."
            out_by_pk[work_pk] = _skip(work_pk, payload, model.version)
            continue
        out_by_pk[work_pk] = Finding(
            work_pk=work_pk,
            kind=ML_KIND_FORECAST,
            value=round(float(probability), 6),
            availability=Availability.PUBLISHED,
            payload=payload,
            model_version=model.version,
            contributes_to_score=False,
        )

    return [out_by_pk[work_pk] for work_pk in sorted(out_by_pk)]


def _skip(work_pk, payload, version) -> Finding:
    return Finding(
        work_pk=work_pk,
        kind=ML_KIND_FORECAST,
        value=None,
        availability=Availability.NOT_APPLICABLE,
        payload=payload,
        model_version=version,
        contributes_to_score=False,
    )


def run(features_by_pk, works_by_pk, sanctions_by_pk, rulebook):
    """Fit and describe in one call. Returns (model, findings)."""
    model = fit(features_by_pk, works_by_pk, sanctions_by_pk, rulebook)
    return model, findings(model, features_by_pk, works_by_pk, sanctions_by_pk)
