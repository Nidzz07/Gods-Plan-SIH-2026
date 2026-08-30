"""F2 - the rulebook grammar, and the three-valued skip it extends it with."""

from __future__ import annotations

import pytest

from app.constants import Availability
from app.engine import derive as derive_mod
from app.engine import rulebook as rulebook_mod
from app.engine.rulebook import (
    MissingAvailabilityError,
    OPERATORS,
    RulebookError,
    evaluate,
    load,
    loads,
    severity_bands,
    validate,
    weight_total,
)

MINIMAL = """
version: "v-test"
severity_bands:
  high: 75
  medium: 50
rules:
  - id: sanction_delay
    label: Sanction issued long after recommendation
    field: sanction_lag_days
    operator: gt
    threshold: 180
    severity: medium
    weight: 16
corroboration:
  id: agency_pattern_bonus
  min_high_cases: 3
  weight: 10
"""


def features(values=None, availability=None):
    """A feature set where anything unset is missing WITH a recorded reason."""
    values = dict(values or {})
    reasons = dict(availability or {})
    for key in derive_mod.FEATURE_KEYS:
        values.setdefault(key, None)
        if values[key] is None:
            reasons.setdefault(key, Availability.NOT_PUBLISHED)
    return derive_mod.FeatureSet(values, reasons)


# ---------------------------------------------------------------------------
# The shipped rulebook, against DOMAIN-MODEL.md section (g)
# ---------------------------------------------------------------------------

SHIPPED = {
    # rule_id: (field, operator, threshold, weight, severity)
    "utilisation_shortfall": ("variance_sanction_to_disbursement", "lt", -15, 22, "high"),
    "execution_delay": ("execution_days", "gt", 365, 20, "high"),
    "duplicate_work": ("duplicate_similarity", "gte", 0.85, 18, "high"),
    "sanction_delay": ("sanction_lag_days", "gt", 180, 16, "medium"),
    "stalled_work": ("days_since_last_payment", "gt", 270, 16, "medium"),
    "vendor_concentration": ("vendor_share_in_agency_pct", "gt", 60, 12, "medium"),
    "status_payment_mismatch": ("completed_without_payment", "eq", True, 12, "medium"),
    "split_sanction": ("same_desc_same_agency_count", "gte", 3, 10, "medium"),
    "asset_evidence_missing": ("asset_image_absent", "eq", True, 10, "low"),
    "account_underutilisation": ("mp_utilisation_pct", "lt", 25, 8, "low"),
}


def test_shipped_rulebook_is_the_one_the_domain_model_specifies(rulebook):
    got = {
        rule["id"]: (
            rule["field"],
            rule["operator"],
            rule["threshold"],
            rule["weight"],
            rule["severity"],
        )
        for rule in rulebook["rules"]
    }
    assert got == SHIPPED


def test_shipped_weights_total_144_and_the_bonus_is_10(rulebook):
    assert weight_total(rulebook) == 144
    assert rulebook["corroboration"]["weight"] == 10
    assert rulebook["corroboration"]["min_high_cases"] == 3


def test_every_threshold_carries_its_measured_firing_count():
    """CLAUDE.md invariant 6: a threshold with no measurement behind it is a guess.

    Read as text rather than through the parser, because a YAML comment is
    exactly what a loader throws away - and the comment is the evidence.
    """
    text = rulebook_mod.RULES_PATH.read_text(encoding="utf-8")
    blocks = text.split("  - id: ")[1:]
    assert len(blocks) == 10
    for block in blocks:
        rule_id = block.split("\n", 1)[0].strip()
        comments = "\n".join(line for line in block.splitlines() if line.strip().startswith("#"))
        assert "DATA-PROFILE" in comments, rule_id
        assert any(char.isdigit() for char in comments), rule_id


def test_shipped_rulebook_validates_against_the_feature_dictionary(rulebook):
    assert validate(rulebook, derive_mod.FEATURE_KEYS) is rulebook


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def test_load_reads_from_disk_on_every_call(tmp_path):
    """An officer's edit must reach the next evaluation without a restart."""
    path = tmp_path / "rules.yaml"
    path.write_text(MINIMAL, encoding="utf-8")
    assert load(path)["rules"][0]["threshold"] == 180

    path.write_text(MINIMAL.replace("threshold: 180", "threshold: 90"), encoding="utf-8")
    assert load(path)["rules"][0]["threshold"] == 90


