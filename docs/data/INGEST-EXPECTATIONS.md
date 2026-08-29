# INGEST-EXPECTATIONS — what a correct `python -m ingest.run` must print

This is the reference a future ingestion run is checked against **by eye**. If a
run does not reproduce the numbers below, either the data changed or the
ingestion changed, and the difference must be explained before anything
downstream is trusted. `docs/data/DATA-PROFILE.md` is the authority on what the
data *contains*; this file is the authority on what loading it *produces*.

## What this was measured against

| | |
| --- | --- |
| Measured on | 29 August 2026 |
| Repository commit | `aaa8726` |
| `backend/ingest/run.py` blob | `7a423cb`, last changed by `96e2127` |
| Corpus | the twelve exports in `data/raw/`, downloaded 26 August 2026 |
| Command | `cd backend && python -m ingest.run` |
| Exit code | `0` |

The run was executed twice in succession and produced identical output apart
from its own timestamp line. Ingestion is idempotent by rebuild: it drops and
recreates every table, so a second run does not double the data.

**These expectations are void after a fresh download.** Re-download, re-run,
re-measure `DATA-PROFILE.md`, and regenerate this file in the same commit as the
data (CLAUDE.md git conventions).

## How to read the per-file row count

**The `rows` column counts data rows plus the portal's `Grand Total` footer. It
never counts the header.** The header line is consumed by `pandas.read_csv` as
column names and never becomes a row, so it can be neither loaded nor rejected
and cannot appear on either side of the reconciliation.

Worked for the largest file:

```
Works_Recommended_lok_sabha.csv
  35,000  data rows          <- the figure DATA-PROFILE.md section 1 records
     + 1  "Grand Total" footer row, rejected with reason grand_total_row
  ------
  35,001  rows, as printed in the `rows` column
     + 1  header line, consumed as column names, never counted
  ------
  35,002  physical lines in the file
```

So `118,716` in the TOTAL row is `118,704` data rows plus `12` footers, one per
export. `data/raw/README.md` and `DATA-PROFILE.md` both quote `118,704` because
they describe the data; this file quotes `118,716` because it describes the read.

## Per file

`loaded + rejected == rows` for all twelve files, asserted by the run itself
(CLAUDE.md invariant 11). A `NO` in the `ok` column makes `main()` return 1.

| File | rows | loaded | rejected | ok |
| --- | ---: | ---: | ---: | :-: |
| `Works_Recommended_lok_sabha.csv` | 35,001 | 33,143 | 1,858 | yes |
| `Works_Recommended_rajya_sabha.csv` | 7,001 | 6,853 | 148 | yes |
| `Works_Sanctioned_lok_sabha.csv` | 8,001 | 8,000 | 1 | yes |
| `Works_Sanctioned_rajya_sabha.csv` | 19,079 | 19,078 | 1 | yes |
| `Works_Completed_lok_sabha.csv` | 5,001 | 5,000 | 1 | yes |
| `Works_Completed_rajya_sabha.csv` | 9,831 | 9,830 | 1 | yes |
| `Expenditure_on_Completed_and_On-going_Works_as_on_Date_lok_sabha.csv` | 29,001 | 29,000 | 1 | yes |
| `Expenditure_on_Completed_and_On-going_Works_as_on_Date_rajya_sabha.csv` | 5,001 | 5,000 | 1 | yes |
| `Allocated_Limit_for_Honble_MPs_lok_sabha.csv` | 544 | 543 | 1 | yes |
| `Allocated_Limit_for_Honble_MPs_rajya_sabha.csv` | 222 | 221 | 1 | yes |
| `Amount_consented_for_Calamity_lok_sabha.csv` | 13 | 12 | 1 | yes |
| `Amount_consented_for_Calamity_rajya_sabha.csv` | 21 | 20 | 1 | yes |
| **TOTAL** | **118,716** | **116,700** | **2,016** | **yes** |

## Rejects by reason

| Reason | Count | Where |
| --- | ---: | --- |
| `work_id_unparseable` | 2,004 | 1,857 in Works_Recommended LS, 147 in RS. The cell reads `NA-<category text>`: a category published with no work behind it. |
| `grand_total_row` | 12 | One footer at the end of every export. |
| **TOTAL** | **2,016** | |

`RejectReason` declares eleven members. Two are emitted above; the other **nine**
are emitted **zero** times on this corpus:
`unparseable_amount`, `unparseable_date`, `null_required_field`,
`duplicate_work_id`, `case_id_collision`, `unresolved_reference`, `column_shift`,
`negative_lag`, `unknown_category`. They are retained deliberately —
`column_shift` and `negative_lag` in particular, because a run that starts
emitting them has found something the profile says is not there.

**A non-zero count against any of those nine is a finding, not a failure.**
Investigate it and record it in `DATA-PROFILE.md` section 9 before changing any
ingestion code.

## Table counts

