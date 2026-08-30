"""Plain-language memo for one case.

**THIS IS A TEMPLATE, NOT AN LLM.** Nothing in this module calls a model, an
API or a service. It is a set of f-string phrasings joined into a paragraph in
a fixed order. The honest answer to "what generates the memo?" is "a template".
"Template now, LLM later" is a declared scoping decision (CLAUDE.md, honesty
rules) and this file stays truthful about it, including in the last sentence of
every memo it writes.

The memo says five things, in the order an officer needs them:

  1. what this work is, what it cost, and how long the sanction took
  2. where the money got to, and how long it has been quiet
  3. whether the description repeats, phrased as a REVIEW and never as an
     accusation - a repeated description is very often 244 legitimate street
     lights (DOMAIN-MODEL.md section h)
  4. whether the agency already carries a pattern this financial year
  5. what could NOT be checked, each with the reason it could not be - F5 in
     prose, so the gap in the evidence sits on the page beside the score
     instead of hiding behind a coverage badge

Point 5 is the one that matters most and is the easiest to drop. "We could not
check whether a photograph was filed" is a different sentence from "a
photograph was filed", and a memo that omitted the first would be read as
asserting the second.
"""

from __future__ import annotations

from ..constants import RULE_STATUS_FIRED, RULE_STATUS_SKIPPED, Availability

TEMPLATE_DISCLAIMER = "This memo is generated from a fixed template, not by a language model."

_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

# Why a rule could not be evaluated, in words an officer reads aloud. Keyed by
# the same three-valued vocabulary the trace and the storage layer use, so the
# distinction CLAUDE.md invariant 2 protects survives all the way into prose.
SKIP_PHRASINGS = {
    Availability.NOT_PUBLISHED.value: "this figure is not published for this work",
    Availability.PUBLISHED_ZERO.value: "the portal published this figure as zero, "
    "which leaves nothing to measure against",
    Availability.NOT_APPLICABLE.value: "this work has not yet reached the stage the rule reads",
}

# Where the generic phrasing above would overreach, the specific reason. A rule
# skipped because an agency sits below the vendor-concentration floor has not
# "failed to reach a stage", and saying so would be a small lie in the one
# sentence an officer is most likely to read out loud.
RULE_SKIP_PHRASINGS = {
    ("execution_delay", Availability.NOT_APPLICABLE.value): (
        "no completion has been reported for this work"
    ),
    ("asset_evidence_missing", Availability.NOT_PUBLISHED.value): (
        "the Image column is published only in the completed export, and this work has not "
        "been reported complete, so the portal has published nothing either way"
    ),
    ("duplicate_work", Availability.NOT_APPLICABLE.value): (
        "no other work under this agency carries a readable description to compare against"
    ),
    ("duplicate_work", Availability.NOT_PUBLISHED.value): (
        "the portal published no readable description for this work"
    ),
    ("split_sanction", Availability.NOT_PUBLISHED.value): (
        "the portal published no readable description for this work"
    ),
    ("vendor_concentration", Availability.NOT_APPLICABLE.value): (
        "this agency has disbursed Rs 50 lakh or less in total, below the floor at which one "
        "vendor's share carries any meaning"
    ),
    ("vendor_concentration", Availability.NOT_PUBLISHED.value): (
        "no payment row joins to this work, so it cannot be attributed to a vendor"
    ),
    ("utilisation_shortfall", Availability.NOT_PUBLISHED.value): (
        "no expenditure row joins to this work in the truncated export"
    ),
    ("stalled_work", Availability.NOT_PUBLISHED.value): (
        "no payment row joins to this work, so there is no last payment to measure from"
    ),
    ("account_underutilisation", Availability.NOT_PUBLISHED.value): (
        "no allocation is published for this work's member"
    ),
}

