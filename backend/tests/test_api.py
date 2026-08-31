"""The API layer, over a real populated database.

Every test here runs against a COPY of `backend/nigrani.db` in a tmp_path, for
two reasons. The obvious one is that `POST .../notes` and `POST .../recompute`
append to `audit_log`, and a test suite that grew the developer's audit trail
by four rows per run would be writing history nobody asked for. The less
obvious one is that the materialisation test rebuilds four tables, and it has
to be able to do that without the developer losing their build.

The copy is the corpus, so these are acceptance tests: they assert that the
HTTP layer serves the numbers `docs/contract/fixtures.md` fixed and Phases 2,
3 and 4 produced, not that it serves numbers of the right shape. Where a value
appears below it is transcribed from `fixtures.md` and from nowhere else.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest
from sqlalchemy import select, text

from app.constants import RULE_WEIGHT_TOTAL, case_id_for
from app.engine import derive as derive_mod
from app.models import Sanction, Work

from .accounts import ROLE_MINISTRY_EMAIL
from .conftest import (
    FIXTURE_A,
    FIXTURE_B,
    FIXTURE_C,
    api_client,
    copy_corpus,
    provision_accounts,
    sessionmaker_on,
)

pytestmark = pytest.mark.corpus

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs" / "contract" / "case_detail.json"

CASE_A = case_id_for(FIXTURE_A)
CASE_B = case_id_for(FIXTURE_B)
CASE_C = case_id_for(FIXTURE_C)

# docs/contract/fixtures.md, the summary table. Transcribed from the document.
EXPECTED = {
    CASE_A: {
        "work_id": FIXTURE_A,
        "score": 92,
        "raw_score": 92,
        "severity": "HIGH",
        "coverage_pct": 79,
        "gap_hop": "sanction_to_disbursement",
        "slowest_lag": "recommend_to_sanction",
        "fired": 5,
        "passed": 3,
        "skipped": 2,
        "corroboration": 10,
        "is_synthetic": False,
    },
    CASE_B: {
        "work_id": FIXTURE_B,
        "score": 60,
        "raw_score": 60,
        "severity": "MEDIUM",
        "coverage_pct": 65,
        "gap_hop": None,
        "slowest_lag": "recommend_to_sanction",
        "fired": 4,
        "passed": 3,
        "skipped": 3,
        "corroboration": 0,
        "is_synthetic": False,
    },
    CASE_C: {
        "work_id": FIXTURE_C,
        "score": 20,
        "raw_score": 20,
        "severity": "LOW",
        "coverage_pct": 74,
        "gap_hop": "disbursement_to_certification",
        "slowest_lag": "first_payment_to_completion",
        "fired": 1,
        "passed": 6,
        "skipped": 3,
        "corroboration": 0,
        "is_synthetic": True,
    },
}


# ---------------------------------------------------------------------------
# The server these tests read
# ---------------------------------------------------------------------------
#
# `client` is a session-scoped fixture in `conftest.py`, shared with the auth
# and scoping modules: one copy of the corpus, one set of seeded accounts, one
# TestClient signed in as MINISTRY. The Ministry role is the widest scope
# (DOMAIN-MODEL.md (k)), so every acceptance assertion below still describes
# the whole corpus - and that this file passes unchanged under a real token is
# itself the claim, that adding authentication narrowed nobody entitled to the
# rows. `sessionmaker_on` and `copy_corpus` come from the same place, for the
# two tests further down that need a corpus copy of their own.


def get(client, url, **params):
    response = client.get(url, params=params or None)
    assert response.status_code == 200, f"{url} -> {response.status_code} {response.text[:300]}"
    return response.json()


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health_reports_the_build_steps_rather_than_only_liveness(client):
    """A green service over an empty database is the most misleading answer here."""
    body = get(client, "/health")
    assert body["status"] == "ok"
    assert body["service"] == "nigrani"
    assert body["data_as_of"] == "2026-08-24"
    assert body["cases"] == 27079
    assert body["rulebook_version"] == "v1.0.0"
    assert body["ml_findings"] > 0
    assert body["ablation_findings"] == 9


# ---------------------------------------------------------------------------
# GET /api/cases/{case_id} - the three fixtures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case_id", list(EXPECTED))
def test_the_case_sheet_serves_the_fixture_document_exactly(client, case_id):
    """Every scored value fixtures.md fixes, over HTTP, for A, B and C."""
    expected = EXPECTED[case_id]
    body = get(client, f"/api/cases/{case_id}")

    assert body["case_id"] == case_id
    assert body["work"]["work_id"] == expected["work_id"]
    assert body["score"] == expected["score"]
    assert body["raw_score"] == expected["raw_score"]
    assert body["severity"] == expected["severity"]
    assert body["coverage_pct"] == expected["coverage_pct"]
    assert body["gap_hop"] == expected["gap_hop"]
    assert body["slowest_lag"] == expected["slowest_lag"]
    assert body["corroboration"]["contribution"] == expected["corroboration"]
    assert body["work"]["is_synthetic"] is expected["is_synthetic"]

    statuses = [hit["status"] for hit in body["rule_hits"]]
    assert len(statuses) == 10, "all ten rules, including the passes and the skips"
    assert statuses.count("fired") == expected["fired"]
    assert statuses.count("passed") == expected["passed"]
    assert statuses.count("skipped") == expected["skipped"]


@pytest.mark.parametrize("case_id", list(EXPECTED))
def test_the_score_over_http_is_still_the_sum_an_officer_can_add_on_paper(client, case_id):
    """CLAUDE.md invariant 1, asserted on the wire and not only in the engine.

    The serialised score is the sum of the serialised contributions plus the
    serialised bonus. If any badge had leaked a point into the number on its
    way through the API, this is where it would show.
    """
    body = get(client, f"/api/cases/{case_id}")
    fired = sum(hit["contribution"] for hit in body["rule_hits"] if hit["status"] == "fired")
    assert body["raw_score"] == fired + body["corroboration"]["contribution"]
    assert body["score"] == min(body["raw_score"], body["score_cap"])
    for block in ("statistical", "forecast", "concentration"):
        assert body[block]["contribution"] == 0


@pytest.mark.parametrize("case_id", list(EXPECTED))
def test_coverage_is_weight_based_and_skipped_weight_is_not_redistributed(client, case_id):
    """Invariant 2's arithmetic, end to end."""
    body = get(client, f"/api/cases/{case_id}")
    hits = body["rule_hits"]
    assert sum(hit["weight"] for hit in hits) == RULE_WEIGHT_TOTAL
    skipped = sum(hit["weight"] for hit in hits if hit["status"] == "skipped")
    assert body["coverage_pct"] == round((RULE_WEIGHT_TOTAL - skipped) / RULE_WEIGHT_TOTAL * 100)
    for hit in hits:
        assert (hit["skip_reason"] is not None) == (hit["status"] == "skipped")
        # A skipped rule contributes zero and keeps its full undivided weight.
        if hit["status"] == "skipped":
            assert hit["contribution"] == 0


