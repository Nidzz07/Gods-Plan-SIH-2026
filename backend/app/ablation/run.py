"""`python -m app.ablation.run` - measure the gaps, rank them, write the report.

Reads the ingested corpus, scores it through `engine/` exactly as a case screen
would, reduces each case to the handful of facts `measure.py` needs, measures
all nine fields, ranks them, rebuilds `ablation_findings`, and writes
`docs/reports/DATA-GAP-RECOMMENDATION.md`.

**Read-only over everything that matters.** It calls `engine.score.compute` to
obtain the same trace an officer sees, and writes nothing back into `cases`,
`rule_hits` or `ml_findings`. No score anywhere in the corpus moves because
this ran.

**Idempotent, and here is why rather than merely that.** Three things could
have made a second run differ from a first, and each is closed:

* *The stored rows.* `ablation_findings` is dropped and recreated before the
  insert, the same idiom `ml/base.rebuild` and `ingest/run.py` use, so a second
  run replaces its own output instead of doubling it. It is DDL rather than a
  row removal because CLAUDE.md invariant 4 forbids any helper anywhere in
  `backend/` capable of removing a row, and the right response to an absolute
  is to obey it.
* *A timestamp.* Every row and the document carry `DATA_AS_OF`, the corpus
  as-of date, never a wall clock. A generated document that changed on every
  run could not be diffed, and a reader would have no way to tell a real
  movement from the clock.
* *The measurement itself.* It is arithmetic over rows that ingest wrote. The
  scoring pass is deterministic, the similarity ranking inside
  `derive.CorpusContext` is a stable sort, and nothing here samples, shuffles
  or fits anything.

`tests/test_ablation.py` asserts the document is byte-identical across two runs
rather than taking the three paragraphs above at their word.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict

from sqlalchemy import func, select

from ..constants import (
    DATA_AS_OF,
    REPO_ROOT,
    RULE_STATUS_FIRED,
    RULE_STATUS_PASSED,
    SEVERITY_HIGH,
)
from ..db import SessionLocal
from ..engine import derive as derive_mod
from ..engine import rulebook as rulebook_mod
from ..engine.rulebook import weight_total
from ..engine.score import compute
from ..models import (
    AblationFinding,
    Agency,
    Certification,
    Completion,
    Payment,
    Sanction,
    Vendor,
    Work,
)
from . import measure as measure_mod
from . import report as report_mod
from .fields import FIELDS
from .measure import RuleTrace, WorkRecord
from .rank import rank

REPORT_PATH = REPO_ROOT / "docs" / "reports" / "DATA-GAP-RECOMMENDATION.md"


# --------------------------------------------------------------------------
# Reading the corpus through the engine
# --------------------------------------------------------------------------


def build_records(session, rulebook) -> tuple:
    """Score every sanctioned work and reduce each case to a `WorkRecord`.

    The two-pass corroboration resolution is the one `engine.score.corroboration`
    describes and cannot perform for itself: whether a peer case is HIGH depends
    on that case's own score. It is repeated here rather than imported from
    `tests/corpus.py`, for the reason `ml/run.py` gives - a module under
    `backend/` that imported from `tests/` would make the test harness a runtime
    dependency.

    **The labelled synthetic control is excluded from the returned records**
    (CLAUDE.md invariant 12). It is scored, because dropping it before the
    corroboration pass would silently change nothing on this corpus and might
    not on the next; it is filtered out of the population every figure in the
    report is measured over.
    """
    context = derive_mod.CorpusContext.from_session(session)
    works = {w.id: w for w in session.scalars(select(Work))}
    sanctions = {s.work_id: s for s in session.scalars(select(Sanction))}
    completions = {c.work_id: c for c in session.scalars(select(Completion))}
    certifications = {c.work_id: c for c in session.scalars(select(Certification))}
    payments = defaultdict(list)
    for payment in session.scalars(select(Payment)):
        payments[payment.work_id].append(payment)

    features = {
        work_pk: derive_mod.derive(
            works[work_pk],
            sanctions.get(work_pk),
            completions.get(work_pk),
            certifications.get(work_pk),
            payments.get(work_pk, []),
            context,
        )
        for work_pk in sanctions
    }

    base = {
        work_pk: compute(feature_set, rulebook, 0)["severity"]
        for work_pk, feature_set in features.items()
    }
    peers = defaultdict(set)
    for work_pk, severity in base.items():
        if severity == SEVERITY_HIGH:
            work = works[work_pk]
            peers[(work.agency_id, work.fy)].add(work_pk)

    records = []
    for work_pk, feature_set in features.items():
        work = works[work_pk]
        if work.is_synthetic:
            continue
        count = len(peers[(work.agency_id, work.fy)] - {work_pk})
        body = compute(feature_set, rulebook, count)
        completion = completions.get(work_pk)
        records.append(
            WorkRecord(
                work_pk=work_pk,
                raw_score=body["raw_score"],
                score=body["score"],
                severity=body["severity"],
                hits=tuple(
                    RuleTrace(
                        rule_id=hit["rule_id"],
                        status=hit["status"],
                        weight=hit["weight"],
                        skip_reason=hit["skip_reason"],
                    )
                    for hit in body["rule_hits"]
                ),
                payment_count=feature_set["payment_count"],
                has_completion_date=(
                    completion is not None and completion.completion_date is not None
                ),
                is_synthetic=False,
            )
        )
    records.sort(key=lambda record: record.work_pk)
    return tuple(records)


# --------------------------------------------------------------------------
# The corroborating figures - real query results, never ranking inputs
# --------------------------------------------------------------------------


def corpus_measures(session, records) -> dict:
    """Every figure `fields.py` may cite beside a field, resolved once.

    Each is a query or a count over the trace. They describe the shape of a gap
    the ranking criterion measures at zero; `rank.py` explains at length why
    they are reported beside the criterion rather than folded into it.
    """
    matched = session.execute(
        select(Sanction.recommended_amt, Sanction.sanctioned_amt)
        .join(Work, Work.id == Sanction.work_id)
        .where(Work.is_synthetic.is_(False), Sanction.recommended_availability == "published")
    ).all()

    fired = defaultdict(int)
    passed = defaultdict(int)
    for record in records:
        for hit in record.hits:
            if hit.status == RULE_STATUS_FIRED:
                fired[hit.rule_id] += 1
            elif hit.status == RULE_STATUS_PASSED:
                passed[hit.rule_id] += 1

    with_payment = sum(1 for record in records if record.payment_count > 0)
    with_completion = sum(1 for record in records if record.has_completion_date)

    return {
        "corpus_works": len(records),
        "degeneracy_matched": len(matched),
        "degeneracy_differing": sum(1 for rec, sanc in matched if rec != sanc),
        "recommended_not_published": session.scalar(
            select(func.count())
            .select_from(Sanction)
            .join(Work, Work.id == Sanction.work_id)
            .where(
                Work.is_synthetic.is_(False),
                Sanction.recommended_availability == "not_published",
            )
        ),
        # Every real work: MoSPI publishes no certified amount for any of them,
        # and the one row in `certifications` is the labelled control.
        "certification_not_published": len(records),
        "certification_rows": session.scalar(select(func.count()).select_from(Certification)),
        "works_with_payment": with_payment,
        "works_without_payment": len(records) - with_payment,
        "works_without_completion": len(records) - with_completion,
        "paid_without_completion": sum(
            1
            for record in records
            if record.payment_count > 0 and not record.has_completion_date
        ),
        "asset_image_published": with_completion,
        "asset_evidence_fires": fired["asset_evidence_missing"],
        "asset_evidence_passes": passed["asset_evidence_missing"],
        "duplicate_work_fires": fired["duplicate_work"],
        "split_sanction_fires": fired["split_sanction"],
        "vendor_concentration_fires": fired["vendor_concentration"],
        # Counted through a join to a real work rather than by matching the
        # control's name, so the exclusion survives a rename of the fixture.
        "vendors": session.scalar(
            select(func.count(func.distinct(Payment.vendor_id)))
            .join(Work, Work.id == Payment.work_id)
            .where(Work.is_synthetic.is_(False), Payment.vendor_id.is_not(None))
        ),
        "agencies": session.scalar(
            select(func.count(func.distinct(Work.agency_id)))
            .where(Work.is_synthetic.is_(False), Work.agency_id.is_not(None))
        ),
        # Rendered rather than raw: rupees at this scale are read in crore, and
        # a bare eleven-digit integer in a table is a number nobody checks.
        "sanctioned_value": _crore(
            session.scalar(
                select(func.sum(Sanction.sanctioned_amt))
                .join(Work, Work.id == Sanction.work_id)
                .where(Work.is_synthetic.is_(False))
            )
        ),
    }


def _crore(rupees) -> str:
    return f"Rs {(rupees or 0) / 1e7:,.2f} crore"


def resolve_corroborating(entries, measures) -> dict:
    """Turn each field's declared (label, measure_key) pairs into (label, value)."""
    resolved = {}
    for entry in entries:
        pairs = []
        for label, key in entry.corroborating:
            if key not in measures:
                raise KeyError(
                    f"field {entry.key!r} cites corroborating measure {key!r}, which "
                    "`corpus_measures` does not produce. Every figure in the report is a "
                    "query result; a citation with nothing behind it is the defect this "
                    "raises rather than renders."
                )
            pairs.append((label, measures[key]))
        resolved[entry.key] = tuple(pairs)
    return resolved


