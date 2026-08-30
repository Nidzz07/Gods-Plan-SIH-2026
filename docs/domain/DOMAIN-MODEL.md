# DOMAIN-MODEL — NIGRANI

The authoritative model of the MPLADS domain as NIGRANI represents it.
Everything here is grounded in `docs/data/DATA-PROFILE.md`. Where the data
cannot support a construct, this document says so rather than inventing one.

Contents:
(a) case unit · (b) fund ladder · (c) lifecycle ladder · (d) account ladder ·
(e) tables · (f) derived feature dictionary · (g) the rulebook ·
(h) the ML boundary · (i) the ablation module · (j) audit events ·
(k) role scoping matrix

---

## (a) The case unit

**One case is one WORK**, keyed by the portal work id.

Not one MP, not one agency, not one payment. A work is the smallest object that
has a complete fund journey, a complete lifecycle, one implementing agency, one
recommending MP and one district. It is also the object an officer can actually
go and inspect.

- Natural key: the canonicalised work id, pattern `WS/MP{code}/{FY}/{serial}`.
- Canonicalisation: uppercase, then remove **all** whitespace including embedded
  tabs. `WS/<TAB> MP620/2024-2025/133166` and `WS/MP620/2024-2025/133166` are the
  same work.
- Case id: deterministic from the canonical work id, never from row order
  (CLAUDE.md invariant 8).

```python
# app/constants.py
CASE_ID_PREFIX = "NG-"

def case_id_for(work_id_raw: str) -> str:
    canon = "".join(work_id_raw.split()).upper()
    return CASE_ID_PREFIX + hashlib.sha256(canon.encode()).hexdigest()[:10].upper()
```

Ten hex characters give 2^40 values against ~27K works. Collision probability is
negligible, and ingest asserts uniqueness anyway — a collision is an
`ingest_rejects` row with reason `case_id_collision`, never a silent overwrite.

A case exists for every **sanctioned** work. A recommendation that was never
sanctioned has no fund journey and is not a case; it appears only in the account
ladder and in the sanction-lag distribution.

---

## (b) Fund ladder

Where the money is, for one work. Two hops.

```
sanctioned_amt --[ sanction_to_disbursement ]--> disbursed_amt
               --[ disbursement_to_certification ]--> certified_amt
```

Variance is signed, expressed as a percentage of the upper rung, and always
negative or zero on real MPLADS data (profile §6: max is exactly 0.0%).

```
variance_sanction_to_disbursement      = (disbursed_amt - sanctioned_amt) / sanctioned_amt * 100
variance_disbursement_to_certification = (certified_amt - disbursed_amt)  / disbursed_amt  * 100
```

A hop is **open** when its variance is below the tolerance the rulebook sets for
it. `gap_hop` is the first open hop, walking down. If no hop is open, `gap_hop`
is `null`. If a hop cannot be computed, it is `unavailable` and is skipped over,
not treated as closed.

### Hop 1 — `sanction_to_disbursement`

| | |
| --- | --- |
| **Computable from public data?** | Yes, for the 3,529 works where an expenditure row joins |
| **Opens when** | Money was sanctioned but materially less than that reached the vendor. Tolerance −15%; 288 of 944 works in the profiled population fall below it |
| **What it means** | The sanction is committed but the work has drawn only part of it — the work may be stalled part-built, the agency may be holding funds, or the sanction may have been made against a demand that never materialised |
| **HOP_ACTION** — what the officer checks | Pull the agency's payment register for this work. Confirm whether the balance is committed against an unpaid bill, unspent, or was returned. If unspent for more than one financial year, the sanction should be revalidated or surrendered rather than left standing. |

### Hop 2 — `disbursement_to_certification`

| | |
| --- | --- |
| **Computable from public data?** | **No. Never.** MoSPI publishes no utilisation certificate date and no certified amount |
| **Opens when** | Money left the account but was never certified as spent on the sanctioned asset |
| **What it means** | The most serious fund finding available in principle: cash out, nothing certified in. On this corpus it can only be demonstrated against a labelled synthetic control |
| **HOP_ACTION** — what the officer checks | Obtain the utilisation certificate from the implementing agency and match the certified amount and asset description against the sanction. If no UC exists for a disbursement older than 12 months, that is a recovery proceeding, not a query. |

Hop 2 is retained in the model deliberately. It has a derivation function and a
test (CLAUDE.md invariant 3), it returns `None` with reason `not_published` on
every real row, and it is the headline entry in the ablation report §(i). A
model that quietly dropped it would hide the gap instead of measuring it.

---

## (c) Lifecycle ladder

Where the time went, for one work. Four dates, three lags.

```
recommended_date --[ recommend_to_sanction ]--> sanction_date
                 --[ sanction_to_first_payment ]--> first_payment_date
                 --[ first_payment_to_completion ]--> completion_date
```

All lags are whole days, computed date-to-date. Zero negative lags were measured
(profile §6); a negative lag is an `ingest_rejects` row with reason
`negative_lag`, not a clamp to zero.

`slowest_lag` is the lag with the largest value among those that are computable.
Ties break in ladder order. If no lag is computable, `slowest_lag` is `null`.

