"""The plain-language memo - asserted to be a TEMPLATE, and asserted to be honest.

Two things are being protected here, and they are not the same thing.

**That it is a template.** `memo.py` is a set of f-strings joined in a fixed
order. "Template now, LLM later" is a declared scoping decision (CLAUDE.md
honesty rules), so the module must neither call a model nor let anyone read its
output as though one had. The first two tests hold that line: one greps the
module for a client library, the other asserts the disclaimer sentence is on
every memo the module can produce.

**That it does not overclaim.** The memo is the artefact an officer is most
likely to read aloud, so three of its clauses carry the honesty rules directly:
a duplicate cluster is a candidate for REVIEW and never fraud, a skipped rule
is named with the reason it could not be evaluated rather than omitted, and the
three availability reasons stay distinguishable all the way into prose
(CLAUDE.md invariant 2). A memo that dropped the skip clause would be read as
asserting the very findings nobody made.

The fixture memos at the bottom are the acceptance half: the same three cases
`docs/contract/fixtures.md` works by hand, run through the real corpus.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.constants import Availability
from app.engine import derive as derive_mod
from app.engine.memo import (
    PHRASINGS,
    RULE_SKIP_PHRASINGS,
    SKIP_PHRASINGS,
    TEMPLATE_DISCLAIMER,
    build_memo,
    case_facts,
    join,
    long_date,
    rupees,
)
from app.engine.rulebook import loads
from app.engine.score import compute_with_memo

from .conftest import FIXTURE_A, FIXTURE_B, FIXTURE_C, completion, payment, sanction, work

MEMO_SOURCE = Path(__file__).resolve().parents[1] / "app" / "engine" / "memo.py"

# A feature vector that fires enough rules for every clause to have something
# to say. Deliberately the same shape as test_score.py's BASELINE so the two
# modules describe the same case.
BASELINE = {
    "variance_sanction_to_disbursement": -40.01,
    "variance_disbursement_to_certification": None,
    "sanction_lag_days": 333,
    "sanction_to_first_payment_days": 9,
    "first_payment_to_completion_days": 100,
    "execution_days": 400,
    "days_since_last_payment": 271,
    "duplicate_similarity": 0.4,
    "same_desc_same_agency_count": 15,
    "vendor_share_in_agency_pct": 17.35,
    "completed_without_payment": False,
    "asset_image_absent": True,
    "mp_utilisation_pct": 73.8,
    "payment_count": 1,
}

FACTS = {
    "work_id": "WS/MP001/2025-2026/000001",
    "description": "construction of a boundary wall",
    "agency": "TEST DISTRICT MAGISTRATE",
    "fy": "2025-2026",
    "sanctioned_amt": 199_539,
    "sanction_date": date(2025, 11, 17),
    "recommended_date": date(2024, 12, 19),
    "disbursed_amt": 119_711,
    "payment_count": 1,
    "last_payment_date": date(2025, 11, 26),
    "completion_date": None,
    "is_synthetic": False,
}


def memo_for(rulebook, features_factory, values=None, availability=None, count=0, facts=None):
    """Score a hand-built feature vector and return its memo."""
    features = features_factory(
        dict(BASELINE, **(values or {})),
        availability=availability,
        evidence={"duplicate_work": {"matched_work_ids": ["WS/MP001/2025-2026/2"]}},
    )
    body = compute_with_memo(features, rulebook, count, facts=dict(FACTS, **(facts or {})))
    return body["memo"], body


# ---------------------------------------------------------------------------
# It is a template, and it says so
# ---------------------------------------------------------------------------

# Assembled from fragments so this file does not match the grep it performs.
_CLIENT_LIBRARIES = tuple(
    "".join(parts)
    for parts in (
        ("open", "ai"),
        ("anthro", "pic"),
        ("langch", "ain"),
        ("transform", "ers"),
        ("requ", "ests"),
        ("htt", "px"),
        ("url", "lib.request"),
    )
)


def test_the_memo_module_calls_no_model_and_no_service():
    """The honesty rule, enforced by reading the module rather than trusting it.

    `memo.py` may not reach a model, an API or a network at all. If a future
    session wires one in, the honest move is to change the copy on the screen
    and in the pitch at the same moment - and this test is what makes that a
    deliberate act rather than a drift.
    """
    source = MEMO_SOURCE.read_text(encoding="utf-8").lower()
    for library in _CLIENT_LIBRARIES:
        assert library not in source, library


def test_the_module_docstring_states_it_is_a_template_not_an_llm():
    from app.engine import memo as memo_mod

    docstring = memo_mod.__doc__ or ""
    assert "TEMPLATE, NOT AN LLM" in docstring
    assert "template" in docstring.lower()


def test_every_memo_ends_by_saying_it_is_a_template(rulebook, features_factory):
    """Not a footnote and not a caption: the last sentence of the memo itself."""
    memo, _ = memo_for(rulebook, features_factory)
    assert memo.endswith(TEMPLATE_DISCLAIMER)
    assert "language model" in TEMPLATE_DISCLAIMER


# ---------------------------------------------------------------------------
# Formatting helpers - the memo is read aloud, so these are not cosmetic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "amount,expected",
    [
        (199_539, "Rs 1,99,539"),
        (119_711, "Rs 1,19,711"),
        (4_000_000, "Rs 40,00,000"),
        (1_000_000, "Rs 10,00,000"),
        (996_458, "Rs 9,96,458"),
        (500, "Rs 500"),
        (0, "Rs 0"),
        (-1_200, "Rs -1,200"),
    ],
)
def test_rupees_uses_indian_digit_grouping(amount, expected):
    """MPLADS is administered in rupees and read by Indian officers. 40,00,000."""
    assert rupees(amount) == expected


def test_rupees_names_an_unpublished_amount_rather_than_printing_zero():
    """A missing amount is not Rs 0, and the sentence must not say it is."""
    assert rupees(None) == "an unpublished amount"


def test_long_date_is_spelled_out_and_a_missing_date_says_so():
    assert long_date(date(2025, 11, 17)) == "17 November 2025"
    assert long_date(date(2026, 5, 14)) == "14 May 2026"
    assert long_date(None) == "an unpublished date"


@pytest.mark.parametrize(
    "parts,expected",
    [
        ([], ""),
        (["a"], "a"),
        (["a", "b"], "a and b"),
        (["a", "b", "c"], "a, b and c"),
    ],
)
def test_join_reads_aloud(parts, expected):
    assert join(parts) == expected


# ---------------------------------------------------------------------------
# The five things the memo says
# ---------------------------------------------------------------------------


def test_the_memo_identifies_the_work_its_cost_and_its_sanction_lag(
    rulebook, features_factory
):
    memo, _ = memo_for(rulebook, features_factory)
    assert "WS/MP001/2025-2026/000001" in memo
    assert "'construction of a boundary wall'" in memo
    assert "Rs 1,99,539" in memo
    assert "17 November 2025" in memo
    assert "TEST DISTRICT MAGISTRATE" in memo
    assert "333 days earlier on 19 December 2024" in memo


def test_the_memo_says_where_the_money_got_to_and_how_long_it_has_been_quiet(
    rulebook, features_factory
):
    memo, _ = memo_for(rulebook, features_factory)
    assert "Rs 1,19,711 has been disbursed across 1 payment," in memo
    assert "40.01% below the sanctioned amount" in memo
    assert "271 days since 26 November 2025" in memo


def test_a_work_with_no_payment_row_says_so_rather_than_saying_nothing(
    rulebook, features_factory
):
    """Fixture B's sentence. "We cannot say" is a finding; silence is not.

    A memo that simply omitted the money clause would read as a memo about a
    work whose disbursement was checked and found unremarkable.
    """
    memo, _ = memo_for(
        rulebook,
        features_factory,
        values={
            "variance_sanction_to_disbursement": None,
            "days_since_last_payment": None,
            "vendor_share_in_agency_pct": None,
            "payment_count": 0,
        },
        facts={"payment_count": 0, "disbursed_amt": None, "last_payment_date": None},
    )
    assert "No payment is recorded against this work" in memo
    assert "cannot be said either way" in memo


def test_the_synthetic_control_is_labelled_in_the_first_sentence(
    rulebook, features_factory
):
    """Invariant 12 on the page an officer reads, not in a footnote."""
    memo, _ = memo_for(rulebook, features_factory, facts={"is_synthetic": True})
    assert memo.startswith("SYNTHETIC CONTROL.")
    assert "excluded from every published aggregate" in memo


# ---------------------------------------------------------------------------
# A duplicate cluster is a candidate for review, never an accusation
# ---------------------------------------------------------------------------

FORBIDDEN_WORDS = ("fraud", "fraudulent", "duplicate payment", "ghost work", "embezzl")


def test_the_duplicate_clause_asks_for_review_and_never_alleges(
    rulebook, features_factory
):
    """The wording here is not decoration - it is DOMAIN-MODEL.md section (h).

    The largest cluster in the corpus is 244 street lights under one district
    magistrate, and the overwhelmingly likely explanation is 244 street lights.
    The flag buys ten minutes of an officer's attention; it does not allege
    anything, and the sentence must not either.
    """
    memo, _ = memo_for(rulebook, features_factory, values={"duplicate_similarity": 0.99})
    assert "The same description appears on 15 works under this agency" in memo
    assert "should be opened before any conclusion is drawn" in memo
    assert "often entirely legitimate" in memo
    lowered = memo.lower()
    for word in FORBIDDEN_WORDS:
        assert word not in lowered, word


def test_no_sentence_the_module_can_emit_alleges_fraud(rulebook, features_factory):
    """Every canned sentence, not only the ones this suite happens to render.

    Checked over the emitted prose rather than over the source file, because
    the source legitimately uses the word in a docstring that says never to
    use it. Two memos bracket the range: one where all ten rules fire and one
    where all ten are skipped, so between them every phrasing dictionary and
    every clause in `build_memo` is exercised.
    """
    everything_fires, _ = memo_for(
        rulebook,
        features_factory,
        values={
            "duplicate_similarity": 0.99,
            "vendor_share_in_agency_pct": 90.0,
            "completed_without_payment": True,
            "mp_utilisation_pct": 6.8,
        },
        count=25,
    )
    nothing_evaluates, _ = memo_for(
        rulebook,
        features_factory,
        values={rule: None for rule in BASELINE},
        availability={
            "variance_sanction_to_disbursement": Availability.NOT_PUBLISHED,
            "execution_days": Availability.NOT_APPLICABLE,
            "duplicate_similarity": Availability.NOT_APPLICABLE,
            "sanction_lag_days": Availability.NOT_PUBLISHED,
            "days_since_last_payment": Availability.NOT_PUBLISHED,
            "vendor_share_in_agency_pct": Availability.NOT_APPLICABLE,
            "completed_without_payment": Availability.NOT_PUBLISHED,
            "same_desc_same_agency_count": Availability.NOT_PUBLISHED,
            "asset_image_absent": Availability.NOT_PUBLISHED,
            "mp_utilisation_pct": Availability.PUBLISHED_ZERO,
        },
    )
    emitted = " ".join(
        (everything_fires, nothing_evaluates, *SKIP_PHRASINGS.values(), *RULE_SKIP_PHRASINGS.values())
    ).lower()
    for word in FORBIDDEN_WORDS:
        assert word not in emitted, word


def test_the_duplicate_clause_is_absent_when_neither_repetition_rule_fires(
    rulebook, features_factory
):
    memo, _ = memo_for(
        rulebook,
        features_factory,
        values={"duplicate_similarity": 0.10, "same_desc_same_agency_count": 1},
    )
    assert "under this agency" not in memo


# ---------------------------------------------------------------------------
# Corroboration - both directions
# ---------------------------------------------------------------------------


def test_the_corroboration_clause_states_the_count_when_awarded(
    rulebook, features_factory
):
    memo, body = memo_for(rulebook, features_factory, count=25)
    assert body["corroboration"]["applied"] is True
    assert "already carries 25 other HIGH cases" in memo
    assert "one bad work is an incident" in memo


def test_the_corroboration_clause_says_why_it_was_not_awarded(rulebook, features_factory):
    """The F4 negative control, in prose. Fixture B's case.

    An officer must be able to see the bonus NOT fire and understand why, so
    the clause is rendered with the count and the minimum rather than omitted.
    """
    memo, body = memo_for(rulebook, features_factory, count=2)
    assert body["corroboration"]["applied"] is False
    assert "was not awarded" in memo
    assert "2 other HIGH cases" in memo
    assert "against a minimum of 3" in memo


# ---------------------------------------------------------------------------
# The skip clause - CLAUDE.md invariant 2, in prose
# ---------------------------------------------------------------------------


def test_the_skip_clause_names_every_unevaluated_rule_with_its_reason(
    rulebook, features_factory
):
    memo, body = memo_for(
        rulebook,
        features_factory,
        values={
            "variance_sanction_to_disbursement": None,
            "days_since_last_payment": None,
            "vendor_share_in_agency_pct": None,
        },
    )
    assert [hit["rule_id"] for hit in body["rule_hits"] if hit["status"] == "skipped"] == [
        "utilisation_shortfall",
        "stalled_work",
        "vendor_concentration",
    ]
    assert "Not evaluated:" in memo
    assert "disbursement materially below sanction" in memo
    assert "no payment activity for an extended period" in memo
    assert "one vendor takes most of the agency's disbursement" in memo


def test_the_skip_clause_states_the_weight_the_coverage_and_the_non_redistribution(
    rulebook, features_factory
):
    """Fixture B's arithmetic in words: 50 points, 65% coverage, not reassigned."""
    memo, body = memo_for(
        rulebook,
        features_factory,
        values={
            "variance_sanction_to_disbursement": None,
            "days_since_last_payment": None,
            "vendor_share_in_agency_pct": None,
        },
    )
    assert body["coverage_pct"] == 65
    assert "That is 50 rulebook points that could not be assessed either way" in memo
    assert "scored on 65% coverage" in memo
    assert "not redistributed to the rules that did run" in memo