# --------------------------------------------------------------------------
# Persistence - rebuilt, never appended to
# --------------------------------------------------------------------------


def rows_for(ranked, context) -> list:
    """One `ablation_findings` mapping per field, in ranked order."""
    rows = []
    for entry in ranked:
        measurement = entry.measurement
        field = measurement.field
        attributed = bool(measurement.attributions)
        rows.append(
            {
                "field_key": field.key,
                "field_label": field.label,
                "gap_kind": field.gap_kind,
                "source": field.source,
                "basis": field.basis,
                "rank": entry.position,
                "rank_note": entry.note,
                "corpus_works": measurement.corpus_works,
                "rule_skips": measurement.rule_skips,
                "works_affected": measurement.works_affected,
                "unrealised_weight": measurement.unrealised_weight,
                "coverage_pct_now": round(measurement.coverage_now, 4),
                "coverage_pct_if_published": round(measurement.coverage_if_published, 4),
                "coverage_uplift_pct": round(measurement.coverage_uplift, 4),
                "band_change_floor": measurement.band_range.floor,
                "band_change_ceiling": measurement.band_range.ceiling,
                "extrapolation_json": (
                    json.dumps(
                        [
                            {
                                "rule_id": attribution.rule_id,
                                "observed_firing_rate_pct": round(
                                    attribution.firing_rate * 100, 4
                                ),
                                "measured_over_works": attribution.evaluable,
                                "applied_to_skips": attribution.skips,
                                "additional_fires": attribution.extrapolated_fires,
                            }
                            for attribution in measurement.attributions
                        ],
                        sort_keys=True,
                    )
                    if attributed
                    else None
                ),
                "attribution_json": json.dumps(
                    {
                        "rule_ids": list(field.attribution.rule_ids) if attributed else [],
                        "skip_reason": field.attribution.skip_reason if attributed else None,
                        "condition": field.attribution.condition if attributed else None,
                        "zero_reason": field.zero_reason or None,
                        "per_rule": [
                            {
                                "rule_id": attribution.rule_id,
                                "weight": attribution.weight,
                                "skips": attribution.skips,
                                "unrealised_weight": attribution.unrealised_weight,
                            }
                            for attribution in measurement.attributions
                        ],
                    },
                    sort_keys=True,
                ),
                "corroborating_json": json.dumps(
                    [{"label": label, "value": value} for label, value in measurement.corroborating],
                    sort_keys=True,
                ),
                "publish_as": field.publish_as,
                "effort": field.effort,
                "measured_as_of": DATA_AS_OF,
                "rulebook_version": context["rulebook_version"],
                "rulebook_sha256": context["rulebook_sha256"],
            }
        )
    return rows