| Lag | Median | p90 | Meaning when it is the slowest |
| --- | ---: | ---: | --- |
| `recommend_to_sanction` | 88 d | 262 d | The delay is administrative and sits **before** implementation — with the district sanctioning office, not the agency or the MP |
| `sanction_to_first_payment` | — | — | The sanction issued but nothing moved. Vendor identification, tender, or agency capacity |
| `first_payment_to_completion` | — | — | Execution itself is slow. This is the one an inspector can go and look at |

`sanction_to_first_payment` and `first_payment_to_completion` have no measured
percentiles in the current profile because both require the truncated
expenditure join. They must be measured on the next full download.

**`execution_days` is not one of the three lags.** It is
`completion_date − sanction_date`, and it is computable whenever those two dates
exist — including for the many works that have a completion date and no payment
row at all. When both payment dates are present the identity
`execution_days = sanction_to_first_payment + first_payment_to_completion` holds,
and a test asserts it. Keeping `execution_days` separate is what lets
`execution_delay` fire on works that the payment join never reached.

---

## (d) Account ladder

Where an MP's allocation stands. Grain: **one MP × one financial year.**

```
allocated_amt --> sanctioned_amt --> disbursed_amt
```

| Quantity | Source |
| --- | --- |
| `allocated_amt` | `Allocated_Limit_for_Honble_MPs`, per MP per FY |
| `sanctioned_amt` | sum of `sanctions.sanctioned_amt` for that MP and FY |
| `disbursed_amt` | sum of `payments.paid_amt` for works of that MP and FY |

```
mp_utilisation_pct = sanctioned_amt / allocated_amt * 100
```

Measured on 419 MPs: median 19.6%, p25 6.6%, p75 44.9%, max 95.8%, 246 below
25%, and **zero above 100%**. The ceiling is hard in the data, so an account
reading above 100% is a data error to reject, not an over-spend to flag.

The account ladder is a **rollup, not a case**. It contributes exactly one input
to a work's score — `mp_utilisation_pct`, read by `account_underutilisation`,
weight 8, the smallest weight in the rulebook. That is deliberate: an MP's
aggregate underuse is context for a work, never the substance of a finding
against it.

---

## (e) Tables

SQLAlchemy 2.x declarative. SQLite. Every foreign key is enforced
(`PRAGMA foreign_keys=ON`).

**Availability is modelled explicitly.** Wherever a nullable amount or date can
be null for two different reasons, a companion enum column records which. This
is what keeps CLAUDE.md invariant 2 enforceable at the storage layer rather than
only in the engine.

```
availability := 'published' | 'not_published' | 'published_zero'
```

`published_zero` means the portal supplied the field with the value 0.
`not_published` means the portal supplied no value, or supplied no row at all.
They are different findings and are never collapsed.

### `states`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `name` | text | no | unique, canonicalised |
| `lgd_code` | text | yes | not published by the portal; reserved |

32 rows.

### `constituencies`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `state_id` | int FK -> states.id | no | |
| `name` | text | no | unique within state |
| `house` | text | no | `lok_sabha` only — see note |

Rajya Sabha members are seated by state and have no constituency. The Rajya
Sabha allocation file has no `Constituency` column, which is correct, not a
defect (profile §9).

### `mps`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `name_raw` | text | no | as published, suffixes intact |
| `name_canon` | text | no | term suffixes stripped; the join key |
| `house` | text | no | `lok_sabha` \| `rajya_sabha` |
| `state_id` | int FK -> states.id | no | |
| `constituency_id` | int FK -> constituencies.id | **yes** | null for every Rajya Sabha member |
| `term_start` | int | yes | null when the suffix was `(NaN-NaN)` |
| `term_end` | int | yes | |

766 rows measured; see profile §10 note 2 for the 766-against-764 discrepancy.

### `agencies`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `name_canon` | text | no | unique; the merged entity |
| `district` | text | yes | |
| `state_id` | int FK -> states.id | no | |
| `variant_count` | int | no | how many raw strings merged into this row |
| `merge_confidence` | real | yes | rapidfuzz ratio of the weakest merged variant |

### `agency_name_variants`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `agency_id` | int FK -> agencies.id | no | |
| `name_raw` | text | no | unique; e.g. `DISTRICT MAGISTRAE BUDAUN` |
| `score` | real | no | match score against `name_canon` |

Kept as its own table so a disputed merge is inspectable in the UI rather than
lost inside the loader (declared limitation 9).

### `vendors`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `name_canon` | text | no | unique |
| `agency_span` | int | no | distinct agencies paying this vendor; max measured 7 |

15,245 rows.

### `fund_accounts` — the account ladder, materialised
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `mp_id` | int FK -> mps.id | no | unique with `fy` |
| `fy` | text | no | e.g. `2024-2025` |
| `allocated_amt` | int | yes | paise-free rupees |
| `allocated_availability` | enum | no | |
| `sanctioned_amt` | int | no | rollup, default 0 |
| `disbursed_amt` | int | yes | null when no payment row joins |
| `disbursed_availability` | enum | no | |
| `mp_utilisation_pct` | real | yes | null when `allocated_amt` is null or 0 |