def test_fixture_a_carries_both_skip_reasons_and_says_which_is_which(client):
    """A skips one rule for `not_applicable` and one for `not_published`.

    fixtures.md standing caveat 3: that is the whole reason A is a better
    fixture than the constructed one it replaced. A reporting gap and a work
    that has not reached a stage are different findings, and the response has
    to keep them apart.
    """
    body = get(client, f"/api/cases/{CASE_A}")
    reasons = {
        hit["rule_id"]: hit["skip_reason"] for hit in body["rule_hits"] if hit["status"] == "skipped"
    }
    assert reasons == {
        "execution_delay": "not_applicable",
        "asset_evidence_missing": "not_published",
    }
    # And every skipped rule says so in prose too, with its reason.
    assert "Not evaluated:" in body["memo"]
    assert "has not been reported complete" in body["memo"]


def test_a_fired_duplicate_row_cites_its_evidence_and_calls_it_review(client):
    """DOMAIN-MODEL.md (h): the one model-fed rule earns its points by citation.

    A fired `duplicate_work` with a null citation is a failed test, not a
    degraded row - and the word on the row is "review", never "fraud".
    """
    body = get(client, f"/api/cases/{CASE_A}")
    hit = next(h for h in body["rule_hits"] if h["rule_id"] == "duplicate_work")
    assert hit["status"] == "fired"
    citation = hit["citation"]
    assert citation is not None
    assert len(citation["matched_work_ids"]) == 2
    assert citation["matched_case_ids"] == [
        case_id_for(work_id) for work_id in citation["matched_work_ids"]
    ]
    assert citation["cluster_size"] == 15
    assert "rapidfuzz" in citation["method"]
    lowered = (citation["reading"] + hit["caveat"]).lower()
    assert "review" in lowered
    assert "fraud" not in lowered


