"""Tier 4 - the agency-vendor bipartite graph. Worth exactly ZERO points.

**Badge only.** Nothing under `engine/` imports this module and no key it
produces appears in `engine/derive.FEATURE_KEYS`, so no rulebook edit can route
a centrality figure into a score (CLAUDE.md invariant 1).

**What this does NOT do: recompute `vendor_share_in_agency_pct`.**

`engine/derive.vendor_share_in_agency_pct` already answers one question, per
work: what share of everything this work's agency has disbursed went to the
vendor this work paid? `vendor_concentration` reads it, it fires on 48 works
across 65 agency-vendor pairs above the Rs 50 lakh floor, and that number is
calibrated in `DATA-PROFILE.md` section 6. Computing it a second time here
would create two numbers that can disagree, so the graph does not. It builds
the same edge weights from the same payments and **asserts that its own view
reproduces the profile's 65 pairs** (`concentrated_pairs()`, pinned by
`tests/test_ml_concentration.py`) - a consistency check on the graph, not a
second opinion the rule might read.

**What a graph genuinely adds, and a single ratio cannot.**

A share is a number about one edge. These are properties of the STRUCTURE, and
each of them needs the whole bipartite graph to exist at all:

1.  **Vendor span** - how many distinct agencies pay one vendor. It is the
    degree of a vendor node. `DATA-PROFILE.md` section 6 measures 650 vendors
    under more than one agency, the widest spanning 10, and this module
    reproduces both from the graph rather than from the stored
    `vendors.agency_span` rollup, so the two are checkable against each other.
2.  **Shared-vendor exposure** - the share of an agency's disbursement paid to
    vendors that also work for other agencies. A ratio about one vendor cannot
    express it, because it is a sum over the agency's edges weighted by the
    degree of the node at the far end. Median 0.00%, p90 39.08%, max 100%.
3.  **HHI over an agency's vendors** - the Herfindahl index of its edge
    weights. One top-vendor share of 60% describes a very different office
    depending on whether the rest is split between two vendors or two hundred,
    and the index says which. Median 0.165, p90 0.840.
4.  **Component reach** - the size of the connected component an agency sits in
    once agencies are linked through the vendors they share. The corpus has 418
    components and the largest holds 9,430 nodes: most district offices in this
    sample are, through shared contractors, one structure.

**None of it is an accusation.** A vendor working for ten district offices is
overwhelmingly likely to be a firm that works across a region, and an agency
whose whole disbursement went to one vendor is very often an agency with one
work. Every figure here is context for reading a case, and the word for what a
high reading buys is an officer's attention, not a finding.
"""

from __future__ import annotations

from collections import defaultdict

from ..constants import (
    ML_KIND_GRAPH,
    VENDOR_CONCENTRATION_AGENCY_FLOOR,
    Availability,
)
from .base import Finding, model_version

AGENCY = "A"
VENDOR = "V"

METHOD = (
    "networkx bipartite graph of implementing agencies and vendors, edge weight = total "
    "disbursed between the pair, built over every payment on any work of the agency"
)

_READING = (
    "Badge only. Contributes zero points to the score (CLAUDE.md invariant 1). A "
    "vendor working for several district offices is very often a firm that works "
    "across a region; these figures are context for reading a case, never a finding."
)


def build(rows):
    """Build the bipartite graph from (agency_id, vendor_id, paid_amt) rows.

    The denominator is every payment the agency made on ANY of its works, not
    only its sanctioned ones. Restricting it turns a 17% vendor into a 100% one
    and is the error `DATA-PROFILE.md` section 6 warns against; the derived
    feature reads the same population for the same reason.
    """
    import networkx as nx

    weights: dict[tuple, int] = defaultdict(int)
    for agency_id, vendor_id, paid_amt in rows:
        if agency_id is None or vendor_id is None or paid_amt is None:
            continue
        weights[(agency_id, vendor_id)] += paid_amt

    graph = nx.Graph()
    for (agency_id, vendor_id), amount in weights.items():
        graph.add_node((AGENCY, agency_id), bipartite=0)
        graph.add_node((VENDOR, vendor_id), bipartite=1)
        graph.add_edge((AGENCY, agency_id), (VENDOR, vendor_id), weight=amount)
    return graph