### `works`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `work_id_canon` | text | no | **unique**; whitespace-stripped, uppercased |
| `work_id_raw` | text | no | exactly as published, tabs intact |
| `mp_id` | int FK -> mps.id | no | |
| `agency_id` | int FK -> agencies.id | yes | null when the agency string was blank |
| `state_id` | int FK -> states.id | no | |
| `district` | text | yes | |
| `category` | text | yes | one of four values, profile §7 |
| `description` | text | **yes** | 50 rows are null; drives two skips |
| `status` | text | yes | one of six values, profile §7 |
| `fy` | text | no | parsed from the work id |
| `asset_image_present` | bool | no | `Image == 'Images'` |
| `is_synthetic` | bool | no | default false; CLAUDE.md invariant 12 |
| `source_file` | text | no | which of the twelve exports this row came from |

### `sanctions`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `work_id` | int FK -> works.id | no | unique |
| `recommended_amt` | int | yes | |
| `recommended_availability` | enum | no | |
| `recommended_date` | date | yes | |
| `sanctioned_amt` | int | no | |
| `sanction_date` | date | no | |

Recommended equals sanctioned in 14,831 of 14,831 matched works (profile §5).
Both columns are kept because that identity is itself the finding, and because a
future download may break it.

### `payments`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `work_id` | int FK -> works.id | no | |
| `vendor_id` | int FK -> vendors.id | yes | |
| `paid_amt` | int | yes | |
| `paid_availability` | enum | no | `published_zero` is common and meaningful |
| `payment_date` | date | yes | |
| `payment_status` | text | no | `Payment Success` \| `Payment In-Progress` |

34,002 rows; mean 1.51 per work, max 49.

### `completions`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `work_id` | int FK -> works.id | no | unique |
| `completion_date` | date | yes | |
| `completed_amt` | int | yes | |
| `completed_availability` | enum | no | |

There is **no** `certified_amt` and no `certification_date` column anywhere,
because MoSPI publishes neither. The fund ladder's hop 2 reads a certification
rung that exists in the derivation layer and is `not_published` on every real
row. See §(i).

### `calamity_consents`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `mp_id` | int FK -> mps.id | no | |
| `event_name` | text | no | 7 distinct events |
| `consented_amt` | int | no | |
| `consent_date` | date | yes | |

32 rows, Rs 29.01 crore. Context only; no rule reads this table in v1.

### `cases`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `case_id` | text PK | no | deterministic, `NG-` + 10 hex |
| `work_id` | int FK -> works.id | no | unique |
| `score` | int | no | capped 0-100 |
| `raw_score` | int | no | uncapped, 0-154 |
| `severity` | text | no | `HIGH` \| `MEDIUM` \| `LOW` |
| `status` | text | no | `open` \| `under_review` \| `escalated` \| `resolved` |
| `coverage_pct` | int | no | 0-100 |
| `gap_hop` | text | yes | |
| `slowest_lag` | text | yes | |
| `rulebook_version_id` | int FK -> rulebook_versions.id | no | the snapshot it was scored under |
| `corroboration_bonus` | int | no | 0 or 10 |
| `opened_at` | datetime | no | |
| `is_synthetic` | bool | no | mirrors `works.is_synthetic` for query speed |

### `rule_hits`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `case_id` | text FK -> cases.case_id | no | |
| `rule_id` | text | no | |
| `label` | text | no | as snapshotted, not as currently in rules.yaml |
| `raw_value` | text | yes | stringified so numbers, booleans and nulls share one column |
| `threshold` | text | no | |
| `operator` | text | no | |
| `weight` | int | no | |
| `contribution` | int | no | `weight` if fired, else 0 |
| `severity` | text | no | |
| `status` | text | no | `fired` \| `passed` \| `skipped` |
| `skip_reason` | text | yes | `not_published` \| `published_zero` \| `not_applicable`; non-null exactly when status is `skipped` |
| `citation_json` | text | yes | non-null only on `duplicate_work`; see §(h) |
| `caveat` | text | yes | e.g. the truncation caveat on `status_payment_mismatch` |

One row per rule per case, always ten rows, including passed and skipped. A
trace that omitted the passes would not be re-derivable.

### `audit_log`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | monotonic |
| `at` | datetime | no | |
| `actor_role` | text | no | |
| `actor_id` | int | yes | |
| `event` | text | no | one of the ten in §(j) |
| `case_id` | text FK -> cases.case_id | yes | |
| `payload_json` | text | yes | before/after trace on SCORE_RECOMPUTED |
| `prev_hash` | text | yes | sha256 of the previous row |
| `row_hash` | text | no | sha256 over this row plus `prev_hash` |

**Append-only.** No UPDATE, no DELETE, no helper capable of either, anywhere in
`backend/` (CLAUDE.md invariant 4). The hash chain makes a tamper visible even
if someone reaches the SQLite file directly.

### `rulebook_versions`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `version` | text | no | unique, e.g. `v1.0.0` |
| `yaml_snapshot` | text | no | the complete rulebook text, verbatim |
| `yaml_sha256` | text | no | |
| `created_at` | datetime | no | |
| `created_by_role` | text | no | |
| `note` | text | yes | why the officer changed it |

An edit **creates a version**; it never mutates one. Recompute reads
`cases.rulebook_version_id` and parses `yaml_snapshot` (CLAUDE.md invariant 5).

### `ml_findings`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `work_id` | int FK -> works.id | no | |
| `kind` | text | no | `duplicate` \| `anomaly` \| `forecast` \| `graph` |
| `value` | real | yes | |
| `payload_json` | text | yes | matched ids, components, feature attributions |
| `model_version` | text | no | |
| `contributes_to_score` | bool | no | **false for every kind except `duplicate`** |

