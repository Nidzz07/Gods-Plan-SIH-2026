"""Reading the ingested corpus through the engine, for the fixture tests.

Not a test module. This is the thin harness that turns `backend/nigrani.db`
into scored cases so the fixture tests can assert against real rows rather than
against values typed back in from `docs/contract/fixtures.md`.

The two-pass structure here is the one `engine.score.corroboration` describes
and cannot perform for itself: whether a peer case is HIGH depends on that
case's own score, so the corroboration count has to be resolved over the whole
corpus before any case can carry its bonus.

    pass 1   score every case with no bonus            -> base severities
    pass 2   count OTHER HIGH cases per (agency, FY)   -> score again with it

Synthetic rows are read in, not filtered out. The labelled control carries its
own synthetic member, agency and vendor (`ingest/synthetic.py`), so it cannot
land inside any real agency's vendor share or any real member's account. What
invariant 12 forbids is a synthetic row inside a *published aggregate*, and the
firing counts this module is checked against are computed over real works only.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select

from app.constants import SEVERITY_HIGH
from app.engine import derive as derive_mod
from app.engine import memo as memo_mod
from app.engine.score import compute, compute_with_memo
from app.models import Agency, Certification, Completion, Payment, Sanction, Work


class Corpus:
    """Every sanctioned work, its raw rows, and its derived feature set."""

    def __init__(self, session, rulebook):
        self.session = session
        self.rulebook = rulebook
        self.context = derive_mod.CorpusContext.from_session(session)

        self.works = {w.id: w for w in session.scalars(select(Work))}
        self.agency_names = dict(session.execute(select(Agency.id, Agency.name_canon)).all())
        self.sanctions = {s.work_id: s for s in session.scalars(select(Sanction))}
        self.completions = {c.work_id: c for c in session.scalars(select(Completion))}
        self.certifications = {c.work_id: c for c in session.scalars(select(Certification))}
        self.payments = defaultdict(list)
        for payment in session.scalars(select(Payment)):
            self.payments[payment.work_id].append(payment)

        self.by_work_id = {w.work_id_canon: w.id for w in self.works.values()}
        self.features = {
            work_pk: self.derive(work_pk) for work_pk in self.sanctions
        }
        self._base_severity = None
        self._high_peers = None

    # -- derivation --------------------------------------------------------

    def derive(self, work_pk):
        return derive_mod.derive(
            self.works[work_pk],
            self.sanctions.get(work_pk),
            self.completions.get(work_pk),
            self.certifications.get(work_pk),
            self.payments.get(work_pk, []),
            self.context,
        )

    def features_for(self, work_id_canon):
        return self.features[self.by_work_id[work_id_canon]]

    def facts_for(self, work_id_canon):
        work_pk = self.by_work_id[work_id_canon]
        work = self.works[work_pk]
        return memo_mod.case_facts(
            work,
            self.sanctions.get(work_pk),
            self.payments.get(work_pk, []),
            self.completions.get(work_pk),
            agency_name=self.agency_names.get(work.agency_id),
        )

    # -- the two passes ----------------------------------------------------

    def base_severities(self):
        """Pass 1: every case scored with no corroboration bonus."""
        if self._base_severity is None:
            self._base_severity = {
                work_pk: compute(features, self.rulebook, 0)["severity"]
                for work_pk, features in self.features.items()
            }
        return self._base_severity

    def high_peers(self):
        """(agency_id, fy) -> set of work pks whose BASE severity is HIGH."""
        if self._high_peers is None:
            peers = defaultdict(set)
            for work_pk, severity in self.base_severities().items():
                if severity == SEVERITY_HIGH:
                    work = self.works[work_pk]
                    peers[(work.agency_id, work.fy)].add(work_pk)
            self._high_peers = peers
        return self._high_peers

    def corroboration_count(self, work_pk) -> int:
        """OTHER HIGH cases under this work's agency in the same FY.

        A case never corroborates itself, which is why fixture A's count is the
        25 the frozen contract prints and not 26.
        """
        work = self.works[work_pk]
        return len(self.high_peers()[(work.agency_id, work.fy)] - {work_pk})

    def corroboration_evidence(self, work_pk) -> dict:
        from app.constants import CORROBORATION_CITATION_LIMIT, case_id_for

        work = self.works[work_pk]
        peers = sorted(
            self.works[peer].work_id_canon
            for peer in self.high_peers()[(work.agency_id, work.fy)] - {work_pk}
        )
        return {
            "agency": self.agency_names.get(work.agency_id),
            "window": f"FY{work.fy}",
            "matched_case_ids": [
                case_id_for(peer) for peer in peers[:CORROBORATION_CITATION_LIMIT]
            ],
        }

    # -- scoring -----------------------------------------------------------

    def score(self, work_id_canon, with_memo=False):
        work_pk = self.by_work_id[work_id_canon]
        args = (
            self.features[work_pk],
            self.rulebook,
            self.corroboration_count(work_pk),
            self.corroboration_evidence(work_pk),
        )
        if with_memo:
            return compute_with_memo(*args, facts=self.facts_for(work_id_canon))
        return compute(*args)

    def score_all(self):
        """Every sanctioned case, scored with its bonus. Keyed by work pk."""
        return {
            work_pk: compute(
                features, self.rulebook, self.corroboration_count(work_pk)
            )
            for work_pk, features in self.features.items()
        }
