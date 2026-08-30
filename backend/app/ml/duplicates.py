"""Duplicate CLUSTERS, and a second opinion on the similarity number.

**This module does not compute the number the rulebook reads, and that is the
decision, stated plainly.**

`duplicate_similarity` is the one model output that reaches the score, and
three documents already fix how it is measured: `DATA-PROFILE.md` section 6
measured it with `rapidfuzz.token_set_ratio` over the normalised description
blocked by canonical agency, `docs/contract/fixtures.md` records fixture A's
1.000 and its cluster of 15 as a contract, and
`docs/contract/case_detail.json` prints the method string on the citation.
`engine/derive.py` computes it inline by exactly that method, and the fixture
tests hold it to those numbers.

Two paths were open. Moving that computation here and importing it back into
`derive.py` would make `engine/` depend on `ml/`, and with it `score.py`, which
imports `derive`. The single strongest structural guarantee NIGRANI has for
invariant 1 is that the scoring path cannot reach this package at all; trading
it for tidier code would be a bad bargain, and re-pointing the rulebook's one
model-fed input at a different module is exactly the kind of quiet change that
puts an engine out of step with a published figure.

So the shipped path is unchanged. `derive.py` still computes
`duplicate_similarity`, by the same method, from the same normalisation this
module imports from it, and the trace still cites what it always cited. What
this module adds is the three things a pairwise best-match score cannot give:

1.  **Cluster identity.** A stable `cluster_id` per (agency, normalised
    description), so the 447 clusters of two or more and the 275 of three or
    more that `DATA-PROFILE.md` section 6 measured become addressable objects
    rather than a count in a document. `cluster()` reproduces those figures and
    a test asserts it.
2.  **A citation built from the cluster.** `citation_for()` returns the exact
    dict `engine/derive.duplicate_citation` returns, assembled from the cluster
    rather than from the pairwise ranking, and a test asserts the two are equal
    on fixture A. That is what makes the claim "the trace citation can be built
    from `ml_findings`" checkable instead of asserted.
3.  **A cross-check on the scorer, for the calibration question the profile
    left open.** `DATA-PROFILE.md` section 6 records that the 0.85 threshold on
    `token_set_ratio` fires on 16,491 works - 61% of the corpus - because
    MPLADS descriptions share heavy boilerplate and `token_set_ratio` ignores
    word order and duplication, and that a scorer and a threshold must be
    chosen together before those 18 points are trusted. This module measures a
    TF-IDF cosine over the same normalised text against the same best-matching
    peer and records it beside the rapidfuzz number on every finding.

**The cross-check changes nothing and decides nothing.** It does not touch
`rules.yaml`, it does not touch `derive.py`, and it is not a recalibration:
choosing the scorer and the threshold together, and re-measuring the resulting
distribution into `DATA-PROFILE.md`, is the pass that document reserves for
itself. What this module supplies is the measurement that pass will need.

**A cluster is a candidate for review, never an accusation.** The largest in
the corpus is 244 high-mast street lights under one district magistrate, which
is overwhelmingly likely to be 244 street lights. The word is "review".
"""

from __future__ import annotations

import hashlib
from collections import defaultdict

from ..constants import (
    DUPLICATE_CITATION_LIMIT,
    ML_KIND_DUPLICATE,
    Availability,
    case_id_for,
)
from ..engine.derive import SIMILARITY_METHOD, normalise_description
from .base import Finding, model_version

# Prefix on a cluster id, the way `NG-` prefixes a case id.
CLUSTER_ID_PREFIX = "DC-"
CLUSTER_ID_HEX_LEN = 8

# The rapidfuzz components quoted on every citation, in the order the frozen
# contract prints them. `token_set_ratio` is the headline - it is the scorer
# the rule reads - and the other two are there so a reader can see WHY it is
# what it is: a token_set_ratio of 1.00 beside a partial_ratio of 0.62 is a
# very different claim from three components all reading 1.00.
COMPONENT_SCORERS = ("token_set_ratio", "partial_ratio", "token_sort_ratio")