def test_load_rejects_a_file_that_is_not_a_mapping(tmp_path):
    path = tmp_path / "rules.yaml"
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(RulebookError):
        load(path)


# ---------------------------------------------------------------------------
# Validation - load-time errors, never silent skips
# ---------------------------------------------------------------------------


def test_a_rule_naming_an_unknown_field_is_a_load_time_error():
    """The structural bar on the ML tier reaching the score (invariant 1).

    `anomaly_score` is not in the derived feature dictionary, so no rulebook
    edit - by us or by an officer in the UI - can make the scorer read one.
    """
    book = loads(MINIMAL.replace("field: sanction_lag_days", "field: anomaly_score"))
    with pytest.raises(RulebookError, match="anomaly_score"):
        validate(book, derive_mod.FEATURE_KEYS)


def test_an_unknown_operator_is_a_load_time_error():
    book = loads(MINIMAL.replace("operator: gt", "operator: roughly"))
    with pytest.raises(RulebookError, match="roughly"):
        validate(book, derive_mod.FEATURE_KEYS)


def test_a_duplicate_rule_id_is_a_load_time_error():
    doubled = loads(MINIMAL)
    doubled["rules"].append(dict(doubled["rules"][0], label="Duplicated on purpose"))
    with pytest.raises(RulebookError, match="appears twice"):
        validate(doubled, derive_mod.FEATURE_KEYS)


def test_a_skip_caveat_for_an_unknown_reason_is_a_load_time_error():
    book = loads(
        MINIMAL.replace(
            "    weight: 16",
            "    weight: 16\n    skip_caveats:\n      published: nope\n",
        )
    )
    with pytest.raises(RulebookError, match="published"):
        validate(book, derive_mod.FEATURE_KEYS)


# ---------------------------------------------------------------------------
# Operators - six, and no more
# ---------------------------------------------------------------------------


def test_the_six_operators_and_only_the_six():
    assert set(OPERATORS) == {"lt", "lte", "gt", "gte", "eq", "ne"}


@pytest.mark.parametrize(
    "operator,value,threshold,fires",
    [
        ("lt", 4, 5, True),
        ("lt", 5, 5, False),
        ("lte", 5, 5, True),
        ("lte", 6, 5, False),
        ("gt", 6, 5, True),
        ("gt", 5, 5, False),
        ("gte", 5, 5, True),
        ("gte", 4, 5, False),
        ("eq", True, True, True),
        ("eq", False, True, False),
        # `ne` is the operator NIGRANI adds to the inherited five.
        ("ne", 4, 5, True),
        ("ne", 5, 5, False),
    ],
)
def test_each_operator(operator, value, threshold, fires):
    assert OPERATORS[operator](value, threshold) is fires


def test_ne_is_evaluable_end_to_end():
    book = loads(MINIMAL.replace("operator: gt", "operator: ne"))
    hit = evaluate(features({"sanction_lag_days": 42}), book)[0]
    assert hit["status"] == "fired"
    assert hit["contribution"] == 16


# ---------------------------------------------------------------------------
# The three-valued skip - the extension over the inherited grammar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reason",
    [Availability.NOT_PUBLISHED, Availability.PUBLISHED_ZERO, Availability.NOT_APPLICABLE],
)
def test_all_three_availability_reasons_produce_differentiated_skips(reason):
    """Invariant 2 into the trace: a skip that cannot say why is not enough."""
    book = loads(MINIMAL)
    hit = evaluate(features(availability={"sanction_lag_days": reason}), book)[0]
    assert hit["status"] == "skipped"
    assert hit["skip_reason"] == reason.value
    assert hit["contribution"] == 0
    assert hit["raw_value"] is None


