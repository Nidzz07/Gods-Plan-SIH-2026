# DATA-PROFILE — what the real MPLADS data actually contains

> ### Changelog — 29 August 2026, Phase 1
>
> **Every figure below was re-measured against a full ingestion run**
> (`python -m ingest.run`, all 118,704 rows loaded into `backend/nigrani.db`)
> and no longer against the sample probes Phase 0 used. Several figures moved.
> The corrections, old → new:
>
> | Figure | Was | Is | Why it moved |
> | --- | ---: | ---: | --- |
> | Payment rows | 34,002 | **34,000** | The two surplus rows were portal footers |
> | MPs | 766 | **764 on the roll, 701 named on works** | Same footers, plus two different populations |
> | Total allocated | Rs 23,242 crore | **Rs 11,621.06 crore** | The footer row was summed with the data, doubling it exactly |
> | Calamity consents | 34, Rs 29.01 crore | **32, Rs 14.51 crore** | Same doubling |
> | Calamity events | 7 | **6** | Counted with the footer |
> | Vendors | 15,245 | **14,743** | The footer plus case and spacing variants |
> | States | 32 | **36** | Under-counted |
> | Agencies | 638 | **757** | Under-counted |
> | MP name → allocation | 100% (416 / 416) | **100% (701 / 701)** | 416 was the utilisation population, not the name-match one |
> | Sanctioned → recommended | 99.7% | **54.77% (14,831 / 27,078)** | The old figure is unsupported by any measurement we can reproduce |
> | Sanction lag population | 14,831 | **27,078** | Both dates are published in the sanctioned export itself |
> | Duplicate clusters | 363 / 2,843 works / Rs 157.12 cr | **275 / 3,240 works / Rs 166.59 cr** | Re-measured after agency canonicalisation |
> | Vendor concentration pairs | 66 | **65** | Re-measured |
> | Vendors spanning >1 agency | 489 | **650**, max span **10** | Re-measured |
> | Sanction–disbursement disagreement (completed) | 1,318 of 12,974 | **1,329 of 12,953 published pairs**, 21 unpublished | The unpublished pairs were being counted as disagreements |
> | Column-shift defect | 2 rows | **0 rows; 12 "Grand Total" footers** | Reclassified, see section 9 |
> | Agency typo variants | 638 raw strings split one agency | **no split occurs on this corpus** | See section 9 |
>
> A single root cause explains five of these: **every export ends with a
> "Grand Total" footer row**, and Phase 0's probes counted it as data. That is
> also what the "two shifted-column rows" turned out to be.
>
> Three figures are **new** and were not measured before: the per-rule firing
> counts in section 6, the asset-evidence availability split, and the 163 works
> reported complete before their first payment.
>
> The three-way intersection (944 works), the execution-delay distribution, the
> utilisation distribution on that intersection, the 1,371-of-1,629 status
> finding, the 244-work largest cluster at Rs 3.98 crore and the whole of
> section 7 all **reproduced exactly**. Section 8 is unchanged.

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
The row counts a correct ingestion run must reproduce live in
`docs/data/INGEST-EXPECTATIONS.md`.

---

## 1. Files

Twelve files, each dataset published separately for the two Houses. Row counts
are **data rows**: they exclude the header and the portal's "Grand Total"
footer, one of which ends every file (section 9).

| Dataset | Lok Sabha | Rajya Sabha | Total |
| --- | ---: | ---: | ---: |
| `Works_Recommended` | 35,000 | 7,000 | 42,000 |
| `Works_Sanctioned` | 8,000 | 19,078 | 27,078 |
| `Works_Completed` | 5,000 | 9,830 | 14,830 |
| `Expenditure_on_Completed_and_On-going_Works_as_on_Date` | 29,000 | 5,000 | 34,000 |
| `Allocated_Limit_for_Honble_MPs` | 543 | 221 | 764 |
| `Amount_consented_for_Calamity` | 12 | 20 | 32 |
| **Total** | **77,555** | **41,149** | **118,704** |

Add the twelve footer rows and the reader sees 118,716 records.

Format facts the loader must honour: UTF-8 **with BOM** (`encoding='utf-8-sig'`),
CRLF line endings, every field quoted including numerics, amounts as plain
integer rupee strings, dates as `%d-%b-%Y`. Column headers embed the rupee sign
with irregular spacing (`RECOMMENDED AMOUNT   ( ₹ )`, three spaces before the
bracket) and must be matched loosely, never by exact string equality.