`syn` counts the labelled synthetic-control rows of fixture C, which are excluded
from every published aggregate (CLAUDE.md invariant 12).

| Table | Rows | of which synthetic |
| --- | ---: | ---: |
| `states` | 36 | — |
| `constituencies` | 542 | — |
| `mps` | 765 | 1 |
| `agencies` | 758 | 1 |
| `agency_name_variants` | 757 | — |
| `vendors` | 14,744 | 1 |
| `works` | 65,270 | 1 |
| `sanctions` | 27,079 | — † |
| `payments` | 34,004 | 4 |
| `completions` | 14,831 | 1 |
| `certifications` | 1 | 1 |
| `calamity_consents` | 32 | — |
| `fund_accounts` | 2,416 | — |
| `ingest_rejects` | 2,016 | — |

Subtract the synthetic rows and every count is the figure `DATA-PROFILE.md`
section 4 records: 65,269 works, 27,078 sanctioned works, 34,000 payment rows,
14,830 completions, 764 members, 757 agencies, 14,743 vendors, 36 states.

**† `sanctions` prints no synthetic count, and the reason is a real asymmetry in
the model.** The count of 27,079 *is* 27,078 real rows plus the synthetic
control's sanction row, but `sanctions` is the only one of the control's child
tables with no `is_synthetic` column of its own — `payments`, `completions` and
`certifications` all have one — so `count_tables` cannot report it and prints a
dash. The row is still reachable and still excludable:

```sql
SELECT count(*) FROM sanctions s JOIN works w ON w.id = s.work_id
WHERE w.is_synthetic = 1;   -- returns 1
```

Invariant 12 is satisfied through that join, not through a column. Whether
`sanctions` should carry the flag directly, like its siblings, is a models.py
decision that has not been taken; it is recorded here so it is not discovered by
someone writing an aggregate that forgets the join.

**`certifications` holds exactly one row and that row is synthetic.** MoSPI
publishes no utilisation certificate for any real work, so a real row in this
table would mean the portal started publishing a field it has never published —
which is the outcome the ablation module asks for, and would be very good news.

## Join yields

| Join | Expected |
| --- | --- |
| sanctioned works with a recommendation row | 14,831 of 27,078 — **54.77%** |
| completed works with a sanction row | 12,974 of 14,830 — **87.48%** |
| works with expenditure and a sanction row | 3,529 of 22,471 — **15.70%** |
| recommended **and** sanctioned **and** expenditure | **944** |
| members named on works matched to an allocation row | 701 of 701 — **100.00%** |
| members holding an allocation | **764** |
| members holding an allocation and at least one work | **701** |

Three of these are different populations and are routinely confused. **701**
members are named on a work or payment row and every one matches an allocation
after name normalisation; **764** hold an allocation; **416** hold both an
allocation and at least one *sanction*, and 416 — not 701 — is the population
`DATA-PROFILE.md` section 6 measures account utilisation over. The report's last
line counts works, not sanctions, which is why it prints 701.

## Canonicalisation

| | Expected |
| --- | ---: |
| raw agency strings seen | 757 |
| canonical agencies | 757 |
| folded by a fuzzy merge | **0** |

**Zero fuzzy merges is the correct result on this corpus, not a broken
canonicaliser.** The portal publishes exactly one `IDA` string per district
office. `DISTRICT MAGISTRAE` is a consistent portal-wide misspelling of the
title, used for many districts, and never appears beside `DISTRICT MAGISTRATE`
for the same district (`DATA-PROFILE.md` section 9). The rapidfuzz step and the
`agency_name_variants` ledger are kept because a later download may split a name,
and because every raw string is recorded either way.

**No claim may be made on stage that NIGRANI merged agency typos on this data.**
It did not, and the load report says so in as many words.

A non-zero merge count on a future download is expected and fine — but each merge
must then be inspectable in `agency_name_variants` with its score, and a merge an
officer disputes is a UI-visible decision, never a silent one.

## Vocabulary drift

Expected: **none**. Every `Work Status` and `Work category` value in the corpus
appears in `DATA-PROFILE.md` section 7.

Drift is reported, never rejected. A work carrying an unrecognised label is still
loaded, because dropping a real work over a label would lose evidence. If the
report prints a drift line, add the value to the profile and to
`app/constants.py`.

## Synthetic control

| | Expected |
| --- | --- |
| work id | `WS/MP503/2025-2026/140882` |
| case id | `NG-622268C00E` |
| inserted | yes |

The id is reserved (`docs/contract/fixtures.md` caveat 6). If the portal ever
publishes it, the real work wins, the control is not inserted, and a row is
written to `ingest_rejects` with reason `case_id_collision`. `inserted: NO` is
therefore a legitimate outcome after a fresh download and must be read as a
collision, not a bug.

## Reconciliation line

```
RECONCILIATION: all twelve files reconcile.
```

Anything else means `loaded + rejected != rows` for at least one file, `main()`
returns 1, and no downstream figure may be quoted until it is resolved.
