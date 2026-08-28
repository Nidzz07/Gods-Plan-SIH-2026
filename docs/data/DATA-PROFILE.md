# DATA-PROFILE — what the real MPLADS data actually contains

**Every figure on this page was measured on the twelve portal exports committed
in `data/raw/`, downloaded 26 August 2026 from
https://mplads.mospi.gov.in/digigov/dashboard.html.**

**Those exports are truncated samples, not the full portal.** Several files stop
at round row limits (35,000 / 29,000 / 8,000 / 7,000 / 5,000). Every number
below is therefore a finding *on this sample*, never a national total, and
nothing here may be presented publicly as a national figure.

**These figures MUST be re-measured after any fresh download.** The rulebook
thresholds in `backend/app/rules.yaml` are calibrated against the firing counts
recorded here (CLAUDE.md invariant 6). A new download invalidates that
calibration until this file is regenerated.

Provenance and licence live in `data/raw/README.md`. This file is the profile.

---

## 1. Files

Twelve files, each dataset published separately for the two Houses. Row counts
exclude the header.

| Dataset | Lok Sabha | Rajya Sabha | Total |
| --- | ---: | ---: | ---: |
| `Works_Recommended` | 35,000 | 7,000 | 42,000 |
| `Works_Sanctioned` | 8,000 | 19,078 | 27,078 |
| `Works_Completed` | 5,000 | 9,830 | 14,830 |
| `Expenditure_on_Completed_and_On-going_Works_as_on_Date` | 29,000 | 5,000 | 34,000 |
| `Allocated_Limit_for_Honble_MPs` | 543 | 221 | 764 |
| `Amount_consented_for_Calamity` | 12 | 20 | 32 |
| **Total** | **77,555** | **41,149** | **118,704** |

Format facts the loader must honour: UTF-8 **with BOM** (`encoding='utf-8-sig'`),
CRLF line endings, every field quoted including numerics, amounts as plain
integer rupee strings, dates as `%d-%b-%Y`. Column headers embed the rupee sign
with irregular spacing (`RECOMMENDED AMOUNT   ( ₹ )`, three spaces before the
bracket) and must be matched
loosely, never by exact string equality.

---

## 2. Join key

The work id, pattern `WS/MP{code}/{FY}/{serial}`.

| Where it lives | Column | Form |
| --- | --- | --- |
| Works_Recommended | `Work` | embedded at the start, followed by a hyphen and the category text |
| Works_Sanctioned | `Work` | same |
| Works_Completed | `Work` | same |
| Expenditure | `Work ID` | explicit, its own column |

Canonicalisation: strip **all** internal whitespace and tab characters before
comparing. Some Lok Sabha rows carry a literal tab inside the id
(`WS/<TAB> MP620/2024-2025/133166`).

Parse success rate:

| File | Work ids parsed |
| --- | ---: |
| Works_Recommended, Lok Sabha | 94.7% |
| Works_Recommended, Rajya Sabha | 97.9% |
| All other files | 99.98% - 100% |

---

## 3. Join yield

| Join | Result |
| --- | ---: |
| sanctioned to recommended | 99.7% |
| completed to sanctioned | 12,974 works |
| expenditure to sanctioned | 3,529 works |
| recommended **and** sanctioned **and** expenditure | 944 works |
| MP name to allocation (after name normalisation) | 100% (416 / 416) |

The 944-work three-way intersection is the population for every
sanction-to-disbursement figure in section 6. It is small because the
expenditure export is truncated, not because the works lack payments.

---

## 4. Scale

| Quantity | Value |
| --- | ---: |
| Unique sanctioned works | 27,078 |
| Payment rows | 34,002 |
| MPs | 766 |
| Implementing agencies | 638 |
| Vendors | 15,245 |
| States | 32 |
| Financial years covered | FY2023-24 to FY2026-27 |
| Sanction date range | 2023-07-07 to 2026-08-22 |
| Payment date range | 2025-02-14 to 2026-08-24 |
| Total allocated | Rs 23,242 crore |

`2026-08-24`, the maximum payment date, is the corpus **as-of date**. Every
"days since" feature is measured against it, never against `today`, so a
re-derivation months later reproduces the same number. It is defined once as a
constant and imported (CLAUDE.md invariant 7).

---

## 5. The degeneracy finding

**This is the single most important measurement in the project. It determines
what the rulebook can and cannot contain.**

| Comparison | Works matched | Works where the two amounts differ |
| --- | ---: | ---: |
| Recommended amount vs Sanctioned amount | 14,831 | **0** |
| Sanctioned amount vs Disbursed amount (completed works) | 12,974 | 1,318 (11,656 identical) |