The `IDA` column carries two published facts in one string,
`DISTRICT(AGENCY NAME_IDA)`. The `_IDA` suffix is a portal artefact; a few rows
carry `_<digit>` instead.

---

## 2. Join key

The work id, pattern `WS/MP{code}/{FY}/{serial}`.

| Where it lives | Column | Form |
| --- | --- | --- |
| Works_Recommended | `WORK` | embedded at the start, followed by a hyphen and the category text |
| Works_Sanctioned | `Work` | same |
| Works_Completed | `Work` | same |
| Expenditure | `Work ID` | explicit, its own column |

Canonicalisation: strip **all** internal whitespace and tab characters before
comparing. Some Lok Sabha rows carry a literal tab inside the id
(`WS/<TAB> MP620/2024-2025/133166`).

The id cannot be recovered by splitting the cell on its first hyphen: the
financial year contains two of its own.

Parse success rate, measured on the ingestion run:

| File | Data rows | Work ids parsed |
| --- | ---: | ---: |
| Works_Recommended, Lok Sabha | 35,000 | 33,143 — **94.69%** |
| Works_Recommended, Rajya Sabha | 7,000 | 6,853 — **97.90%** |
| All other work-level files | 65,908 | **100.00%** |

The 2,004 unparseable rows read literally `NA-<category text>`: the portal
published a category with no work behind it. Every one is an `ingest_rejects`
row with reason `work_id_unparseable`.

---

## 3. Join yield

Measured over canonical work ids after ingestion.

| Join | Result |
| --- | ---: |
| sanctioned works with a recommendation row | **14,831 of 27,078 — 54.77%** |
| completed works with a sanction row | **12,974 of 14,830 — 87.48%** |
| works with expenditure and a sanction row | **3,529 of 22,471 — 15.70%** |
| recommended **and** sanctioned **and** expenditure | **944 works** |
| MP name to allocation (after name normalisation) | **100% (701 / 701)** |
| MPs holding an allocation **and** at least one sanction | **416** |

Three of those numbers are different populations and are routinely confused:
**701** members are named on a work or a payment row and every one of them
matches an allocation row; **764** members hold an allocation; **416** hold both
an allocation and at least one sanction, and that last is the population the
account-utilisation distribution in section 6 is measured over.

The 944-work three-way intersection is the population Phase 0 profiled for
sanction-to-disbursement. It is small because the expenditure export is
truncated, not because the works lack payments. **The population the
`utilisation_shortfall` rule actually reads is the 3,529 works that have both a
sanction and an expenditure row**, and both distributions are given in
section 6.

**The old 99.7% figure for sanctioned-to-recommended could not be reproduced
and is withdrawn.** 12,247 sanctioned works — 45% of them — have no row in the
recommended export at all, so `sanctions.recommended_amt` is `not_published`
for all of them and the degeneracy comparison in section 5 runs over the 14,831
that do.

---

## 4. Scale

| Quantity | Value |
| --- | ---: |
| Unique sanctioned works | 27,078 |
| Works of any kind (union of the four work-level exports) | 65,269 |
| Payment rows | **34,000** |
| Completion rows | 14,830 |
| MPs on the allocation roll | **764** |
| MPs named on a work or payment row | **701** |
| Implementing agencies | **757** |
| Vendors | **14,743** |
| States and union territories | **36** |
| Financial years covered | FY2023-24 to FY2026-27 |
| Sanction date range | 2023-07-07 to 2026-08-22 |
| Payment date range | 2025-02-14 to 2026-08-24 |
| Total allocated | **Rs 11,621.06 crore** |

`2026-08-24`, the maximum payment date, is the corpus **as-of date**. Every
"days since" feature is measured against it, never against `today`, so a
re-derivation months later reproduces the same number. It is defined once, as
`app.constants.DATA_AS_OF`, and imported (CLAUDE.md invariant 7).

`works` is the union of every work id in the four work-level exports, not only
the sanctioned ones. A recommendation that was never sanctioned carries its own
recommendation and sanction dates, and a payment row has to attach to
something. Cases are opened only for the 27,078 sanctioned works.

---

## 5. The degeneracy finding

