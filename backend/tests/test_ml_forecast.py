"""`app/ml/forecast.py` - the delay-risk panel, its target, and its honesty.

Four things are held here.

**The target is the rule's own threshold**, read from the rulebook rather than
restated in Python, so an officer who edits `execution_delay` moves the
forecast's definition of "late" with it.

**The accuracy figure is the grouped one.** A random split scores AUC 0.960 on
this corpus and an agency-grouped split scores 0.755. The gap is sibling works
from the same batch appearing on both sides, and the test pins both numbers so
the higher one cannot quietly become the quoted one.

**A settled outcome is not forecast.** 7,275 works have been under way for more
than the horizon with no completion reported; their execution has already
exceeded it, and NIGRANI states the elapsed days rather than dressing a known
outcome as a risk.

**And the panel cannot move a score**, proved against its real output on
fixtures A, B and C, the same way the anomaly module's is.
"""

from __future__ import annotations

import pytest

from app.constants import Availability, ML_KIND_FORECAST
from app.engine import derive as derive_mod
from app.engine.rulebook import RulebookError
from app.ml import forecast
from app.ml.badges import attach

from .conftest import FIXTURE_A, FIXTURE_B, FIXTURE_C

pytestmark = pytest.mark.corpus


# ---------------------------------------------------------------------------
# Invariant 1, extended to this module's real output
# ---------------------------------------------------------------------------

FIXTURE_SCORES = {
    FIXTURE_A: (92, 92, "HIGH", 79),
    FIXTURE_B: (60, 60, "MEDIUM", 65),
    FIXTURE_C: (20, 20, "LOW", 74),
}


@pytest.mark.parametrize("work_id", sorted(FIXTURE_SCORES))
def test_the_real_forecast_output_cannot_move_the_score(ml_run, work_id):
    """The classifier's actual prediction, in the case body, changes nothing."""
    expected = FIXTURE_SCORES[work_id]
    body = ml_run.rescore(work_id)
    badged = attach(body, forecast=ml_run.finding("forecast", work_id))
    assert (
        badged["score"],
        badged["raw_score"],
        badged["severity"],
        badged["coverage_pct"],
    ) == expected
    assert badged["rule_hits"] == body["rule_hits"]
    assert badged["forecast"]["contribution"] == 0


def test_perturbing_the_forecast_leaves_every_score_untouched(ml_run):
    """A delay risk driven to 1.0 moves nothing it is attached to."""
    from dataclasses import replace as dataclass_replace

    findings = ml_run.findings_for("forecast")
    checked = 0
    for work_pk, body in list(ml_run.bodies.items()):
        finding = findings[work_pk]
        if finding.availability != Availability.PUBLISHED:
            continue
        loud = dataclass_replace(finding, value=1.0)
        before = attach(body, forecast=finding)
        after = attach(body, forecast=loud)
        for key in ("score", "raw_score", "severity", "coverage_pct", "rule_hits"):
            assert after[key] == before[key] == body[key]
        checked += 1
        if checked >= 500:
            break
    assert checked == 500


def test_no_forecast_key_is_addressable_from_the_rulebook():
    for field in ("delay_risk", "risk_percentile", "horizon_days"):
        assert field not in derive_mod.FEATURE_KEYS


# ---------------------------------------------------------------------------
# The target, read from the rulebook and never restated
# ---------------------------------------------------------------------------


def test_the_horizon_is_the_execution_delay_threshold(ml_run, rulebook):
    """365 on the shipped rulebook, and read from it rather than hardcoded."""
    assert forecast.horizon_days(rulebook) == 365
    rule = next(r for r in rulebook["rules"] if r["id"] == "execution_delay")
    assert forecast.horizon_days(rulebook) == rule["threshold"]
    assert ml_run.forecast_model.horizon == rule["threshold"]


def test_an_edited_threshold_moves_the_target_with_it():
    """The point of reading the rulebook: an officer's edit reaches the panel."""
    book = {
        "rules": [
            {
                "id": "execution_delay",
                "label": "Work under execution beyond one year",
                "field": "execution_days",
                "operator": "gt",
                "threshold": 200,
                "severity": "high",
                "weight": 20,
            }
        ]
    }
    assert forecast.horizon_days(book) == 200


def test_a_rulebook_with_no_execution_rule_raises_rather_than_guessing(ml_run):
    """A silent default is how a threshold starts disagreeing with the YAML."""
    with pytest.raises(RulebookError, match="no definition of 'late'"):
        forecast.horizon_days({"rules": []})