The column is not decoration. The test for CLAUDE.md invariant 1 asserts that
the sum of scored contributions from rows where `contributes_to_score` is false
is exactly zero.

### `ingest_rejects`
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | int PK | no | |
| `source_file` | text | no | |
| `row_number` | int | no | 1-based, excluding the header |
| `raw_row` | text | no | the line as read |
| `reason` | text | no | `column_shift` \| `work_id_unparseable` \| `negative_lag` \| `case_id_collision` \| `unknown_category` \| `duplicate_work_id` |
| `at` | datetime | no | |

Ingestion never silently drops a row (CLAUDE.md invariant 11). A test asserts
`loaded + rejected == rows_in_file` for all twelve files.

---

## (f) Derived feature dictionary

Every key the rulebook may reference. Nothing else is addressable from
`rules.yaml`; a rule naming an unknown field is a load-time error, not a silent
skip.

| Key | Type | Source columns | `None` when |
| --- | --- | --- | --- |
| `work_id` | str | `works.work_id_canon` | never |
| `variance_sanction_to_disbursement` | float % | `sanctions.sanctioned_amt`, sum of `payments.paid_amt` | no payment row joins (`not_published`), or `sanctioned_amt` is 0 |
| `variance_disbursement_to_certification` | float % | disbursed rollup, certified rung | **always, on real data** — `not_published` |
| `sanction_lag_days` | int | `sanctions.recommended_date`, `sanctions.sanction_date` | either date is null (`not_published`) |
| `sanction_to_first_payment_days` | int | `sanctions.sanction_date`, min `payments.payment_date` | no payment row (`not_applicable` if the work has not reached payment stage, `not_published` otherwise) |
| `execution_days` | int | `sanctions.sanction_date`, `completions.completion_date` | no completion row (`not_applicable` — the work is not finished) |
| `days_since_last_payment` | int | max `payments.payment_date`, `DATA_AS_OF` | no payment row (`not_published`) |
| `duplicate_similarity` | float 0-1 | `works.description` within `agency_id` | description is null (50 rows), or the agency has only this work |
| `same_desc_same_agency_count` | int | `works.description`, `works.agency_id` | description is null, or `agency_id` is null |
| `vendor_share_in_agency_pct` | float % | `payments.paid_amt` by `vendor_id` within `agency_id` | the work has no payment, or the agency's total disbursement is at or below the Rs 50 lakh floor |
| `completed_without_payment` | bool | `works.status`, count of `payments` | `works.status` is null |
| `asset_image_absent` | bool | `works.asset_image_present` | `works.asset_image_availability` is `not_published` — 14,104 of 27,078 sanctioned works |
| `mp_utilisation_pct` | float % | `fund_accounts` for this work's MP and FY | no allocation row for that MP and FY (`not_published`) |
| `payment_count` | int | count of `payments` | never — 0 is a real value, not a null |

Three rows deserve their reasoning stated:

- **`asset_image_absent` is `None` on more than half the corpus, and this row
  previously claimed it never was.** The claim was wrong and is corrected here.
  The portal publishes the `Image` column **only in the completed export**, so a
  sanctioned work that has not been reported complete has no image field to
  read at all. That is `not_published` — a reporting gap — and it is a different
  finding from a work whose `Image` column *was* published carrying `N/A`, which
  is `published` with `asset_image_absent = true` and a photograph genuinely
  never filed. Collapsing the two would fire `asset_evidence_missing` on a
  reporting gap across 52% of the corpus, which is precisely what invariant 2
  exists to prevent. Measured on the sanctioned population: 12,974 published
  (8,481 present, 4,493 absent) and **14,104 `not_published`**, so the rule
  fires on 4,493 and is skipped on 14,104 (DATA-PROFILE.md §6).

  Because `works.asset_image_present` is itself nullable, the availability
  companion `works.asset_image_availability` is what the derivation reads: the
  feature is `None` exactly when the companion is `not_published`. The
  underlying column being nullable is what makes the distinction storable, and
  the companion is what makes it *legible* — a bare null could not say which of
  the two findings it was.
- **`payment_count` is never `None`.** Zero payments is a fact about the work,
  not a missing measurement. Making it nullable would have let a real zero
  masquerade as an unmeasured field, which is exactly the confusion invariant 2
  exists to prevent.
- **`days_since_last_payment` is measured against `DATA_AS_OF = 2026-08-24`**,
  the maximum payment date in the corpus, and never against `today`. Otherwise
  a case re-derived six months from now would score differently from the case an
  officer acted on, and the audit trail would be a lie.

---

## (g) The rulebook

Ten rules. 144 points of weight, plus a 10-point corroboration bonus, 154
maximum. Display capped at 100, **never renormalised**.

Every threshold is drawn from a measured distribution in
`docs/data/DATA-PROFILE.md` §6, and carries a YAML comment naming its firing
count on the profiled sample (CLAUDE.md invariant 6).