**This is the single most important measurement in the project. It determines
what the rulebook can and cannot contain.**

| Comparison | Works matched | Works where the two amounts differ |
| --- | ---: | ---: |
| Recommended amount vs Sanctioned amount | 14,831 | **0** |
| Sanctioned amount vs the completed export's disbursed amount | 12,953 published pairs (of 12,974 joined) | 1,329 (11,624 identical, 21 not published) |

Recommended amount equals sanctioned amount in **14,831 of 14,831** matched
works. Zero variance. The portal does not publish revised estimates, so there is
no second cost figure to compare the first against.

**Cost overrun is NOT computable from public MPLADS data.** A `cost_overrun`
rule was designed, and then removed, on the strength of this measurement. See
`docs/domain/DOMAIN-MODEL.md` section (g) and the ablation module in section (i).

The consequence, stated plainly:

> **MPLADS public data is financially flat and temporally rich. The detectable
> signal lives in TIME and REPETITION, not in amount variance.**

Every rule in the rulebook follows from that sentence. Seven of the ten read a
date difference, a repetition count or a concentration share. Only one reads an
amount variance, and it reads the one variance that survives — sanctioned
against the sum of the expenditure rows.

---

## 6. Measured signal distributions

These are the distributions the thresholds are calibrated against. Each
threshold in `rules.yaml` carries a YAML comment naming its firing count drawn
from here.

### Sanction lag — recommendation to sanction

Both dates are published in the sanctioned export itself, so the population is
every sanctioned work, not only the 14,831 that also appear in the recommended
export.

| Statistic | All sanctioned works | Restricted to the 14,831 |
| --- | ---: | ---: |
| n | **27,078** | 14,831 |
| Median | **77 d** | 88 d |
| p75 | **142 d** | 150 d |
| p90 | **257 d** | 262 d |
| p95 | **336 d** | 364 d |
| Max | 1,058 d | 1,058 d |
| Works > 180 d | **4,800** | 2,868 |
| Works > 365 d | **1,025** | 739 |
| Negative lags | **0** | 0 |

The second column is what Phase 0 measured. The threshold of 180 d still sits
between p75 and p90 on the corrected distribution, so `sanction_delay` keeps its
threshold; only its firing count changes, from 2,868 to **4,800**.

### Execution delay — sanction to completion

| Statistic | Value |
| --- | ---: |
| n | 12,974 |
| Median | 169 d |
| p75 | 308 d |
| p90 | 444 d |
| Max | 948 d |
| Works > 365 d | 2,568 |
| Works > 730 d | 276 |
| Negative | 0 |

### The two payment-side lags

Phase 0 could not measure these. They are measured now.

| Lag | n | Median | p75 | p90 | Max | Negative |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `sanction_to_first_payment` | 3,529 | 134 d | 268 d | 382 d | 945 d | 0 |
| `first_payment_to_completion` | 1,066 | 0 d | 56 d | 113 d | 316 d | **163** |

**163 works are reported complete before their first payment is recorded**, the
earliest by 446 days. Neither source row is malformed — the completed export and
the expenditure export simply disagree — so this is not an ingest reject. It is
a derivation-layer decision Phase 2 must make explicitly, and a negative lag
must not be clamped to zero.

The identity
`sanction_to_first_payment + first_payment_to_completion = execution_days`
holds for **1,066 of 1,066** works where all three are computable.

### Utilisation — sanctioned to disbursed

| Statistic | Rule population (n = 3,529) | Three-way intersection (n = 944) |
| --- | ---: | ---: |
| Mean | **-16.60%** | -18.23% |
| Median | **-0.37%** | -0.19% |
| p5 | **-76.66%** | -83.98% |
| Min | **-99.62%** | -98.58% |
| Max | **0.00%** | 0.00% |
| Works below -15% | **1,140** | 288 |
| Over-disbursement (> 0%) | **0** | 0 |

The maximum is exactly zero on both populations. No work in the sample is
disbursed more than it was sanctioned, so the utilisation rule is one-sided by
measurement, not by choice.

### Payments per work

| Statistic | All works with a payment | Rule population (n = 3,529) | Three-way (n = 944) |
| --- | ---: | ---: | ---: |
| Works | 22,471 | 3,529 | 944 |
| Mean | 1.51 | 1.68 | 1.40 |
| Max | 49 | 41 | 27 |
| More than one payment | 4,238 | 647 | 115 |