def test_fixture_b_skips_three_rules_for_not_published_and_none_for_passing(client):
    """B is the graceful-degradation fixture: 50 of 144 points never evaluated."""
    body = get(client, f"/api/cases/{CASE_B}")
    skipped = {
        hit["rule_id"]: hit["skip_reason"] for hit in body["rule_hits"] if hit["status"] == "skipped"
    }
    assert skipped == {
        "utilisation_shortfall": "not_published",
        "stalled_work": "not_published",
        "vendor_concentration": "not_published",
    }
    assert body["corroboration"]["applied"] is False
    assert body["corroboration"]["high_case_count"] == 0
    # The negative control is rendered, not omitted: an officer has to be able
    # to see the bonus fail to fire and understand why.
    assert body["corroboration"]["min_high_cases"] == 3


def test_fixture_c_shows_an_open_certification_hop_worth_zero_points(client):
    """The whole of the ablation module's headline, in one case.

    C's fund hop 2 is open at -25.00% beside a score of 20 and a LOW band,
    because rulebook v1.0.0 has no rule reading that hop. NIGRANI can see the
    shape of the gap and cannot price it.
    """
    body = get(client, f"/api/cases/{CASE_C}")
    hop = next(h for h in body["fund_ladder"]["hops"] if h["key"] == "disbursement_to_certification")
    assert hop["state"] == "open"
    assert hop["variance_pct"] == -25.0
    assert body["score"] == 20
    assert body["severity"] == "LOW"
    assert not any(hit["field"] == "variance_disbursement_to_certification" for hit in body["rule_hits"])
    # Labelled as synthetic in the response and in the first sentence of the
    # memo, not in a footnote (CLAUDE.md invariant 12).
    assert body["work"]["is_synthetic"] is True
    assert body["memo"].startswith("SYNTHETIC CONTROL.")


def test_the_certification_rung_is_not_published_on_a_real_work(client):
    body = get(client, f"/api/cases/{CASE_A}")
    rung = next(r for r in body["fund_ladder"]["rungs"] if r["key"] == "certified_amt")
    assert rung["amount"] is None
    assert rung["availability"] == "not_published"


def test_the_memo_says_it_is_a_template(client):
    """The honesty rule, asserted rather than trusted: memos are not generated text."""
    for case_id in EXPECTED:
        memo = get(client, f"/api/cases/{case_id}")["memo"]
        assert memo.endswith(
            "This memo is generated from a fixed template, not by a language model."
        )


# ---------------------------------------------------------------------------
# The contract file and the response move together (invariant 9)
# ---------------------------------------------------------------------------


def test_fixture_a_matches_the_frozen_contract_key_for_key(client):
    """`docs/contract/case_detail.json` IS the response, not a description of it.

    Keys beginning with an underscore are notes about the file and are removed
    before the comparison; everything else is compared as a whole object, so a
    renamed key, a dropped key or a moved value fails here rather than in a
    frontend six weeks later.
    """
    contract = {
        key: value
        for key, value in json.loads(CONTRACT_PATH.read_text(encoding="utf-8")).items()
        if not key.startswith("_")
    }
    assert get(client, f"/api/cases/{CASE_A}") == contract


def test_every_contract_key_is_a_field_the_schema_declares():
    """The other direction of invariant 9, without a server.

    A key present in the contract that `CaseDetail` does not declare would be
    silently dropped from every response, and a test that only compared the
    response against the contract would never see it.
    """
    from app.schemas import CaseDetail

    contract = {
        key
        for key in json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        if not key.startswith("_")
    }
    assert contract == set(CaseDetail.model_fields)


# ---------------------------------------------------------------------------
# GET /api/cases - ranking and filters
# ---------------------------------------------------------------------------