| # | `rule_id` | Field | Op | Threshold | Weight | Severity | Fires on |
| --- | --- | --- | --- | ---: | ---: | --- | ---: |
| 1 | `utilisation_shortfall` | `variance_sanction_to_disbursement` | `lt` | −15 | 22 | high | 288 of 944 |
| 2 | `execution_delay` | `execution_days` | `gt` | 365 | 20 | high | 2,568 |
| 3 | `duplicate_work` | `duplicate_similarity` | `gte` | 0.85 | 18 | high | 2,843 in 363 clusters |
| 4 | `sanction_delay` | `sanction_lag_days` | `gt` | 180 | 16 | medium | 2,868 |
| 5 | `stalled_work` | `days_since_last_payment` | `gt` | 270 | 16 | medium | see note |
| 6 | `vendor_concentration` | `vendor_share_in_agency_pct` | `gt` | 60 | 12 | medium | 66 agency-vendor pairs |
| 7 | `status_payment_mismatch` | `completed_without_payment` | `eq` | `true` | 12 | medium | 1,371 of 1,629 |
| 8 | `split_sanction` | `same_desc_same_agency_count` | `gte` | 3 | 10 | medium | 2,843 |
| 9 | `asset_evidence_missing` | `asset_image_absent` | `eq` | `true` | 10 | low | not directly measured - see note |
| 10 | `account_underutilisation` | `mp_utilisation_pct` | `lt` | 25 | 8 | low | 246 of 419 MPs |

### Rationale, one line each

1. **`utilisation_shortfall`** — the only amount variance the data supports.
   −15% sits between the median (−0.19%) and p5 (−84.0%): well clear of rounding
   noise, well short of the tail, and it selects 288 of 944. Weight 22, the
   highest, because money sanctioned and not delivered is the scheme's core
   failure.
2. **`execution_delay`** — 365 d is p90-adjacent (p90 = 444 d, p75 = 308 d) and
   is the threshold a citizen would recognise: a year to build it. Fires on
   2,568 works.
3. **`duplicate_work`** — 0.85 similarity is above near-identical boilerplate and
   below unrelated descriptions in the same category. Weight 18, but see §(h):
   it is the only ML-fed rule and it earns its points only by citing evidence.
4. **`sanction_delay`** — 180 d sits between p75 (150 d) and p90 (262 d), so it
   selects the slow quarter without firing on the ordinary half. Fires on 2,868.
5. **`stalled_work`** — 270 d of silence after the last payment, measured to
   `DATA_AS_OF`. Nine months exceeds any normal inter-instalment gap on a mean of
   1.51 payments per work. The firing count is not yet measured; it must be
   recorded here on the next profile pass, and this line is a standing TODO
   rather than a fabricated number.
6. **`vendor_concentration`** — >60% of one agency's disbursement to one vendor,
   with a Rs 50 lakh agency floor so a tiny agency with one work does not fire.
   66 pairs qualify.
7. **`status_payment_mismatch`** — reported complete, no payment ever recorded.
   Fires on 1,371 of 1,629. **This rule carries a mandatory caveat on its trace
   row**: the expenditure export is truncated, so some of these are export
   artefacts rather than reporting failures (profile §6). The caveat is displayed
   with the flag, not in a footnote.
8. **`split_sanction`** — three or more works with the same description under the
   same agency. Three is the smallest count that is not a coincidence. Weight is
   only 10 because legitimate repetition is common.
9. **`asset_evidence_missing`** — no photograph filed at all. Weight 10 and
   severity low: it is an evidence gap, not a finding. The `Image` column is
   binary with no geotag, so this is the most the data permits. **Its firing
   count is not directly measured.** The profile records 9,445 rows carrying
   `Images`, but not over which population, so subtracting it from 27,078 would
   be an inference dressed as a measurement. The count must be measured on the
   next profile pass; until then this cell reads "not directly measured".
10. **`account_underutilisation`** — below 25% of allocation, against a median of
    19.6%. Deliberately the smallest weight: aggregate MP underuse is context
    for a work, never the substance of a finding against it.

### Corroboration

```yaml
corroboration:
  id: agency_pattern_bonus
  min_high_cases: 3
  window: FY
  weight: 10
```

Awarded when the work's implementing agency already has **3 or more HIGH cases
in the same financial year**. One bad work is an incident; a pattern under one
agency in one year is a posture. Three is the smallest count that survives the
objection "a large district will have some". The bonus applies once per case and
is the only non-rule source of score.

### Totals and bands

```
raw_score = sum(weight for rules with status == 'fired') + corroboration_bonus
score     = min(raw_score, 100)
severity  = HIGH if score >= 75 else MEDIUM if score >= 50 else LOW
```

Both numbers are stored and both are shown. Capping is not renormalisation:
weights are never divided by 1.54, because an officer re-deriving the trace on
paper must be able to add the printed weights and reach the printed raw total.

### Operators

`lt` · `lte` · `gt` · `gte` · `eq` · `ne`. Six, and no more.

**There is no AND, no OR and no nesting, and that is a decision, not an
omission.** A rule with boolean structure cannot be explained in one line to an
officer or edited safely by one in the UI, and its contribution cannot be
attributed to a single field in the trace. Composite conditions are expressed as
separate rules whose weights add — which is also what makes partial evidence
degrade gracefully, since one leg can be `skipped` while the other still
evaluates. A nested rule would have to be skipped entirely.

If a genuine conjunction is ever needed, the correct move is a derived feature
in §(f) that computes it, with its own null semantics and its own test — not a
grammar in the YAML.

### `cost_overrun` — designed, then removed

A `cost_overrun` rule comparing sanctioned amount against a revised estimate was
designed and carried a weight of 20. It was **removed** when the profile
measured recommended amount equal to sanctioned amount in **14,831 of 14,831**
matched works, with zero variance (profile §5). The portal publishes no revised
estimate, so the rule had no second number to read and would have been skipped
on every row in the corpus.

