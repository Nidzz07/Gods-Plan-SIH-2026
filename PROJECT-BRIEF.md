# NIGRANI — project brief

Smart India Hackathon, problem statement **PS 26102**.
Organisation: Ministry of Statistics and Programme Implementation (MoSPI),
Data Informatics and Innovation Division (DIID).
Team ExploreeTinkerBell.

*Nigrani* — निगरानी — is the Hindi word for oversight or watch-keeping. That is
the whole product in one word: not an accusation engine, a watch-keeper that
shows its working.

---

## Problem

MPLADS gives every Member of Parliament an annual allocation — currently ₹ 5
crore — to recommend local development works. An MP recommends; a District
Authority sanctions and implements through a government agency; payments run to
vendors; the work is reported complete. Roughly ₹ 4,000 crore a year moves
through this route, across 543 Lok Sabha and 245 Rajya Sabha members, hundreds
of implementing agencies and tens of thousands of vendors.

MoSPI publishes all of it on the MPLADS portal. The data is public, structured,
and effectively unread. Nobody is systematically asking:

- Which sanctions sat for a year before money moved?
- Which works were paid once and then went silent?
- Which agency sanctioned the same description 244 times?
- Which vendor takes two-thirds of one agency's disbursement?
- Which MP has used 6% of an allocation with the year nearly gone?
- Which works are reported complete with no payment ever recorded?

These are answerable today from published data. They are not being answered,
because the volume defeats manual review and because the portal is built for
disclosure, not for detection.

The problem statement asks for an AI-powered system that detects anomalies,
fraud and inefficiencies in MPLADS implementation. The hard part is not
detection. It is **detection an officer will act on** — every flag has to be
explainable, re-derivable, and honest about what it does not know.

## Solution

NIGRANI ingests the twelve published MPLADS exports, reconstructs each work's
fund and lifecycle journey, evaluates it against a versioned rulebook of ten
measured rules, and produces a case with a full reasoning trace: every rule, the
value it read, the threshold it compared against, and the points it contributed.

Four properties make it different from a dashboard:

1. **Every score is arithmetic an officer can re-derive on paper.** No black box
   contributes a single point.
2. **Missing data is visible.** A rule we could not evaluate is marked *skipped*,
   lowers the case's coverage, and is never silently counted as a pass.
3. **Every score is reproducible months later.** Cases store the rulebook
   snapshot they were scored under, and recompute re-derives against that
   snapshot, not against today's rules.
4. **The system reports on its own blind spots.** The ablation module measures
   what NIGRANI cannot see, and turns that into a specific reporting
   recommendation back to MoSPI.

## Users and roles

Four personas, four scopes. Scoping is enforced server-side in the query
(CLAUDE.md invariant 10).

| Role | Who they are | What they see | What they do |
| --- | --- | --- | --- |
| **Ministry** | MoSPI / DIID analyst | Everything, all states | National patterns, rulebook governance, ablation report, exports |
| **State Nodal Authority** | State MPLADS nodal officer | All districts in one state | Triage escalations, compare districts, track agency patterns |
| **District Authority** | District Magistrate / implementing office | Works in one district | Work the case queue, add notes, resolve or escalate |
| **Member of Parliament** | MP or MP's office | Own works and own account rollup, all years | See account utilisation, see which recommendations stalled |

The MP role is read-only and deliberately included: MPLADS criticism often lands
on the MP for a delay that occurred entirely inside the district administration.
The lifecycle ladder shows exactly where the time went.

**Honest scoping:** the role switcher is a dropdown over seeded accounts, not an
identity provider. Passwords are hashed with `passlib[bcrypt]` and sessions
carry a `python-jose` JWT, so the server-side scoping is real. The login screen
is a demo.

---

## The two ladders and the account rollup

The full definitions, with types and null semantics, are in
`docs/domain/DOMAIN-MODEL.md`. In brief:

**Fund ladder** — where the money is, for one work.
```
sanctioned_amt  --[ sanction_to_disbursement ]-->  disbursed_amt
                --[ disbursement_to_certification ]-->  certified_amt
```
Hop 1 is computable from published data. Hop 2 is modelled, derivable, and
**permanently unavailable in public MPLADS data** — MoSPI does not publish
utilisation certificates. That is not a gap we hide; it is finding number one in
the ablation report.

**Lifecycle ladder** — where the time went, for one work.
```
recommended --[ recommend_to_sanction ]--> sanctioned
            --[ sanction_to_first_payment ]--> first_payment
            --[ first_payment_to_completion ]--> completed
```

**Account ladder** — where an MP's allocation stands, per MP per financial year.
```
allocated --> sanctioned --> disbursed
```

The two ladders answer different questions and both are needed. Fund reconciles
*amount*; lifecycle reconciles *time*. On MPLADS data, which is financially flat
and temporally rich (see `docs/data/DATA-PROFILE.md` §5), the lifecycle ladder
carries most of the signal — which is precisely the finding the project is built
on.

---

## Features