def test_the_list_is_ranked_worst_first(client):
    body = get(client, "/api/cases", limit=200)
    scores = [item["score"] for item in body["items"]]
    assert scores == sorted(scores, reverse=True)
    assert body["ranked_by"].startswith("score desc")
    assert body["total"] == 27078, "the labelled control is excluded by default"


def test_the_bands_are_the_ones_the_profile_records(client):
    """37 HIGH, 1,006 MEDIUM, 26,035 LOW over real works - DATA-PROFILE.md section 6."""
    counts = {
        band: get(client, "/api/cases", severity=band, limit=1)["total"]
        for band in ("HIGH", "MEDIUM", "LOW")
    }
    assert counts == {"HIGH": 37, "MEDIUM": 1006, "LOW": 26035}
    assert sum(counts.values()) == 27078


def test_filters_narrow_and_compose(client):
    everything = get(client, "/api/cases", limit=1)["total"]
    in_up = get(client, "/api/cases", state="Uttar Pradesh", limit=1)["total"]
    in_jalaun = get(client, "/api/cases", district="JALAUN", limit=1)["total"]
    high_in_jalaun = get(client, "/api/cases", district="JALAUN", severity="HIGH", limit=1)["total"]
    assert 0 < high_in_jalaun <= in_jalaun <= in_up < everything

    page = get(client, "/api/cases", district="JALAUN", severity="HIGH", limit=100)
    assert len(page["items"]) == high_in_jalaun
    assert {item["district"] for item in page["items"]} == {"JALAUN"}
    assert {item["severity"] for item in page["items"]} == {"HIGH"}


def test_an_agency_filter_selects_that_agency_only(client):
    page = get(client, "/api/cases", agency="DISTRICT MAGISTRATE JALAUN", limit=100)
    assert page["total"] > 0
    assert {item["agency"] for item in page["items"]} == {"DISTRICT MAGISTRATE JALAUN"}


def test_the_synthetic_control_is_out_of_the_list_until_it_is_asked_for(client):
    """Invariant 12: labelled rows stay out of published aggregates by default."""
    default_total = get(client, "/api/cases", limit=1)["total"]
    with_control = get(client, "/api/cases", include_synthetic=True, limit=1)["total"]
    assert with_control == default_total + 1

    # And when it IS asked for it comes back labelled, not silently mixed in.
    nashik = get(client, "/api/cases", include_synthetic=True, district="NASHIK", limit=500)
    synthetic = [item for item in nashik["items"] if item["is_synthetic"]]
    assert [item["case_id"] for item in synthetic] == [CASE_C]
    default_nashik = get(client, "/api/cases", district="NASHIK", limit=500)
    assert CASE_C not in {item["case_id"] for item in default_nashik["items"]}


def test_paging_does_not_drop_or_repeat_a_case(client):
    first = get(client, "/api/cases", severity="HIGH", limit=20, offset=0)["items"]
    second = get(client, "/api/cases", severity="HIGH", limit=20, offset=20)["items"]
    ids = [item["case_id"] for item in first + second]
    assert len(ids) == len(set(ids)) == 37


# ---------------------------------------------------------------------------
# Notes and recompute
# ---------------------------------------------------------------------------


def test_a_note_becomes_an_audit_event_and_nothing_else(client):
    """There is no notes table. A note IS an audit event, hash-chained."""
    before = get(client, f"/api/audit/{CASE_B}")["events"]
    response = client.post(
        f"/api/cases/{CASE_B}/notes",
        json={"text": "Payment register requested.", "actor_role": "district_authority"},
    )
    assert response.status_code == 201
    written = response.json()["event"]
    assert written["event"] == "NOTE_ADDED"
    assert written["payload"] == {"text": "Payment register requested."}
    assert written["actor_role"] == "district_authority"

    after = get(client, f"/api/audit/{CASE_B}")
    assert len(after["events"]) == len(before) + 1
    assert after["events"][-1]["id"] == written["id"]
    # The new row links to the one before it and its own hash still holds.
    assert after["events"][-1]["prev_hash"] == written["prev_hash"]
    assert after["rows_intact"] is True