def test_the_label_is_the_documented_one(ml_run):
    """2,568 of 12,974 completed works exceed 365 days - DATA-PROFILE section 6.

    That is exactly the population `execution_delay` fires on, which is the
    point: the panel anticipates the rule rather than a private idea of delay.
    """
    metrics = ml_run.forecast_model.metrics
    assert metrics["labelled_works"] == 12974
    assert metrics["positives"] == 2568
    assert metrics["positive_rate"] == 0.1979
    assert metrics["horizon_days"] == 365


# ---------------------------------------------------------------------------
# The accuracy figure, and the one that would have been flattering
# ---------------------------------------------------------------------------


def test_the_quoted_accuracy_is_the_agency_grouped_one(ml_run):
    """AUC 0.755 grouped against 0.960 random, and the gap is the finding.

    Works sanctioned by one office in one batch share their features and their
    fate, so a random split puts siblings on both sides and the model scores
    well by recognising the batch. The grouped split answers the question a
    deployment asks - can this say anything about an office it has not seen -
    and it is the conservative answer for one it has.
    """
    metrics = ml_run.forecast_model.metrics
    assert metrics["split"] == "GroupShuffleSplit grouped by implementing agency"
    assert metrics["roc_auc"] == pytest.approx(0.7552, abs=0.002)
    assert metrics["roc_auc_random_split_not_quoted"] == pytest.approx(0.9599, abs=0.002)
    assert metrics["roc_auc"] < metrics["roc_auc_random_split_not_quoted"]
    assert metrics["train_works"] + metrics["holdout_works"] == metrics["labelled_works"]
    assert metrics["holdout_works"] == 2352


def test_the_panel_says_it_is_a_ranking_and_shows_the_number_that_proves_it(ml_run):
    """Brier 0.111 against 0.105 for a constant at the base rate.

    The model ORDERS works usefully and its probabilities, read literally, are
    no better calibrated than saying "12%" about everything. Both numbers ride
    on the panel so the comparison is visible rather than buried, and
    `risk_percentile` is the figure meant for an officer's eye. Isotonic
    calibration was tried and rejected: it traded a number nobody should read
    literally for readings of a hard 0.0 and 1.0, which look like certainty.
    """
    metrics = ml_run.forecast_model.metrics
    assert metrics["brier"] > metrics["brier_baseline_constant"]
    assert "Not calibrated" in metrics["calibration"]
    finding = ml_run.finding("forecast", FIXTURE_A)
    assert "RANKING" in finding.payload["reading"]
    assert 0.0 <= finding.payload["risk_percentile"] <= 100.0


def test_the_control_is_excluded_from_the_training_population(ml_run):
    """Invariant 12: one injected row may not sit inside a quoted figure.

    C's execution ran 481 days, over the horizon, so it would have been a
    positive label had it been let in. 2,568 is the real count and stays so.
    """
    assert ml_run.corpus.features_for(FIXTURE_C)["execution_days"] == 481
    assert ml_run.forecast_model.metrics["positives"] == 2568


# ---------------------------------------------------------------------------
# Who is forecast, and who is not
# ---------------------------------------------------------------------------


def test_the_three_populations_are_the_documented_ones(ml_run):
    """12,975 observed, 7,275 already past the horizon, 6,829 still open."""
    outcomes = {}
    for finding in ml_run.forecast_findings:
        outcome = finding.payload.get("outcome")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    assert outcomes["open"] == 6829
    assert outcomes["already_exceeded"] == 7275
    assert outcomes["within_horizon"] + outcomes["exceeded"] == 12975  # includes C
    assert sum(outcomes.values()) == len(ml_run.corpus.features)


def test_a_settled_outcome_is_stated_as_fact_and_not_dressed_as_a_risk(ml_run):
    """7,275 works are already past the horizon with no completion reported.

    A "risk" of an outcome that has already occurred is a restatement wearing a
    forecast's clothes. NIGRANI reports the elapsed days instead - and those are
    precisely the works `execution_delay` is SKIPPED on, because the rule reads
    a completion date that does not exist. The rulebook is silent about them by
    design and this panel does not fill the silence with a number.
    """
    already = [
        f for f in ml_run.forecast_findings if f.payload.get("outcome") == "already_exceeded"
    ]
    assert len(already) == 7275
    for finding in already[:200]:
        assert finding.value is None
        assert finding.availability == Availability.NOT_APPLICABLE
        assert finding.payload["elapsed_days"] > ml_run.forecast_model.horizon
        assert "already exceeded" in finding.payload["detail"]
        # And the rule really is skipped on it.
        hit = next(
            h
            for h in ml_run.bodies[finding.work_pk]["rule_hits"]
            if h["rule_id"] == "execution_delay"
        )
        assert hit["status"] == "skipped"
        assert hit["skip_reason"] == "not_applicable"


