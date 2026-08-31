"""Ablation endpoint - F9's surface. The measured gap report, read back.

**Read-only, and no measurement happens here.** `python -m app.ablation.run`
scores the corpus, measures the nine fields, ranks them and writes one
`ablation_findings` row per field. This router reads those rows. Re-measuring
per request would mean re-scoring 27,079 works inside an HTTP handler - the
same mistake the case list exists not to make - and it would also mean the
number on screen could differ from the number in the committed
`docs/reports/DATA-GAP-RECOMMENDATION.md`, which is generated from the same
run. One measurement, two renderings.

**Where each part of the response comes from, so nothing looks recomputed.**

* The per-field numbers, the rank and the extrapolation are columns and JSON
  blobs on `ablation_findings`, exactly as `ablation/run.rows_for` wrote them.
* `publish_as`, `reads_as`, `unlocks_rules` and `improves_rules` are the static
  declarations in `ablation/fields.py` - the field list itself, not a
  measurement - joined by key.
* `title`, `addressed_to`, `method` and the ranking criterion are the constants
  `ablation/report.py` and `ablation/rank.py` already define for the generated
  document, imported rather than restated so the API and the document cannot
  drift apart on what the method was.
* The severity bands in `corpus` are three indexed counts over `cases`.

**The two things this report is careful about are carried into the response.**
`basis` is the module's availability companion: `measured_skips` means rules do
read the field and are skipped for its absence; `no_rule_reads_it` means
nothing can be skipped, and the gap sits upstream of the rulebook rather than
being harmless. And `severity_band_effect` is a floor and a ceiling, never a
point estimate, because saying how many rules would fire is defensible while
saying which works they fire on is fabrication.

**Ministry-only, and DOMAIN-MODEL.md (k) did not settle it.** The matrix has
a row for every table this API reads except `ablation_findings`, which did not
exist when the matrix was written. The call made here, and now recorded in that
matrix: this is a report about MoSPI's own publishing - which fields the
ministry does not publish, and what the rulebook cannot evaluate for their
absence. It names no state, district, agency or member and contains no finding
about anyone; what it contains is a criticism of the data source, addressed to
the data source. A state nodal officer reading it would learn nothing about
their state, and a member reading it would learn only that the system that
scores their works has gaps - which the case sheet already tells them, per
case, in `unavailable_fields`.

The narrower reason to gate it: `GET /api/rulebook` is readable by all four
roles because the rulebook is the document by which an officer is being judged,
and everyone judged by a rule is entitled to read it. That argument does not
extend to a recommendation the ministry has not acted on yet.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ablation.fields import FIELDS
from ..ablation.rank import RANKING_CRITERION, RANKING_CRITERION_DETAIL
from ..ablation.report import ADDRESSEE, METHOD, TITLE
from ..auth import require_role
from ..constants import (
    ROLE_MINISTRY,
    RULE_WEIGHT_TOTAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from ..db import get_db
from ..models import AblationFinding, Case, User

router = APIRouter(prefix="/ablation", tags=["ablation"])

NOT_MEASURED = (
    "No ablation findings have been measured. Run `python -m app.ablation.run` in "
    "backend/, after `python -m ingest.run` and `python -m app.derive_all`."
)

DECLARED = {field.key: field for field in FIELDS}


def _finding(row: AblationFinding) -> dict:
    """One stored row plus its static declaration, in `report.as_dict`'s shape."""
    declared = DECLARED.get(row.field_key)
    attribution = json.loads(row.attribution_json) if row.attribution_json else {}
    extrapolation = json.loads(row.extrapolation_json) if row.extrapolation_json else None
    attributed = row.basis == "measured_skips"
    return {
        "field": row.field_key,
        "label": row.field_label,
        "gap_kind": row.gap_kind,
        "source": row.source,
        "basis": row.basis,
        "rank": row.rank,
        "rank_note": row.rank_note,
        "publish_as": row.publish_as,
        "reads_as": getattr(declared, "reads_as", None),
        "effort": row.effort,
        "unlocks_rules": list(getattr(declared, "unlocks_rules", ())),
        "improves_rules": list(getattr(declared, "improves_rules", ())),
        # Non-null exactly when `basis` is `no_rule_reads_it`. A zero that
        # explains itself is a measurement; a bare zero is a shrug.
        "zero_reason": attribution.get("zero_reason"),
        "attribution": {
            "rule_ids": attribution.get("rule_ids", []),
            "skip_reason": attribution.get("skip_reason"),
            "condition": attribution.get("condition"),
        },
        "measured": {
            "corpus_works": row.corpus_works,
            "rule_skips": row.rule_skips,
            "works_affected": row.works_affected,
            "unrealised_weight": row.unrealised_weight,
            "coverage_pct_now": row.coverage_pct_now,
            "coverage_pct_if_published": row.coverage_pct_if_published,
            "coverage_uplift_pct": row.coverage_uplift_pct,
            "per_rule": attribution.get("per_rule", []),
        },
        "extrapolated": (
            {
                "basis": "observed firing rate on the population where the rule is evaluable",
                "additional_fires_total": sum(
                    entry.get("additional_fires", 0) for entry in extrapolation
                ),
                "per_rule": extrapolation,
            }
            if attributed and extrapolation
            else None
        ),
        # A floor and a ceiling, never a point estimate. Between the two
        # endpoints the measurement licenses nothing.
        "severity_band_effect": (
            {"floor": row.band_change_floor, "ceiling": row.band_change_ceiling}
            if attributed
            else None
        ),
        "corroborating": json.loads(row.corroborating_json) if row.corroborating_json else [],
    }


