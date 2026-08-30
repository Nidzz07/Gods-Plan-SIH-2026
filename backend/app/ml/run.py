"""`python -m app.ml.run` - compute all four ML tiers and write `ml_findings`.

Kept as its own entry point rather than folded into `python -m ingest.run`.
Two reasons, and the first is the important one:

**The ML tier must be re-runnable without re-ingesting, and skippable without
breaking anything.** A demo, a test and an officer's session all need a scored
corpus; none of them needs a fitted forest to exist first. If a model fails to
fit, or scikit-learn is not installed, NIGRANI still ingests, still derives,
still scores and still produces a full trace - because the score has never
depended on this package and this file is where that stays true.

Second, `backend/ingest/` is the loader for the twelve portal exports and
nothing else. A model fit is not a load.

The corroboration two-pass this module performs is the one
`engine.score.corroboration` describes and cannot perform for itself: whether a
peer case is HIGH depends on that case's own score. It is duplicated from
`tests/corpus.py` deliberately rather than imported - a `backend/` module that
imported from `tests/` would make the test harness a runtime dependency.

Output, on the committed corpus - 27,079 rows per kind, one per sanctioned work
including the labelled synthetic control, so no work is silently absent:

    duplicate  26,897 with a value   129 not_published,   53 not_applicable
    anomaly     3,261 with a value                    23,818 not_applicable
    forecast    6,829 with a value                    20,250 not_applicable
    graph      26,366 with a value                       713 not_applicable

Every row of the last three carries `contributes_to_score = False`.
"""

from __future__ import annotations

import sys
from collections import defaultdict

from sqlalchemy import select

from ..constants import (
    ML_KIND_ANOMALY,
    ML_KIND_DUPLICATE,
    ML_KIND_FORECAST,
    ML_KIND_GRAPH,
    SEVERITY_HIGH,
    Availability,
)
from ..db import SessionLocal
from ..engine import derive as derive_mod
from ..engine import rulebook as rulebook_mod
from ..engine.score import compute
from ..models import (
    Agency,
    Certification,
    Completion,
    Payment,
    Sanction,
    State,
    Vendor,
    Work,
)
from . import anomaly, concentration, duplicates, forecast
from .base import rebuild


class CorpusView:
    """Everything the four modules need, read once."""

    def __init__(self, session, rulebook):
        self.session = session
        self.rulebook = rulebook
        self.context = derive_mod.CorpusContext.from_session(session)
        self.works = {w.id: w for w in session.scalars(select(Work))}
        self.sanctions = {s.work_id: s for s in session.scalars(select(Sanction))}
        self.completions = {c.work_id: c for c in session.scalars(select(Completion))}
        self.certifications = {c.work_id: c for c in session.scalars(select(Certification))}
        self.payments = defaultdict(list)
        for payment in session.scalars(select(Payment)):
            self.payments[payment.work_id].append(payment)
        self.agency_names = dict(session.execute(select(Agency.id, Agency.name_canon)).all())
        self.vendor_names = dict(session.execute(select(Vendor.id, Vendor.name_canon)).all())
        self.state_names = dict(session.execute(select(State.id, State.name)).all())

        self.features = {
            work_pk: derive_mod.derive(
                self.works[work_pk],
                self.sanctions.get(work_pk),
                self.completions.get(work_pk),
                self.certifications.get(work_pk),
                self.payments.get(work_pk, []),
                self.context,
            )
            for work_pk in self.sanctions
        }

    def fired_counts(self) -> dict[int, int]:
        """How many rules fired per case, with the corroboration bonus resolved.

        Pass 1 scores with no bonus to get base severities; pass 2 counts OTHER
        HIGH cases under the same (agency, FY) and scores again. Only the fired
        RULE count is returned, because that is all the anomaly badge needs in
        order to say whether it confirms anything.
        """
        base = {
            work_pk: compute(features, self.rulebook, 0)["severity"]
            for work_pk, features in self.features.items()
        }
        peers = defaultdict(set)
        for work_pk, severity in base.items():
            if severity == SEVERITY_HIGH:
                work = self.works[work_pk]
                peers[(work.agency_id, work.fy)].add(work_pk)
        counts = {}
        for work_pk, features in self.features.items():
            work = self.works[work_pk]
            count = len(peers[(work.agency_id, work.fy)] - {work_pk})
            body = compute(features, self.rulebook, count)
            counts[work_pk] = sum(
                1 for hit in body["rule_hits"] if hit["status"] == "fired"
            )
        return counts


def _summarise(kind, findings) -> str:
    published = sum(1 for f in findings if f.availability == Availability.PUBLISHED)
    reasons = defaultdict(int)
    for finding in findings:
        if finding.availability != Availability.PUBLISHED:
            reasons[finding.availability.value] += 1
    tail = ", ".join(f"{count} {reason}" for reason, count in sorted(reasons.items()))
    return f"  {kind:10s} {len(findings):6d} rows   {published:6d} with a value" + (
        f", {tail}" if tail else ""
    )


def main() -> int:
    session = SessionLocal()
    try:
        rulebook = rulebook_mod.validate(rulebook_mod.load(), derive_mod.FEATURE_KEYS)
        view = CorpusView(session, rulebook)
        print(f"corpus: {len(view.features)} sanctioned works")

        rows = session.execute(
            select(Work.id, Work.work_id_canon, Work.agency_id, Work.description).join(
                Sanction, Sanction.work_id == Work.id
            )
        ).all()
        clusters = duplicates.cluster(rows, view.context)
        cross_check = duplicates.cross_check_cosine(clusters)
        duplicate_findings = clusters.findings(view.agency_names, cross_check)

        fired = view.fired_counts()
        _, anomaly_findings = anomaly.run(
            view.features, view.works, fired, view.state_names
        )

        forecast_model, forecast_findings = forecast.run(
            view.features, view.works, view.sanctions, rulebook
        )

        payment_rows = session.execute(
            select(Work.agency_id, Payment.vendor_id, Payment.paid_amt).join(
                Payment, Payment.work_id == Work.id
            )
        ).all()
        graph, graph_findings = concentration.run(
            payment_rows,
            {pk: view.works[pk] for pk in view.features},
            view.payments,
            view.agency_names,
            view.vendor_names,
        )

        batches = (
            (ML_KIND_DUPLICATE, duplicate_findings),
            (ML_KIND_ANOMALY, anomaly_findings),
            (ML_KIND_FORECAST, forecast_findings),
            (ML_KIND_GRAPH, graph_findings),
        )
        # One rebuild for all four kinds: the table is dropped and recreated,
        # so a per-kind call would take the other three with it.
        written = rebuild(session, [f for _, batch in batches for f in batch])
        for kind, findings in batches:
            print(_summarise(kind, findings))
        print(f"  {'total':10s} {written:6d} rows written to ml_findings")

        print(
            f"\nclusters: {len(clusters.clusters_of_at_least(2))} of two or more over "
            f"{clusters.works_in_clusters_of_at_least(2)} works; "
            f"{len(clusters.clusters_of_at_least(3))} of three or more over "
            f"{clusters.works_in_clusters_of_at_least(3)} works"
        )
        print(f"forecast holdout: {forecast_model.metrics}")
        print(
            f"graph: {len(graph.agencies)} agencies, {len(graph.vendors)} vendors, "
            f"{len(graph.spanning_vendors())} vendors under more than one agency, "
            f"widest span {graph.max_span()}"
        )
        print(
            "\nEvery anomaly, forecast and graph row carries contributes_to_score = "
            "false. The score is the rulebook plus the corroboration bonus and nothing "
            "else (CLAUDE.md invariant 1)."
        )
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