def store(session, rows) -> int:
    """Drop `ablation_findings`, recreate it, insert. Returns the row count.

    Idempotent by rebuild, exactly as `ml/base.rebuild` is, and DDL rather than
    a row removal for the same reason: CLAUDE.md invariant 4 is written as an
    absolute over the whole of `backend/`, and obeying it is cheaper than
    arguing that a derived cache should be an exception.
    """
    session.commit()
    bind = session.get_bind()
    AblationFinding.__table__.drop(bind, checkfirst=True)
    AblationFinding.__table__.create(bind)
    if rows:
        session.bulk_insert_mappings(AblationFinding, rows)
    session.commit()
    return len(rows)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def analyse(session) -> tuple:
    """Everything except the writing. Returns (ranked, context, records)."""
    yaml_text = rulebook_mod.RULES_PATH.read_text(encoding="utf-8")
    rulebook = rulebook_mod.validate(rulebook_mod.loads(yaml_text), derive_mod.FEATURE_KEYS)

    records = build_records(session, rulebook)
    measures = corpus_measures(session, records)
    corroborating = resolve_corroborating(FIELDS, measures)
    measurements = measure_mod.measure_all(FIELDS, records, rulebook, corroborating)
    ranked = rank(measurements)

    total_weight = weight_total(rulebook)
    context = {
        "corpus_as_of": DATA_AS_OF.isoformat(),
        "corpus_works": len(records),
        "rule_weight_total": total_weight,
        "mean_coverage_pct": round(measure_mod.mean_coverage(records, total_weight), 2),
        "bands": measure_mod.band_counts(records),
        "rulebook_version": rulebook.get("version"),
        "rulebook_sha256": hashlib.sha256(yaml_text.encode("utf-8")).hexdigest(),
        "synthetic_excluded": True,
    }
    return ranked, context, records


def main() -> int:
    session = SessionLocal()
    try:
        ranked, context, records = analyse(session)
        print(f"corpus: {len(records)} real sanctioned works, mean coverage "
              f"{context['mean_coverage_pct']}%")

        written = store(session, rows_for(ranked, context))
        print(f"ablation_findings: {written} rows rebuilt")

        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        markdown = report_mod.render_markdown(ranked, context)
        REPORT_PATH.write_text(markdown, encoding="utf-8", newline="\n")
        print(f"report: {REPORT_PATH.relative_to(REPO_ROOT).as_posix()} "
              f"({len(markdown.splitlines())} lines)")

        print()
        header = f"  {'#':>2}  {'field':34s} {'skips':>7} {'works':>7} {'weight':>10} {'uplift':>8}"
        print(header)
        for entry in ranked:
            measurement = entry.measurement
            print(
                f"  {str(entry.position) if entry.position else '-':>2}  "
                f"{measurement.field.key:34s} {measurement.rule_skips:7,d} "
                f"{measurement.works_affected:7,d} {measurement.unrealised_weight:10,d} "
                f"{measurement.coverage_uplift:+7.2f}pp"
            )
        print(
            "\nNo score in the corpus moved because this ran. This module measures what the "
            "rulebook could not evaluate; it never contributes a point to what it could "
            "(CLAUDE.md invariant 1)."
        )
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