It is not deleted from the project. It is entry two in the ablation report
§(i), where it becomes a specific, costed request to MoSPI: publish the revised
estimate and this rule turns on.

---

## (h) The ML boundary

Four tiers. **Exactly one can move the score.**

| Tier | Component | Library | Moves the score? |
| --- | --- | --- | --- |
| 1 | Reconciliation and derived features | pandas / numpy | **No** — it produces inputs, not points |
| 2 | Rulebook evaluation | PyYAML, pure Python | **YES — the only source of score, with the F4 bonus** |
| 3 | Statistical: peer z-score, IsolationForest anomaly, delay forecast | scikit-learn | **No. Zero. Badge only** |
| 4 | Graph: agency-vendor bipartite concentration and centrality | networkx | **No. Zero. Badge only** |

Tier 3 and tier 4 confirm, or fail to confirm, what tier 2 already found. A
badge reading "confirms" raises an officer's confidence; it does not raise the
number. One test per model asserts this by perturbing the model output and
asserting the score is unchanged (CLAUDE.md invariant 1).

### The `duplicate_work` exception

`duplicate_work` is a tier-2 rule that reads `duplicate_similarity`, a number
produced by a `rapidfuzz` similarity model. It contributes 18 points. That is a
genuine exception to "no model moves the score", and it is admissible for one
reason only: **the trace row cites its evidence.**

`rule_hits.citation_json` on a fired `duplicate_work` MUST contain:

```json
{
  "matched_work_ids": ["WS/MP410/2024-2025/118431", "WS/MP410/2024-2025/118455"],
  "cluster_size": 244,
  "shared_description": "high mast led light 95 mtrs ms pole with 6 led",
  "agency": "District Magistrate, Budaun",
  "similarity": 0.97,
  "components": {
    "token_set_ratio": 1.00,
    "partial_ratio": 0.98,
    "length_ratio": 0.93
  },
  "method": "rapidfuzz.token_set_ratio over normalised description, blocked by agency_id"
}
```

The officer opens both works and judges for themselves. Nobody is asked to
believe the number; they are handed the two records the number came from. That
is **explainability by citation, not by trust**, and it is why this one model
output is allowed into the score while the other three are not.

A citation is mandatory. A `duplicate_work` hit with `status == 'fired'` and a
null `citation_json` is a failed test, not a degraded row.

### A duplicate cluster is a candidate for review, never an accusation

This has to be said in the code, in the UI and on stage. The largest cluster in
the corpus is 244 high-mast LED street lights under one district magistrate. The
overwhelmingly likely explanation is that a constituency needed 244 street
lights and they were sanctioned with a copy-pasted description. That is not
fraud; it is administrative convenience.

What the cluster is worth is an officer's ten minutes. The UI word is
**"review"** — never "fraud", never "duplicate payment", never "ghost work".
Copy that implies otherwise is a bug.

---

## (i) The ablation module (F9)

Implemented in `backend/app/ablation/` — `fields.py` (the field list and its
traceability), `measure.py` (the measurement), `rank.py`, `report.py`,
`run.py`. It is a tier of its own beside `engine/` and `ml/`, under the same
one-way rule: `ablation/` reads `engine/`, and neither `engine/` nor `ml/` may
import `ablation/`. The AST walk in `tests/test_ml_boundary.py` enforces both
arrows, so nothing this module measures can reach `score.py`'s addition
(CLAUDE.md invariant 1).

> ### Correction — Phase 4
>
> **The masking method this section previously described is withdrawn for
> absent fields, and the worked example it carried was illustrative rather than
> measured.** The old text said: mask the field, re-run the rulebook, and for
> the seven absent fields take the result as a labelled counterfactual. For a
> field NIGRANI *does* read that is sound — masking a real column is a real
> experiment. For a field MoSPI has never published there is nothing to mask:
> the value is already `None` with reason `not_published` on every row, so the
> only way to produce a delta is to invent a value and re-score a work against
> it. That is a fabricated score, and it is the exact failure the project
> rejected when fixture C was corrected from an invented 42 to the 20 the
> labelled control actually produces (`docs/contract/fixtures.md`, standing
> caveats 7 and 9).
>
> The old example row carried `weight_recoverable: 20` and
> `coverage_gain_pct: 12.2` for the utilisation certificate. Neither was a
> measurement — they were placed to show the shape of the JSON. The measured
> figure for that field is **zero**, for the reason given below, and the
> corrected shape is at the end of this section.

**Method — structural, over real Availability data.** For each field, measure
what its absence costs the rulebook that exists today, using only facts already
recorded in the corpus and in the reasoning trace. Nothing is imputed and no
work is re-scored.

Measured exactly:

1. **Which rules skip because of this field**, counted from the `skip_reason`
   values `engine/derive.py`'s Availability companions actually produced, on
   works meeting a stated condition read straight off the row. Each field
   declares that attribution — rule ids, skip reason, condition — and
   `tests/test_ablation.py` asserts it holds in **both** directions: every skip
   claimed is a skip the engine recorded, and every skip matching the condition
   is claimed. One direction alone would let an attribution under- or
   over-count.