# One phrasing per rule id, for the fired rules the narrative sentences above
# do not already carry. A rule an officer adds to the YAML still gets a
# sentence - a generic one quoting the trace row - because the rulebook is
# theirs to edit and the memo must not block on us.
PHRASINGS = {
    "execution_delay": lambda hit: f"execution has run {hit['raw_value']:,} days "
    f"against a {hit['threshold']}-day threshold",
    "vendor_concentration": lambda hit: f"one vendor holds {hit['raw_value']}% of this "
    f"agency's disbursement, against a {hit['threshold']}% threshold",
    "status_payment_mismatch": lambda hit: "the work is reported complete with no payment "
    "recorded against it in the published expenditure export",
    "asset_evidence_missing": lambda hit: "no asset photograph was filed",
    "account_underutilisation": lambda hit: f"this member's account stands at "
    f"{hit['raw_value']}% of allocation, below the {hit['threshold']}% threshold",
    "utilisation_shortfall": lambda hit: f"disbursement is {abs(hit['raw_value'])}% below "
    "the sanctioned amount",
    "sanction_delay": lambda hit: f"the sanction issued {hit['raw_value']:,} days after the "
    f"recommendation, against a {hit['threshold']}-day threshold",
    "stalled_work": lambda hit: f"no payment has been recorded for {hit['raw_value']:,} days",
    "split_sanction": lambda hit: f"{hit['raw_value']} works under this agency carry an "
    "identical description",
    "duplicate_work": lambda hit: "the description closely matches other works under this agency",
}

# Rules already carried by a narrative sentence, so the "also" clause does not
# say the same thing twice.
_NARRATED = ("sanction_delay", "utilisation_shortfall", "stalled_work", "duplicate_work", "split_sanction")