# The cross-check scorer. Word unigrams and bigrams over the same normalised
# text, sublinear term frequency, no stop-word list - MPLADS descriptions are
# short administrative noun phrases and an English stop-word list removes
# meaningful tokens from them ("light with 6 led" loses "with").
CROSS_CHECK_METHOD = (
    "sklearn.TfidfVectorizer(1-2 word grams, sublinear_tf) cosine over the same "
    "normalised description, against the same best-matching peer"
)

_READING = (
    "A cluster for review, not an accusation. Repeated works of this kind - street "
    "lights across a constituency, hand pumps across a block - are routinely "
    "legitimate. Open the cited works and judge."
)


def cluster_id_for(agency_id, normalised_text: str) -> str:
    """Deterministic from the agency and the text, never from row order.

    The same rule case ids follow (invariant 8): re-running over the same
    corpus produces the same cluster id for the same cluster, so a finding
    written today and a finding written after a reload name the same object.
    """
    key = f"{agency_id}\x1f{normalised_text}".encode()
    return CLUSTER_ID_PREFIX + hashlib.sha256(key).hexdigest()[:CLUSTER_ID_HEX_LEN].upper()


class DuplicateClusters:
    """Every exact-description cluster in the corpus, blocked by agency.

    A cluster is a set of sanctioned works under ONE canonical agency whose
    normalised descriptions are byte-identical. That is the definition
    `DATA-PROFILE.md` section 6 measured - 447 clusters of two or more over
    3,584 works, 275 of three or more over 3,240 - and it is the definition
    `split_sanction` counts against, so the two cannot drift.

    It is deliberately NOT a fuzzy-linkage cluster. Chaining works together
    through pairwise similarity above a threshold produces components that grow
    without bound on boilerplate text - at 0.85 on this corpus, where the
    median pairwise score is 0.893, near enough every work under a large agency
    would land in one component - and an officer cannot open a component of
    four thousand works. The fuzzy number stays where it belongs: as a per-work
    reading on the trace row, with two named peers to open.
    """

    def __init__(self, rows, similarity, peers, best_text):
        """Build from (work_pk, work_id_canon, agency_id, description) rows.

        `similarity`, `peers` and `best_text` are the mappings
        `engine.derive.CorpusContext` already computed for the corpus. They are
        passed in rather than recomputed: the rapidfuzz matrix over 27,078
        descriptions is the expensive part of a scoring run, and a second
        computation that drifted from the first by so much as a sort order
        would put the citation this module builds out of step with the trace
        the officer reads.
        """
        self.similarity = dict(similarity)
        self.peers = {pk: list(v) for pk, v in peers.items()}
        self.best_text = dict(best_text)

        self.work_id: dict[int, str] = {}
        self.agency_of: dict[int, int | None] = {}
        self.normalised: dict[int, str] = {}
        self.cluster_of: dict[int, str] = {}
        self.members: dict[str, list[int]] = defaultdict(list)

        for work_pk, work_id_canon, agency_id, description in rows:
            self.work_id[work_pk] = work_id_canon
            self.agency_of[work_pk] = agency_id
            text = normalise_description(description)
            if agency_id is None or not text:
                # No readable description, or no agency to block on. There is
                # nothing to cluster and nothing to compare - and that is a
                # skip with a reason, handled in `findings()`.
                continue
            self.normalised[work_pk] = text
            cluster_id = cluster_id_for(agency_id, text)
            self.cluster_of[work_pk] = cluster_id
            self.members[cluster_id].append(work_pk)

        for member_list in self.members.values():
            member_list.sort(key=lambda pk: self.work_id[pk])

    # -- the corpus picture ------------------------------------------------

    def size_of(self, work_pk) -> int | None:
        cluster_id = self.cluster_of.get(work_pk)
        return len(self.members[cluster_id]) if cluster_id else None

    def clusters_of_at_least(self, minimum: int) -> list[str]:
        """Cluster ids holding `minimum` works or more, in id order."""
        return sorted(cid for cid, members in self.members.items() if len(members) >= minimum)

    def works_in_clusters_of_at_least(self, minimum: int) -> int:
        return sum(
            len(members) for members in self.members.values() if len(members) >= minimum
        )

    def largest(self, limit: int = 3) -> list[tuple[str, int]]:
        """(cluster_id, size) for the biggest clusters, largest first."""
        ranked = sorted(
            ((cid, len(members)) for cid, members in self.members.items()),
            key=lambda pair: (-pair[1], pair[0]),
        )
        return ranked[:limit]

    # -- the citation ------------------------------------------------------

    def citation_for(self, work_pk, agency_name=None, cross_check=None) -> dict | None:
        """The evidence object a fired `duplicate_work` row must carry.

        Byte-for-byte the shape `engine.derive.duplicate_citation` produces -
        and `tests/test_ml_duplicates.py` asserts the two are equal on fixture
        A, so the claim that the trace citation can be built from this module's
        output is checked rather than asserted.

        `cross_check`, when supplied, rides alongside the rapidfuzz components
        under its own key. It never replaces `similarity`, which is the number
        the rule read.
        """
        from rapidfuzz import fuzz

        text = self.normalised.get(work_pk)
        peers = self.peers.get(work_pk)
        if not text or not peers:
            return None
        cited = peers[:DUPLICATE_CITATION_LIMIT]
        match = self.best_text.get(work_pk, text)
        citation = {
            "matched_work_ids": list(cited),
            "matched_case_ids": [case_id_for(work_id) for work_id in cited],
            "cluster_size": self.size_of(work_pk),
            "shared_description": text,
            "agency": agency_name,
            "similarity": round(self.similarity.get(work_pk, 0.0), 3),
            "components": {
                name: round(getattr(fuzz, name)(text, match) / 100.0, 3)
                for name in COMPONENT_SCORERS
            },
            "method": SIMILARITY_METHOD,
            "reading": _READING,
        }
        if cross_check is not None:
            citation["cross_check"] = {
                "cosine": round(float(cross_check), 3),
                "method": CROSS_CHECK_METHOD,
                "reading": (
                    "A second opinion on the similarity number, recorded because "
                    "DATA-PROFILE.md section 6 leaves the scorer and the threshold "
                    "open. It contributes nothing and changes nothing."
                ),
            }
        return citation

    # -- findings ----------------------------------------------------------

    def findings(self, agency_names=None, cross_check=None, version=None):
        """One `duplicate` finding per work, including the ones with nothing to say.

        A work whose portal description is missing or unreadable, or whose
        agency holds no other described work, gets a finding with a null value
        and the reason - `not_published` for the first, `not_applicable` for
        the second. The two are different findings and stay apart
        (CLAUDE.md invariant 2): one is a reporting gap that belongs in the
        ablation report, the other is a fact about a work with no peers.
        Fixture C is the second kind and stays that way; giving the labelled
        control synthetic peers to close the gap was rejected in Phase 2 and is
        not reopened here.

        `contributes_to_score` is True on every row, matching the declaration
        in `models.py`: this KIND of finding is the one that feeds a rulebook
        rule. It does not mean `score.py` reads this table - it does not, and
        no module under `engine/` imports this package. It means the number a
        `duplicate` finding records is the same number `duplicate_work` reads,
        and that the rule is admissible only because these matched work ids
        travel with it (DOMAIN-MODEL.md (h)).
        """
        agency_names = agency_names or {}
        cross_check = cross_check or {}
        version = version or self.model_version()
        out = []
        for work_pk in sorted(self.work_id):
            text = self.normalised.get(work_pk)
            if not text:
                out.append(
                    Finding(
                        work_pk=work_pk,
                        kind=ML_KIND_DUPLICATE,
                        value=None,
                        availability=Availability.NOT_PUBLISHED,
                        payload={
                            "work_id": self.work_id[work_pk],
                            "detail": (
                                "The portal published no readable description, or no "
                                "implementing agency, for this work, so it can neither be "
                                "clustered nor compared."
                            ),
                        },
                        model_version=version,
                        contributes_to_score=True,
                    )
                )
                continue
            similarity = self.similarity.get(work_pk)
            cluster_id = self.cluster_of[work_pk]
            size = self.size_of(work_pk)
            payload = {
                "work_id": self.work_id[work_pk],
                "cluster_id": cluster_id,
                "cluster_size": size,
                "shared_description": text,
                "agency": agency_names.get(self.agency_of[work_pk]),
                "cluster_work_ids": [self.work_id[pk] for pk in self.members[cluster_id]],
            }
            if similarity is None:
                payload["detail"] = (
                    "No other work under this agency carries a readable description, so "
                    "there is no population to compare this one against."
                )
                out.append(
                    Finding(
                        work_pk=work_pk,
                        kind=ML_KIND_DUPLICATE,
                        value=None,
                        availability=Availability.NOT_APPLICABLE,
                        payload=payload,
                        model_version=version,
                        contributes_to_score=True,
                    )
                )
                continue
            citation = self.citation_for(
                work_pk,
                agency_name=agency_names.get(self.agency_of[work_pk]),
                cross_check=cross_check.get(work_pk),
            )
            payload["citation"] = citation
            payload["reading"] = _READING
            out.append(
                Finding(
                    work_pk=work_pk,
                    kind=ML_KIND_DUPLICATE,
                    value=float(similarity),
                    availability=Availability.PUBLISHED,
                    payload=payload,
                    model_version=version,
                    contributes_to_score=True,
                )
            )
        return out

    def model_version(self) -> str:
        return model_version(
            "dup1",
            method=SIMILARITY_METHOD,
            cluster="exact normalised description within canonical agency",
            works=len(self.work_id),
            described=len(self.normalised),
            clusters=len(self.members),
        )


