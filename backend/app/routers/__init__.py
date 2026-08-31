"""The API routers. Seven, all read-only except two appends to the audit trail.

    auth       sign in, and read back who you are and what your role reaches
    scoping    the role predicate itself - not a router, no routes of its own
    cases      the ranked list, the case sheet, notes and recompute
    works      the published record, before NIGRANI concluded anything
    rulebook   rules.yaml as parsed, plus what is stored in rulebook_versions
    audit      the append-only trail for one case, and the whole-chain walk
    analytics  the four persona dashboards, off pre-aggregated rollups
    ablation   the measured data-gap report, read back from ablation_findings

Nothing in this package derives a case, fits a model or measures a gap. Those
are build steps - `python -m app.derive_all`, `python -m app.ml.run`,
`python -m app.ablation.run` - and the reasoning is in `app/derive_all.py`.

`routers/scoping.py` is the single place the role predicate lands; every
case-bearing query in this package starts from `scoped_cases` or `scope_works`,
and the three grain checks beside them decide which aggregate views a role may
ask for at all. Nothing in this package filters rows after a query has run. See
`docs/api/ROLE-SCOPING-PLAN.md` for the endpoint-by-endpoint commitment and
`docs/domain/DOMAIN-MODEL.md` (k) for the matrix it keeps.
"""