def test_an_empty_note_is_refused(client):
    assert client.post(f"/api/cases/{CASE_B}/notes", json={"text": "   "}).status_code == 422
    assert client.post(f"/api/cases/{CASE_B}/notes", json={"text": ""}).status_code == 422


def test_a_note_on_an_unknown_case_is_a_404_and_writes_nothing(client):
    before = get(client, "/api/audit/chain")["rows"]
    assert client.post("/api/cases/NG-0000000000/notes", json={"text": "x"}).status_code == 404
    assert get(client, "/api/audit/chain")["rows"] == before


@pytest.mark.parametrize("case_id", list(EXPECTED))
def test_recompute_re_derives_against_the_snapshot_and_finds_no_difference(client, case_id):
    """Invariant 5, over HTTP.

    The rulebook has not changed since the cases were opened, so the honest
    answer is `identical: true` with an empty trace diff. What makes this a
    real test rather than a tautology is that the comparison is of the full
    ten-row trace - `tests/test_audit.py` drives the disagreeing case, with a
    snapshot deliberately diverged from today's file.
    """
    response = client.post(f"/api/cases/{case_id}/recompute")
    assert response.status_code == 200
    body = response.json()
    assert body["rulebook_version"] == "v1.0.0"
    assert body["trace_diff"] == []
    assert body["identical"] is True
    assert len(body["stored_trace"]) == len(body["recomputed_trace"]) == 10
    assert body["stored"] == body["recomputed"]


def test_recompute_leaves_the_stored_case_exactly_as_it_was(client):
    before = get(client, f"/api/cases/{CASE_A}")
    client.post(f"/api/cases/{CASE_A}/recompute")
    after = get(client, f"/api/cases/{CASE_A}")
    assert before == after


def test_recompute_writes_one_event_carrying_both_traces(client):
    before = get(client, f"/api/audit/{CASE_C}")["events"]
    client.post(f"/api/cases/{CASE_C}/recompute")
    after = get(client, f"/api/audit/{CASE_C}")["events"]
    assert len(after) == len(before) + 1
    event = after[-1]
    assert event["event"] == "SCORE_RECOMPUTED"
    # The before and after TRACE, not only the before and after number.
    assert len(event["payload"]["stored_trace"]) == 10
    assert len(event["payload"]["recomputed_trace"]) == 10


# ---------------------------------------------------------------------------
# The trail
# ---------------------------------------------------------------------------


def test_the_opening_trail_carries_the_four_events_the_domain_model_declares(client):
    events = get(client, f"/api/audit/{CASE_A}")["events"]
    kinds = [event["event"] for event in events]
    assert kinds[0] == "CASE_OPENED"
    assert kinds.count("RULE_FIRED") == 5, "one per fired rule on fixture A"
    assert "DUPLICATE_LINKED" in kinds
    assert "PATTERN_LINKED" in kinds, "the bonus was awarded, so the pattern is linked"


def test_a_case_that_earned_no_bonus_has_no_pattern_event(client):
    kinds = {event["event"] for event in get(client, f"/api/audit/{CASE_B}")["events"]}
    assert "PATTERN_LINKED" not in kinds


def test_the_whole_chain_is_intact(client):
    chain = get(client, "/api/audit/chain")
    assert chain["intact"] is True
    assert chain["broken_at"] is None
    assert chain["rows"] > 84_000


# ---------------------------------------------------------------------------
# Works, rulebook, analytics, ablation
# ---------------------------------------------------------------------------


def test_a_work_is_browsable_and_names_its_case(client):
    body = get(client, f"/api/works/{FIXTURE_A}")
    assert body["work"]["work_id"] == FIXTURE_A
    assert body["case_id"] == CASE_A
    assert body["sanctioned_amt"] == 199539
    assert body["recommended_amt"] is None
    assert body["recommended_availability"] == "not_published"
    assert len(body["payments"]) == 1
    assert body["certified_amt"] is None, "MoSPI publishes no certified amount for any real work"


def test_a_work_id_with_whitespace_is_canonicalised_before_the_lookup(client):
    assert get(client, f"/api/works/ {FIXTURE_A} ")["work"]["work_id"] == FIXTURE_A


