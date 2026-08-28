# FIXTURES — three worked cases

Three cases, worked end to end with the arithmetic shown. Every engine function
gets its pytest assertion written against this file **before** the
implementation (CLAUDE.md working rules).

Fixture A is the case reproduced in full in `docs/contract/case_detail.json`.
Every number in that file appears here with its derivation.

---

## Standing caveats — read before using these fixtures

**1. The work ids are PROVISIONAL.** Phase 0 was a documentation phase and did
not parse the CSVs. The three works below are constructed to match the documented
shape of real rows — the id pattern, the largest measured duplicate cluster, the
measured percentiles — but they have **not** been pinned to actual rows in
`data/raw/`. Phase 1 must:

- locate a real row matching each fixture's profile,
- replace the `work_id_raw` here and in `case_detail.json`,
- re-derive every value in the derived table below from the real row,
- re-run the arithmetic and update both files in one commit.

Fixture C is synthetic by design and is exempt from that step.

**2. The arithmetic is already correct and will stay correct.** The derived
values below follow from the raw inputs by the definitions in
`docs/domain/DOMAIN-MODEL.md` §(f), and the scores follow from the derived values
by the rulebook in §(g). Substituting a real row changes the inputs, and
therefore the outputs — it does not change the method, and the tests written
against the method survive the substitution.

**3. Fixture C's work id is reserved.** `WS/MP503/2025-2026/140882` must not
collide with a real portal id. Phase 1 asserts non-collision at ingest and
rejects with reason `case_id_collision` if it ever does.

**4. No weight and no threshold was altered to reach any score below.** The
weights are those in `DOMAIN-MODEL.md` §(g), fixed from measured firing counts.
The three scores — 92, 50, 42 — are whatever the arithmetic produced. 92 is not a
target, 50 is not a boundary chosen for effect, and the fact that B lands exactly
on the MEDIUM cut-off is a coincidence of this input set, not a design.

**5. No claim is made that these combinations are unique or unreachable by other
works.** The inherited LEAKPROOF `fixtures.md` asserted that its fixture states
were unreachable by any other row, and its own seed data contradicted it. Many
works in the corpus will produce the same rule combinations, and several will
produce the same score. That is expected. These three are chosen because between
them they exercise every branch the engine has, not because they are rare.

---

## Case ids

Derived, not assigned. `case_id = "NG-" + sha256(canonical_work_id)[:10].upper()`
where the canonical id is the raw id uppercased with all whitespace removed
(CLAUDE.md invariant 8). These are reproducible from a shell:

```
python -c "import hashlib;print('NG-'+hashlib.sha256(b'WS/MP410/2024-2025/118427').hexdigest()[:10].upper())"
```

| Fixture | Work id | Case id |
| --- | --- | --- |
| A | `WS/MP410/2024-2025/118427` | `NG-27060CB62F` |
| B | `WS/MP128/2023-2024/094311` | `NG-F011D47878` |
| C | `WS/MP503/2025-2026/140882` | `NG-622268C00E` |

---

## What the three exercise between them

| Requirement | A | B | C |
| --- | :-: | :-: | :-: |
| Fund hop 1 (`sanction_to_disbursement`) open | **yes** | unavailable | closed |
| Fund hop 2 (`disbursement_to_certification`) open | unavailable | unavailable | **yes** |
| `slowest_lag` = `recommend_to_sanction` | **yes** | yes | no |
| `slowest_lag` = `first_payment_to_completion` | no | no | **yes** |
| Rule skipped from a genuinely unpublished field | 1 skip | **3 skips** | none |
| Corroboration bonus applied | **yes** | **no** | yes |
| Duplicate citation present | **yes** | no | no |
| `is_synthetic` | false | false | **true** |
| Coverage below 100% | 86% | **65%** | 100% |
| Severity band | HIGH | MEDIUM | LOW |

**`published_zero` is not exercised by these three fixtures.** All three of the
missing values below are `not_published` or `not_applicable`. The third
availability state — a field the portal supplied with the value zero, which is a
fact about the work rather than a reporting gap — is covered by a unit test,
`tests/test_derive.py::test_zero_payment_is_published_zero_not_missing`, rather
than by a fixture. Building a fourth fixture solely to carry one enum value would
add a case an officer would never see. The distinction itself is not optional:
CLAUDE.md invariant 2 requires it end to end, and the test enforces it.

---

## Raw inputs

As they arrive from ingest, before any derivation. Amounts are whole rupees.
`—` means the source supplied no value.