Phase 0 recorded the first column's mean and max under the third column's
heading. Both figures were right; the label was not.

### Days since last payment — the stalled-work signal

Measured to `DATA_AS_OF = 2026-08-24`, over the 3,529 sanctioned works that have
a payment.

| Statistic | Value |
| --- | ---: |
| Median | 126 d |
| p75 | 201 d |
| p90 | 268 d |
| Max | 556 d |
| Works > 270 d | **345** |

This fills the standing TODO Phase 0 left against `stalled_work`. The threshold
of 270 d sits just above p90 (268 d) and selects 345 works.

### Duplicate descriptions within one agency

Exact match on the normalised description (lowercased, punctuation stripped,
whitespace collapsed), blocked by canonical agency.

| Quantity | Clusters of 2 or more | Clusters of 3 or more |
| --- | ---: | ---: |
| Clusters | 447 | **275** |
| Works inside a cluster | 3,584 | **3,240** |
| Sanctioned value inside clusters | Rs 199.44 crore | **Rs 166.59 crore** |

The 3-or-more column is the population `split_sanction` fires on.

Largest clusters:

| Works | Agency | District | Value |
| ---: | --- | --- | ---: |
| **244** | District Magistrate, Budaun | Budaun, UP | Rs 3.98 crore |
| 115 | District Magistrate, Jalaun | Jalaun, UP | Rs 2.79 crore |
| 108 | District Magistrate, Siddharth Nagar | Siddharthnagar, UP | Rs 0.22 crore |

A cluster is a candidate for review, never an accusation. Street lights repeat
across a constituency for entirely legitimate reasons.

**`duplicate_similarity` is not yet calibrated, and its threshold is wrong.**
Measured with `rapidfuzz.token_set_ratio` over normalised descriptions, blocked
by agency, the distribution over 26,897 sanctioned works is median **0.893**,
p75 0.969, p90 1.000. The rulebook's threshold of 0.85 therefore fires on
**16,491 works — 61% of the corpus** — because MPLADS descriptions share heavy
boilerplate and `token_set_ratio` ignores word order and duplication. Either the
threshold or the scorer has to change in Phase 7, and the choice must be
re-measured here before `duplicate_work` is trusted. The firing counts below
carry that caveat.

### Vendor concentration

Share is one vendor's receipts as a fraction of **all** payments made by that
agency, on any of its works. Restricting the denominator to sanctioned works
turns a 17% vendor into a 100% one and is wrong.

| Quantity | Value |
| --- | ---: |
| Median share for a work's own vendor | 5.11% |
| p90 | 30.64% |
| Agency-vendor pairs above 60% with agency total > Rs 50 lakh | **65** |
| Sanctioned works where the rule fires | **48** |
| Vendors appearing under more than one agency | **650** |
| Maximum agencies spanned by one vendor | **10** |

### MP account utilisation — sanctioned / allocated

The portal publishes **one cumulative allocation per member and no per-year
breakdown**, so this ratio is term-to-date, not per financial year. Population:
the 416 members holding both an allocation and at least one sanction.

| Statistic | Value |
| --- | ---: |
| p25 | 6.80% |
| Median | 19.77% |
| p75 | 44.75% |
| Max | 95.78% |
| Min | 0.18% |
| MPs below 25% | **243** |
| MPs above 100% | **0** |
| MPs with an allocation and no sanction at all | 347 |

The ceiling is hard in the data, so an account reading above 100% is a data
error to reject, not an over-spend to flag.

### Status against payment

1,371 of the 1,629 sanctioned works whose status is `Work Completed` have **no
payment row at all**.

> **Caveat, and it is a large one.** The expenditure export is truncated to
> 29,000 + 5,000 rows, and expenditure joins to only 3,529 sanctioned works. A
> missing payment row is therefore partly an artefact of the truncated export
> and not necessarily a real reporting failure. The `status_payment_mismatch`
> rule is calibrated with this caveat attached, and its trace row must carry the
> caveat text so an officer reads it at the same moment as the flag.
> Re-measure on a full download before quoting this figure to anyone.

### Asset evidence — and the availability split that governs it

**The `Image` column is published only in the completed export.** A sanctioned
work that has not been reported complete has no image field at all, and that is
`not_published`, not "no photograph was filed".