| # | Feature | One line |
| --- | --- | --- |
| **F1** | Dual reconciliation | Fund ladder (2 hops) and lifecycle ladder (3 lags) for every work, plus the per-MP account rollup |
| **F2** | Versioned rulebook | Ten rules in YAML, editable by an officer in the UI, versioned and applied live |
| **F3** | Reasoning trace | Every rule, the value read, the threshold, the contribution, the status |
| **F4** | Pattern-of-conduct corroboration | A repeat-offender agency bonus, awarded only on corroborated repetition |
| **F5** | Graceful degradation | Coverage percentage, and "not published" kept distinct from "published as zero" |
| **F6** | Append-only audit trail | With true re-derivation against the stored rulebook snapshot |
| **F7** | ML layer | Duplicate detection by citation, anomaly badge, delay forecast, agency-vendor concentration graph |
| **F8** | Risk-routed early warning | Alerts routed by score and scope, with real escalation between roles |
| **F9** | Data-Gap Ablation | Mask a field, re-score, measure the coverage loss, and report it to MoSPI as a quantified recommendation |

---

## The four-tier detection architecture

Four tiers. **Exactly one of them can move the score.**

| Tier | What it does | Moves the score? |
| --- | --- | --- |
| **1. Reconciliation** | Derives the ladders and the feature dictionary from published columns | **No** — it produces inputs, not points |
| **2. Rulebook** | Evaluates ten deterministic rules over those features | **YES — this tier and the F4 bonus are the only sources of score** |
| **3. Statistical** | Peer-group z-scores, IsolationForest anomaly score, delay forecast | **No. Zero points. Badge only** |
| **4. Graph** | Agency-vendor bipartite graph, concentration and centrality | **No. Zero points. Badge only** |

Tier 3 and tier 4 confirm or fail to confirm what tier 2 already found. A badge
that says "confirms" raises an officer's confidence. It does not raise the
number. A test per model asserts this: perturb the model output, assert the
score is byte-identical (CLAUDE.md invariant 1).

**The one apparent exception, stated plainly.** The `duplicate_work` rule reads
`duplicate_similarity`, a number produced by a similarity model. It is a tier-2
rule, and it does contribute points. It is admissible because the trace row
**cites its evidence**: the matched work ids, the shared description text, and
the similarity components. The officer opens both works and judges for
themselves. That is explainability by citation, not by trust. See
`docs/domain/DOMAIN-MODEL.md` §(h).

---

## Scoring

Ten rules, 144 points of weight, plus a 10-point corroboration bonus.

| Rule | Field | Op | Threshold | Weight |
| --- | --- | --- | ---: | ---: |
| `utilisation_shortfall` | `variance_sanction_to_disbursement` | lt | −15 | 22 |
| `execution_delay` | `execution_days` | gt | 365 | 20 |
| `duplicate_work` | `duplicate_similarity` | gte | 0.85 | 18 |
| `sanction_delay` | `sanction_lag_days` | gt | 180 | 16 |
| `stalled_work` | `days_since_last_payment` | gt | 270 | 16 |
| `vendor_concentration` | `vendor_share_in_agency_pct` | gt | 60 | 12 |
| `status_payment_mismatch` | `completed_without_payment` | eq | true | 12 |
| `split_sanction` | `same_desc_same_agency_count` | gte | 3 | 10 |
| `asset_evidence_missing` | `asset_image_absent` | eq | true | 10 |
| `account_underutilisation` | `mp_utilisation_pct` | lt | 25 | 8 |
| | | | **Rule total** | **144** |
| `agency_pattern_bonus` | corroboration, min 3 HIGH cases in the FY | | | 10 |
| | | | **Maximum** | **154** |

Display is capped at **100**. The raw total is retained and shown alongside.
The cap is not renormalisation — weights are never divided by 1.54 — because
renormalising would change the arithmetic an officer re-derives.

Severity: **HIGH ≥ 75 · MEDIUM ≥ 50 · LOW below 50**, applied to the capped
display score.

Every threshold is drawn from a measured distribution in
`docs/data/DATA-PROFILE.md` §6 and carries a YAML comment naming its firing
count. No threshold is back-solved to make a demo case land on a round number.

---

## Graceful degradation

`coverage_pct` = the share of total rulebook weight that could actually be
evaluated:

```
coverage_pct = (144 − sum of weights of skipped rules) / 144
```

Three statuses, and the difference between the last two is the whole point:

| Status | Meaning | Contribution |
| --- | --- | --- |
| `fired` | The rule evaluated and the condition held | its weight |
| `passed` | The rule evaluated and the condition did not hold | 0 |
| `skipped` | The rule could not be evaluated | 0, and coverage falls |

A skipped rule's weight is **never redistributed**. A case with 65% coverage and
a score of 50 is a different object from a case with 100% coverage and a score
of 50, and the UI must never let them look alike.

Skips carry a reason, because these are different findings:

| `skip_reason` | Meaning |
| --- | --- |
| `not_published` | MoSPI does not publish this field, or published no row |
| `published_zero` | The field was published, with the value zero |
| `not_applicable` | The work has not reached the stage the rule reads |