| Field | A | B | C |
| --- | --- | --- | --- |
| `work_id_raw` | `WS/MP410/2024-2025/118427` | `WS/MP128/2023-2024/094311` | `WS/MP503/2025-2026/140882` |
| `description` | high mast led light 95 mtrs ms pole with 6 led | construction of interlocking cc road in village kothra | construction of community hall at ward no 7 |
| `category` | Normal/Others | Normal/Others | Normal/Others |
| `status` | Work partially Completed | Work Completed | Work Completed |
| `state` / `district` | Uttar Pradesh / Budaun | Maharashtra / Satara | Maharashtra / Nashik |
| `agency` (canonical) | District Magistrate, Budaun | Executive Engineer, Rural Works Division, Satara | District Magistrate, Nashik |
| `agency` (raw) | `DISTRICT MAGISTRAE BUDAUN` | `EXECUTIVE ENGINEER RURAL WORKS DIVISION SATARA` | `DISTRICT MAGISTRATE NASHIK` |
| MP house | lok_sabha | **rajya_sabha** | lok_sabha |
| MP constituency | Budaun | **— (Rajya Sabha, seated by state)** | Nashik |
| `recommended_amt` | 1,630,000 | 2,500,000 | 4,000,000 |
| `sanctioned_amt` | 1,630,000 | 2,500,000 | 4,000,000 |
| `disbursed_amt` | 1,062,000 | **— (no expenditure row)** | 3,880,000 |
| `certified_amt` | **— (never published)** | **— (never published)** | 2,910,000 *(synthetic)* |
| `recommended_date` | 2024-03-11 | 2023-09-05 | 2025-01-14 |
| `sanction_date` | 2024-12-04 | 2023-12-02 | 2025-04-08 |
| `first_payment_date` | 2025-04-19 | — | 2025-05-20 |
| `last_payment_date` | 2025-07-11 | — | 2026-02-11 |
| `completion_date` | **— (not completed)** | 2025-06-18 | 2026-08-02 |
| `payment_count` | 3 | 0 | 4 |
| `Image` column | `Images` | `N/A` | `Images` |
| vendor share in agency | 38.2% | — | 67.3% |
| same description under agency | 244 | 1 | 2 |
| best similarity in agency | 0.97 | 0.42 | 0.31 |
| MP account, this FY | 44.9% utilised | 6.6% utilised | 44.9% utilised |
| agency HIGH cases, this FY | 7 | 1 | 4 |
| `is_synthetic` | false | false | **true** |

`DATA_AS_OF = 2026-08-24` for all three — the maximum payment date in the corpus
(`docs/data/DATA-PROFILE.md` §4). Never `today`.

**Note on `recommended_amt` = `sanctioned_amt` in all three.** That is not a
convenience. It is the degeneracy finding (profile §5): recommended equals
sanctioned in 14,831 of 14,831 matched works. A fixture where the two differed
would be unrepresentative of the corpus, and would quietly reintroduce the
`cost_overrun` rule the data proved uncomputable.

---

## Derived values

By the definitions in `DOMAIN-MODEL.md` §(f). Arithmetic shown for every
non-trivial value.

| Feature | A | B | C |
| --- | --- | --- | --- |
| `variance_sanction_to_disbursement` | `(1062000−1630000)/1630000×100` = **−34.85%** | **None** · `not_published` | `(3880000−4000000)/4000000×100` = **−3.00%** |
| `variance_disbursement_to_certification` | **None** · `not_published` | **None** · `not_published` | `(2910000−3880000)/3880000×100` = **−25.00%** |
| `sanction_lag_days` | `2024-03-11 → 2024-12-04` = **268** | `2023-09-05 → 2023-12-02` = **88** | `2025-01-14 → 2025-04-08` = **84** |
| `sanction_to_first_payment_days` | `2024-12-04 → 2025-04-19` = **136** | **None** · `not_applicable` | `2025-04-08 → 2025-05-20` = **42** |
| `first_payment_to_completion_days` | **None** · `not_applicable` | **None** · `not_applicable` | `2025-05-20 → 2026-08-02` = **439** |
| `execution_days` | **None** · `not_applicable` | `2023-12-02 → 2025-06-18` = **564** | `2025-04-08 → 2026-08-02` = **481** |
| `days_since_last_payment` | `2025-07-11 → 2026-08-24` = **409** | **None** · `not_published` | `2026-02-11 → 2026-08-24` = **194** |
| `duplicate_similarity` | **0.97** | 0.42 | 0.31 |
| `same_desc_same_agency_count` | **244** | 1 | 2 |
| `vendor_share_in_agency_pct` | 38.2 | **None** · `not_published` | **67.3** |
| `completed_without_payment` | false | **true** | false |
| `asset_image_absent` | false | **true** | false |
| `mp_utilisation_pct` | 44.9 | **6.6** | 44.9 |
| `payment_count` | 3 | **0** *(a real zero, never None)* | 4 |
| `gap_hop` | `sanction_to_disbursement` | **null** *(both hops unavailable)* | `disbursement_to_certification` |
| `slowest_lag` | `recommend_to_sanction` (268) | `recommend_to_sanction` (88) | `first_payment_to_completion` (439) |