Recommended amount equals sanctioned amount in **14,831 of 14,831** matched
works. Zero variance. The portal does not publish revised estimates, so there is
no second cost figure to compare the first against.

**Cost overrun is NOT computable from public MPLADS data.** A `cost_overrun`
rule was designed, and then removed, on the strength of this measurement. See
`docs/domain/DOMAIN-MODEL.md` section (g) and the ablation module in section (i).

Similarly, disbursement equals sanction in 11,656 of 12,974 completed works.

The consequence, stated plainly:

> **MPLADS public data is financially flat and temporally rich. The detectable
> signal lives in TIME and REPETITION, not in amount variance.**

Every rule in the rulebook follows from that sentence. Seven of the ten read a
date difference, a repetition count or a concentration share. Only one reads an
amount variance, and it reads the one variance that survives — sanctioned
against disbursed.

---

## 6. Measured signal distributions

These are the distributions the thresholds are calibrated against. Each
threshold in `rules.yaml` carries a YAML comment naming the firing count drawn
from here.

### Sanction lag — recommendation to sanction

| Statistic | Value |
| --- | ---: |
| Median | 88 d |
| p75 | 150 d |
| p90 | 262 d |
| p95 | 364 d |
| Max | 1,058 d |
| Works > 180 d | 2,868 |
| Works > 365 d | 739 |
| Negative lags | 0 |

### Execution delay — sanction to completion

| Statistic | Value |
| --- | ---: |
| Median | 169 d |
| p75 | 308 d |
| p90 | 444 d |
| Max | 948 d |
| Works > 365 d | 2,568 |
| Works > 730 d | 276 |

### Utilisation — sanctioned to disbursed (n = 944)

| Statistic | Value |
| --- | ---: |
| Mean | -18.2% |
| Median | -0.19% |
| p5 | -84.0% |
| Min | -98.6% |
| Max | **0.0%** |
| Works below -15% | 288 |
| Over-disbursement (> 0%) | **0** |

The maximum is exactly zero. No work in the sample is disbursed more than it was
sanctioned, so the utilisation rule is one-sided by measurement, not by choice.

### Payments per work (n = 944)

| Statistic | Value |
| --- | ---: |
| Mean | 1.51 |
| Max | 49 |
| Works with more than one payment | 115 |

### Duplicate descriptions within one agency

| Quantity | Value |
| --- | ---: |
| Clusters | 363 |
| Works inside a cluster | 2,843 |
| Value inside clusters | Rs 157.12 crore |

Largest cluster: **244 works**, agency *District Magistrate, Budaun*,
description *"high mast led light 95 mtrs ms pole with 6 led"*, Rs 3.98 crore.

A cluster is a candidate for review, never an accusation. Street lights repeat
across a constituency for entirely legitimate reasons.

### Vendor concentration

| Quantity | Value |
| --- | ---: |
| Agency-vendor pairs where one vendor takes > 60% of that agency's disbursement (agency total > Rs 50 lakh) | 66 |
| Vendors appearing under more than one agency | 489 |
| Maximum agencies spanned by one vendor | 7 |

### MP account utilisation — sanctioned / allocated (n = 419)

| Statistic | Value |
| --- | ---: |
| p25 | 6.6% |
| Median | 19.6% |
| p75 | 44.9% |
| Max | 95.8% |
| MPs below 25% | 246 |
| MPs above 100% | **0** |

### Status against payment

1,371 of the 1,629 works whose status is `Work Completed` have **no payment row
at all**.

> **Caveat, and it is a large one.** The expenditure export is truncated to
> 29,000 + 5,000 rows, and expenditure joins to only 3,529 sanctioned works. A
> missing payment row is therefore partly an artefact of the truncated export
> and not necessarily a real reporting failure. The `status_payment_mismatch`
> rule is calibrated with this caveat attached, and its trace row must carry the
> caveat text so an officer reads it at the same moment as the flag.
> Re-measure on a full download before quoting this figure to anyone.

---

## 7. Categorical vocabularies

Recorded in full so that an unseen value in a later download is detected as new
rather than silently bucketed.

### Work Status

| Value | Count |
| --- | ---: |
| Physical Inspection | 14,714 |
| Sanction | 4,366 |
| Vendor Identification | 3,910 |
| Work partially Completed | 2,353 |
| Work Completed | 1,629 |
| Time Estimation | 106 |

### Work category

| Value | Count |
| --- | ---: |
| Normal/Others | 26,469 |
| Repair and Renovation | 353 |
| Trust and Society | 246 |
| Bar and Associations | 3 |