def test_the_rulebook_endpoint_serves_the_yaml_and_says_whether_it_still_matches(client):
    body = get(client, "/api/rulebook")
    assert body["version"] == "v1.0.0"
    assert len(body["rules"]) == 10
    assert body["rule_weight_total"] == RULE_WEIGHT_TOTAL
    assert body["severity_bands_resolved"] == {"high": 75, "medium": 50}
    assert body["file_matches_stored_version"] is True
    assert body["cases_scored_under"]["yaml_sha256"] == body["file_sha256"]
    # The YAML reaches the client unfiltered: an officer adding a caveat to a
    # rule should see it without a code change.
    assert any(rule.get("skip_caveats") for rule in body["rules"])


def test_the_national_rollup_totals_the_case_list(client):
    body = get(client, "/api/analytics/national")
    assert body["total_cases"] == get(client, "/api/cases", limit=1)["total"]
    assert body["high_cases"] == 37
    assert body["medium_cases"] == 1006
    assert body["low_cases"] == 26035
    assert body["corroborated_cases"] == 191
    assert sum(row["cases"] for row in body["states"]) == body["total_cases"]
    assert body["top_states_by_high"][0]["state"] == "Uttar Pradesh"
    assert "truncated sample" in body["caption"]
    assert "not the national record" in body["caption"]


def test_the_state_and_district_rollups_agree_with_the_national_one(client):
    national = get(client, "/api/analytics/national")
    up = next(row for row in national["states"] if row["state"] == "Uttar Pradesh")
    state = get(client, "/api/analytics/state/Uttar Pradesh")
    assert state["summary"]["cases"] == up["cases"]
    assert state["summary"]["high_cases"] == up["high_cases"]
    assert sum(row["cases"] for row in state["districts"]) == up["cases"]

    jalaun = next(row for row in state["districts"] if row["district"] == "JALAUN")
    district = get(client, "/api/analytics/district/JALAUN")
    assert district["summary"]["cases"] == jalaun["cases"]
    assert district["state"] == "Uttar Pradesh"
    assert sum(row["cases"] for row in district["agencies"]) <= district["summary"]["cases"]
    assert district["cases"][0]["score"] >= district["cases"][-1]["score"]


def test_the_mp_endpoint_returns_the_account_ladder_and_a_named_peer_group(client):
    body = get(client, "/api/analytics/mp/91")
    assert body["mp"]["house"] == "rajya_sabha"
    assert body["mp"]["constituency"] is None, "Rajya Sabha members are seated by state"
    term = next(ladder for ladder in body["account"] if ladder["fy"] == "term_to_date")
    assert [rung["key"] for rung in term["rungs"]] == [
        "allocated_amt",
        "sanctioned_amt",
        "disbursed_amt",
    ]
    assert term["mp_utilisation_pct"] == pytest.approx(73.80, abs=0.01)
    assert 0 < body["utilisation_percentile"] <= 100
    assert body["utilisation_peers"] > 100
    assert "members holding both" in body["utilisation_peer_group"]
    assert body["portfolio"]["cases"] > 0


def test_the_ablation_report_is_the_ranked_table_the_module_measured(client):
    """Read back from `ablation_findings`, not re-measured in the router."""
    body = get(client, "/api/ablation/report")
    assert body["ranking"]["criterion"] == "total unrealised rulebook weight, measured"
    assert body["ranking"]["ranked_fields"] == 2
    assert body["ranking"]["unranked_fields"] == 7
    assert len(body["findings"]) == len(body["table"]) == 9

    first, second = body["table"][0], body["table"][1]
    assert (first["rank"], first["field"]) == (1, "expenditure_linkage")
    assert first["rule_skips"] == 70647
    assert first["works_affected"] == 23549
    assert first["unrealised_weight"] == 1177450
    assert (second["rank"], second["field"]) == (2, "asset_image_publication_scope")
    assert second["unrealised_weight"] == 141040

    # The seven fields the current rulebook cannot price are reported as a tie
    # at zero, each saying WHY it is zero rather than shrugging.
    zeros = [row for row in body["findings"] if row["basis"] == "no_rule_reads_it"]
    assert len(zeros) == 7
    for row in zeros:
        assert row["rank"] is None
        assert row["measured"]["unrealised_weight"] == 0
        assert row["zero_reason"]
        assert row["extrapolated"] is None
        assert row["severity_band_effect"] is None

    # A floor and a ceiling, never a point estimate.
    effect = body["findings"][0]["severity_band_effect"]
    assert effect["floor"] <= effect["ceiling"]
    assert body["corpus"]["synthetic_excluded"] is True
    assert body["corpus"]["rule_weight_total"] == RULE_WEIGHT_TOTAL