Two identities are asserted by tests, not merely stated:

- **C:** `sanction_to_first_payment + first_payment_to_completion = execution_days`
  → `42 + 439 = 481`. ✓
- **A and B:** the identity does not apply, because one of the two payment-side
  lags is `None` while `execution_days` is computed from the sanction and
  completion dates directly (`DOMAIN-MODEL.md` §c). B is the case that proves the
  point: `execution_days = 564` is computed on a work with **zero payment rows**.
  Had `execution_days` been defined as the sum of the two lags, B's only fired
  high-severity rule would have vanished.

**B's `slowest_lag` is degenerate and the UI must say so.** Only one of B's three
lags is computable, so "slowest" is a comparison over a set of one. The lifecycle
panel shows the other two as unavailable with their reasons, never as zero.

---

## Scoring — Fixture A

Work `WS/MP410/2024-2025/118427`, case `NG-27060CB62F`.

| Rule | Value read | Op | Threshold | Status | Weight | Contribution |
| --- | ---: | :-: | ---: | --- | ---: | ---: |
| `utilisation_shortfall` | −34.85 | lt | −15 | **fired** | 22 | **22** |
| `execution_delay` | None | gt | 365 | *skipped* `not_applicable` | 20 | 0 |
| `duplicate_work` | 0.97 | gte | 0.85 | **fired** | 18 | **18** |
| `sanction_delay` | 268 | gt | 180 | **fired** | 16 | **16** |
| `stalled_work` | 409 | gt | 270 | **fired** | 16 | **16** |
| `vendor_concentration` | 38.2 | gt | 60 | passed | 12 | 0 |
| `status_payment_mismatch` | false | eq | true | passed | 12 | 0 |
| `split_sanction` | 244 | gte | 3 | **fired** | 10 | **10** |
| `asset_evidence_missing` | false | eq | true | passed | 10 | 0 |
| `account_underutilisation` | 44.9 | lt | 25 | passed | 8 | 0 |
| | | | | **Rule subtotal** | 144 | **82** |
| `agency_pattern_bonus` | 7 HIGH cases in FY2024-2025 | gte | 3 | **applied** | 10 | **10** |

```
raw_score    = 22 + 18 + 16 + 16 + 10 = 82,  + 10 bonus = 92
score        = min(92, 100)                              = 92
severity     = 92 >= 75                                  = HIGH
skipped wt   = 20 (execution_delay)
coverage_pct = (144 − 20) / 144 = 0.8611                 = 86
```

The 20 skipped points are **not** redistributed. A's 92 is 92 out of a possible
154, evaluated over 86% of the rulebook — not 92 out of a rescaled 124.

**Duplicate citation.** `duplicate_work` fired, so `citation_json` is mandatory
and non-null (`DOMAIN-MODEL.md` §h). It names `WS/MP410/2024-2025/118431` and
`WS/MP410/2024-2025/118455`, cluster size 244, the shared description, the
similarity components, and the method. An officer opens those two works and
decides. **244 high-mast street lights under one district magistrate is very
probably 244 street lights.** The flag buys ten minutes of an officer's
attention; it does not allege anything.

---

## Scoring — Fixture B

Work `WS/MP128/2023-2024/094311`, case `NG-F011D47878`. Rajya Sabha member, so
no constituency — the loader difference documented in profile §9.

| Rule | Value read | Op | Threshold | Status | Weight | Contribution |
| --- | ---: | :-: | ---: | --- | ---: | ---: |
| `utilisation_shortfall` | None | lt | −15 | *skipped* `not_published` | 22 | 0 |
| `execution_delay` | 564 | gt | 365 | **fired** | 20 | **20** |
| `duplicate_work` | 0.42 | gte | 0.85 | passed | 18 | 0 |
| `sanction_delay` | 88 | gt | 180 | passed | 16 | 0 |
| `stalled_work` | None | gt | 270 | *skipped* `not_published` | 16 | 0 |
| `vendor_concentration` | None | gt | 60 | *skipped* `not_published` | 12 | 0 |
| `status_payment_mismatch` | true | eq | true | **fired** | 12 | **12** |
| `split_sanction` | 1 | gte | 3 | passed | 10 | 0 |
| `asset_evidence_missing` | true | eq | true | **fired** | 10 | **10** |
| `account_underutilisation` | 6.6 | lt | 25 | **fired** | 8 | **8** |
| | | | | **Rule subtotal** | 144 | **50** |
| `agency_pattern_bonus` | 1 HIGH case in FY2023-2024 | gte | 3 | **not applied** | 10 | **0** |