### Payment Status

| Value | Count |
| --- | ---: |
| Payment Success | 30,753 |
| Payment In-Progress | 3,247 |

### Image

| Value | Count |
| --- | ---: |
| `Images` | 9,445 |
| `N/A` | remainder |

Binary presence only. **There is no geotag, no timestamp and no image URL.** The
column asserts that an image exists; it does not let anyone verify what it shows.

### Calamity

34 consents, Rs 29.01 crore, across 7 named events.

---

## 8. Fields absent entirely — the basis of the ablation module

Each row names a detection rule the field would unlock. **Every one of these
rules is currently NOT computable.** This table is the input to feature F9 and
to the reporting recommendation NIGRANI makes back to MoSPI.

| Absent field | Rule it would unlock | Status |
| --- | --- | --- |
| Geo coordinates of the asset | `asset_colocation_conflict` — two works claiming the same physical location | **Not computable** |
| Revised cost estimate | `cost_overrun` — sanctioned against revised estimate | **Not computable** (designed, then removed; see section 5) |
| Utilisation certificate date | `certification_shortfall` — the second fund hop, disbursed against certified | **Not computable** |
| Milestone / progress percentage | `physical_financial_mismatch` — money released ahead of physical progress | **Not computable** |
| Tender / bid records | `single_bid_award`, `bid_rotation` — competition failure | **Not computable** |
| Beneficiary counts | `cost_per_beneficiary_outlier` | **Not computable** |
| Asset photo geotag or timestamp | `asset_photo_reuse` — one photograph filed against several works | **Not computable** |

The `asset_evidence_missing` rule that *does* ship reads only the binary `Image`
presence flag. It can say a photograph was never filed. It can say nothing about
a photograph that was.

---

## 9. Data quality defects

Recorded so that nobody "fixes" them by editing the CSVs. Every one must be
handled in ingest, and every rejected row must land in `ingest_rejects` with a
reason (CLAUDE.md invariant 11).

| Defect | Extent | Handling |
| --- | --- | --- |
| Shifted columns — a formatted amount string lands in `Work Status` (`40,79,58,27,851.08`, `16,78,67,73,690.87`) | 2 rows | Reject to `ingest_rejects`, reason `column_shift` |
| Null work description | 50 rows | Load the row; `duplicate_similarity` and `same_desc_same_agency_count` become `None`, so those rules are **skipped**, never passed |
| Unparseable work id, `Works_Recommended_lok_sabha` | 5.3% of rows | Reject to `ingest_rejects`, reason `work_id_unparseable` |
| Literal tab inside the work id (`WS/<TAB> MP620/...`) | scattered | Canonicalise: strip all whitespace before comparing |
| MP name term suffixes — `(2022-28) (2022-2028)`, `(NaN-NaN)` | widespread | Normalise before the name-to-allocation join (yields 416/416) |
| Agency typo variants split one real agency (`DISTRICT MAGISTRAE` against `DISTRICT MAGISTRATE`) | 638 raw strings | Canonicalise to one `agencies` row; the raw string stays on the work |
| Rajya Sabha allocation file has no `Constituency` column | whole file | **Not a defect.** Rajya Sabha members are seated by state. `constituency_id` is nullable and the two loaders differ |
| Original filenames used spaces, not underscores | all 12 | Renamed on disk to match the documented convention |

---

## 10. Internal consistency notes — re-check on the next measurement

Honesty items. These are small discrepancies between figures measured in
different passes. They are recorded rather than smoothed over, and the ingest
reconciliation in Phase 1 must resolve each one.

1. **Payment rows: 34,002 measured, against 34,000 raw expenditure rows.** A
   surplus of two. Suspected to originate in the two shifted-column rows, but
   that is not confirmed. Ingest must reconcile loaded + rejected = 34,000
   exactly, and this line must be updated with the answer.
2. **MPs: 766 distinct, against 764 allocation rows.** The 766 counts MP names
   appearing on works; the 764 counts allocation-file rows. Different
   populations, so they need not be equal — but the difference must be explained.
3. **MP name to allocation matches 416/416, while MP account utilisation has
   n = 419.** Again different populations: matched-name MPs, against MPs holding
   both an allocation and at least one sanction. Both are recorded as measured.
4. **`sanctioned to recommended` is 99.7%, but the amount-degeneracy comparison
   ran over 14,831 works.** The smaller figure is the subset where both amount
   columns are non-null. Stated as measured; the exact null counts were not
   captured and must be on the next pass.