| Population | Image published | Image present | Image absent | Image not published |
| --- | ---: | ---: | ---: | ---: |
| All works (65,269) | 14,830 | 9,445 | 5,385 | 50,439 |
| Sanctioned works (27,078) | 12,974 | 8,481 | **4,493** | **14,104** |

`asset_evidence_missing` therefore fires on **4,493** works and is **skipped on
14,104** — 52% of the corpus, worth 10 points of coverage each. This fills the
second standing TODO Phase 0 left, and it is a material correction: treating an
absent `Image` column as "no photograph" would have fired the rule on a
reporting gap on more than half the corpus.

### Firing counts per rule

Measured by a Phase 1 reference pass that applies the ten rules of
`DOMAIN-MODEL.md` section (g) to all 27,078 sanctioned works with the null
semantics of section (f). **Phase 3's engine must reproduce this table; a
difference is a bug in one of the two, not a matter of taste.**

| Rule | Weight | Fired | Passed | Skipped |
| --- | ---: | ---: | ---: | ---: |
| `utilisation_shortfall` | 22 | 1,140 | 2,389 | 23,549 |
| `execution_delay` | 20 | 2,568 | 10,406 | 14,104 |
| `duplicate_work` | 18 | 16,491 † | 10,406 | 181 |
| `sanction_delay` | 16 | 4,800 | 22,278 | 0 |
| `stalled_work` | 16 | 345 | 3,184 | 23,549 |
| `vendor_concentration` | 12 | 48 | 3,344 | 23,686 |
| `status_payment_mismatch` | 12 | 1,371 | 25,707 | 0 |
| `split_sanction` | 10 | 3,240 | 23,709 | 129 |
| `asset_evidence_missing` | 10 | 4,493 | 8,481 | 14,104 |
| `account_underutilisation` | 8 | 6,371 | 20,707 | 0 |

† Not calibrated. See the `duplicate_similarity` note above.

Resulting bands, with the corroboration bonus applied: **37 HIGH · 1,006 MEDIUM
· 26,035 LOW**, and the bonus is awarded to 191 cases. Mean coverage is 58.5%;
1,011 works reach 100% coverage and the minimum is 25%.

That coverage figure is the honest headline of the whole corpus: **NIGRANI can
evaluate a little under three-fifths of its own rulebook on the average
published work**, and it says so on every case rather than scoring the rest as
passes.

---

## 7. Categorical vocabularies

Recorded in full so that an unseen value in a later download is detected as new
rather than silently bucketed. Ingest reports vocabulary drift; it does not
reject a work for carrying an unrecognised label.

### Work Status — 27,078 sanctioned works

| Value | Count |
| --- | ---: |
| Physical Inspection | 14,714 |
| Sanction | 4,366 |
| Vendor Identification | 3,910 |
| Work partially Completed | 2,353 |
| Work Completed | 1,629 |
| Time Estimation | 106 |

### Work category — 27,078 sanctioned works

| Value | Count |
| --- | ---: |
| Normal/Others | 26,469 |
| Repair and Renovation | 353 |
| Trust and Society | 246 |
| **Not published (`N/A`)** | **7** |
| Bar and Associations | 3 |

### Payment Status — 34,000 payment rows

| Value | Count |
| --- | ---: |
| Payment Success | 30,753 |
| Payment In-Progress | 3,247 |

### Image — 14,830 completed works

| Value | Count |
| --- | ---: |
| `Images` | 9,445 |
| `N/A` | 5,385 |

Binary presence only. **There is no geotag, no timestamp and no image URL.** The
column asserts that an image exists; it does not let anyone verify what it shows.

### Calamity

**32 consents, Rs 14.51 crore, across 6 named events** — 3 national and 3 state.

---

## 8. Fields absent entirely — the basis of the ablation module

Each row names a detection rule the field would unlock. **Every one of these
rules is currently NOT computable.** This table is the input to feature F9 and
to the reporting recommendation NIGRANI makes back to MoSPI. It is unchanged by
the Phase 1 re-measurement.