# ---------------------------------------------------------------------------
# 404s
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "/api/cases/NG-0000000000",
        "/api/works/WS/MP999/1999-2000/000000",
        "/api/audit/NG-0000000000",
        "/api/analytics/state/Atlantis",
        "/api/analytics/district/ATLANTIS",
        "/api/analytics/mp/999999",
    ],
)
def test_an_unknown_id_is_a_404(client, url):
    """404 rather than 403 or an empty body, and the same once roles exist.

    A 403 would confirm that another district's case id is real, which is a
    scoping leak spelled with a status code (docs/api/ROLE-SCOPING-PLAN.md).
    """
    response = client.get(url)
    assert response.status_code == 404
    assert response.json()["detail"]


# ---------------------------------------------------------------------------
# The scoped context, and the materialisation step
# ---------------------------------------------------------------------------


def test_the_scoped_context_reproduces_the_corpus_wide_one(db_session, corpus):
    """The claim `routers/cases.case_context` rests on, checked over every work.

    A work's four corpus-dependent features are determined entirely by its
    agency (similarity, cluster size, vendor share) and by its member
    (account utilisation). So a context built from one agency's rows must agree
    with the corpus-wide context on every work in that agency - and this walks
    all 638 agencies that carry a sanctioned work, which between them are every
    case in the corpus.

    Checking it per agency rather than per work is what makes the check
    affordable; it is not weaker, because the scoped context for two works
    under one agency is the same object built twice.
    """
    from app.routers.cases import case_context

    global_context = corpus.context
    by_agency: dict = defaultdict(list)
    for work_pk in corpus.sanctions:
        by_agency[corpus.works[work_pk].agency_id].append(work_pk)

    checked = 0
    for agency_id, work_pks in by_agency.items():
        scoped = case_context(db_session, corpus.works[work_pks[0]])
        for work_pk in work_pks:
            assert scoped.similarity.get(work_pk) == global_context.similarity.get(work_pk)
            assert scoped.cluster_size.get(work_pk) == global_context.cluster_size.get(work_pk)
            assert scoped.normalised.get(work_pk) == global_context.normalised.get(work_pk)
            assert scoped.similarity_peers.get(work_pk) == global_context.similarity_peers.get(
                work_pk
            )
            checked += 1
        if agency_id is not None:
            assert scoped.agency_disbursed.get(agency_id) == global_context.agency_disbursed.get(
                agency_id
            )
    assert checked == len(corpus.sanctions)


def test_the_scoped_context_derives_the_fixtures_identically(db_session, corpus):
    """The same claim one level up: identical FEATURES, not merely inputs."""
    from app.routers.cases import features_for

    for work_id in (FIXTURE_A, FIXTURE_B, FIXTURE_C):
        work = corpus.works[corpus.by_work_id[work_id]]
        scoped = features_for(db_session, work)
        wide = corpus.features_for(work_id)
        assert dict(scoped) == dict(wide)
        assert scoped.availability == wide.availability
        assert scoped.evidence == wide.evidence