def test_a_case_with_nothing_skipped_carries_no_skip_clause(rulebook, features_factory):
    memo, body = memo_for(
        rulebook,
        features_factory,
        values={"variance_disbursement_to_certification": -25.0},
    )
    assert body["coverage_pct"] == 100
    assert "Not evaluated:" not in memo


@pytest.mark.parametrize(
    "reason,phrase",
    [
        (Availability.NOT_PUBLISHED, "not published"),
        (Availability.PUBLISHED_ZERO, "published this figure as zero"),
        (Availability.NOT_APPLICABLE, "not yet reached the stage"),
    ],
)
def test_all_three_availability_reasons_reach_prose_distinguishably(reason, phrase):
    """Invariant 2 end to end: three reasons, three sentences, no collapsing.

    `sanction_delay` is used because it carries no bespoke override, so what is
    being read here is the generic vocabulary itself rather than one rule's
    hand-written line.
    """
    assert phrase in SKIP_PHRASINGS[reason.value]
    assert len({SKIP_PHRASINGS[r.value] for r in Availability if r.value in SKIP_PHRASINGS}) == 3


def test_a_reporting_gap_and_a_stage_gap_read_as_different_sentences(
    rulebook, features_factory
):
    """Fixture A's two skips: one not_published, one not_applicable, one memo.

    "The portal has published nothing either way" and "no completion has been
    reported for this work" are different findings, and an officer reading the
    memo aloud must hear the difference.
    """
    memo, _ = memo_for(
        rulebook,
        features_factory,
        values={"execution_days": None, "asset_image_absent": None},
        availability={
            "execution_days": Availability.NOT_APPLICABLE,
            "asset_image_absent": Availability.NOT_PUBLISHED,
        },
    )
    assert "no completion has been reported for this work" in memo
    assert (
        "the Image column is published only in the completed export, and this work has not "
        "been reported complete, so the portal has published nothing either way"
    ) in memo


