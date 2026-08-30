# FIXTURES — three worked cases

Three cases, worked end to end with the arithmetic shown. Every engine function
gets its pytest assertion written against this file **before** the
implementation (CLAUDE.md working rules).

Fixture A is the case reproduced in full in `docs/contract/case_detail.json`.
Every number in that file appears here with its derivation.

---

## Standing caveats — read before using these fixtures

**1. The work ids are PINNED to real rows.** Phase 0 wrote A and B against
constructed ids that matched the documented shape of real rows but had never
been checked against `data/raw/`. Phase 1 loaded the corpus and confirmed that
neither provisional id existed: `WS/MP410/2024-2025/118427` and
`WS/MP128/2023-2024/094311` return no row. Both fixtures were re-pinned to real
sanctioned works, and every raw input and derived value below was re-measured
from the loaded corpus rather than carried over. Fixture C is synthetic by
design and is exempt.

| Fixture | Was (provisional, not a real row) | Is (real, in `data/raw/`) |
| --- | --- | --- |
| A | `WS/MP410/2024-2025/118427` | `WS/MP847/2025-2026/160261` |
| B | `WS/MP128/2023-2024/094311` | `WS/MP163/2024-2025/136111` |
| C | `WS/MP503/2025-2026/140882` | unchanged — synthetic, labelled |

**2. The values below are a CONTRACT, not engine output.** `backend/app/engine/`
does not exist yet; it is Phase 3. Every derived value and every rule status in
this file was produced by a Phase 1 reference pass that applies the
`DOMAIN-MODEL.md` §(f) feature definitions and §(g) rulebook verbatim to the
loaded corpus. That pass reproduces `DATA-PROFILE.md` §6's firing-count table
exactly — all ten rules, the 37 / 1,006 / 26,035 severity bands, the 191
corroboration awards, and the 58.5% mean coverage — which is what licenses it to
stand in for the engine here.

**Phase 3's `engine/derive.py` and `engine/score.py` must reproduce every number
below; a difference is a bug in one of the two, not a matter of taste.** This is
the same standing that `DATA-PROFILE.md` §6's firing-count table already has, and
for the same reason: a fixture the engine cannot reproduce is not a test, it is a
wish.

**3. Fixture A cannot have exactly one skipped rule, and the requirement table
below was corrected rather than forced.** Phase 0 specified A with a single
skipped rule and 86% coverage. That state does not exist anywhere in the corpus,
and it cannot: `execution_delay` reads `execution_days` and
`asset_evidence_missing` reads `asset_image_absent`, and **both hang off the
completion row**. The portal publishes the `Image` column only in the completed
export, so a work with no completion row has neither field. Measured over all
27,078 cases:

| | count |
| --- | ---: |
| both skipped together | 14,104 |
| `execution_delay` skipped, `asset_evidence_missing` evaluated | **0** |
| `asset_evidence_missing` skipped, `execution_delay` evaluated | **0** |

They never skip independently. A's coverage is therefore **79%**, not 86%, and
its skipped weight is 30, not 20. The requirement table records two skips.

This is a better fixture than the one it replaces, not a worse one. Phase 0's A
skipped one rule for `not_applicable` — the work had not reached the stage the
rule reads — which is not a reporting gap at all. The real A skips one rule for
`not_applicable` **and** one for `not_published`, so it exercises both skip
reasons on a single case, which is precisely the distinction CLAUDE.md invariant
2 exists to protect.

**4. Two properties of B changed because they were never requirements.** B's
required profile — reported complete with no payment, a Rajya Sabha member with
no constituency, three rules skipped from unpublished fields, MEDIUM band,
corroboration not applied — is satisfied by 74 real works, and all 74 land on
exactly 65% coverage skipping exactly the documented three rules. Two
*incidental* values from Phase 0 did not survive:

- **`duplicate_work` fires on B instead of passing.** It fires on all 74
  candidates. This is not a property of B; it is the uncalibrated
  `duplicate_similarity` threshold that `DATA-PROFILE.md` §6 already flags as
  firing on 61% of the corpus. When Phase 7 recalibrates the scorer, B's score
  will move, and that is the point of recording it here.