def test_the_materialisation_step_is_idempotent(tmp_path):
    """Run it twice, same case count, same scores, same hash chain.

    Run one is whatever produced the copied database; run two happens here. The
    audit chain is compared as well as the scores, because every timestamp the
    build writes is `DATA_AS_OF` rather than a wall clock - which is what makes
    the chain a property of the corpus rather than of the moment somebody
    happened to run the command.
    """
    from app.derive_all import materialise

    engine, factory = sessionmaker_on(copy_corpus(tmp_path / "nigrani.db"))
    try:
        with factory() as session:
            before = session.execute(
                text(
                    "SELECT case_id, score, raw_score, severity, coverage_pct, gap_hop, "
                    "slowest_lag, corroboration_bonus FROM cases ORDER BY case_id"
                )
            ).all()
            chain_before = session.execute(
                text("SELECT COUNT(*), MAX(row_hash) FROM audit_log")
            ).one()
            hits_before = session.execute(text("SELECT COUNT(*) FROM rule_hits")).scalar_one()

        with factory() as session:
            counts = materialise(session)

        with factory() as session:
            after = session.execute(
                text(
                    "SELECT case_id, score, raw_score, severity, coverage_pct, gap_hop, "
                    "slowest_lag, corroboration_bonus FROM cases ORDER BY case_id"
                )
            ).all()
            chain_after = session.execute(
                text("SELECT COUNT(*), MAX(row_hash) FROM audit_log")
            ).one()
            hits_after = session.execute(text("SELECT COUNT(*) FROM rule_hits")).scalar_one()
            rolled = session.execute(text("SELECT SUM(cases) FROM rollup_state")).scalar_one()

        assert counts["cases"] == len(before) == len(after)
        assert after == before, "a second run reproduced every stored score exactly"
        assert hits_after == hits_before == counts["cases"] * 10
        assert chain_after == chain_before, "and the same audit hash chain"
        assert rolled == counts["cases"] - counts["synthetic"]
    finally:
        engine.dispose()


def test_the_analytics_endpoints_refuse_a_stale_rollup(tmp_path):
    """The guard that makes the DDL-built rollup tables safe.

    They are not declared in `models.py`, so `ingest/run.py`'s `drop_all` does
    not know about them; a re-ingest without a re-derive would leave them
    describing a corpus that no longer exists. Serving that silently would be
    worse than an error, because nobody would know to doubt it. Simulated here
    by rebuilding the rollups over a corpus with a case removed - done with
    DDL, because nothing in `backend/` may hold a row-removal helper
    (CLAUDE.md invariant 4).
    """
    from app.derive_all import rebuild_rollups

    engine, factory = sessionmaker_on(copy_corpus(tmp_path / "nigrani.db"))
    try:
        with engine.begin() as connection:
            # A rollup built over strictly fewer cases than `cases` holds.
            connection.execute(text("DROP VIEW IF EXISTS v_case_facts"))
            rebuild_rollups(connection)
            connection.execute(text("DROP TABLE rollup_state"))
            connection.execute(
                text(
                    "CREATE TABLE rollup_state AS SELECT * FROM v_case_facts "
                    "WHERE 0 = 1"
                )
            )

        # Signed in as Ministry, because `/api/analytics/national` is
        # Ministry-only: an anonymous request would 401 and prove nothing about
        # the staleness guard.
        provision_accounts(factory)
        with api_client(factory, email=ROLE_MINISTRY_EMAIL) as stale_client:
            response = stale_client.get("/api/analytics/national")
            assert response.status_code == 503
            assert "derive_all" in response.json()["detail"]
    finally:
        engine.dispose()


def test_the_corpus_the_api_serves_is_the_corpus_the_engine_scored(db_session):
    """Every sanctioned work has exactly one case, and no case has no work.

    Invariant 8's consequence: case ids are deterministic from the work id, so
    a case can be located from a work and the two populations must match
    exactly rather than approximately.
    """
    sanctioned = db_session.execute(
        select(Work.work_id_canon).join(Sanction, Sanction.work_id == Work.id)
    ).scalars().all()
    stored = db_session.execute(text("SELECT case_id FROM cases")).scalars().all()
    assert len(sanctioned) == len(stored)
    assert {case_id_for(work_id) for work_id in sanctioned} == set(stored)


def test_no_feature_key_reaches_the_api_that_the_engine_does_not_define():
    """A trace row can only ever read a field in the derived feature dictionary."""
    from app.engine.rulebook import load

    fields = {rule["field"] for rule in load()["rules"]}
    assert fields <= set(derive_mod.FEATURE_KEYS)
    # And no ML output is on that list, which is what structurally bars the
    # badge tiers from the score (CLAUDE.md invariant 1).
    assert not {"anomaly_score", "delay_risk", "hhi", "z_score"} & set(derive_mod.FEATURE_KEYS)