def test_a_skipped_rule_is_never_phrased_as_a_finding(rulebook, features_factory):
    """"No asset photograph filed" is an assertion; the label must not stand alone.

    The clause is "Not evaluated: <label> - <reason>", so the assertion is
    always immediately disarmed by the reason it could not be checked.
    """
    memo, _ = memo_for(
        rulebook,
        features_factory,
        values={"asset_image_absent": None},
        availability={"asset_image_absent": Availability.NOT_PUBLISHED},
    )
    assert "Not evaluated: no asset photograph filed - " in memo


def test_every_rule_skip_phrasing_is_keyed_to_a_real_rule_and_reason(rulebook):
    """A phrasing for a rule that no longer exists would silently never render."""
    rule_ids = {rule["id"] for rule in rulebook["rules"]}
    reasons = {reason.value for reason in Availability}
    for rule_id, reason in RULE_SKIP_PHRASINGS:
        assert rule_id in rule_ids, rule_id
        assert reason in reasons, reason


# ---------------------------------------------------------------------------
# Per-rule phrasings
# ---------------------------------------------------------------------------


def test_there_is_a_phrasing_for_every_shipped_rule(rulebook):
    assert {rule["id"] for rule in rulebook["rules"]} == set(PHRASINGS)


def test_an_officer_added_rule_quotes_the_trace_row_rather_than_saying_nothing(
    features_factory
):
    """The rulebook is the officer's to edit and the memo must not block on us."""
    book = loads(
        """
        version: "v-test"
        severity_bands: {high: 75, medium: 50}
        rules:
          - id: payment_count_floor
            label: Fewer payments than expected
            field: payment_count
            operator: lt
            threshold: 3
            severity: low
            weight: 5
        """
    )
    memo, _ = memo_for(book, features_factory, facts={})
    assert "fewer payments than expected (1 against 3)" in memo