def test_a_completed_work_reports_its_observed_days_rather_than_a_prediction(ml_run):
    for work_id in (FIXTURE_B, FIXTURE_C):
        finding = ml_run.finding("forecast", work_id)
        assert finding.value is None
        assert finding.availability == Availability.NOT_APPLICABLE
        assert finding.payload["outcome"] in ("exceeded", "within_horizon")
        assert finding.payload["observed_execution_days"] == (
            ml_run.corpus.features_for(work_id)["execution_days"]
        )
        assert "observed, not predicted" in finding.payload["detail"]


def test_fixture_a_is_forecast_because_its_outcome_is_still_open(ml_run):
    """A was sanctioned 280 days ago with 85 days of the horizon left."""
    finding = ml_run.finding("forecast", FIXTURE_A)
    assert finding.availability == Availability.PUBLISHED
    assert finding.kind == ML_KIND_FORECAST
    assert finding.contributes_to_score is False
    assert finding.payload["outcome"] == "open"
    assert finding.payload["elapsed_days"] == 280
    assert finding.payload["days_remaining"] == 85
    assert 0.0 <= finding.value <= 1.0
    assert finding.payload["horizon_days"] == 365
    assert "not reported complete within 365 days" in finding.payload["horizon_meaning"]


def test_elapsed_days_is_measured_to_the_corpus_as_of_date_never_to_today(ml_run):
    """Otherwise a panel re-derived in six months would not reproduce itself."""
    from app.constants import DATA_AS_OF

    work_pk = ml_run.pk(FIXTURE_A)
    sanction = ml_run.corpus.sanctions[work_pk]
    assert forecast.elapsed_days(sanction) == (DATA_AS_OF - sanction.sanction_date).days
    assert ml_run.finding("forecast", FIXTURE_A).payload["elapsed_days"] == 280


# ---------------------------------------------------------------------------
# Features, missingness and the version string
# ---------------------------------------------------------------------------


def test_the_shifting_features_are_excluded_and_the_stable_ones_are_not():
    """Chosen against distribution shift, and the honest model is the weaker one.

    `days_since_last_payment` is small for a slow completed work and large for
    a stalled in-progress one - the same number pointing opposite ways between
    the population the model is trained on and the one it is applied to.
    `variance_sanction_to_disbursement` and `payment_count` shift the same way.
    All three are out.
    """
    for shifting in (
        "days_since_last_payment",
        "variance_sanction_to_disbursement",
        "payment_count",
        "execution_days",
        "first_payment_to_completion_days",
    ):
        assert shifting not in forecast.STABLE_FEATURES
    for stable in forecast.STABLE_FEATURES:
        assert stable in derive_mod.FEATURE_KEYS


def test_a_missing_reading_reaches_the_estimator_as_nan_and_is_not_imputed(ml_run):
    """`HistGradientBoostingClassifier` routes a NaN natively, so nothing is filled.

    B has no payment row, so its `sanction_to_first_payment_days` is unmeasured.
    The row carries a NaN, not the average number of days to a first payment.
    """
    import math

    work_pk = ml_run.pk(FIXTURE_B)
    row = ml_run.forecast_model.encode(
        ml_run.corpus.features[work_pk],
        ml_run.corpus.sanctions[work_pk],
        ml_run.corpus.works[work_pk],
    )
    index = forecast.STABLE_FEATURES.index("sanction_to_first_payment_days")
    assert ml_run.corpus.features[work_pk]["sanction_to_first_payment_days"] is None
    assert math.isnan(row[index])


def test_a_finding_is_produced_for_every_work_and_every_one_is_a_badge(ml_run):
    assert len(ml_run.forecast_findings) == len(ml_run.corpus.features)
    assert {f.work_pk for f in ml_run.forecast_findings} == set(ml_run.corpus.features)
    for finding in ml_run.forecast_findings:
        assert finding.contributes_to_score is False
        if finding.value is None:
            assert finding.payload["detail"]


def test_the_model_version_names_the_fit_and_moves_with_the_horizon(ml_run):
    version = ml_run.forecast_model.version
    assert version.startswith("fc1-")
    assert all(f.model_version == version for f in ml_run.forecast_findings)
    # A different horizon is a different model, and the version says so.
    from app.ml.base import model_version

    assert model_version("fc1", horizon=365) != model_version("fc1", horizon=200)


def test_the_panel_never_claims_more_than_a_truncated_sample_supports(ml_run):
    """The honesty rules, checked in the words that reach a screen."""
    reading = ml_run.finding("forecast", FIXTURE_A).payload["reading"]
    assert "Illustrative" in reading
    assert "truncated" in reading
    assert "zero points" in reading
    lowered = reading.lower()
    for overclaim in ("ai-", "guarantee", "will be late", "predicts fraud"):
        assert overclaim not in lowered