@router.get("/report")
def get_report(
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(ROLE_MINISTRY)),
):
    """The ranked field table and the full measurement, as measured and stored.

    No response model, matching `GET /api/rulebook`: what comes back is a
    report whose shape belongs to `ablation/report.py`, and pinning it in
    Pydantic here would mean the API and the generated document could disagree
    about what a finding contains. The case detail IS modelled, because it is a
    finding about a work that the frontend renders column by column; this is a
    document about MoSPI's publishing.
    """
    rows = db.scalars(
        select(AblationFinding).order_by(
            # Ranked fields first, in rank order; the tied zeros after them, in
            # the order DATA-PROFILE.md section 8 lists them, which is the
            # order `ablation/run.rows_for` inserted them in. `rank.py` refuses
            # to invent a separator for the tie and this endpoint does not
            # supply one either.
            AblationFinding.rank.is_(None),
            AblationFinding.rank,
            AblationFinding.id,
        )
    ).all()
    if not rows:
        raise HTTPException(status_code=503, detail=NOT_MEASURED)

    findings = [_finding(row) for row in rows]
    head = rows[0]
    bands = {
        band: db.scalar(
            select(func.count())
            .select_from(Case)
            .where(Case.severity == band, Case.is_synthetic.is_(False))
        )
        for band in (SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW)
    }

    return {
        "title": TITLE,
        "addressed_to": ADDRESSEE,
        "corpus": {
            "corpus_as_of": head.measured_as_of,
            "corpus_works": head.corpus_works,
            "rule_weight_total": RULE_WEIGHT_TOTAL,
            # The corpus mean coverage as it stands. It is the same number on
            # every row - each field measures its uplift from this baseline -
            # so it is lifted out of the rows rather than repeated in them.
            "mean_coverage_pct": head.coverage_pct_now,
            "bands": bands,
            "rulebook_version": head.rulebook_version,
            "rulebook_sha256": head.rulebook_sha256,
            "synthetic_excluded": True,
        },
        "method": METHOD,
        "ranking": {
            "criterion": RANKING_CRITERION,
            "detail": RANKING_CRITERION_DETAIL,
            "ranked_fields": sum(1 for row in rows if row.rank is not None),
            "unranked_fields": sum(1 for row in rows if row.rank is None),
        },
        # The compact ranked table, the same columns the generated document
        # prints, so a screen can render it without walking every finding.
        "table": [
            {
                "rank": row.rank,
                "field": row.field_key,
                "label": row.field_label,
                "gap_kind": row.gap_kind,
                "basis": row.basis,
                "rule_skips": row.rule_skips,
                "works_affected": row.works_affected,
                "unrealised_weight": row.unrealised_weight,
                "coverage_uplift_pct": row.coverage_uplift_pct,
            }
            for row in rows
        ],
        "findings": findings,
    }