def test_the_score_sentence_carries_the_cap_the_band_and_the_rulebook_version(
    rulebook, features_factory
):
    memo, body = memo_for(rulebook, features_factory)
    assert f"Score {body['score']} of 100, {body['severity']}, under rulebook v1.0.0." in memo


# ---------------------------------------------------------------------------
# case_facts - the identifying details, none of which any rule may read
# ---------------------------------------------------------------------------


def test_case_facts_reads_the_narrative_details_off_the_raw_rows():
    facts = case_facts(
        work(),
        sanction(),
        [payment(paid_amt=300_000, payment_date=date(2025, 6, 1)),
         payment(paid_amt=200_000, payment_date=date(2025, 9, 1))],
        completion(),
        agency_name="TEST DISTRICT MAGISTRATE",
    )
    assert facts["work_id"] == "WS/MP001/2025-2026/000001"
    assert facts["sanctioned_amt"] == 1_000_000
    assert facts["disbursed_amt"] == 500_000
    assert facts["payment_count"] == 2
    assert facts["last_payment_date"] == date(2025, 9, 1)
    assert facts["agency"] == "TEST DISTRICT MAGISTRATE"
    assert facts["is_synthetic"] is False


def test_case_facts_holds_no_key_the_rulebook_could_read():
    """None of these is a measurement, so none may be addressable from the YAML."""
    facts = case_facts(work(), sanction(), [payment()], completion())
    assert not set(facts) & set(derive_mod.FEATURE_KEYS) - {"work_id", "payment_count"}