```
raw_score    = 20 + 12 + 10 + 8 = 50,  + 0 bonus = 50
score        = min(50, 100)                      = 50
severity     = 50 >= 50, 50 < 75                 = MEDIUM
skipped wt   = 22 + 16 + 12                      = 50
coverage_pct = (144 − 50) / 144 = 0.6528         = 65
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
travels on the trace row and is displayed with the flag, not in a footnote.

**Corroboration does not apply.** The agency has one HIGH case in the window
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

| Rule | Value read | Op | Threshold | Status | Weight | Contribution |
| --- | ---: | :-: | ---: | --- | ---: | ---: |
| `utilisation_shortfall` | −3.00 | lt | −15 | passed | 22 | 0 |
| `execution_delay` | 481 | gt | 365 | **fired** | 20 | **20** |
| `duplicate_work` | 0.31 | gte | 0.85 | passed | 18 | 0 |
| `sanction_delay` | 84 | gt | 180 | passed | 16 | 0 |
| `stalled_work` | 194 | gt | 270 | passed | 16 | 0 |
| `vendor_concentration` | 67.3 | gt | 60 | **fired** | 12 | **12** |
| `status_payment_mismatch` | false | eq | true | passed | 12 | 0 |
| `split_sanction` | 2 | gte | 3 | passed | 10 | 0 |
| `asset_evidence_missing` | false | eq | true | passed | 10 | 0 |
| `account_underutilisation` | 44.9 | lt | 25 | passed | 8 | 0 |
| | | | | **Rule subtotal** | 144 | **32** |
| `agency_pattern_bonus` | 4 HIGH cases in FY2025-2026 | gte | 3 | **applied** | 10 | **10** |

```
raw_score    = 20 + 12 = 32,  + 10 bonus = 42
score        = min(42, 100)               = 42
severity     = 42 < 50                    = LOW
skipped wt   = 0
coverage_pct = (144 − 0) / 144            = 100
```

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
disbursed money uncertified, on a ladder rung marked open, next to a score of 42
and a LOW band.

That is not a bug and it must not be "fixed" by inventing a rule. It is the
clearest single demonstration of what the ablation module (`DOMAIN-MODEL.md` §i,
entry 1) is for: NIGRANI can see the shape of the gap and cannot score it,
because MoSPI does not publish the field. The recommendation that comes out of
F9 — *export one date and one certified amount per work* — is worth 20 points of
rulebook weight and roughly 12 points of coverage across 3,529 cases, and C is
the case that makes that concrete on screen.

**C also demonstrates that 100% coverage is attainable.** Coverage is measured
over rules, and no rule reads a never-published field. A real work with a
complete payment and completion history reaches 100% too. C is not privileged by
being synthetic; it is privileged only in having a certified amount.

---

## Summary

| | A | B | C |
| --- | ---: | ---: | ---: |
| Case id | `NG-27060CB62F` | `NG-F011D47878` | `NG-622268C00E` |
| Rules fired | 5 | 4 | 2 |
| Rules passed | 4 | 3 | 8 |
| Rules skipped | 1 | 3 | 0 |
| Rule subtotal | 82 | 50 | 32 |
| Corroboration | +10 | +0 | +10 |
| `raw_score` | **92** | **50** | **42** |
| `score` (capped) | 92 | 50 | 42 |
| Severity | HIGH | MEDIUM | LOW |
| `coverage_pct` | 86 | 65 | 100 |
| `gap_hop` | `sanction_to_disbursement` | null | `disbursement_to_certification` |
| `slowest_lag` | `recommend_to_sanction` | `recommend_to_sanction` | `first_payment_to_completion` |
| `is_synthetic` | false | false | **true** |

None of the three reaches the 100-point cap, so the cap is not exercised by a
fixture either. A work firing seven or more rules will exceed it — 144 + 10
points of weight against a 100-point display means capping is routine for the
worst cases, not exceptional. `tests/test_score.py::test_cap_does_not_renormalise`
covers it: it asserts that a case with a raw score of 118 stores `raw_score = 118`
and `score = 100`, and that every `rule_hits.contribution` still equals the
rule's full undivided weight.

**Confirmation, stated plainly: no weight and no threshold in
`DOMAIN-MODEL.md` §(g) was altered, tuned or chosen to make any of 92, 50 or 42
come out. The weights were fixed from measured firing counts before these three
inputs were assembled, and the scores are what the addition produced.**