- **`account_underutilisation` passes on B instead of firing.** Only 4 of the 74
  candidates have a member below 25% utilisation, and none of those 4 also
  matched the rest of B's shape.

B's score is therefore **60**, not 50. B still lands in MEDIUM, still carries
exactly three `not_published` skips, and still fails to earn the corroboration
bonus, which is everything it was built to exercise.

**5. The arithmetic is correct and follows the method.** The derived values
follow from the raw inputs by `DOMAIN-MODEL.md` §(f), and the scores follow from
the derived values by §(g). Substituting a real row changed the inputs, and
therefore the outputs — it did not change the method, and the tests written
against the method survive the substitution.

**6. Fixture C's work id is reserved.** `WS/MP503/2025-2026/140882` must not
collide with a real portal id. Ingest checks this on every run and rejects with
reason `case_id_collision` if it ever does. On the current corpus it does not
collide, and the control is inserted.

**7. No weight and no threshold was altered to reach any score below.** The
weights are those in `DOMAIN-MODEL.md` §(g), fixed from measured firing counts
before any of these three rows was selected. The three scores — 92, 60, 20 — are
whatever the arithmetic produced on the rows that matched each profile.

**A's score of 92 is the same number Phase 0's constructed fixture carried, and
that is a coincidence, not a target.** The real row fires a different set of
rules from the constructed one — `asset_evidence_missing` is skipped where the
constructed row passed it — and arrives at the same rule subtotal of 82 by a
different route. Nothing was tuned to land there, and if the row had scored 78 it
would say 78.

**8. No claim is made that these combinations are unique or unreachable by other
works.** 36 real works match A's relaxed profile and 74 match B's; the
duplicate cluster A sits in has 15 members, all of which score identically. Many
works in the corpus produce the same rule combinations and the same score. These
three are chosen because between them they exercise every branch the engine has,
not because they are rare.

**9. Fixture C scores 20, not the 42 this file carried through Phase 1, and the
correction is to this file rather than to the control.** Four of C's stated
inputs were never properties of the work. `vendor_share_in_agency_pct`,
`duplicate_similarity`, `same_desc_same_agency_count`, `mp_utilisation_pct` and
the count of corroborating HIGH cases are all properties of the **corpus around**
a work — its agency's other works, its agency's other vendors, its member's
allocation, its agency's other HIGH cases — and the labelled control
`backend/ingest/synthetic.py` inserts is a single work under a single synthetic
agency with a single synthetic member. It has no corpus around it, so those five
readings are `not_applicable` or `not_published`, and the tables below now say
so.

**Why that is correct rather than a defect.** C exists for exactly three things
that no real MPLADS row can do: it populates the certification rung, so fund
hop 2 has a derivation that has actually run (invariant 3); it is the only
fixture whose `slowest_lag` is the third stage, `first_payment_to_completion`;
and it is the only one where all three lags are computable, so the identity
`42 + 439 = 481` can be asserted. **All three are derived from the real ingested
row and are unaffected by this correction.** Reaching 42 instead would mean
giving the control sibling works to be similar to, a second vendor to be
concentrated against, an allocation row to be a fraction of, and three HIGH peer
cases to be corroborated by — inventing a corpus for the sole purpose of landing
a target score. Caveat 7 above forbids exactly that, and the reason it forbids it
is that a fixture engineered to produce a number stops being evidence about the
engine and becomes evidence about the fixture. C's honest score is 20, LOW, on
74% coverage, and its three skips are themselves a finding: a work with no peers
is a work three of the ten rules cannot say anything about.

---

## Case ids

Derived, not assigned. `case_id = "NG-" + sha256(canonical_work_id)[:10].upper()`
where the canonical id is the raw id uppercased with all whitespace removed
(CLAUDE.md invariant 8). These are reproducible from a shell:

```
python -c "import hashlib;print('NG-'+hashlib.sha256(b'WS/MP847/2025-2026/160261').hexdigest()[:10].upper())"
```

| Fixture | Work id | Case id |
| --- | --- | --- |
| A | `WS/MP847/2025-2026/160261` | `NG-8F0E3213D8` |
| B | `WS/MP163/2024-2025/136111` | `NG-736D95571D` |
| C | `WS/MP503/2025-2026/140882` | `NG-622268C00E` |

---

## What the three exercise between them

| Requirement | A | B | C |
| --- | :-: | :-: | :-: |
| Fund hop 1 (`sanction_to_disbursement`) open | **yes** | unavailable | closed |
| Fund hop 2 (`disbursement_to_certification`) open | unavailable | unavailable | **yes** |
| `slowest_lag` = `recommend_to_sanction` | **yes** | yes | no |
| `slowest_lag` = `first_payment_to_completion` | no | no | **yes** |
| Rule skipped, reason `not_applicable` | **1** | 0 | **2** |
| Rule skipped, reason `not_published` | **1** | **3** | 1 |
| Corroboration bonus applied | **yes** | **no** | no |
| Duplicate citation present | **yes** | yes | no |
| `is_synthetic` | false | false | **true** |
| Coverage below 100% | 79% | **65%** | 74% |
| Severity band | HIGH | MEDIUM | LOW |

**`published_zero` is not exercised by these three fixtures.** All of the missing
values below are `not_published` or `not_applicable`. The third availability
state — a field the portal supplied with the value zero, which is a fact about
the work rather than a reporting gap — is covered by a unit test,
`tests/test_derive.py::test_zero_payment_is_published_zero_not_missing`, rather
than by a fixture. Building a fourth fixture solely to carry one enum value would
add a case an officer would never see. The distinction itself is not optional:
CLAUDE.md invariant 2 requires it end to end, and the test enforces it.

**Both A and B are Rajya Sabha members, and that is a consequence of the corpus,
not a choice.** A's requirement table demands the corroboration bonus, which
needs three or more HIGH cases under one agency in one financial year. Only 3 of
the 37 HIGH cases in the corpus sit with a Lok Sabha member, and none of those 3
has a corroborating peer. The Lok Sabha path — a member with a constituency — is
exercised by C and by `tests/test_ingest.py`, and the loader difference the two
Houses require is exercised directly by B, which is a Rajya Sabha member with
`constituency_id` null.

---

## Raw inputs

As they arrive from ingest, before any derivation. Amounts are whole rupees.
`—` means the source supplied no value.