class ConcentrationGraph:
    """The fitted graph, with the four structural measures read off it."""

    def __init__(self, graph):
        import networkx as nx

        self.graph = graph
        self.agencies = [n for n, d in graph.nodes(data=True) if d["bipartite"] == 0]
        self.vendors = [n for n, d in graph.nodes(data=True) if d["bipartite"] == 1]
        # Component id per node, so an agency can name the structure it sits in.
        self.component_of: dict = {}
        self.component_size: dict = {}
        for index, component in enumerate(nx.connected_components(graph)):
            for node in component:
                self.component_of[node] = index
                self.component_size[node] = len(component)

    # -- vendor-side -------------------------------------------------------

    def span(self, vendor_id) -> int:
        """How many distinct agencies pay this vendor. The vendor node's degree."""
        node = (VENDOR, vendor_id)
        return self.graph.degree(node) if node in self.graph else 0

    def spanning_vendors(self, minimum: int = 2) -> list[int]:
        return sorted(v[1] for v in self.vendors if self.graph.degree(v) >= minimum)

    def max_span(self) -> int:
        return max((self.graph.degree(v) for v in self.vendors), default=0)

    # -- agency-side -------------------------------------------------------

    def agency_total(self, agency_id) -> int:
        node = (AGENCY, agency_id)
        if node not in self.graph:
            return 0
        return sum(self.graph[node][v]["weight"] for v in self.graph[node])

    def measures(self, agency_id) -> dict | None:
        """The four structural readings for one agency, or None if it has no edge.

        `top_vendor_share_pct` is present so a reader can see the graph agrees
        with the per-work feature the rulebook reads - it is a check, not a
        second source. The three readings BELOW it are the ones a single ratio
        cannot express.
        """
        node = (AGENCY, agency_id)
        if node not in self.graph:
            return None
        edges = {v: self.graph[node][v]["weight"] for v in self.graph[node]}
        total = sum(edges.values())
        if total <= 0:
            return None
        shares = [amount / total for amount in edges.values()]
        top_vendor = max(edges, key=lambda v: (edges[v], -v[1]))
        shared = sum(
            amount for v, amount in edges.items() if self.graph.degree(v) > 1
        )
        return {
            "vendor_count": len(edges),
            "disbursed_total": int(total),
            "above_floor": total > VENDOR_CONCENTRATION_AGENCY_FLOOR,
            "top_vendor_id": top_vendor[1],
            "top_vendor_share_pct": round(max(shares) * 100, 2),
            # -- the graph-native three --
            "hhi": round(sum(share**2 for share in shares), 4),
            "shared_vendor_exposure_pct": round(shared / total * 100, 2),
            "widest_vendor_span": max((self.graph.degree(v) for v in edges), default=0),
            "component_size": self.component_size.get(node, 1),
            "component_agencies": sum(
                1
                for other in self.agencies
                if self.component_of.get(other) == self.component_of.get(node)
            ),
        }

    def concentrated_pairs(self, threshold_pct: float) -> list[tuple[int, int, float]]:
        """(agency_id, vendor_id, share) above the threshold and above the floor.

        The consistency check described in the module docstring: on the shipped
        rulebook's threshold of 60 this returns the 65 pairs
        `DATA-PROFILE.md` section 6 measured. A different count means the graph
        and the derived feature have drifted, which is a bug in one of them.
        """
        out = []
        for node in self.agencies:
            total = self.agency_total(node[1])
            if total <= VENDOR_CONCENTRATION_AGENCY_FLOOR:
                continue
            for vendor in self.graph[node]:
                share = self.graph[node][vendor]["weight"] / total * 100
                if share > threshold_pct:
                    out.append((node[1], vendor[1], share))
        return sorted(out)

    def model_version(self) -> str:
        return model_version(
            "gr1",
            method=METHOD,
            agencies=len(self.agencies),
            vendors=len(self.vendors),
            edges=self.graph.number_of_edges(),
        )


def findings(
    graph: ConcentrationGraph,
    works_by_pk,
    payments_by_pk=None,
    agency_names=None,
    vendor_names=None,
    version=None,
):
    """One `graph` finding per work, carrying its agency's structural position.

    The value on the row is the agency's HHI over its vendors - the single
    number that best summarises the structure and the one no per-work ratio
    supplies. Everything else rides in the payload.

    A work whose agency has no payment edge at all gets `not_applicable` with
    the reason, not a zero: an office that has disbursed nothing is not an
    office with a perfectly even vendor spread.
    """
    agency_names = agency_names or {}
    vendor_names = vendor_names or {}
    payments_by_pk = payments_by_pk or {}
    version = version or graph.model_version()
    out = []
    for work_pk in sorted(works_by_pk):
        work = works_by_pk[work_pk]
        agency_id = getattr(work, "agency_id", None)
        measures = graph.measures(agency_id) if agency_id is not None else None
        payload = {"agency": agency_names.get(agency_id), "method": METHOD, "reading": _READING}

        if measures is None:
            payload["detail"] = (
                "No graph position: this work's implementing agency has no published "
                "payment to any vendor, so it has no edge in the agency-vendor graph. "
                "That is a work with no measurable structure around it, not an agency "
                "with a perfectly even vendor spread."
            )
            out.append(
                Finding(
                    work_pk=work_pk,
                    kind=ML_KIND_GRAPH,
                    value=None,
                    availability=Availability.NOT_APPLICABLE,
                    payload=payload,
                    model_version=version,
                    contributes_to_score=False,
                )
            )
            continue

        payload.update(measures)
        payload["top_vendor"] = vendor_names.get(measures["top_vendor_id"])
        # This work's own vendors and how widely each of them travels. The
        # per-work reading the rulebook uses stays in engine/derive.py; what is
        # added here is the span, which only the graph knows.
        vendors = sorted(
            {
                getattr(payment, "vendor_id", None)
                for payment in payments_by_pk.get(work_pk, [])
                if getattr(payment, "vendor_id", None) is not None
            }
        )
        payload["work_vendors"] = [
            {
                "vendor_id": vendor_id,
                "vendor": vendor_names.get(vendor_id),
                "agency_span": graph.span(vendor_id),
            }
            for vendor_id in vendors
        ]
        out.append(
            Finding(
                work_pk=work_pk,
                kind=ML_KIND_GRAPH,
                value=float(measures["hhi"]),
                availability=Availability.PUBLISHED,
                payload=payload,
                model_version=version,
                contributes_to_score=False,
            )
        )
    return out


def run(rows, works_by_pk, payments_by_pk=None, agency_names=None, vendor_names=None):
    """Build and describe in one call. Returns (graph, findings)."""
    graph = ConcentrationGraph(build(rows))
    return graph, findings(graph, works_by_pk, payments_by_pk, agency_names, vendor_names)