2. **The rulebook weight those skips leave unrealised**, summed over the corpus.
3. **The distinct works** carrying at least one such skip.
4. **Mean `coverage_pct` as it stands, and as it would stand if those skips
   became evaluable** — evaluable, not fired. Both come from
   `engine.score.coverage_pct`, the function the case body already uses;
   `ablation/` does not carry a second copy of the coverage formula.

Extrapolated, and labelled as such wherever it appears:

5. **Additional rule fires**, if a newly evaluable rule fired at the rate it
   fires today among the works where it *is* evaluable. The rate is real —
   `fired / (fired + passed)` over a named population — and multiplying it by a
   measured skip count is an extrapolation a reader can check.

Refused:

- No value is invented, imputed or simulated for an absent field, and no work is
  re-scored as if the field were present.
- The extrapolated fire counts are **never allocated to specific works**, so the
  severity-band effect is a floor and a ceiling and never a point estimate.
  Saying how many rules would fire is defensible; saying which works they fire
  on is the fabrication. The floor is checked against the affected population's
  absorbing capacity rather than asserted; the ceiling relaxes the per-rule
  budgets into one total, so it bounds rather than constructs.
- The corroboration bonus is held at its measured value inside the ceiling,
  because re-resolving it would begin by deciding which cases became HIGH.

**The finding, and it was not the expected one.** Applying that method to
`DATA-PROFILE.md` §8's seven absent fields returns **zero unrealised weight for
all seven** — not because their absence is harmless, but because rulebook
v1.0.0 contains no rule that reads any of them. A rule that was never written
cannot be skipped. That is a proof rather than a claim: `tests/test_ablation.py`
asserts every rule id those fields would unlock (`cost_overrun`,
`certification_shortfall`, `physical_financial_mismatch`, `single_bid_award`,
`bid_rotation`, `asset_colocation_conflict`, `asset_photo_reuse`,
`cost_per_beneficiary_outlier`) is absent from `rules.yaml`, and fails the
moment one is added.

**The entire measured detection loss sits in two fields MoSPI already publishes,
and publishes incompletely.** The second of the two is not on §8's list at all —
it was surfaced by running the attribution the other way round, asking which
skip reasons the corpus records and which field each traces back to, and it is
labelled `surfaced_by_measurement` so it can be told apart from the seven the
profile named.

| Rank | Field | Kind | Rule skips | Works | Unrealised weight | Coverage uplift |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 1 | Complete expenditure linkage | published incompletely | **70,647** | 23,549 | **1,177,450** | 58.47% → 88.91%, **+30.44 pp** |
| 2 | Asset evidence for works not yet complete | published incompletely, surfaced by measurement | 14,104 | 14,104 | 141,040 | 58.47% → 62.12%, +3.65 pp |
| — | The seven fields of profile §8 | never collected | **0** | 0 | **0** | 0.00 pp |

Rank 1's three skipped rules are `utilisation_shortfall` (22 × 23,549),
`stalled_work` (16 × 23,549) and `vendor_concentration` (12 × 23,549) — the
23,549 sanctioned works no expenditure row joins to. `vendor_concentration`'s
other 137 skips are `not_applicable` for the Rs 50 lakh agency floor and are
**not** attributed here: a small agency is a fact about the agency, not a gap in
MoSPI's export.

**Ranking criterion: total unrealised rulebook weight, measured. One criterion,
and no composite.** Works-affected counts a case touched rather than evidence
lost; coverage uplift is the same quantity divided by
`RULE_WEIGHT_TOTAL × corpus works` and gives an identical ordering, so it is
reported beside the criterion and not as a second one. The criterion does not
separate the seven fields tied at zero, and `rank.py` does not invent a
separator for them — they are reported as tied, in profile §8's own order, each
with its own measured corroborating figures. Those figures are not commensurable
and are deliberately not folded into a tiebreak.

**Output shape** — one row per recommendation, returned by `GET /api/ablation`.
Two rows, because the difference between them is the point:

```json
{
  "field": "expenditure_linkage",
  "label": "Complete expenditure linkage",
  "gap_kind": "published_incompletely",
  "basis": "measured_skips",
  "rank": 1,
  "publish_as": "The existing expenditure export, complete. Every payment row for every sanctioned work, rather than the first 34,000 rows.",
  "improves_rules": ["utilisation_shortfall", "stalled_work", "vendor_concentration"],
  "measured": {
    "rule_skips": 70647,
    "works_affected": 23549,
    "unrealised_weight": 1177450,
    "coverage_pct_now": 58.47,
    "coverage_pct_if_published": 88.91,
    "coverage_uplift_pct": 30.44
  },
  "extrapolated": { "additional_fires_total": 10242 },
  "severity_band_effect": { "floor": 0, "ceiling": 9271 }
}
```

```json
{
  "field": "utilisation_certificate",
  "gap_kind": "never_collected",
  "basis": "no_rule_reads_it",
  "rank": null,
  "unlocks_rules": ["certification_shortfall"],
  "zero_reason": "No rule in rulebook v1.0.0 reads variance_disbursement_to_certification, because there is no published data to calibrate a threshold against. A rule that does not exist cannot be skipped.",
  "measured": { "rule_skips": 0, "works_affected": 0, "unrealised_weight": 0, "coverage_uplift_pct": 0.0 },
  "extrapolated": null,
  "severity_band_effect": null
}
```