def test_a_skip_carries_the_rules_own_caveat_for_that_reason():
    book = loads(
        MINIMAL.replace(
            "    weight: 16",
            "    weight: 16\n    skip_caveats:\n"
            "      not_published: the recommendation date is not published\n"
            "      not_applicable: this work has not been recommended yet\n",
        )
    )
    published = evaluate(
        features(availability={"sanction_lag_days": Availability.NOT_PUBLISHED}), book
    )[0]
    applicable = evaluate(
        features(availability={"sanction_lag_days": Availability.NOT_APPLICABLE}), book
    )[0]
    assert published["caveat"] == "the recommendation date is not published"
    assert applicable["caveat"] == "this work has not been recommended yet"
    assert published["caveat"] != applicable["caveat"]


def test_a_none_with_no_recorded_reason_raises_rather_than_guessing():
    """Defaulting the reason is how a reporting gap starts reading as clean."""
    plain = {key: None for key in derive_mod.FEATURE_KEYS}
    with pytest.raises(MissingAvailabilityError, match="sanction_lag_days"):
        evaluate(plain, loads(MINIMAL))


def test_published_is_not_an_acceptable_skip_reason():
    """A rule that read a value is never skipped, so the enum's fourth member
    cannot appear on a skipped row."""
    with pytest.raises(MissingAvailabilityError, match="published"):
        evaluate(
            features(availability={"sanction_lag_days": Availability.PUBLISHED}),
            loads(MINIMAL),
        )


def test_a_passed_rule_is_not_a_skipped_rule():
    book = loads(MINIMAL)
    hit = evaluate(features({"sanction_lag_days": 10}), book)[0]
    assert hit["status"] == "passed"
    assert hit["skip_reason"] is None
    assert hit["raw_value"] == 10


# ---------------------------------------------------------------------------
# The trace row
# ---------------------------------------------------------------------------


def test_every_rule_produces_a_row_in_rulebook_order(rulebook):
    hits = evaluate(features({"sanction_lag_days": 400}), rulebook)
    assert [hit["rule_id"] for hit in hits] == [rule["id"] for rule in rulebook["rules"]]
    assert len(hits) == 10


def test_the_trace_carries_the_contract_keys_and_no_others(rulebook):
    hit = evaluate(features({"sanction_lag_days": 400}), rulebook)[3]
    assert set(hit) == {
        "rule_id",
        "label",
        "field",
        "raw_value",
        "operator",
        "threshold",
        "weight",
        "contribution",
        "severity",
        "status",
        "skip_reason",
        "citation",
        "caveat",
    }


def test_the_comparison_uses_the_measured_value_and_the_trace_shows_the_rounded_one(rulebook):
    """Rounding before comparing moves 11 works across duplicate_work's line.

    0.8495 rounds to 0.85 and would fire; measured, it does not. The engine
    compares what it measured and displays two decimals, which is what keeps it
    in step with DATA-PROFILE.md section 6.
    """
    hits = {
        hit["rule_id"]: hit
        for hit in evaluate(features({"duplicate_similarity": 0.8495}), rulebook)
    }
    hit = hits["duplicate_work"]
    assert hit["status"] == "passed"
    assert hit["raw_value"] == 0.85


def test_a_caveat_marked_fired_only_travels_on_a_fired_row(rulebook):
    """`account_underutilisation` explains how to READ its number, so it travels
    on a pass; `status_payment_mismatch` warns against OVER-reading a flag, so
    it travels only once the flag is raised."""
    passed = {
        hit["rule_id"]: hit
        for hit in evaluate(
            features({"mp_utilisation_pct": 90.0, "completed_without_payment": False}), rulebook
        )
    }
    fired = {
        hit["rule_id"]: hit
        for hit in evaluate(
            features({"mp_utilisation_pct": 90.0, "completed_without_payment": True}), rulebook
        )
    }
    assert passed["account_underutilisation"]["caveat"] is not None
    assert passed["status_payment_mismatch"]["caveat"] is None
    assert fired["status_payment_mismatch"]["caveat"] is not None


# ---------------------------------------------------------------------------
# Bands
# ---------------------------------------------------------------------------


def test_severity_bands_come_from_the_rulebook(rulebook):
    assert severity_bands(rulebook) == (75, 50)


def test_severity_bands_fall_back_to_the_shipped_values():
    """The fallback matches rules.yaml and app.constants: 75 and 50."""
    assert severity_bands({}) == (75, 50)