"Not published" is a reporting failure and belongs in the ablation report.
"Published as zero" is a fact about the work. Collapsing them would let a
reporting gap masquerade as a clean record.

---

## Fixtures

Three worked cases, defined with full arithmetic in
`docs/contract/fixtures.md`. Between them they exercise a gap at each fund hop,
the slowest lag at two different lifecycle stages, skipped rules from genuinely
unpublished fields, the corroboration bonus both firing and not firing, and a
duplicate citation.

| Fixture | Score | Severity | Coverage | Exercises |
| --- | ---: | --- | ---: | --- |
| A · high-mast LED, Budaun | 92 | HIGH | 86% | Fund hop 1 open, duplicate citation, corroboration fires |
| B · completed with no payment | 50 | MEDIUM | 65% | Three skipped rules, corroboration does not fire |
| C · synthetic certification control | 42 | LOW | 100% | Fund hop 2 open, `is_synthetic = true` |

Fixture C is a **labelled synthetic control**. Real MPLADS data can never
populate the certification hop, so the only way to test that derivation is to
inject a row and mark it. It carries `is_synthetic = true`, is labelled on
screen, and is excluded from every aggregate.

---

## API contract

`docs/contract/case_detail.json` is the frozen worked response for
`GET /api/cases/{case_id}`. It and `backend/app/schemas.py` move together or not
at all (CLAUDE.md invariant 9).

Principal endpoints:

```
POST   /api/auth/login
GET    /api/cases                      role-scoped list, filter + sort
GET    /api/cases/{case_id}            the frozen contract shape
POST   /api/cases/{case_id}/notes
POST   /api/cases/{case_id}/recompute  re-derives against the stored snapshot
GET    /api/cases/{case_id}/audit
GET    /api/rulebook                   current version
PUT    /api/rulebook                   creates a new version, never mutates
GET    /api/rulebook/versions
GET    /api/accounts/{mp_id}           account ladder rollup, per FY
GET    /api/alerts                     role-routed queue
POST   /api/alerts/{alert_id}/escalate
GET    /api/ablation                   the MoSPI recommendation report
GET    /api/ingest/report              load counts, rejects, reconciliation
```

## Audit events

Ten event types, append-only, one table (CLAUDE.md invariant 4):

`CASE_OPENED` · `RULE_FIRED` · `DUPLICATE_LINKED` · `PATTERN_LINKED` ·
`NOTE_ADDED` · `SCORE_RECOMPUTED` · `ALERT_RAISED` · `ALERT_ESCALATED` ·
`RULEBOOK_UPDATED` · `INGEST_COMPLETED`

A `SCORE_RECOMPUTED` event records the before and after trace, not just the
before and after number, so an auditor can see which rule changed and why.

## Screens per persona

| Persona | Screens |
| --- | --- |
| **Ministry** | National overview · Case list (all) · Case detail · Rulebook editor + version history · Ablation report · Ingest report |
| **State Nodal** | State overview · District comparison · Escalation queue · Case detail · Agency pattern view |
| **District** | Case queue · Case detail · Alerts · Agency and vendor view |
| **MP** | Account ladder by FY · Own works list · Case detail (read-only) |

Shared: **Case detail** is one screen for every role — the ladders, the trace
table, coverage, badges, memo and audit trail. What differs by role is which
cases can be reached, and that is decided in the query.

---

## Declared limitations

Stated on the slide, in the README, and in the UI where relevant. These are
scoping decisions, not defects.

1. **The data is a truncated portal sample**, 118,704 rows, not the national
   record. No figure is presented as a national total.
2. **Memos are templates**, not generated language. Template now, LLM later.
3. **Cost overrun is not computable.** Recommended equals sanctioned in 14,831
   of 14,831 matched works. The rule was designed and then removed.
4. **The certification hop has no public data.** It is modelled and tested
   against a labelled synthetic control.
5. **The delay forecast horizon is illustrative**, trained on a truncated sample.
6. **The completed-without-payment signal is partly a truncation artefact.** The
   expenditure export joins to only 3,529 sanctioned works. The caveat travels
   with the flag.
7. **Login is a demo.** Scoping is server-side and real; identity is seeded.
8. **Escalation queues in-app** and writes an audit event. It sends no email.
9. **Agency canonicalisation is fuzzy.** `rapidfuzz` merges typo variants; a
   merge that an officer disputes is a UI-visible decision, not a silent one.
10. **A duplicate cluster is a candidate for review, never an accusation.**
11. **No geospatial precision.** MPLADS publishes no coordinates. Maps join at
    state and district level only and never imply a point-located asset.

## Out of scope

Deliberately not built, and not claimed:

- Any LLM API call anywhere in the product.
- Bank, treasury, PFMS or e-procurement integration.
- Real-time portal scraping. Data refresh is a re-download, documented in
  `data/raw/README.md`.
- Citizen-facing grievance intake.
- Beneficiary-level or personal data of any kind.
- Case management beyond note, escalate and resolve. No workflow engine.
- Mobile applications. The UI is responsive; it is not an app.
- Any automated action against a vendor, agency or MP. NIGRANI raises cases for
  human decision and nothing else.