`basis` replaces the old `estimate_basis`, and it is this module's availability
companion. Every number above is always computed and a zero is always a measured
zero, so what needs recording is *why* a zero is zero: `measured_skips` means
rules do read the field and are skipped for its absence; `no_rule_reads_it`
means nothing can be skipped, and the gap is upstream of the rulebook rather
than harmless. `rank` and `extrapolated` are null exactly when `basis` is
`no_rule_reads_it`, and `basis` is what explains both nulls.

**Storage.** `ablation_findings`, one row per field, written by
`python -m app.ablation.run` and rebuilt by drop-and-create the way
`ml_findings` is — so a second run replaces its own output and no helper here is
capable of removing a row (invariant 4). Every row carries `DATA_AS_OF` rather
than a wall clock, so two runs over the same corpus produce identical rows and a
byte-identical `docs/reports/DATA-GAP-RECOMMENDATION.md`. That document is
generated, never hand-written, and a test asserts the committed copy is what the
code produces.

**Fixture C is what makes the certification entry concrete on screen.** Its fund
ladder shows hop 2 open at −25.00% beside a score of 20 and a LOW band, because
no rule reads that hop. NIGRANI can see the shape of the gap and cannot score
it — which is the whole of this section in one case.

This is the feature that turns NIGRANI from a detector into a contribution: the
system's own blind spots become a measured, prioritised reporting recommendation
back to the ministry that publishes the data. What changed in Phase 4 is that
the measurement is now honest about which of those blind spots the current
rulebook can actually price, and which it cannot price at all.

---

## (j) Audit events

Ten event types. Append-only, hash-chained (CLAUDE.md invariant 4).

| Event | Written when | Payload carries |
| --- | --- | --- |
| `CASE_OPENED` | A case row is first created by ingest or rescore | work id, rulebook version, initial score |
| `RULE_FIRED` | A rule evaluates to fired during scoring | rule id, raw value, threshold, contribution |
| `DUPLICATE_LINKED` | A `duplicate_work` citation is attached | matched work ids, cluster size, similarity |
| `PATTERN_LINKED` | The corroboration bonus is awarded | agency id, the HIGH case ids counted, the FY window |
| `NOTE_ADDED` | An officer adds a note | actor role, note text |
| `SCORE_RECOMPUTED` | A recompute runs | **before and after full `rule_hits` trace**, not only the scalar |
| `ALERT_RAISED` | An alert enters a role queue | alert id, target role, target scope, score |
| `ALERT_ESCALATED` | An alert moves between roles | from role, to role, reason |
| `RULEBOOK_UPDATED` | A new rulebook version is created | old version, new version, yaml diff, sha256 of both |
| `INGEST_COMPLETED` | An ingest run finishes | per-file loaded, rejected, reconciliation result |

`SCORE_RECOMPUTED` carrying the full before-and-after trace is what makes
CLAUDE.md invariant 5 auditable rather than merely asserted: an auditor can see
*which rule* changed and by how much, not only that a number moved.

---

## (k) Role scoping matrix

Enforced in the query, server-side, on every endpoint (CLAUDE.md invariant 10).
A District Authority editing a URL gets a 404, not another district's case.

Let `S` = the user's state, `D` = the user's district, `M` = the user's MP id.

| Table | Ministry | State Nodal | District Authority | Member of Parliament |
| --- | --- | --- | --- | --- |
| `states` | all | own state | own state | own state |
| `constituencies` | all | in `S` | in `S` | own only |
| `mps` | all | seated in `S` | recommending into `D` | **own row only** |
| `agencies` | all | in `S` | in `D` | agencies on own works |
| `vendors` | all | paid by agencies in `S` | paid by agencies in `D` | paid on own works |
| `fund_accounts` | all | MPs seated in `S` | none | **own rows, all FYs** |
| `works` | all | `state_id == S` | `district == D` | `mp_id == M` |
| `sanctions` | all | via `works` | via `works` | via `works` |
| `payments` | all | via `works` | via `works` | via `works` |
| `completions` | all | via `works` | via `works` | via `works` |
| `calamity_consents` | all | MPs seated in `S` | none | own rows |
| `cases` | all | via `works` | via `works` | via `works`, **read-only** |
| `rule_hits` | all | via `cases` | via `cases` | via `cases` |
| `audit_log` | all | rows for visible cases | rows for visible cases | rows for own cases, **excluding other actors' note text** |
| `rulebook_versions` | all, **write** | all, read | all, read | all, read |
| `ml_findings` | all | via `works` | via `works` | via `works` |
| `ingest_rejects` | **all** | none | none | none |

Four rows carry a deliberate decision:

- **`fund_accounts` is invisible to a District Authority.** A district officer
  has no business seeing an MP's aggregate account position; it is not evidence
  about any work in their district. The one derived value they need,
  `mp_utilisation_pct`, reaches them through the case trace, where it is scoped
  to that case's MP.
- **The MP role is read-only everywhere.** An MP can see, and cannot annotate,
  escalate, resolve or recompute. The scheme's subject does not adjudicate the
  scheme's findings.
- **`audit_log` hides other actors' note text from the MP.** An MP sees that a
  note was added, by which role, and when. The text is the administration's
  working record.
- **`ingest_rejects` is Ministry-only.** It contains raw rejected source lines,
  including the two malformed rows, and it is a data-quality artefact rather
  than a finding about anyone.