def test_a_work_with_no_published_description_is_named_without_one(
    rulebook, features_factory
):
    memo, _ = memo_for(rulebook, features_factory, facts={"description": None})
    assert "description not published," in memo


# ---------------------------------------------------------------------------
# The fixture memos, on the real corpus
# ---------------------------------------------------------------------------


@pytest.mark.corpus
def test_fixture_a_memo_reads_the_way_the_contract_works_it(corpus):
    memo = corpus.score(FIXTURE_A, with_memo=True)["memo"]
    assert "Rs 1,99,539 on 17 November 2025 by DISTRICT MAGISTRATE JALAUN" in memo
    assert "333 days earlier on 19 December 2024" in memo
    assert "40.01% below the sanctioned amount" in memo
    assert "271 days since 26 November 2025" in memo
    assert "The same description appears on 15 works under this agency" in memo
    assert "already carries 25 other HIGH cases in FY2025-2026" in memo
    assert "That is 30 rulebook points" in memo
    assert "scored on 79% coverage" in memo
    assert "Score 92 of 100, HIGH, under rulebook v1.0.0." in memo
    assert memo.endswith(TEMPLATE_DISCLAIMER)


@pytest.mark.corpus
def test_fixture_b_memo_states_the_three_gaps_and_the_absent_bonus(corpus):
    """B is the graceful-degradation fixture, and the memo is where it shows."""
    memo = corpus.score(FIXTURE_B, with_memo=True)["memo"]
    assert "No payment is recorded against this work" in memo
    assert "execution has run 539 days against a 365-day threshold" in memo
    assert "The agency pattern bonus was not awarded" in memo
    assert "0 other HIGH cases in FY2024-2025, against a minimum of 3" in memo
    assert "That is 50 rulebook points" in memo
    assert "scored on 65% coverage" in memo
    assert "Score 60 of 100, MEDIUM, under rulebook v1.0.0." in memo


@pytest.mark.corpus
def test_fixture_c_memo_labels_itself_synthetic_before_it_says_anything_else(corpus):
    memo = corpus.score(FIXTURE_C, with_memo=True)["memo"]
    assert memo.startswith("SYNTHETIC CONTROL.")
    assert "excluded from every published aggregate" in memo
    assert "scored on 74% coverage" in memo
    assert "Score 20 of 100, LOW, under rulebook v1.0.0." in memo
