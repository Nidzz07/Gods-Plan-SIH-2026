# Raw MPLADS data

Twelve CSV exports downloaded from the MPLADS portal operated by the Ministry
of Statistics and Programme Implementation (MoSPI).

**Source:** https://mplads.mospi.gov.in/digigov/dashboard.html
**Downloaded:** 26 August 2026
**Downloaded by:** Nidhi Dhyani
**Licence:** Government of India open data, published for public access.

These files are committed to the repository on purpose, so that a fresh clone
reproduces the same figures without re-downloading. Do not edit them by hand.
Everything derived from them lives in `data/interim/` and `data/processed/`,
which are generated and gitignored.

The authoritative profile of what these files contain is
`docs/data/DATA-PROFILE.md`. This README covers provenance only.

## Files

Each dataset is published separately for the two Houses of Parliament.
Row counts exclude the header.

| File | Rows | Size |
| --- | ---: | ---: |
| `Works_Recommended_lok_sabha.csv` | 35,000 | 10.8 MB |
| `Works_Recommended_rajya_sabha.csv` | 7,000 | 2.4 MB |
| `Works_Sanctioned_lok_sabha.csv` | 8,000 | 2.6 MB |
| `Works_Sanctioned_rajya_sabha.csv` | 19,078 | 7.1 MB |
| `Works_Completed_lok_sabha.csv` | 5,000 | 1.5 MB |
| `Works_Completed_rajya_sabha.csv` | 9,830 | 3.4 MB |
| `Expenditure_on_Completed_and_On-going_Works_as_on_Date_lok_sabha.csv` | 29,000 | 7.4 MB |
| `Expenditure_on_Completed_and_On-going_Works_as_on_Date_rajya_sabha.csv` | 5,000 | 1.4 MB |
| `Allocated_Limit_for_Honble_MPs_lok_sabha.csv` | 543 | 35 KB |
| `Allocated_Limit_for_Honble_MPs_rajya_sabha.csv` | 221 | 20 KB |
| `Amount_consented_for_Calamity_lok_sabha.csv` | 12 | 1.3 KB |
| `Amount_consented_for_Calamity_rajya_sabha.csv` | 20 | 2.5 KB |
| **Total** | **118,704** | **36.7 MB** |

## These are truncated exports, not the full portal

Several files stop at suspiciously round numbers — 35,000, 29,000, 8,000,
7,000, 5,000. The portal appears to cap an export at a fixed row limit. These
are therefore a large sample of MPLADS, not the complete national record.

Anything stated publicly about these numbers must be phrased as a finding on
the sample profiled, never as a national total.

## Format notes that the ingestion pipeline must handle

- **Encoding:** UTF-8 with a byte-order mark. Read with `encoding='utf-8-sig'`
  or the first column name arrives with a `\ufeff` prefix.
- **Line endings:** CRLF.
- **Quoting:** every field is quoted, including numerics.
- **Amounts:** plain integer strings in rupees. Column headers embed the rupee
  sign and irregular spacing, e.g. `RECOMMENDED AMOUNT   ( ₹ )` has three
  spaces before the bracket. Match headers loosely, not exactly.
- **Dates:** `%d-%b-%Y`, e.g. `08-Jul-2024`.
- **Work ID:** pattern `WS/MP{code}/{FY}/{serial}`. In Recommended, Sanctioned
  and Completed it is embedded at the start of the `Work` / `WORK` column and
  followed by a hyphen and the category text. In Expenditure it has its own
  `Work ID` column. Some Lok Sabha rows contain a literal tab inside the id
  (`WS/\t MP620/2024-2025/133166`) — strip all whitespace before comparing.

## Known defects in the source data

Recorded here so nobody "fixes" them by editing the CSVs.

- Two rows have shifted columns; a formatted amount string lands in the
  `Work Status` field (`40,79,58,27,851.08`, `16,78,67,73,690.87`).
- 50 rows have a null work description.
- 5.3% of `Works_Recommended_lok_sabha.csv` rows have an unparseable work ID.
- MP names carry inconsistent term suffixes: `(2022-28) (2022-2028)`, and in
  the Completed files sometimes `(NaN-NaN)`.
- Implementing-agency names contain typos that split one real agency into
  several distinct strings — `DISTRICT MAGISTRAE` appears alongside
  `DISTRICT MAGISTRATE`. Canonicalisation is required.
- The Rajya Sabha allocation file has no `Constituency` column; the Lok Sabha
  one does. Rajya Sabha members are seated by state, so this is correct, not a
  defect, but the loaders differ.

## Refreshing this data

1. Re-download all twelve files from the portal in one session, so the
   snapshot is internally consistent.
2. Replace the files in this directory.
3. Update the download date above.
4. Re-run `python -m ingest.run` and re-measure `docs/data/DATA-PROFILE.md`.
   The thresholds in `backend/app/rules.yaml` are calibrated against measured
   firing counts and must be re-checked against the new profile.
5. Commit the data and the regenerated profile together in one commit.