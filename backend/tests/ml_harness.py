"""Running the four ML modules over the ingested corpus, once, for the tests.

Not a test module. The forest and the classifier are fitted once per session
and shared, because refitting per test would spend a minute proving nothing.

**Every tier is lazy.** A test module that only reads the clusters never pays
for a gradient-boosting fit, and - more usefully - each tier can be added to
the repository in its own commit without the harness importing a module that
does not exist yet.

It is deliberately thin. Every number the tests assert is produced by
`app/ml/`, never by this file: a harness that computed a value would be a
harness that could hand a test the right answer.
"""

from __future__ import annotations

from functools import cached_property

from sqlalchemy import select

from app.constants import SEVERITY_HIGH
from app.engine.score import compute
from app.models import Agency, Payment, Sanction, State, Vendor, Work


class MLRun:
    """All four tiers over the corpus the fixture tests already read."""

    def __init__(self, corpus):
        self.corpus = corpus
        self.session = corpus.session
        self.rulebook = corpus.rulebook

    # -- names -------------------------------------------------------------

    @cached_property
    def agency_names(self) -> dict:
        return dict(self.session.execute(select(Agency.id, Agency.name_canon)).all())

    @cached_property
    def vendor_names(self) -> dict:
        return dict(self.session.execute(select(Vendor.id, Vendor.name_canon)).all())

    @cached_property
    def state_names(self) -> dict:
        return dict(self.session.execute(select(State.id, State.name)).all())

    # -- the scored corpus, which every badge is read against ---------------

    @cached_property
    def bodies(self) -> dict:
        return self.corpus.score_all()

    @cached_property
    def fired_counts(self) -> dict:
        return {
            work_pk: sum(1 for hit in body["rule_hits"] if hit["status"] == "fired")
            for work_pk, body in self.bodies.items()
        }

    # -- tier 3: duplicates -------------------------------------------------

    @cached_property
    def clusters(self):
        from app.ml import duplicates

        rows = self.session.execute(
            select(Work.id, Work.work_id_canon, Work.agency_id, Work.description).join(
                Sanction, Sanction.work_id == Work.id
            )
        ).all()
        return duplicates.cluster(rows, self.corpus.context)

    @cached_property
    def cross_check(self) -> dict:
        from app.ml import duplicates

        return duplicates.cross_check_cosine(self.clusters)

    @cached_property
    def duplicate_findings(self) -> list:
        return self.clusters.findings(self.agency_names, self.cross_check)

    # -- tier 3: anomaly ----------------------------------------------------

    @cached_property
    def _anomaly(self):
        from app.ml import anomaly

        return anomaly.run(
            self.corpus.features, self.corpus.works, self.fired_counts, self.state_names
        )

    @property
    def anomaly_model(self):
        return self._anomaly[0]

    @property
    def anomaly_findings(self) -> list:
        return self._anomaly[1]

    # -- tier 3: forecast ---------------------------------------------------

    @cached_property
    def _forecast(self):
        from app.ml import forecast

        return forecast.run(
            self.corpus.features, self.corpus.works, self.corpus.sanctions, self.rulebook
        )

    @property
    def forecast_model(self):
        return self._forecast[0]

    @property
    def forecast_findings(self) -> list:
        return self._forecast[1]

    # -- tier 4: concentration ---------------------------------------------

    def payment_rows(self):
        """(agency_id, vendor_id, paid_amt) for every payment in the corpus."""
        return self.session.execute(
            select(Work.agency_id, Payment.vendor_id, Payment.paid_amt).join(
                Payment, Payment.work_id == Work.id
            )
        ).all()

    @cached_property
    def synthetic_agency_ids(self) -> set:
        """The labelled control's agency, excluded from published aggregates."""
        return {
            agency_id
            for (agency_id,) in self.session.execute(
                select(Agency.id).where(Agency.is_synthetic.is_(True))
            ).all()
        }

    def synthetic_agency(self, agency_id) -> bool:
        return agency_id in self.synthetic_agency_ids

    @cached_property
    def _concentration(self):
        from app.ml import concentration

        payment_rows = self.payment_rows()
        return concentration.run(
            payment_rows,
            {pk: self.corpus.works[pk] for pk in self.corpus.features},
            self.corpus.payments,
            self.agency_names,
            self.vendor_names,
        )

    @property
    def graph(self):
        return self._concentration[0]

    @property
    def graph_findings(self) -> list:
        return self._concentration[1]

    # -- lookups ------------------------------------------------------------

    def findings_for(self, kind) -> dict:
        """work pk -> finding, for ONE kind.

        Only the requested tier is touched. Building a dict of all four would
        fit every model to answer a question about one of them - and would make
        a test module depend on a tier that, mid-history, does not exist yet.
        """
        from app.ml.base import by_work

        sources = {
            "duplicate": lambda: self.duplicate_findings,
            "anomaly": lambda: self.anomaly_findings,
            "forecast": lambda: self.forecast_findings,
            "graph": lambda: self.graph_findings,
        }
        return by_work(sources[kind]())

    def pk(self, work_id_canon) -> int:
        return self.corpus.by_work_id[work_id_canon]

    def finding(self, kind, work_id_canon):
        return self.findings_for(kind)[self.pk(work_id_canon)]

    def body(self, work_id_canon) -> dict:
        return self.bodies[self.pk(work_id_canon)]

    def rescore(self, work_id_canon) -> dict:
        """Score the work again from scratch, with its corroboration bonus."""
        work_pk = self.pk(work_id_canon)
        return compute(
            self.corpus.features[work_pk],
            self.rulebook,
            self.corpus.corroboration_count(work_pk),
            self.corpus.corroboration_evidence(work_pk),
        )

    def real(self, findings) -> list:
        """Drop the labelled control - it is excluded from every aggregate."""
        return [f for f in findings if not self.corpus.works[f.work_pk].is_synthetic]

    def high_severity(self) -> set:
        return {
            work_pk
            for work_pk, body in self.bodies.items()
            if body["severity"] == SEVERITY_HIGH
            and not self.corpus.works[work_pk].is_synthetic
        }