def rupees(amount) -> str:
    """`199539` -> `Rs 1,99,539`. Indian digit grouping, whole rupees.

    MPLADS is administered in rupees and every threshold in the rulebook is a
    percentage or a count, so no memo ever prints paise.
    """
    if amount is None:
        return "an unpublished amount"
    text = str(abs(int(amount)))
    if len(text) > 3:
        head, tail = text[:-3], text[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        text = ",".join(parts + [tail])
    return f"Rs {'-' if amount < 0 else ''}{text}"


def long_date(value) -> str:
    """`date(2025, 11, 17)` -> `17 November 2025`."""
    if value is None:
        return "an unpublished date"
    return f"{value.day} {_MONTHS[value.month - 1]} {value.year}"


def join(parts) -> str:
    """'A', 'A and B', 'A, B and C' - read aloud in a hearing, not parsed."""
    parts = list(parts)
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return f"{', '.join(parts[:-1])} and {parts[-1]}"


def case_facts(work, sanction, payments, completion, agency_name=None) -> dict:
    """The narrative facts a memo needs, pulled off the raw rows.

    Kept separate from the feature dictionary because none of these is a
    measurement the rulebook may read: they are the identifying details an
    officer needs to recognise the work, and no rule can address them.
    """
    from .derive import _field, disbursed_amount

    payments = list(payments or [])
    dates = sorted(
        d for d in (_field(p, "payment_date") for p in payments) if d is not None
    )
    disbursed, _ = disbursed_amount(payments)
    return {
        "work_id": _field(work, "work_id_canon"),
        "description": _field(work, "description"),
        "agency": agency_name,
        "fy": _field(work, "fy"),
        "sanctioned_amt": _field(sanction, "sanctioned_amt"),
        "sanction_date": _field(sanction, "sanction_date"),
        "recommended_date": _field(sanction, "recommended_date"),
        "disbursed_amt": disbursed,
        "payment_count": len(payments),
        "last_payment_date": dates[-1] if dates else None,
        "completion_date": _field(completion, "completion_date"),
        "is_synthetic": bool(_field(work, "is_synthetic")),
    }


def build_memo(features, body, facts=None) -> str:
    """One paragraph an officer can act on and an auditor can re-derive."""
    facts = facts or {}
    hits = {hit["rule_id"]: hit for hit in body["rule_hits"]}
    fired = [hit for hit in body["rule_hits"] if hit["status"] == RULE_STATUS_FIRED]
    sentences = []

    if facts.get("is_synthetic"):
        sentences.append(
            "SYNTHETIC CONTROL. This is an injected, labelled row, not a published MPLADS "
            "work. It exists to exercise the certification hop, which no real row can "
            "populate, and it is excluded from every published aggregate."
        )

    sentences.append(_identification(features, facts))
    money = _money(features, facts)
    if money:
        sentences.append(money)
    duplicate = _duplicate(features, hits)
    if duplicate:
        sentences.append(duplicate)

    others = [
        _clause(hit) for hit in fired if hit["rule_id"] not in _NARRATED
    ]
    if others:
        sentences.append(f"The case also flags that {join(others)}.")

    corroboration = body.get("corroboration") or {}
    if corroboration.get("applied"):
        window = corroboration.get("window") or "the same financial year"
        sentences.append(
            f"This agency already carries {corroboration['high_case_count']} other HIGH "
            f"cases in {window}: one bad work is an incident, a pattern under one agency in "
            "one year is a posture."
        )
    elif corroboration:
        sentences.append(
            f"The agency pattern bonus was not awarded: it carries "
            f"{corroboration.get('high_case_count', 0)} other HIGH cases in "
            f"{corroboration.get('window')}, against a minimum of "
            f"{corroboration.get('min_high_cases')}."
        )

    skipped = [hit for hit in body["rule_hits"] if hit["status"] == RULE_STATUS_SKIPPED]
    if skipped:
        sentences.append(_not_evaluated(skipped, body))

    sentences.append(
        f"Score {body['score']} of {body['score_cap']}, {body['severity']}, under rulebook "
        f"{body['rulebook_version']}."
    )
    sentences.append(TEMPLATE_DISCLAIMER)
    return " ".join(sentences)


def _identification(features, facts) -> str:
    description = facts.get("description")
    named = f", '{description}'," if description else ", description not published,"
    text = (
        f"Work {facts.get('work_id')}{named} was sanctioned for "
        f"{rupees(facts.get('sanctioned_amt'))} on {long_date(facts.get('sanction_date'))}"
    )
    if facts.get("agency"):
        text += f" by {facts['agency']}"
    lag = features.get("sanction_lag_days")
    if lag is not None:
        text += (
            f", on a recommendation made {lag:,} days earlier on "
            f"{long_date(facts.get('recommended_date'))}"
        )
    return text + "."


def _money(features, facts) -> str | None:
    variance = features.get("variance_sanction_to_disbursement")
    if variance is None:
        if facts.get("payment_count") == 0:
            return (
                "No payment is recorded against this work in the published expenditure "
                "export, which is truncated and reaches only a sixth of sanctioned works, so "
                "how much of the sanction was drawn cannot be said either way."
            )
        return None
    count = facts.get("payment_count", 0)
    plural = "" if count == 1 else "s"
    text = (
        f"{rupees(facts.get('disbursed_amt'))} has been disbursed across {count} payment"
        f"{plural}, {abs(variance):.2f}% below the sanctioned amount"
    )
    silence = features.get("days_since_last_payment")
    if silence is not None:
        text += (
            f", and no payment has been recorded in the {silence:,} days since "
            f"{long_date(facts.get('last_payment_date'))}"
        )
    return text + "."


def _duplicate(features, hits) -> str | None:
    """Phrased as review, never as fraud. The wording here is not decoration."""
    count = features.get("same_desc_same_agency_count")
    duplicate_hit = hits.get("duplicate_work") or {}
    citation = duplicate_hit.get("citation") or {}
    cited = citation.get("matched_work_ids") or []
    fired = duplicate_hit.get("status") == RULE_STATUS_FIRED
    split_fired = (hits.get("split_sanction") or {}).get("status") == RULE_STATUS_FIRED
    if not fired and not split_fired:
        return None
    if count and count > 1:
        opening = f"The same description appears on {count} works under this agency"
    else:
        opening = "The description closely matches other work under this agency"
    if cited:
        opening += (
            f"; {len(cited)} {'is' if len(cited) == 1 else 'are'} cited on the trace row for "
            "comparison and should be opened before any conclusion is drawn, because "
            "repeated works of this kind are often entirely legitimate"
        )
    else:
        opening += ", which is a candidate for review and not a finding"
    return opening + "."


def _clause(hit) -> str:
    phrasing = PHRASINGS.get(hit["rule_id"])
    if phrasing is None or hit["raw_value"] is None:
        # Officer-added rule, or a value with no bespoke sentence: quote the
        # trace row verbatim rather than say nothing.
        return (
            f"{hit['label'].lower()} ({hit['raw_value']} against {hit['threshold']})"
        )
    return phrasing(hit)


def _not_evaluated(skipped, body) -> str:
    """Name every rule that could not run, WITH its reason. Never a bare count.

    Phrased as "not evaluated: <label>" rather than "<label> could not be
    checked", because a rule label is an assertion - "No asset photograph
    filed" - and must not read as a finding nobody made.
    """
    parts = []
    for hit in skipped:
        reason = RULE_SKIP_PHRASINGS.get(
            (hit["rule_id"], hit["skip_reason"]),
            SKIP_PHRASINGS.get(hit["skip_reason"], "the reading was unavailable"),
        )
        parts.append(f"{hit['label'].lower()} - {reason}")
    weight = sum(hit["weight"] for hit in skipped)
    return (
        f"Not evaluated: {join(parts)}. That is {weight} rulebook points that could not be "
        f"assessed either way, so this case is scored on {body['coverage_pct']}% coverage "
        "and the missing weight is not redistributed to the rules that did run."
    )