| Field | A | B | C |
| --- | --- | --- | --- |
| `work_id_raw` | `WS/MP847/2025-2026/160261` | `WS/MP163/2024-2025/136111` | `WS/MP503/2025-2026/140882` |
| `description` | Led Semi High Mast Light (6LED) with 200-watt, 9.5-meter pole | Providing Bituminous Macadam road from Dwarka Palace to Principal street in  Karruppayurani Village, Madurai District. | construction of community hall at ward no 7 |
| `category` | Normal/Others | Normal/Others | Normal/Others |
| `status` | Work partially Completed | Work Completed | Work Completed |
| `state` / `district` | Uttar Pradesh / JALAUN | Tamil Nadu / MADURAI | Maharashtra / NASHIK |
| `agency` (canonical) | DISTRICT MAGISTRATE JALAUN | DISTRICT COLLECTOR MADURAI | SYNTHETIC CONTROL AGENCY, NASHIK (fixture C) |
| `agency` (raw) | `DISTRICT MAGISTRATE JALAUN` | `DISTRICT COLLECTOR MADURAI` | *(synthetic)* |
| MP (raw) | `Shri Baburam Nishad (2022-28) (2022-2028)` | `Shri R. Girirajan (2022-28) (2022-2028)` | *(synthetic)* |
| MP house | **rajya_sabha** | **rajya_sabha** | lok_sabha |
| MP constituency | **— (Rajya Sabha, seated by state)** | **— (Rajya Sabha, seated by state)** | Nashik |
| `recommended_amt` | **— (no recommendation row)** | 1,000,000 | 4,000,000 |
| `sanctioned_amt` | 199,539 | 1,000,000 | 4,000,000 |
| `disbursed_amt` | 119,711 | **— (no expenditure row)** | 3,880,000 |
| `completed_amt` | **— (not completed)** | 996,458 | 3,880,000 |
| `certified_amt` | **— (never published)** | **— (never published)** | 2,910,000 *(synthetic)* |
| `recommended_date` | 2024-12-19 | 2024-08-17 | 2025-01-14 |
| `sanction_date` | 2025-11-17 | 2024-11-21 | 2025-04-08 |
| `first_payment_date` | 2025-11-26 | — | 2025-05-20 |
| `last_payment_date` | 2025-11-26 | — | 2026-02-11 |
| `completion_date` | **— (not completed)** | 2026-05-14 | 2026-08-02 |
| `payment_count` | 1 | 0 | 4 |
| `Image` column | **— (not published)** | `N/A` | `Images` |
| vendor share in agency | 17.35% | — | **— (agency total Rs 38.80 lakh, below the Rs 50 lakh floor)** |
| same description under agency | 15 | 1 | **1 (the control is the agency's only work)** |
| best similarity in agency | 1.000 | 0.900 | **— (no second work to compare against)** |
| MP account, term to date | 73.80% utilised | 71.37% utilised | **— (synthetic member holds no allocation row)** |
| agency HIGH cases, this FY | 25 | 0 | **0 (the agency's only case is C itself)** |
| `is_synthetic` | false | false | **true** |

`DATA_AS_OF = 2026-08-24` for all three — the maximum payment date in the corpus
(`docs/data/DATA-PROFILE.md` §4). Never `today`.

**C's last five rows are all the same fact.** Each is a property of the corpus
around a work rather than of the work, and the control has no corpus around it:
one work, one agency, one member, one vendor. See standing caveat 9. The rungs,
dates and amounts above it are real values on a real inserted row and are what
C exists to exercise.

**A's `recommended_amt` is `not_published` while its `recommended_date` is
published.** That is not a contradiction, and it is worth stating because it
looks like one. The recommendation *date* is carried in the sanctioned export
itself, on every sanctioned row; the recommendation *amount* lives only in the
recommended export, which joins to 14,831 of 27,078 sanctioned works. A is one of
the 12,247 that has no recommendation row, so `sanction_lag_days` is computable
while `recommended_amt` is not. This is the majority case in the corpus and the
provisional fixture never exercised it.

**Note on `recommended_amt` = `sanctioned_amt` on B and C.** Where both are
published they are equal, which is the degeneracy finding (profile §5):
recommended equals sanctioned in 14,831 of 14,831 matched works. A fixture where
the two differed would be unrepresentative of the corpus and would quietly
reintroduce the `cost_overrun` rule the data proved uncomputable.

**B publishes a `completed_amt` of 996,458 and has no payment row at all.** The
fund ladder's disbursed rung reads the payments rollup, per `DOMAIN-MODEL.md`
§(f), so `variance_sanction_to_disbursement` is `not_published` on B even though
the completed export supplies an amount. Which of the two sources the disbursed
rung should read is the open question `DATA-PROFILE.md` §10 records for Phase 2.
B is the case that makes that question concrete, and whichever way Phase 2 decides
it, this fixture must be re-derived and the decision recorded in the profile.

---

## Derived values

By the definitions in `DOMAIN-MODEL.md` §(f). Arithmetic shown for every
non-trivial value.

| Feature | A | B | C |
| --- | --- | --- | --- |
| `variance_sanction_to_disbursement` | `(119711−199539)/199539×100` = **−40.01%** | **None** · `not_published` | `(3880000−4000000)/4000000×100` = **−3.00%** |
| `variance_disbursement_to_certification` | **None** · `not_published` | **None** · `not_published` | `(2910000−3880000)/3880000×100` = **−25.00%** |
| `sanction_lag_days` | `2024-12-19 → 2025-11-17` = **333** | `2024-08-17 → 2024-11-21` = **96** | `2025-01-14 → 2025-04-08` = **84** |
| `sanction_to_first_payment_days` | `2025-11-17 → 2025-11-26` = **9** | **None** · `not_applicable` | `2025-04-08 → 2025-05-20` = **42** |
| `first_payment_to_completion_days` | **None** · `not_applicable` | **None** · `not_applicable` | `2025-05-20 → 2026-08-02` = **439** |
| `execution_days` | **None** · `not_applicable` | `2024-11-21 → 2026-05-14` = **539** | `2025-04-08 → 2026-08-02` = **481** |
| `days_since_last_payment` | `2025-11-26 → 2026-08-24` = **271** | **None** · `not_published` | `2026-02-11 → 2026-08-24` = **194** |
| `duplicate_similarity` | **1.000** | **0.900** | **None** · `not_applicable` |
| `same_desc_same_agency_count` | **15** | 1 | 1 |
| `vendor_share_in_agency_pct` | 17.35 | **None** · `not_published` | **None** · `not_applicable` |
| `completed_without_payment` | false | **true** | false |
| `asset_image_absent` | **None** · `not_published` | **true** | false |
| `mp_utilisation_pct` | 73.80 | 71.37 | **None** · `not_published` |
| `payment_count` | 1 | **0** *(a real zero, never None)* | 4 |
| `gap_hop` | `sanction_to_disbursement` | **null** *(both hops unavailable)* | `disbursement_to_certification` |
| `slowest_lag` | `recommend_to_sanction` (333) | `recommend_to_sanction` (96) | `first_payment_to_completion` (439) |

Two identities are asserted by tests, not merely stated:

- **C:** `sanction_to_first_payment + first_payment_to_completion = execution_days`
  → `42 + 439 = 481`. ✓
- **A and B:** the identity does not apply, because one of the two payment-side
  lags is `None` while `execution_days` is computed from the sanction and
  completion dates directly (`DOMAIN-MODEL.md` §c). B is the case that proves the
  point: `execution_days = 539` is computed on a work with **zero payment rows**.
  Had `execution_days` been defined as the sum of the two lags, B's
  highest-weighted fired rule would have vanished.

**A's `asset_image_absent` is `None`, not `false`.** A has never been reported
complete, so the portal has published no `Image` column for it. That is
`not_published` — a reporting gap — and it is a different finding from a work
whose `Image` column was published reading `N/A`, which is B. The two sit side by
side in this table for exactly that reason.

**B's `slowest_lag` is degenerate and the UI must say so.** Only one of B's three
lags is computable, so "slowest" is a comparison over a set of one. The lifecycle
panel shows the other two as unavailable with their reasons, never as zero.

---

## Scoring — Fixture A

Work `WS/MP847/2025-2026/160261`, case `NG-8F0E3213D8`.
District Magistrate, Jalaun — the agency carrying the 115-work duplicate cluster
recorded in `DATA-PROFILE.md` §6.

| Rule | Value read | Op | Threshold | Status | Weight | Contribution |
| --- | ---: | :-: | ---: | --- | ---: | ---: |
| `utilisation_shortfall` | −40.01 | lt | −15 | **fired** | 22 | **22** |
| `execution_delay` | None | gt | 365 | *skipped* `not_applicable` | 20 | 0 |
| `duplicate_work` | 1.000 | gte | 0.85 | **fired** | 18 | **18** |
| `sanction_delay` | 333 | gt | 180 | **fired** | 16 | **16** |
| `stalled_work` | 271 | gt | 270 | **fired** | 16 | **16** |
| `vendor_concentration` | 17.35 | gt | 60 | passed | 12 | 0 |
| `status_payment_mismatch` | false | eq | true | passed | 12 | 0 |
| `split_sanction` | 15 | gte | 3 | **fired** | 10 | **10** |
| `asset_evidence_missing` | None | eq | true | *skipped* `not_published` | 10 | 0 |
| `account_underutilisation` | 73.80 | lt | 25 | passed | 8 | 0 |
| | | | | **Rule subtotal** | 144 | **82** |
| `agency_pattern_bonus` | 25 HIGH cases in FY2025-2026 | gte | 3 | **applied** | 10 | **10** |

```
raw_score    = 22 + 18 + 16 + 16 + 10 = 82,  + 10 bonus = 92
score        = min(92, 100)                              = 92
severity     = 92 >= 75                                  = HIGH
skipped wt   = 20 (execution_delay) + 10 (asset_evidence_missing) = 30
coverage_pct = (144 − 30) / 144 = 0.7917                 = 79
```

The 30 skipped points are **not** redistributed. A's 92 is 92 out of a possible
154, evaluated over 79% of the rulebook — not 92 out of a rescaled 114.

**`stalled_work` fires by one day.** 271 against a threshold of 270. That is
recorded here rather than smoothed away: the threshold was set from the measured
distribution (p90 = 268 d) before this row was chosen, and a case that clears a
threshold by a single day is exactly the kind of case an officer should be able
to see the arithmetic for. The trace row shows 271, 270 and the as-of date it was
measured against.

**Duplicate citation.** `duplicate_work` fired, so `citation_json` is mandatory
and non-null (`DOMAIN-MODEL.md` §h). The cluster holds **15 works** under
District Magistrate Jalaun whose descriptions are byte-identical after
normalisation, so every similarity component reads exactly 1.000 — this is an
exact repetition, not a fuzzy near-match. Two are cited:
`WS/MP847/2025-2026/160262` and `WS/MP847/2025-2026/160263`. An officer opens
them and decides. **15 semi-high-mast LED lights under one district magistrate is
very probably 15 street lights.** The flag buys ten minutes of an officer's
attention; it does not allege anything.

---

## Scoring — Fixture B

Work `WS/MP163/2024-2025/136111`, case `NG-736D95571D`. Rajya Sabha member, so
no constituency — the loader difference documented in profile §9.

| Rule | Value read | Op | Threshold | Status | Weight | Contribution |
| --- | ---: | :-: | ---: | --- | ---: | ---: |
| `utilisation_shortfall` | None | lt | −15 | *skipped* `not_published` | 22 | 0 |
| `execution_delay` | 539 | gt | 365 | **fired** | 20 | **20** |
| `duplicate_work` | 0.900 | gte | 0.85 | **fired** | 18 | **18** |
| `sanction_delay` | 96 | gt | 180 | passed | 16 | 0 |
| `stalled_work` | None | gt | 270 | *skipped* `not_published` | 16 | 0 |
| `vendor_concentration` | None | gt | 60 | *skipped* `not_published` | 12 | 0 |
| `status_payment_mismatch` | true | eq | true | **fired** | 12 | **12** |
| `split_sanction` | 1 | gte | 3 | passed | 10 | 0 |
| `asset_evidence_missing` | true | eq | true | **fired** | 10 | **10** |
| `account_underutilisation` | 71.37 | lt | 25 | passed | 8 | 0 |
| | | | | **Rule subtotal** | 144 | **60** |
| `agency_pattern_bonus` | 0 HIGH cases in FY2024-2025 | gte | 3 | **not applied** | 10 | **0** |

```
raw_score    = 20 + 18 + 12 + 10 = 60,  + 0 bonus = 60
score        = min(60, 100)                       = 60
severity     = 60 >= 50, 60 < 75                  = MEDIUM
skipped wt   = 22 + 16 + 12                       = 50
coverage_pct = (144 − 50) / 144 = 0.6528          = 65
```

**B is the graceful-degradation fixture.** Three rules — 50 of 144 points, more
than a third of the rulebook — could not be evaluated at all, because no
expenditure row joins to this work. All three are `not_published`, not `passed`.
If they had been silently treated as passes, B would look like a work that was
checked for utilisation shortfall, stalling and vendor concentration and came
through clean. It was not checked for any of them.

**B carries a mandatory caveat on `status_payment_mismatch`.** The rule fired
because the work is reported complete with no payment row. Profile §6 records
1,371 of 1,629 such works — and records that the expenditure export is truncated
to 34,000 rows and joins to only 3,529 sanctioned works, so an unknown share of
those 1,371 are export artefacts rather than reporting failures. The caveat text
travels on the trace row and is displayed with the flag, not in a footnote. B
makes the caveat unusually concrete: the completed export publishes a
`completed_amt` of 996,458 for this work, so money almost certainly moved and the
expenditure export simply does not carry it.

**`duplicate_work` fires at 0.900 and should not be trusted yet.** Standing
caveat 4 above explains why: the threshold of 0.85 on `token_set_ratio` fires on
61% of the corpus and is not calibrated. B's description is a road in a named
village and its nearest neighbour under the same agency is a different road; the
cluster count is 1. `split_sanction`, which reads exact repetition rather than
similarity, correctly passes. The two rules disagreeing on the same work is the
clearest available demonstration that the similarity scorer, not the repetition
count, is the one that needs Phase 7's attention.

**Corroboration does not apply.** The agency has no HIGH case in the window
against a minimum of three. This is the negative control for F4: an officer must
be able to see the bonus *not* fire and understand why, which is why the
corroboration block is rendered with `applied: false` and the count, rather than
omitted.

---

## Scoring — Fixture C  ·  SYNTHETIC CONTROL

Work `WS/MP503/2025-2026/140882`, case `NG-622268C00E`.
**`is_synthetic = true`.** Labelled on screen, excluded from every published
aggregate (CLAUDE.md invariant 12).

C exists for one reason: **no real MPLADS row can ever populate the certification
rung.** MoSPI publishes no utilisation certificate date and no certified amount
(profile §8). Without an injected control, `variance_disbursement_to_certification`
would have a derivation function that never once ran on real data — precisely the
declared-but-never-computed failure that CLAUDE.md invariant 3 exists to prevent.

C is inserted by `backend/ingest/synthetic.py` on every ingest run, as an actual
queryable row, and it is the only row in the `certifications` table.

| Rule | Value read | Op | Threshold | Status | Weight | Contribution |
| --- | ---: | :-: | ---: | --- | ---: | ---: |
| `utilisation_shortfall` | −3.00 | lt | −15 | passed | 22 | 0 |
| `execution_delay` | 481 | gt | 365 | **fired** | 20 | **20** |
| `duplicate_work` | None | gte | 0.85 | *skipped* `not_applicable` | 18 | 0 |
| `sanction_delay` | 84 | gt | 180 | passed | 16 | 0 |
| `stalled_work` | 194 | gt | 270 | passed | 16 | 0 |
| `vendor_concentration` | None | gt | 60 | *skipped* `not_applicable` | 12 | 0 |
| `status_payment_mismatch` | false | eq | true | passed | 12 | 0 |
| `split_sanction` | 1 | gte | 3 | passed | 10 | 0 |
| `asset_evidence_missing` | false | eq | true | passed | 10 | 0 |
| `account_underutilisation` | None | lt | 25 | *skipped* `not_published` | 8 | 0 |
| | | | | **Rule subtotal** | 144 | **20** |
| `agency_pattern_bonus` | 0 HIGH cases in FY2025-2026 | gte | 3 | **not applied** | 10 | **0** |

```
raw_score    = 20,  + 0 bonus                = 20
score        = min(20, 100)                  = 20
severity     = 20 < 50                       = LOW
skipped wt   = 18 + 12 + 8                   = 38
coverage_pct = (144 − 38) / 144 = 0.7361     = 74
```

**C's three skips are the corpus-shaped ones, and they are a finding rather
than a flaw in the control.** `duplicate_work` and `vendor_concentration` are
`not_applicable` because a single work under a single agency has no peer to be
similar to and no second vendor to be concentrated against;
`account_underutilisation` is `not_published` because the synthetic member holds
no allocation row. A work with no peers is a work three of the ten rules cannot
say anything about, and saying so is the whole of invariant 2. See standing
caveat 9 for why the control is not given a fabricated corpus to close them.

### C's fund ladder — and the point it makes

```
sanctioned  Rs 40,00,000   published
disbursed   Rs 38,80,000   published    hop 1: −3.00%   CLOSED (tolerance −15%)
certified   Rs 29,10,000   published    hop 2: −25.00%  OPEN
```

`gap_hop = "disbursement_to_certification"`.

**And that open hop contributes exactly zero points.** Rulebook v1.0.0 has no
rule reading `variance_disbursement_to_certification`, because there is no public
data to calibrate a threshold against. So C shows an officer a quarter of the
disbursed money uncertified, on a ladder rung marked open, next to a score of 20
and a LOW band.

That is not a bug and it must not be "fixed" by inventing a rule. It is the
clearest single demonstration of what the ablation module (`DOMAIN-MODEL.md` §i,
entry 1) is for: NIGRANI can see the shape of the gap and cannot score it,
because MoSPI does not publish the field. The recommendation that comes out of
F9 — *export one date and one certified amount per work* — is worth 20 points of
rulebook weight and roughly 12 points of coverage across 3,529 cases, and C is
the case that makes that concrete on screen.

**C does not demonstrate 100% coverage, and no fixture here does.** Coverage is
measured over rulebook weight, and C loses 38 points to the three rules a
peerless work cannot support, so it reads 74%. 1,011 real works in the corpus do
reach 100% (profile §6), and that population — not this control — is what shows
full coverage is attainable. C is not privileged by being synthetic; it is
privileged only in having a certified amount, and it pays for its isolation in
coverage.

---

## Summary

| | A | B | C |
| --- | ---: | ---: | ---: |
| Work id | `WS/MP847/2025-2026/160261` | `WS/MP163/2024-2025/136111` | `WS/MP503/2025-2026/140882` |
| Case id | `NG-8F0E3213D8` | `NG-736D95571D` | `NG-622268C00E` |
| Rules fired | 5 | 4 | 1 |
| Rules passed | 3 | 3 | 6 |
| Rules skipped | 2 | 3 | 3 |
| Rule subtotal | 82 | 60 | 20 |
| Corroboration | +10 | +0 | +0 |
| `raw_score` | **92** | **60** | **20** |
| `score` (capped) | 92 | 60 | 20 |
| Severity | HIGH | MEDIUM | LOW |
| `coverage_pct` | 79 | 65 | 74 |
| `gap_hop` | `sanction_to_disbursement` | null | `disbursement_to_certification` |
| `slowest_lag` | `recommend_to_sanction` | `recommend_to_sanction` | `first_payment_to_completion` |
| `is_synthetic` | false | false | **true** |

None of the three reaches the 100-point cap, so the cap is not exercised by a
fixture either. A work firing eight or more rules will exceed it — 144 + 10
points of weight against a 100-point display means capping is routine for the
worst cases, not exceptional. Two unit tests cover it rather than a fixture:
`tests/test_score.py::test_a_case_over_the_cap_still_stores_its_raw_score`
asserts that a case with a raw score of 118 stores `raw_score = 118` and
`score = 100`, and `test_cap_does_not_renormalise` takes the arithmetic to its
ceiling — all ten rules fired plus the bonus, `raw_score = 154`, `score = 100`.
Both assert that every `rule_hits.contribution` still equals the rule's full
undivided weight.

**Confirmation, stated plainly: no weight and no threshold in
`DOMAIN-MODEL.md` §(g) was altered, tuned or chosen to make any of 92, 60 or 20
come out. The weights were fixed from measured firing counts before these rows
were selected from the corpus, and the scores are what the addition produced —
including C's 20, which this file previously recorded as 42 on inputs the
control never carried (standing caveat 9).**