| Absent field | Rule it would unlock | Status |
| --- | --- | --- |
| Geo coordinates of the asset | `asset_colocation_conflict` — two works claiming the same physical location | **Not computable** |
| Revised cost estimate | `cost_overrun` — sanctioned against revised estimate | **Not computable** (designed, then removed; see section 5) |
| Utilisation certificate date | `certification_shortfall` — the second fund hop, disbursed against certified | **Not computable** |
| Milestone / progress percentage | `physical_financial_mismatch` — money released ahead of physical progress | **Not computable** |
| Tender / bid records | `single_bid_award`, `bid_rotation` — competition failure | **Not computable** |
| Beneficiary counts | `cost_per_beneficiary_outlier` | **Not computable** |
| Asset photo geotag or timestamp | `asset_photo_reuse` — one photograph filed against several works | **Not computable** |

`backend/nigrani.db` records the first of these directly: the `certifications`
table holds **one row**, and it is the labelled synthetic control. Every real
work in the corpus has no utilisation certificate, because MoSPI publishes none.

A per-financial-year allocation belongs on this list too. The portal publishes
one cumulative allocation per member, so `fund_accounts.allocated_amt` is
`not_published` on every per-FY row and `mp_utilisation_pct` is computable only
term-to-date.

The `asset_evidence_missing` rule that *does* ship reads only the binary `Image`
presence flag, and only for works that have been reported complete. It can say a
photograph was never filed on 4,493 works. It can say nothing at all about
14,104 others, and nothing about a photograph that was filed.

---

## 9. Data quality defects

Recorded so that nobody "fixes" them by editing the CSVs. Every one is handled
in ingest, and every rejected row lands in `ingest_rejects` with a reason
(CLAUDE.md invariant 11).

| Defect | Extent | Handling |
| --- | ---: | --- |
| **"Grand Total" footer row** — one at the end of every export, carrying an aggregate in one column and blanks elsewhere | **12 rows** | Reject, reason `grand_total_row` |
| Unparseable work id — the cell reads `NA-<category>` | 1,857 rows in Works_Recommended LS, 147 in RS | Reject, reason `work_id_unparseable` |
| Null work description (`N/A`) | 50 of 27,078 sanctioned works | Load the row; `duplicate_similarity` and `same_desc_same_agency_count` become `None`, so those rules are **skipped**, never passed |
| Null work category (`N/A`) | 7 rows | Load the row; `category` is null |
| Literal tab inside the work id (`WS/<TAB> MP620/...`) | scattered | Canonicalise: strip all whitespace before comparing. The published spelling is kept in `works.work_id_raw` |
| MP name term suffixes — `(2022-28) (2022-2028)`, `(NaN-NaN)` | widespread | Normalise before the name-to-allocation join (yields 701 / 701) |
| The `State` column disagrees with the `IDA` column | 70 of 757 agencies | The office is keyed by (district, name); its state is the majority of the referencing rows. `AGRA(DISTRICT MAGISTRAE AGRA_IDA)` is filed under five different states |
| Works reported complete before their first payment | 163 | Not an ingest defect; a derivation-layer decision. Never clamp to zero |
| Rajya Sabha allocation file has no `Constituency` column | whole file | **Not a defect.** Rajya Sabha members are seated by state; `constituency_id` is nullable and the two loaders differ |
| Original filenames used spaces, not underscores | all 12 | Renamed on disk to match the documented convention |

Two entries from the Phase 0 profile are **withdrawn**:

- **"Shifted columns — a formatted amount lands in `Work Status`, 2 rows."**
  Those two rows are the "Grand Total" footers of the two Works_Sanctioned
  files. There is no column-shift defect in the data. The `column_shift` reject
  reason is retained in the enum and is emitted zero times.

- **"Agency typo variants split one real agency, 638 raw strings."** They do
  not, on this corpus. The portal publishes exactly **one** `IDA` string per
  district office: 757 offices across 754 districts, only 3 districts carrying
  more than one office, and no pair inside a district scoring above 70 on
  `token_sort_ratio`. `DISTRICT MAGISTRAE` is a consistent portal-wide
  misspelling of the title, used for many districts, and never appears beside
  `DISTRICT MAGISTRATE` for the same district. **Canonicalisation folded nothing
  and the load report says so.** The rapidfuzz step and the
  `agency_name_variants` ledger are kept, because a later download may split a
  name and because every raw string is recorded either way — but no claim may
  be made on stage that NIGRANI merged agency typos on this data.

---

## 10. Internal consistency — resolved

The four items Phase 0 recorded here are now answered. Three of the four have
the same cause.

