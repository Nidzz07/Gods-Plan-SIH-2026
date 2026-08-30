"""The API routers. Six, all read-only except two appends to the audit trail.

    cases      the ranked list, the case sheet, notes and recompute
    works      the published record, before NIGRANI concluded anything
    rulebook   rules.yaml as parsed, plus what is stored in rulebook_versions
    audit      the append-only trail for one case, and the whole-chain walk
    analytics  the four persona dashboards, off pre-aggregated rollups
    ablation   the measured data-gap report, read back from ablation_findings

Nothing in this package derives a case, fits a model or measures a gap. Those
are build steps - `python -m app.derive_all`, `python -m app.ml.run`,
`python -m app.ablation.run` - and the reasoning is in `app/derive_all.py`.

`routers/cases.scoped_cases` is the single place Phase 7's role predicate
lands; every case-bearing query in this package starts from it. See
`docs/api/ROLE-SCOPING-PLAN.md`.
"""
