"""F7 - the ML tier. Tiers 3 and 4 of the four-tier architecture.

**Nothing in this package can move a score, and the directory layout is what
guarantees it rather than a promise in a comment.**

    engine/  ->  may not import ml/          (asserted by tests/test_ml_boundary.py)
    ml/      ->  may import engine/          (one-way, so the arrow cannot bend)

`engine/score.py` reads its features only through `engine/rulebook.evaluate`,
which reads only the fields the rulebook names, and `engine/rulebook.validate`
rejects any rule naming a field outside `engine/derive.FEATURE_KEYS`. There is
no `anomaly_score`, no `delay_risk` and no `vendor_centrality` on that list, and
no module under `engine/` imports this package, so no rulebook edit and no
feature dict assembled by hand can route a number produced here into the
addition `compute()` performs (CLAUDE.md invariant 1).

The reverse arrow is used and is deliberate: `ml/` reads
`engine/derive.normalise_description` and `engine/rulebook.rule_by_field` so
that the ML tier and the rulebook cannot drift apart on a normalisation or a
threshold. A score is an INPUT to a badge - the anomaly badge needs to know
whether a rule fired in order to say "confirms" - and a badge is never an input
to a score.

**The four kinds, and what each is worth.**

| module            | `ml_findings.kind` | tier | worth |
| ----------------- | ------------------ | ---- | ----- |
| `duplicates.py`   | `duplicate`        | 3    | feeds `duplicate_work` by CITATION (DOMAIN-MODEL.md (h)) |
| `anomaly.py`      | `anomaly`          | 3    | zero. Badge only |
| `forecast.py`     | `forecast`         | 3    | zero. Badge only |
| `concentration.py`| `graph`            | 4    | zero. Badge only |

`duplicates` is the single exception and it is not an exception to invariant 1
so much as a consequence of DOMAIN-MODEL.md (h): the `duplicate_work` rule reads
a similarity number, and it is admissible only because the trace row hands the
officer the matched records to open. This package does not feed that rule -
`engine/derive.py` computes the value the rule reads, by the same method and
from the same normalisation - it clusters the same corpus so that the citation
has a cluster to name, and so that the corpus-level picture is inspectable.

**Availability is three-valued here too.** An anomaly score that cannot be
computed because the work has no comparable peers is `not_applicable`. It is
not zero, and it is not a silent exclusion. Every module in this package
returns a finding for every work it was asked about, and a finding with a null
value carries the reason it is null, in the same `app.constants.Availability`
vocabulary the storage layer and the rule trace use (CLAUDE.md invariant 2).

**The honesty rules apply verbatim.** A duplicate cluster is a candidate for
review, never fraud. A forecast horizon is illustrative, trained on a truncated
sample. A rule-based flag is rule-based, and nothing here is described as
AI-detected anywhere it reaches an officer.
"""