1. **Payment rows: 34,002 measured against 34,000 raw rows. RESOLVED.** The two
   surplus rows are the "Grand Total" footers of the two Expenditure exports.
   The corpus holds **34,000** payment rows and ingestion reconciles exactly.

2. **MPs: 766 distinct against 764 allocation rows. RESOLVED, twice over.** The
   766 counted the two allocation footers. It is also two different populations:
   **764** members hold an allocation, **701** are named on a work or payment
   row, and all 701 match. Neither number is 766.

3. **MP name to allocation 416/416 against a utilisation n = 419. RESOLVED.**
   416 was never a name-match figure. The name match is **701 of 701**. The
   utilisation population — members holding both an allocation and at least one
   sanction — is **416**, and its distribution is in section 6. The 419 is not
   reproducible and is withdrawn.

4. **`sanctioned to recommended` 99.7% against 14,831 works in the degeneracy
   comparison. RESOLVED, and the 99.7% was wrong.** The join yield is
   **54.77%**, exactly the 14,831 of 27,078 the degeneracy comparison used. The
   two figures were never in tension; one of them was simply not a measurement.

Two further doublings, not flagged in Phase 0 but caused by the same footers,
are corrected in the changelog at the top of this file: total allocated
(Rs 23,242 crore → **Rs 11,621.06 crore**) and calamity consents (34 and
Rs 29.01 crore → **32 and Rs 14.51 crore**).

### Phase 2 derivation decisions — settled and recorded

The two items Phase 1 left open for the derivation layer are decided. Both are
implemented in `backend/app/engine/derive.py` and both are asserted by tests, so
this section is the record the code's docstrings point at rather than a plan.

**1. The fund ladder's disbursed rung reads the PAYMENTS ROLLUP, not
`completions.completed_amt`.** Measured over the sanctioned population:

| Quantity | Value |
| --- | ---: |
| Sanctioned works with a published `completed_amt` | **12,953** |
| — of which also have at least one published payment row | 1,066 |
| — — of those, the two figures disagree | **178** |
| — of which have **no payment row at all** | **11,887** |

**Not to be confused with the 1,329 in the changelog above.** That figure
compares the completed export's amount against the **sanctioned** amount and
counts 1,329 of the same 12,953 published pairs. The table here compares it
against the **payments rollup**, which is a different question with a different
population — only 1,066 of the 12,953 have a payment row to compare against at
all. Both are correct; they measure different disagreements.

The last row is the whole of the decision. Reading `completed_amt` would make
`variance_sanction_to_disbursement` computable on 11,887 further works and lift
`utilisation_shortfall` out of `skipped` on all of them — but it would do so
from a single total that names no vendor, no date and no payment status, so an
officer who doubted the resulting flag would have nothing to open. A payment row
can be walked; a completion total can only be believed. Where both readings
exist they disagree on 178 of 1,066, which is enough to show they are not
interchangeable and not enough to prefer the unattributable one.

The consequence is deliberate and visible on fixture B, which publishes a
`completed_amt` of Rs 9,96,458 and has no payment row: its
`variance_sanction_to_disbursement` is `not_published` rather than computed from
a number nobody can trace, and `utilisation_shortfall` is skipped, not passed.
Both columns remain stored, so the alternative reading is still available to a
later pass — it was unselected, not discarded.

**2. The 163 works completed before their first recorded payment keep a signed
`first_payment_to_completion`, never clamped and never dropped.** The earliest
is negative by 446 days. Neither source row is malformed — the completed export
and the expenditure export simply disagree — so this is not an `ingest_rejects`
case, and clamping to zero would erase the disagreement instead of showing it.
The negative value travels into the lifecycle ladder where an officer can see
it. Two consequences follow and are intended: `slowest_lag` can never select a
negative lag over a positive one, and `execution_days` is unaffected, because it
is computed directly from the sanction and completion dates rather than as the
sum of the two payment-side lags (`DOMAIN-MODEL.md` §c).

### Open, for the next measurement pass

- **`duplicate_similarity` is uncalibrated.** Threshold 0.85 on
  `token_set_ratio` fires on 61% of the corpus. Phase 7 must choose a scorer and
  a threshold together and record the resulting distribution here before
  `duplicate_work` contributes its 18 points to anything shown to an officer.