def cluster(rows, context) -> DuplicateClusters:
    """Cluster the corpus, reusing the similarity `derive` already computed.

    `rows` are (work_pk, work_id_canon, agency_id, description) tuples for the
    sanctioned works - the population a case exists for. `context` is the
    `engine.derive.CorpusContext` the scoring run built; its `similarity`,
    `similarity_peers` and `similarity_best_text` mappings are carried through
    unchanged so this module and the trace can never quote different numbers.
    """
    return DuplicateClusters(
        rows,
        context.similarity,
        context.similarity_peers,
        context.similarity_best_text,
    )


def cross_check_cosine(clusters: DuplicateClusters) -> dict[int, float]:
    """TF-IDF cosine between each work and its best rapidfuzz peer.

    The second opinion described in the module docstring. Fitted over every
    normalised description in the corpus at once, so the inverse document
    frequency that downweights MPLADS boilerplate - "construction", "of",
    "village" - is measured on the corpus rather than assumed.

    Returns a mapping only for the works that have a best-matching peer.
    Nothing reads this to make a decision.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    work_pks = [pk for pk in sorted(clusters.normalised) if pk in clusters.best_text]
    if not work_pks:
        return {}
    texts = [clusters.normalised[pk] for pk in work_pks]
    matches = [clusters.best_text[pk] for pk in work_pks]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    matrix = vectorizer.fit_transform(texts + matches)
    left = matrix[: len(work_pks)]
    right = matrix[len(work_pks) :]
    # Rows are L2-normalised by TfidfVectorizer, so the row-wise dot product IS
    # the cosine and no division is needed.
    cosine = left.multiply(right).sum(axis=1).A1
    return {pk: float(value) for pk, value in zip(work_pks, cosine)}
