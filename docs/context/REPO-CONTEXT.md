# REPO-CONTEXT — LEAKPROOF

Read-only reconnaissance dump, generated 2026-08-24. Facts only, no
recommendations. Where something does not exist it is written **ABSENT**.

Scope of the scan: `backend/`, `frontend/src/`, `docs/`, root-level markdown.
Excluded from the tree per instruction: `.git`, `node_modules`, `.venv`,
`__pycache__`, `dist`, `build`, `*.db-journal`.

---

## 0. Repo state

### `git remote -v`

```
origin	https://github.com/Nidzz07/Gods-Plan-SIH-2026.git (fetch)
origin	https://github.com/Nidzz07/Gods-Plan-SIH-2026.git (push)
```

### `git branch --show-current`

```
main
```

### `git log --oneline -5`

```
fatal: your current branch 'main' does not have any commits yet
```

**There are ZERO commits in this repository.** Every file is untracked. `git status --short`:

```
?? .gitignore
?? CLAUDE.md
?? PROJECT-BRIEF.md
?? README.md
?? backend/
?? docs/
?? frontend/
```

Configured git identity: `Nidhi Dhyani <nsdhyani22@gmail.com>`.

### Full recursive file tree

```
.
├── .gitignore
├── CLAUDE.md
├── PROJECT-BRIEF.md
├── README.md
├── backend/
│   ├── .pytest_cache/
│   │   ├── .gitignore
│   │   ├── CACHEDIR.TAG
│   │   ├── README.md
│   │   └── v/cache/{lastfailed, nodeids, stepwise}
│   ├── app/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── rules.yaml
│   │   ├── schemas.py
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── audit.py
│   │   │   ├── complaints.py
│   │   │   ├── memo.py
│   │   │   ├── reconcile.py
│   │   │   ├── rulebook.py
│   │   │   ├── score.py
│   │   │   └── stats.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── audit.py
│   │       ├── cases.py
│   │       └── rulebook.py
│   ├── leakproof.db
│   ├── requirements.txt
│   ├── seed.py
│   └── tests/
│       ├── .gitkeep
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_audit.py
│       ├── test_complaints.py
│       ├── test_memo.py
│       ├── test_reconcile.py
│       ├── test_rulebook.py
│       └── test_score.py
├── docs/
│   ├── contract/
│   │   ├── case_detail.json
│   │   └── fixtures.md
│   └── design/
│       └── REDESIGN-SPEC.md
└── frontend/
    ├── .pytest_cache/          <-- present, stray; frontend has no python
    │   ├── .gitignore
    │   ├── CACHEDIR.TAG
    │   ├── README.md
    │   └── v/cache/{nodeids, stepwise}
    ├── index.html
    ├── package-lock.json
    ├── package.json
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── api.js
        ├── index.css
        ├── main.jsx
        ├── roles.js
        ├── severity.js
        ├── ui.js
        ├── components/
        │   ├── .gitkeep
        │   ├── EmptyState.jsx
        │   ├── Ladder.jsx
        │   ├── Layout.jsx
        │   ├── Logo.jsx
        │   ├── PageHeader.jsx
        │   ├── PageMotif.jsx
        │   ├── SectionHeading.jsx
        │   ├── Sidebar.jsx
        │   ├── Skeleton.jsx
        │   ├── Tag.jsx
        │   ├── TopBar.jsx
        │   └── TraceTable.jsx
        ├── hooks/
        │   └── useApi.js
        └── pages/
            ├── .gitkeep
            ├── Auditor.jsx
            ├── CaseDetail.jsx
            ├── Inspector.jsx
            ├── NotFound.jsx
            ├── Officer.jsx
            ├── Rulebook.jsx
            └── SignIn.jsx
```

Also present but excluded by the stated filter: `frontend/dist/` (a stale Vite
build: `index.html` 13 lines, `assets/index-CmAs-zkb.js` 67 lines,
`assets/index-CnvqTHBL.css` 1 line), `frontend/node_modules/` (101 top-level
entries), `backend/.venv/`, `__pycache__/` directories.

### Line counts (`wc -l`), descending

| Lines | File |
|---:|---|
| 2750 | frontend/package-lock.json |
| 546 | backend/seed.py |
| 364 | backend/app/routers/cases.py |
| 301 | frontend/src/pages/Auditor.jsx |
| 299 | frontend/src/pages/Inspector.jsx |
| 283 | backend/app/models.py |
| 261 | README.md |
| 243 | frontend/src/pages/CaseDetail.jsx |
| 242 | frontend/src/pages/Officer.jsx |
| 218 | frontend/src/pages/Rulebook.jsx |
| 215 | backend/tests/conftest.py |
| 198 | backend/app/schemas.py |
| 191 | PROJECT-BRIEF.md |
| 182 | frontend/src/components/PageMotif.jsx |
| 182 | backend/tests/test_audit.py |
| 176 | frontend/src/pages/SignIn.jsx |
| 169 | backend/tests/test_rulebook.py |
| 167 | backend/tests/test_score.py |
| 157 | docs/design/REDESIGN-SPEC.md |
| 150 | backend/tests/test_api.py |
| 149 | docs/contract/case_detail.json |
| 145 | CLAUDE.md |
| 142 | frontend/src/ui.js |
| 128 | frontend/src/components/Ladder.jsx |
| 125 | backend/app/engine/reconcile.py |
| 124 | frontend/tailwind.config.js |
| 113 | backend/app/engine/rulebook.py |
| 100 | backend/app/engine/memo.py |
| 98 | backend/tests/test_reconcile.py |
| 93 | backend/app/engine/score.py |
| 88 | backend/tests/test_complaints.py |
| 86 | frontend/src/severity.js |
| 84 | frontend/src/hooks/useApi.js |
| 84 | backend/app/engine/audit.py |
| 81 | backend/app/engine/complaints.py |
| 79 | frontend/src/components/TraceTable.jsx |
| 79 | backend/app/engine/stats.py |
| 72 | backend/tests/test_memo.py |
| 69 | frontend/src/components/TopBar.jsx |
| 66 | frontend/src/components/Tag.jsx |
| 65 | backend/app/rules.yaml |
| 63 | frontend/src/components/Logo.jsx |
| 59 | frontend/src/components/Sidebar.jsx |
| 58 | docs/contract/fixtures.md |
| 58 | backend/app/routers/audit.py |
| 56 | frontend/src/components/Skeleton.jsx |
| 53 | frontend/src/roles.js |
| 53 | frontend/src/components/Layout.jsx |
| 52 | frontend/src/index.css |
| 42 | frontend/src/api.js |
| 42 | backend/app/main.py |
| 39 | frontend/src/App.jsx |
| 38 | backend/app/db.py |
| 32 | frontend/src/pages/NotFound.jsx |
| 32 | frontend/src/components/EmptyState.jsx |
| 26 | frontend/src/main.jsx |
| 26 | frontend/src/components/SectionHeading.jsx |
| 25 | frontend/package.json |
| 24 | backend/app/routers/rulebook.py |
| 23 | frontend/vite.config.js |
| 22 | frontend/src/components/PageHeader.jsx |
| 12 | frontend/index.html |
| 7 | backend/requirements.txt |
| 6 | frontend/postcss.config.js |
| 5 | backend/app/engine/__init__.py |
| 2 | backend/tests/__init__.py |
| 1 | frontend/src/components/.gitkeep |
| 1 | frontend/src/pages/.gitkeep |
| 1 | backend/tests/.gitkeep |
| 1 | backend/app/routers/__init__.py |
| 1 | backend/app/__init__.py |
| — | backend/leakproof.db (binary, 5,574,656 bytes) |

Total across all text source (excluding package-lock.json and dist): 7,552 lines
as counted by `wc -l` over `*.py *.js *.jsx *.md *.yaml *.json *.css *.html *.txt`.

### Files present in the repo but NOT mentioned in README.md

- `.gitignore`
- `backend/app/__init__.py`
- `backend/app/engine/__init__.py`
- `backend/app/routers/__init__.py`
- `backend/tests/__init__.py`, `conftest.py`, `test_api.py`, `test_audit.py`,
  `test_complaints.py`, `test_memo.py`, `test_reconcile.py`, `test_rulebook.py`,
  `test_score.py` (README says only "`tests/` pytest suite, fixture-driven")
- `backend/tests/.gitkeep`, `frontend/src/pages/.gitkeep`,
  `frontend/src/components/.gitkeep`
- `backend/leakproof.db` — referred to in prose ("SQLite (single file, committed
  as a rollback artifact)") but absent from the repository-structure tree
- `frontend/index.html`, `package.json`, `package-lock.json`,
  `postcss.config.js`, `tailwind.config.js`, `vite.config.js`
- `frontend/src/App.jsx`, `main.jsx`, `index.css`, `roles.js`
- `frontend/src/components/Layout.jsx`, `Logo.jsx`, `PageMotif.jsx`,
  `SectionHeading.jsx`
- `frontend/src/pages/SignIn.jsx`
- `backend/.pytest_cache/`, `frontend/.pytest_cache/`, `frontend/dist/`

### Files mentioned in README.md but ABSENT

None. Every path named in README's repository-structure block exists.

Two README statements that are inaccurate rather than absent:

1. The clone command names a repository that is not this origin:
   `git clone https://github.com/YOUR-USERNAME/AI-Based-Public-Distribution-System-Diversion-Detection.git`
   — the actual origin is `https://github.com/Nidzz07/Gods-Plan-SIH-2026.git`.
2. Prerequisites say `node --version  # expect v20.x`; the installed Node is
   v24.19.0.

Additionally, `PROJECT-BRIEF.md`'s frozen API contract lists
`GET /api/shops/{shop_id}` — that endpoint is **ABSENT** from the code (see §5).

---

## 1. Governing documents

### 1.1 `CLAUDE.md` (145 lines, verbatim)

```markdown
# CLAUDE.md — LEAKPROOF

## What this is
LEAKPROOF detects diversion of subsidised foodgrain in India's Public
Distribution System and explains every flag in language an officer can
act on and an auditor can re-derive months later.

Hackathon: Innovate 4 Impact, AI SDG Global Hackathon 2026, PS-B16.
Team ExploreeTinkerBell. Two developers, ~36 build hours, hard deadline.
Read PROJECT-BRIEF.md before your first edit in any session.

## Stack — fixed, do not substitute
Backend : Python 3.11 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · PyYAML · SQLite · pytest
Frontend: React 18 · Vite · Tailwind · React Router · Recharts
Storage : SQLite, single file at backend/leakproof.db. Committed on purpose.

Do not introduce Postgres, Supabase, Docker, Redis, Celery, an ORM other
than SQLAlchemy, a state library, a component library, or any LLM API call.
If you think one is needed, say so and stop — do not add it.

## Repo map
backend/
  app/
    main.py            FastAPI app, CORS to :5173, router registration
    db.py              engine, SessionLocal, Base
    models.py          9 SQLAlchemy tables
    schemas.py         Pydantic shapes — MUST mirror docs/contract/case_detail.json
    rules.yaml         F2 rulebook, loaded at runtime, never imported as constants
    engine/
      reconcile.py     F1  four-hop ladder + locate_gap()
      rulebook.py      F2  load() + evaluate()
      score.py         F3+F5 composite score, trace, coverage_pct
      complaints.py    F4  window matching + corroboration bonus
      memo.py          plain-language memo — template f-string, NOT an LLM
      audit.py         F6  append-only log
    routers/           cases.py, audit.py, rulebook.py
  seed.py              synthetic data, random.seed(4521)
  tests/
frontend/
  src/api.js           single fetch wrapper
  src/pages/           Officer, CaseDetail, Inspector, Auditor, Rulebook
  src/components/
docs/contract/         case_detail.json (frozen), fixtures.md

## Invariants — breaking any of these breaks the pitch
1. Shop #4521 scores EXACTLY 87. 30 + 25 + 22 + 10 = 87. The deck promises
   87 on stage. If a change makes it 86 or 88, the change is wrong, not the 87.
2. #4102 scores 55 with coverage_pct 83. #4788 scores 53 with
   gap_hop == "receipt_to_counter".
3. Rule weights total 120, plus a 10-point complaint bonus = 130 possible.
   Display is capped at 100. Do NOT "fix" this by renormalising to 100.
4. Missing data is status "skipped" and reduces coverage_pct. It is never
   treated as "passed". A rule we could not evaluate is not a rule that passed.
5. The z-score layer is a confirming badge only. It contributes ZERO to score.
6. audit_log is append-only. No UPDATE, no DELETE, no helper that could do
   either, anywhere in the codebase. Before any commit touching audit.py, run:
     grep -rn "\.delete(\|UPDATE" backend/ | grep -i audit
   It must return nothing.
7. seed.py uses random.seed(4521). Never remove or change the seed.
8. schemas.py and docs/contract/case_detail.json move together or not at all.
   Changing a key name on one side without the other breaks the frontend
   silently. Flag it, don't just do it.

## Working rules
- Test first. For every engine function, write the pytest assertion against
  the fixture in docs/contract/fixtures.md before writing the implementation.
- One feature per session. Do not touch F4 while fixing F2.
- Never edit files outside the feature currently being built. If a fix needs
  a change elsewhere, say so and ask.
- Prefer boring, readable code. A judge may read this on screen.
- No new dependencies without asking.
- Comments explain WHY a threshold or weight is what it is, not what the
  line does.

## Git conventions
- Never add a "Co-authored-by" or "Co-Authored-By" trailer of any kind to a
  commit message. No variant, no casing, no other attribution line either —
  nothing naming a tool, an assistant, Claude, or Anthropic anywhere in the
  subject or body. Commit as the current user only, and leave author and
  committer as the person running the command.
  This is a hackathon submission judged as the team's own work. It also
  overrides the default convention of the assistant tooling, which asks for
  such a trailer — so it must be applied deliberately on every commit, not
  assumed.
- After committing, verify with:
    git log -1 --format="%B" | grep -iE "co-authored|claude|anthropic"
  It must return nothing.
- One logical unit per commit, and every commit must build. Do not commit a
  file whose imports land in a later commit — a fresh checkout at any point
  in the history should install and build. If a change needs a sibling file
  to work, they go in together.

## Commands
Backend
  cd backend && python -m venv .venv
  source .venv/bin/activate      # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  python seed.py
  uvicorn app.main:app --reload --port 8000
  pytest -v
Frontend
  cd frontend && npm install && npm run dev     # :5173

## UI conventions

Reference spec: docs/design/REDESIGN-SPEC.md — read this before any
styling work. It extends, not replaces, the tokens below.

Brand palette (unchanged, locked since Stage 0):
  bg #FAF8F4 · navy #132A47 · green #2E7D5B · gold #C8952B · coral #D4573D

Text/surface tokens (added in redesign pass):
  ink #14171A (body text) · ink-secondary #5B6169 (meta/captions) ·
  ink-muted #94989E (disabled/skipped) · border #DDD9D0 ·
  border-strong #C7C2B6 · surface #FFFFFF · surface-sunk #F3F0EA

Rule: navy is for headings and the score-display number ONLY. Body text,
labels, and captions use ink or ink-secondary. Navy-colored body text is
the single most common regression — check for it explicitly.

Type    : serif display (headings + score-display) / Inter (everything
          else), tabular-nums on ALL numeric elements. Full scale in
          REDESIGN-SPEC.md — six defined sizes, not two.
Spacing : 8px scale only (4/8/16/24/32/48)
Radius  : one 4px token everywhere, including tags — no second radius
Shadow  : one shadow-card token, no second depth
Severity: TWO valid patterns, do not mix on one element —
  (1) colored left-border on a full data row (Officer, trace table)
  (2) rectangular tag — tinted bg, solid-color text, sentence case,
      ALWAYS with a text label (Rulebook severity, status chips)
Tables  : numeric columns right-aligned + tabular-nums; every table has a
          one-line caption; headers are meta-label style (12px uppercase
          tracked ink-secondary), visually distinct from cells
Banned  : gradients, rounded-full badges/pills, emoji in UI, more than one
          shadow depth, more than one border-radius, unstyled browser
          defaults, spinner-only loading states

## Honesty rules — these appear on stage, keep the code truthful
The following are deliberately hardcoded and are declared to judges as
scoping decisions. Do not write code or comments that overclaim them:
  synthetic data · back-solved rule weights · escalation is a stub ·
  role switcher is a dropdown, not auth · inspector routing is score-sorted,
  not optimised · memos are templates ("template now, LLM later") ·
  headline statistics are illustrative, not sourced
Never describe memo.py output as AI-generated. Never describe the SQLite
setup as row-level security — it is role-scoped queries at the API layer.
```

### 1.2 `PROJECT-BRIEF.md` (191 lines, verbatim)

```markdown
# LEAKPROOF — Project Brief

## Problem
India's Public Distribution System moves subsidised foodgrain to roughly
two-thirds of the population under the National Food Security Act. It moves
through a chain: government allocation → transport consignment → fair-price
shop receipt → beneficiary transaction at an ePoS counter. Grain leaks between
those hops. Today the mismatch surfaces months later in an audit, by which
time the trail is cold, and inspections are allocated by rotation rather than
by evidence.

## Solution
LEAKPROOF reads data the PDS already produces — ePoS-linked weighing scales,
FCI depot weighbridges, vehicle GPS, and public grievance portals — and
reconciles four numbers per cycle. Where they disagree, it localises WHICH
hop the grain left at, scores the case against a rulebook an officer can edit,
and emits a reasoning trace that survives scrutiny in front of a magistrate.

LEAKPROOF installs no hardware. It reads existing infrastructure.

## Users and roles
Officer   — sees the ranked case list, opens a case, reads the trace
Inspector — sees cases ordered by score for field visits, adds notes
Auditor   — sees the append-only trail, presses Recompute

Roles are a dropdown switcher in this build. Real auth is out of scope.

## The four-hop reconciliation model
allocated_kg → dispatched_kg → weighed_kg → dispensed_kg

Three variances, three places grain can go:
  allocated → dispatched   paper diversion at the depot
  dispatched → weighed     transport-leg diversion
  weighed → dispensed      counter skimming at the shop

locate_gap() returns the worst hop. This is the core insight: "985 kg opened
between dispatch and receipt — not the dealer, the transport leg."

## The six features
F1 Four-hop reconciliation ladder      — engine/reconcile.py
F2 Versioned YAML rulebook             — rules.yaml + engine/rulebook.py
F3 Reasoning trace                     — engine/score.py
F4 Complaint auto-linking              — engine/complaints.py
F5 Graceful degradation on missing data— threaded through F1/F3
F6 Reproducibility on append-only trail— engine/audit.py

Deliberately excluded: statistical z-score as a scoring input (badge only),
inspector map optimisation, anything beneficiary-facing, LLM memo generation.

The z-score badge is computed in routers/cases.py at case-open time: each
shop's worst hop variance against the mean and population SD of all 60 shops'
worst hops, confirming at z >= 2.0. #4521 sits at z 1.66, so its badge reads
"does not confirm" — an honest result, not a tuned one. engine/score.py never
reads it; the score is fired weights plus the complaint bonus and nothing else.

## Scoring
Weights live in rules.yaml, loaded at runtime.

  weighing_variance     variance_dispatch_to_receipt  <  -5.0 %   30
  delivery_gap          delivery_gap_hours            >  48 hrs   25
  gps_deviation         gps_deviation_km              >  2.0 km   22
  counter_variance      variance_receipt_to_counter   <  -5.0 %   20
  transaction_mismatch  txn_card_ratio                <  0.6      15
  operating_hours       hour_violations_month         >= 3         8
  complaint_bonus       >=3 complaints in 14 days                 +10

Total possible 130, displayed capped at 100.
Severity bands: HIGH >= 75, MEDIUM >= 50, else LOW.

Every rule hit records: rule_id, label, raw_value, threshold, contribution,
severity, and status (fired | passed | skipped).

## Graceful degradation (F5)
A rule whose input is unavailable gets status "skipped", contributes 0, and
reduces coverage_pct. It is never "passed". The UI displays this as a greyed,
italic row plus a coverage badge: "55 / 100 · signal coverage 83%".

This is the difference between "we checked and it was fine" and "we could not
check". Conflating the two is how audit systems lose credibility.

## Fixtures — three shops that exercise everything

                        #4521 Sitapur   #4102 Barabanki   #4788 Hargaon
archetype               transport       transport, no GPS  counter skim
allocated / dispatched  12,000 / 12,000 8,000 / 8,000      9,000 / 9,000
weighed                 11,015          7,512              8,970
dispensed               10,980          7,490              8,190
dispatch → receipt      -8.21%          -6.10%             -0.33%
receipt → counter       -0.32%          -0.29%             -8.70%
delivery gap            61 h            52 h               44 h
gps deviation           3.4 km          unavailable        0.8 km
txn_card_ratio          0.88            0.71               0.55
hour violations         1               1                  4
complaints in window    7               2                  6
fired rules             30 + 25 + 22    30 + 25            20 + 15 + 8
bonus                   +10             0 (below 3)        +10
SCORE                   87              55                 53
severity                HIGH            MEDIUM             MEDIUM
coverage_pct            100             83                 100
gap_hop                 dispatch_to_    dispatch_to_       receipt_to_
                        receipt         receipt            counter

Between them: gap localisation at two hops, a skipped rule, coverage
reduction, bonus firing, bonus not firing, and all three row states.

### #4521 is not the only 87 — correction, Stage 4

An earlier draft of this brief said no generated shop reaches #4521's
combination. Under seed 4521 that is false. Three generated shops fire the same
30 + 25 + 22 + 10 and land on exactly 87:

  #4910 FPS Hargaon-36 (4 complaints) · #4219 FPS Laharpur-3 (3) ·
  #4458 FPS Mahmudabad-40 (3)

This is not a bug in the fixtures. The `transport` archetype in seed.py draws a
receipt variance in (-9.0, -5.2), a delivery gap in (49, 72) and a GPS deviation
in (2.1, 4.5) — all three thresholds — and 3 or more complaints then adds the
bonus. 87 is simply the ceiling of that archetype, and four of sixty shops
reaching it is realistic rather than embarrassing.

seed.py is NOT to be adjusted to remove them: random.seed(4521) is an invariant,
and changing the archetype bounds would move all 57 generated shops.

Ties are therefore broken in the ranked list, not in the score:

  ORDER BY score DESC, complaint_count DESC, coverage_pct DESC, case_id

Corroborating complaints first — among cases the rulebook scores equally, the
one the public has already complained about seven times is the one to send an
inspector to. Coverage second: between two equally-complained cases, prefer the
one we could evaluate more fully. #4521 has 7 complaints against 4, 3 and 3, so
it holds the top of the list on the tie-break rather than on a special case.

If asked on stage, the honest answer is "four shops hit 87; the demo case leads
because it has the most corroboration", not "only one shop can score 87".

## API contract — frozen at hour 2
GET  /api/cases?severity=&district=   ranked case list
GET  /api/cases/{case_id}             case + trace + linked complaints
GET  /api/shops/{shop_id}             shop profile + cycle history
GET  /api/rulebook                    parsed rules.yaml + version
GET  /api/audit/{case_id}             append-only event list
POST /api/cases/{case_id}/notes       inspector note, writes to audit log
POST /api/cases/{case_id}/recompute   re-derives from stored inputs

Canonical case-detail response: docs/contract/case_detail.json
Frontend builds against that static file until Stage 3.

## Audit events
CASE_OPENED · RULE_FIRED (one per fired rule) · COMPLAINT_LINKED ·
NOTE_ADDED · SCORE_RECOMPUTED

Recompute returns {stored, recomputed, identical} and writes a new row.
It never mutates an old one.

## Screens
Officer   ranked list, severity as left-border, sortable, filter by district
CaseDetail four-node reconciliation ladder · trace table (3 row states) ·
           coverage badge · linked complaints · plain-language memo · trend
Rulebook  rules.yaml rendered with version and updated_by
Inspector cases sorted by score, notes form
Auditor   event timeline + Recompute button

## Declared limitations
Stated proactively to judges as scoping decisions, not discovered as gaps:
1. Data is synthetic, generated under random.seed(4521)
2. Rule weights are back-solved for the demo case, not learned
3. Escalation is a stub — no email or SMS is sent
4. Roles are a dropdown, not authentication
5. Inspector routing is score-sorted, not geographically optimised
6. Memos are f-string templates — "template now, LLM later"
7. Headline statistics (28%, 1-in-5, 4-6 months, 5x) are illustrative
8. Card border tokens (border-strong #C7C2B6, border #DDD9D0) read below
   WCAG 1.4.11's 3:1 non-text contrast threshold against the cream
   background; interactive state is instead conveyed by full fill inversion
   on hover/focus, which clears contrast comfortably.
9. Coral text on the reconciliation ladder's located-hop labels (#D4573D on
   the cream background — the variance figures at 14px medium and the "gap
   located" label at 12px) reads 3.79:1, below WCAG AA's 4.5:1 threshold for
   text. Neither size qualifies as large text, so 4.5:1 is the applicable
   floor. This is a locked brand token; the finding is documented rather than
   silently patched. The label never carries colour alone — it is always read
   with its text.
10. Ink-muted text on skipped trace rows (#94989E on the sunk row ground
    #F3F0EA) reads 2.55:1, below WCAG AA. It reads 2.90:1 where ink-muted
    sits on a white card instead. Same status — locked token, documented
    rather than patched. A skipped row's meaning is carried by its "Skipped"
    text label, not by the muting.

## Out of scope
Deployment, auth, real data integration, mobile app, notifications,
multi-district scaling, ML model training, LLM anything.
```

### 1.3 `docs/design/REDESIGN-SPEC.md` (157 lines, verbatim)

```markdown
# LEAKPROOF — Redesign Spec

Reference: GOV.UK Design System (design-system.service.gov.uk) — chosen
because it is a real, published system built by a government team solving
the same problem this project has: presenting official, high-stakes data
so it reads as trustworthy and scannable, not decorative. Two of its rules
matter more than any specific pixel value and override everything else in
this document if they ever conflict: color is signal, never decoration;
and status is never shown by color alone — always color + a text label
together.

## What stays unchanged
The five brand colors locked in Stage 0 are NOT being replaced:
  bg      #FAF8F4
  navy    #132A47
  green   #2E7D5B
  gold    #C8952B
  coral   #D4573D
These are already muted and appropriate. This spec adds missing tokens
around them and tightens how they're used — it does not swap the palette.

## New tokens (additions, not replacements)

Text
  ink            #14171A   primary body text — NOT navy. Navy is reserved
                            for headings/brand elements, not paragraph text.
  ink-secondary  #5B6169   meta text, captions, timestamps, helper text
  ink-muted      #94989E   disabled/skipped-state text

Border
  border         #DDD9D0   warm-toned to sit on #FAF8F4, replaces any
                            cool-grey border currently in use
  border-strong  #C7C2B6   table rules, dividers that need more presence

Surface
  surface        #FFFFFF   cards, table body
  surface-sunk    #F3F0EA  code-like blocks, the skipped-row background
                            (already exists as bg-navy/5 — this just names
                            it properly instead of leaving it as an opacity
                            trick)

These are additive. Nothing currently using navy/green/gold/coral/bg needs
to change color — they need to stop being used for things ink/ink-secondary
should be doing instead (see rules below).

## Typography — real hierarchy, not just two fonts

Keep serif display (Fraunces/Source Serif) + Inter body. The gap right now
isn't the font choice, it's that too few sizes are actually in use. Lock
this scale:

  score-display   48px / 1.0    serif semibold   navy      (the 87 itself)
  page-title      28px / 1.2    serif semibold   navy
  section-heading 18px / 1.3    serif semibold   navy
  body            15px / 1.5    Inter regular    ink
  body-secondary  14px / 1.5    Inter regular    ink-secondary
  meta-label      12px / 1.4    Inter medium     ink-secondary
                                 uppercase, letter-spacing 0.04em
  table-header    12px / 1.4    Inter medium     ink-secondary
                                 uppercase, letter-spacing 0.04em
  table-cell      14px / 1.5    Inter regular    ink, tabular-nums

Rule: any text currently sitting at "body size, navy color" that ISN'T a
heading should drop to ink at body/body-secondary size. This is the single
biggest fix — navy-colored body text is what's currently flattening the
hierarchy, because heading-color and paragraph-color read as the same
weight of importance.

## Status / severity — tag pattern, not colored pills

This is the second biggest fix. Full-rounded, saturated color pills
("badge soup") are the most overused AI-dashboard tell. GOV.UK's tag
component is the corrective: a small RECTANGLE (2px radius, matching our
existing single radius token — do not introduce a second radius for tags),
tinted background at ~15% of the severity color, solid-color text in the
full-strength severity color, uppercase, sentence case content (not
ALL-CAPS blaring), and it always carries a text label — color is never
the only signal.

  severity-high    bg coral/15   text coral    "High"
  severity-medium  bg gold/15    text gold     "Medium"
  severity-low     bg green/15   text green    "Low"
  status-open      bg gold/15    text gold     "Open"
  status-closed    bg green/15   text green    "Closed"

Existing left-border-on-data-rows pattern (Officer list, trace table) is
CORRECT and stays — that's a different, also-valid pattern for indicating
severity on a full row. The tag component above is for compact inline
status (e.g. a status chip next to a case ID, or in a table cell that
isn't a full severity-colored row). Don't use both patterns on the same
element.

## Tables — real table discipline

Applies to: Officer list, Reasoning trace, Rulebook, Linked complaints,
Auditor timeline. All of these are structurally tables even where some are
currently rendered as stacked cards.

- Numeric columns (score, kg, %, weight) are right-aligned with
  tabular-nums. Currently some of these may be left-aligned — fix.
- Every table gets a real one-line caption above it stating what it shows
  in plain language — CaseDetail's "Every rule in the rulebook, what it
  read, and what it did about it" is already doing this correctly; extend
  the same pattern to Officer, Rulebook, and Auditor if not already there.
- Row density: 12-16px vertical padding per row for list/table views
  (Officer, trace, complaints, audit timeline) — tighter than a "hero
  card" but not cramped. This is what makes a page read as a real data
  product instead of a landing page with numbers on it — information
  density signals seriousness for this category of tool.
- Table headers are meta-label style (12px, uppercase, tracked,
  ink-secondary) — not the same size/weight as body text.

## What "professional, not AI-generated" means as a checklist

Before considering any page done, check it against this list:
  [ ] No text is navy EXCEPT headings and the score-display number
  [ ] No rounded-full badge/pill exists anywhere — tags are rectangular
  [ ] Every status/severity indicator has a text label, not just a color
  [ ] Numeric columns are right-aligned, tabular-nums
  [ ] Table headers are visually distinct (smaller, tracked, muted) from
      table cells
  [ ] Every table/list has a one-line caption explaining what it shows
  [ ] No gradients, no more than one shadow depth, no more than one
      border-radius token (tags included)
  [ ] No emoji; typographic marks only (— · … ✓ → ←)
  [ ] Focus rings visible on every interactive element

## Per-page application

Officer (list)
  Table with real caption ("60 shops, ranked by evidence"). Severity stays
  as left-border on the row (existing pattern, correct). Score column
  right-aligned tabular-nums. Case ID / shop name uses body-secondary
  weight, not navy.

Case Detail
  score-display for the 87 itself — this is the one place the huge serif
  navy number is earned. Everything else on the page (labels, meta,
  memo caption) drops to ink/ink-secondary. Ladder node captions
  ("FCI depot weighbridge") are body-secondary, not navy.

Rulebook
  Full table treatment: caption, meta-label headers, tabular-nums on
  threshold/weight columns, severity as the rectangular tag next to each
  rule's severity field (not the current colored left-border, since these
  rows aren't "cases" — they're config entries. Tag is more correct here).

Inspector
  List stays table-disciplined per above. The notes form gets ink-colored
  labels (not navy), border token on the textarea, and the same tag
  pattern if a note has a status.

Auditor
  Timeline as a real table/list: timestamp and actor in meta-label style,
  action in a small rectangular tag (not colored text), detail in body
  style. The identical/mismatch recompute result uses success-green/
  error-red exactly as GOV.UK reserves those two colors — nowhere else on
  this page should compete with that signal.
```

### 1.4 `docs/contract/fixtures.md` (58 lines, verbatim)

````markdown
# Fixtures — three shops that exercise everything

Copied verbatim from PROJECT-BRIEF.md. This file is the authority the pytest
suite asserts against: write the assertion here first, then the implementation.

```
                        #4521 Sitapur   #4102 Barabanki   #4788 Hargaon
archetype               transport       transport, no GPS  counter skim
allocated / dispatched  12,000 / 12,000 8,000 / 8,000      9,000 / 9,000
weighed                 11,015          7,512              8,970
dispensed               10,980          7,490              8,190
dispatch → receipt      -8.21%          -6.10%             -0.33%
receipt → counter       -0.32%          -0.29%             -8.70%
delivery gap            61 h            52 h               44 h
gps deviation           3.4 km          unavailable        0.8 km
txn_card_ratio          0.88            0.71               0.55
hour violations         1               1                  4
complaints in window    7               2                  6
fired rules             30 + 25 + 22    30 + 25            20 + 15 + 8
bonus                   +10             0 (below 3)        +10
SCORE                   87              55                 53
severity                HIGH            MEDIUM             MEDIUM
coverage_pct            100             83                 100
gap_hop                 dispatch_to_    dispatch_to_       receipt_to_
                        receipt         receipt            counter
```

Between them: gap localisation at two hops, a skipped rule, coverage
reduction, bonus firing, bonus not firing, and all three row states.

## How these land in the database

`seed.py` writes raw inputs only. Everything in the lower half of the table
above — variances, fired rules, bonus, score, severity, coverage_pct,
gap_hop — is derived by `engine/` at evaluation time and is not precomputed
anywhere.

The raw inputs seed hardcodes for these three shops:

| Input | Stored as | #4521 | #4102 | #4788 |
| --- | --- | --- | --- | --- |
| allocated / dispatched / weighed / dispensed | `cycles` (period `2026-08`) | 12000 / 12000 / 11015 / 10980 | 8000 / 8000 / 7512 / 7490 | 9000 / 9000 / 8970 / 8190 |
| delivery gap | `deliveries.arrival_ts − dispatch_ts` | 61 h | 52 h | 44 h |
| gps deviation | `deliveries.gps_deviation_km` / `gps_available` | 3.4, available | null, **unavailable** | 0.8, available |
| txn_card_ratio | distinct `transactions.card_id` ÷ `shops.ration_cards` | 1056 / 1200 | 639 / 900 | 550 / 1000 |
| hour violations | `cycles.hour_violations_month` | 1 | 1 | 4 |
| complaints in window | `complaints.filed_at` within 14 days of case open | 7 | 2 | 6 |

Case open time, and the anchor every complaint window is measured back from,
is `2026-08-14T09:12:00`.

#4521 also carries 2 complaints older than the window and #4102 carries 1.
They are there so a broken window check fails a test instead of passing
quietly.

The other 57 shops are generated. They may fire one or two rules, but no
generated shop is built to reach #4521's combination — the ranked list opens
on the demo case.
````

**Factual note on 1.4:** the final paragraph of `fixtures.md` ("no generated
shop is built to reach #4521's combination") is contradicted by
`PROJECT-BRIEF.md`'s own Stage-4 correction and by the committed database:
four shops score 87 (`4521`, `4910`, `4219`, `4458`). `fixtures.md` was not
updated when the brief was.

---

## 2. Data model

### 2.1 `backend/app/models.py` (283 lines, verbatim)

```python
"""The nine LEAKPROOF tables.

Column notes worth keeping in mind while reading:

* Raw inputs are stored; derived numbers are not. Variances, gap_hop,
  coverage_pct and score are produced by engine/ at evaluation time and only
  persisted on `cases` / `rule_hits` once a case has actually been opened.
  Nothing in seed.py precomputes them — one derivation path, one truth.
* "Unavailable" is modelled explicitly (gps_available, nullable weighed_kg /
  dispensed_kg) rather than as a zero or a magic number. F5 depends on being
  able to tell "we could not check" apart from "we checked and it was fine".
* audit_log is append-only. Nothing in this file, or anywhere else, may offer
  an update or delete path for it.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Shop(Base):
    """A fair-price shop (FPS). The unit an officer inspects."""

    __tablename__ = "shops"

    # Real FPS codes are strings, not counters — #4521 stays "4521".
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    block: Mapped[str] = mapped_column(String(80), nullable=False)
    district: Mapped[str] = mapped_column(String(80), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)

    # Denominator of txn_card_ratio: cards attached to this shop.
    ration_cards: Mapped[int] = mapped_column(Integer, nullable=False)

    # Licensed counter hours, used to judge hour_violations_month.
    opens_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=9)
    closes_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=17)

    dealer_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cycles: Mapped[list["Cycle"]] = relationship(back_populates="shop")
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="shop")
    cases: Mapped[list["Case"]] = relationship(back_populates="shop")


class Cycle(Base):
    """One monthly allocation cycle for one shop — the four-hop ladder.

    allocated_kg -> dispatched_kg -> weighed_kg -> dispensed_kg
    """

    __tablename__ = "cycles"
    __table_args__ = (UniqueConstraint("shop_id", "period", name="uq_cycle_shop_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)

    # "2026-08" — the allocation month this cycle belongs to.
    period: Mapped[str] = mapped_column(String(7), nullable=False)

    # Hop 1: government allocation order.
    allocated_kg: Mapped[float] = mapped_column(Float, nullable=False)
    # Hop 2: FCI depot weighbridge at dispatch.
    dispatched_kg: Mapped[float] = mapped_column(Float, nullable=False)
    # Hop 3: shop-side weighing scale at receipt. Nullable — a scale can be
    # offline, and that must degrade coverage rather than read as zero.
    weighed_kg: Mapped[float | None] = mapped_column(Float)
    # Hop 4: sum of ePoS counter dispensing. Nullable for the same reason.
    dispensed_kg: Mapped[float | None] = mapped_column(Float)

    # Counter sessions opened outside licensed hours during this cycle.
    hour_violations_month: Mapped[int | None] = mapped_column(Integer)

    opened_on: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_on: Mapped[datetime | None] = mapped_column(DateTime)

    shop: Mapped["Shop"] = relationship(back_populates="cycles")
    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="cycle")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="cycle")
    cases: Mapped[list["Case"]] = relationship(back_populates="cycle")


class Delivery(Base):
    """The transport leg: depot dispatch to shop arrival, with GPS."""

    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)

    vehicle_no: Mapped[str] = mapped_column(String(24), nullable=False)
    route_id: Mapped[str] = mapped_column(String(24), nullable=False)

    # delivery_gap_hours = arrival_ts - dispatch_ts. arrival_ts is nullable:
    # a consignment can be in transit or its arrival scan can be missing.
    dispatch_ts: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    arrival_ts: Mapped[datetime | None] = mapped_column(DateTime)

    # Max distance between the vehicle track and its registered route.
    gps_deviation_km: Mapped[float | None] = mapped_column(Float)
    # False when the vehicle has no working GPS unit fitted. Keeps "no device"
    # distinguishable from "device reported 0.0 km deviation".
    gps_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    cycle: Mapped["Cycle"] = relationship(back_populates="deliveries")


class Transaction(Base):
    """One beneficiary collection at the ePoS counter."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)

    # Distinct card_id count over shop.ration_cards gives txn_card_ratio.
    card_id: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    txn_ts: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)

    # ePoS auth mode, kept because a spike in manual overrides is the kind of
    # signal a later rule would want.
    auth_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="biometric")
    # True when the sale happened outside the shop's licensed hours.
    outside_hours: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    cycle: Mapped["Cycle"] = relationship(back_populates="transactions")


class Complaint(Base):
    """A public grievance filed against a shop. Feeds the F4 bonus."""

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)

    filed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # portal | helpline | walk_in
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")

    # Set by engine/complaints.py when a complaint falls inside a case window.
    # Null means unlinked, not unexamined.
    linked_case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.id"), index=True)

    shop: Mapped["Shop"] = relationship(back_populates="complaints")


class Case(Base):
    """A scored, openable case. One cycle of one shop, evaluated once."""

    __tablename__ = "cases"

    # Human-facing identifier printed on the case sheet: "C-0041".
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), nullable=False, index=True)

    # Rule weights sum to 120 and the bonus adds 10; this is the DISPLAY score,
    # capped at 100. Do not renormalise the weights to make the cap disappear.
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)  # HIGH | MEDIUM | LOW
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="OPEN")
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Worst hop from locate_gap(): dispatch_to_receipt | receipt_to_counter |
    # allocation_to_dispatch.
    gap_hop: Mapped[str | None] = mapped_column(String(32))
    # Share of rules we were able to evaluate (rule-count based, not
    # weight-based). Skipped rules pull this down; they never count as passed.
    coverage_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Which rulebook produced this score — a case must stay re-derivable after
    # the rulebook moves on.
    rulebook_version: Mapped[str] = mapped_column(String(16), nullable=False)

    complaint_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    complaint_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    complaint_contribution: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Badge only. Contributes ZERO to score, by design.
    z_score: Mapped[float | None] = mapped_column(Float)
    z_confirms: Mapped[bool | None] = mapped_column(Boolean)

    # Plain-language summary from engine/memo.py. An f-string template, not an
    # LLM, and never to be described as one.
    memo: Mapped[str | None] = mapped_column(Text)

    shop: Mapped["Shop"] = relationship(back_populates="cases")
    cycle: Mapped["Cycle"] = relationship(back_populates="cases")
    rule_hits: Mapped[list["RuleHit"]] = relationship(back_populates="case")


class RuleHit(Base):
    """One row of the reasoning trace: what we checked and what happened."""

    __tablename__ = "rule_hits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)

    rule_id: Mapped[str] = mapped_column(String(48), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)

    # Stored as display strings ("-8.21%", "61 hrs") so the trace an auditor
    # reads months later is the trace we rendered on the day, units included.
    raw_value: Mapped[str | None] = mapped_column(String(48))
    threshold: Mapped[str] = mapped_column(String(48), nullable=False)

    contribution: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)  # high | medium | low
    # fired | passed | skipped. "skipped" means the input was unavailable.
    status: Mapped[str] = mapped_column(String(8), nullable=False)

    case: Mapped["Case"] = relationship(back_populates="rule_hits")


class AuditLog(Base):
    """Append-only event trail. Insert only — never UPDATE, never DELETE.

    Events: CASE_OPENED, RULE_FIRED, COMPLAINT_LINKED, NOTE_ADDED,
    SCORE_RECOMPUTED. A recompute writes a new row; it does not touch old ones.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # Who acted, from the role dropdown: officer | inspector | auditor | system.
    actor_role: Mapped[str] = mapped_column(String(16), nullable=False, default="system")
    # JSON-encoded event body, kept as text so an old row stays readable even
    # if the payload shape of that event type later changes.
    payload: Mapped[str | None] = mapped_column(Text)
    # Rulebook in force when the event was written, for re-derivation.
    rulebook_version: Mapped[str | None] = mapped_column(String(16))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )


class RulebookVersion(Base):
    """A snapshot of rules.yaml as loaded, so a score can be re-derived.

    The YAML file on disk is the runtime source of truth; this table records
    which text was in force when, and is written on load when the version or
    checksum is new.
    """

    __tablename__ = "rulebook_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    updated_by: Mapped[str] = mapped_column(String(120), nullable=False)

    # Full YAML text plus its sha256, so "same version, edited file" is
    # detectable rather than silently accepted.
    yaml_text: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    loaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

### 2.2 Table-by-table breakdown

Nine tables. Column type / nullability / default taken from the model
declarations; indexes confirmed by reading `sqlite_master` in the committed
database.

#### `shops` — class `Shop`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | String(16) | no | — | **PK**. String, not int ("4521") |
| name | String(120) | no | — | e.g. "FPS Sitapur-12" |
| block | String(80) | no | — | what the UI filter labels "District" |
| district | String(80) | no | — | what the API `district` query param filters on |
| lat | Float | no | — | |
| lng | Float | no | — | |
| ration_cards | Integer | no | — | denominator of `txn_card_ratio` |
| opens_hour | Integer | no | 9 | never read by the engine |
| closes_hour | Integer | no | 17 | never read by the engine |
| dealer_name | String(120) | yes | None | never read by the engine or UI |
| created_at | DateTime | yes (no `nullable=False`) | `datetime.utcnow` | |

Indexes: `sqlite_autoindex_shops_1` (PK only). No outgoing FKs.
Relationships: `cycles` (1-N), `complaints` (1-N), `cases` (1-N).

#### `cycles` — class `Cycle`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | Integer | no | autoincrement | **PK** |
| shop_id | String | no | — | **FK → shops.id**, indexed |
| period | String(7) | no | — | "2026-08" |
| allocated_kg | Float | no | — | ladder hop 1 |
| dispatched_kg | Float | no | — | ladder hop 2 |
| weighed_kg | Float | **yes** | None | ladder hop 3; null = scale offline |
| dispensed_kg | Float | **yes** | None | ladder hop 4; null = ePoS unavailable |
| hour_violations_month | Integer | yes | None | |
| opened_on | DateTime | no | — | |
| closed_on | DateTime | yes | None | |

Constraint: `UniqueConstraint("shop_id", "period")` named `uq_cycle_shop_period`.
Indexes: `ix_cycles_shop_id`, `sqlite_autoindex_cycles_1` (the unique constraint).
Relationships: `shop` (N-1), `deliveries` (1-N), `transactions` (1-N), `cases` (1-N).

#### `deliveries` — class `Delivery`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | Integer | no | autoincrement | **PK** |
| cycle_id | Integer | no | — | **FK → cycles.id**, indexed |
| shop_id | String | no | — | **FK → shops.id**, indexed (denormalised) |
| vehicle_no | String(24) | no | — | never read by the engine |
| route_id | String(24) | no | — | never read by the engine |
| dispatch_ts | DateTime | no | — | |
| arrival_ts | DateTime | **yes** | None | null = in transit / scan missing |
| gps_deviation_km | Float | **yes** | None | |
| gps_available | Boolean | no | True | gates the reading; "no device" ≠ "0.0 km" |

Indexes: `ix_deliveries_cycle_id`, `ix_deliveries_shop_id`.
Relationship: `cycle` (N-1). No ORM link back to `Shop`.

#### `transactions` — class `Transaction`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | Integer | no | autoincrement | **PK** |
| cycle_id | Integer | no | — | **FK → cycles.id**, indexed |
| shop_id | String | no | — | **FK → shops.id**, indexed |
| card_id | String(24) | no | — | indexed; DISTINCT count drives `txn_card_ratio` |
| txn_ts | DateTime | no | — | never read by the engine |
| quantity_kg | Float | no | — | never read by the engine |
| auth_mode | String(16) | no | "biometric" | never read by the engine |
| outside_hours | Boolean | no | False | never read by the engine |

Indexes: `ix_transactions_card_id`, `ix_transactions_cycle_id`, `ix_transactions_shop_id`.
Relationship: `cycle` (N-1).

#### `complaints` — class `Complaint`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | Integer | no | autoincrement | **PK** |
| shop_id | String | no | — | **FK → shops.id**, indexed |
| filed_at | DateTime | no | — | indexed; the 14-day window applies to this |
| source | String(32) | no | — | portal / helpline / walk_in |
| category | String(48) | no | — | six values, see §3 |
| text | Text | no | — | |
| status | String(16) | no | "open" | open / closed |
| linked_case_id | String | **yes** | None | **FK → cases.id**, indexed. Null = unlinked |

Indexes: `ix_complaints_filed_at`, `ix_complaints_linked_case_id`, `ix_complaints_shop_id`.
Relationship: `shop` (N-1). The FK to `cases` makes a
`complaints → cases → shops` loop at the schema level.

#### `cases` — class `Case`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | String(16) | no | — | **PK**, "C-0041" |
| shop_id | String | no | — | **FK → shops.id**, indexed |
| cycle_id | Integer | no | — | **FK → cycles.id**, indexed |
| score | Integer | no | — | DISPLAY score, capped at 100 |
| severity | String(8) | no | — | HIGH / MEDIUM / LOW |
| status | String(16) | no | "OPEN" | only ever written as "OPEN" |
| opened_at | DateTime | no | — | always the seed ANCHOR |
| gap_hop | String(32) | yes | None | |
| coverage_pct | Integer | no | 100 | |
| rulebook_version | String(16) | no | — | |
| complaint_count | Integer | no | 0 | |
| complaint_window_days | Integer | no | 14 | |
| complaint_contribution | Integer | no | 0 | |
| z_score | Float | yes | None | badge only |
| z_confirms | Boolean | yes | None | badge only |
| memo | Text | yes | None | |

`score_raw` is **NOT** persisted. `engine/score.py` returns it; the router drops
it. The uncapped total exists only in memory.

Indexes: `ix_cases_cycle_id`, `ix_cases_shop_id`, `sqlite_autoindex_cases_1`.
Relationships: `shop` (N-1), `cycle` (N-1), `rule_hits` (1-N).

#### `rule_hits` — class `RuleHit`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | Integer | no | autoincrement | **PK** |
| case_id | String | no | — | **FK → cases.id**, indexed |
| rule_id | String(48) | no | — | matches a `rules.yaml` `id` |
| label | String(160) | no | — | copied from YAML at evaluation time |
| raw_value | String(48) | **yes** | None | display string with unit; null iff skipped |
| threshold | String(48) | no | — | display string with unit |
| contribution | Integer | no | 0 | |
| severity | String(8) | no | — | lower-case high / medium / low |
| status | String(8) | no | — | fired / passed / skipped |

Index: `ix_rule_hits_case_id`. Relationship: `case` (N-1).

#### `audit_log` — class `AuditLog`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | Integer | no | autoincrement | **PK** |
| case_id | String | no | — | **FK → cases.id**, indexed |
| event_type | String(32) | no | — | five values |
| actor_role | String(16) | no | "system" | officer / inspector / auditor / system |
| payload | Text | yes | None | JSON-encoded string |
| rulebook_version | String(16) | yes | None | |
| created_at | DateTime | no | `datetime.utcnow` | indexed |

Indexes: `ix_audit_log_case_id`, `ix_audit_log_created_at`.
No ORM relationships declared in either direction.

#### `rulebook_versions` — class `RulebookVersion`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | Integer | no | autoincrement | **PK** |
| version | String(16) | no | — | indexed |
| updated_by | String(120) | no | — | |
| yaml_text | Text | no | — | full file text |
| checksum | String(64) | no | — | sha256 hex of the YAML text |
| loaded_at | DateTime | no | `datetime.utcnow` | |
| is_active | Boolean | no | True | never toggled anywhere |

Index: `ix_rulebook_versions_version`. No FKs, no relationships.
**Nothing under `app/` ever reads this table** — it is written by `seed.py` only.

### 2.3 Real-world entity map and cardinality

| Table | Real-world entity |
|---|---|
| `shops` | A fair-price shop (FPS) — the inspected unit |
| `cycles` | One monthly foodgrain allocation for one shop; holds the 4-rung ladder |
| `deliveries` | The transport leg of one cycle (vehicle, route, GPS, timestamps) |
| `transactions` | One beneficiary collection at the ePoS counter |
| `complaints` | A public grievance filed against a shop |
| `cases` | A scored, openable investigation of one shop-cycle |
| `rule_hits` | One row of the reasoning trace for one case |
| `audit_log` | One immutable event in a case's history |
| `rulebook_versions` | A snapshot of the rules.yaml text in force |

Cardinalities as declared:

```
shops  1 ── N  cycles         (unique per shop+period)
shops  1 ── N  complaints
shops  1 ── N  cases
shops  1 ── N  deliveries     (FK exists, no ORM relationship declared)
shops  1 ── N  transactions   (FK exists, no ORM relationship declared)
cycles 1 ── N  deliveries     (in practice exactly 1 per cycle)
cycles 1 ── N  transactions
cycles 1 ── N  cases          (in practice exactly 1, for period 2026-08)
cases  1 ── N  rule_hits      (exactly len(rules.yaml.rules) = 6)
cases  1 ── N  audit_log
cases  1 ── N  complaints     (via complaints.linked_case_id, optional)
rulebook_versions             standalone, no relationships
```

There are **no N-N relationships anywhere** and no association tables.
`complaints ↔ cases` is the only optional/nullable link.

---

## 3. Seed data

### 3.1 `backend/seed.py` (546 lines, verbatim)

```python
"""Synthetic data for LEAKPROOF. 60 shops: 3 fixtures + 57 generated.

Run:  python seed.py      (from backend/)

The data is synthetic. That is a declared scoping decision, not a gap — see
"Declared limitations" in PROJECT-BRIEF.md.

Two rules govern this file:

1. random.seed(4521) is set once, before any generation. Never remove it and
   never change it. Everything downstream — the demo, the fixture assertions,
   the screenshots in the deck — assumes this exact stream.
2. Seed writes RAW INPUTS ONLY. Variances, gap_hop, coverage_pct, scores and
   traces are derived by engine/ at evaluation time, so cases, rule_hits and
   audit_log are left empty here. Precomputing them would give the project two
   derivation paths that could disagree, which is precisely the failure mode
   the audit trail exists to rule out.

Scoping decisions inside this file, kept explicit:
  * Transactions are written for the scored cycle (2026-08) only. Earlier
    cycles carry ladder readings for the trend chart but no per-card rows.
  * Generated shops are held below the fixture archetypes in severity, so the
    demo case (#4521) stays top of the ranked list.
"""

import hashlib
import random
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from app.db import Base, SessionLocal, engine
from app.models import (
    Complaint,
    Cycle,
    Delivery,
    RulebookVersion,
    Shop,
    Transaction,
)

# Set before any generation. Do not move, do not change. See docstring.
random.seed(4521)

# The demo is frozen to a moment in time: this is when case C-0041 opens, and
# every complaint window is measured backwards from here.
ANCHOR = datetime(2026, 8, 14, 9, 12, 0)
SCORED_PERIOD = "2026-08"
HISTORY_PERIODS = ["2026-06", "2026-07"]
PERIOD_START = {
    "2026-06": datetime(2026, 6, 1),
    "2026-07": datetime(2026, 7, 1),
    "2026-08": datetime(2026, 8, 1),
}

RULES_PATH = Path(__file__).resolve().parent / "app" / "rules.yaml"

BLOCKS = {
    "Sitapur": [
        "Sitapur",
        "Biswan",
        "Misrikh",
        "Laharpur",
        "Mahmudabad",
        "Sidhauli",
        "Hargaon",
        "Maholi",
    ],
    "Barabanki": ["Barabanki", "Fatehpur", "Ramnagar", "Dewa", "Haidergarh"],
}

COMPLAINT_SOURCES = ["portal", "helpline", "walk_in"]
COMPLAINT_CATEGORIES = [
    "short_weight",
    "shop_closed",
    "overcharging",
    "quality",
    "epos_failure",
    "refused_entitlement",
]
COMPLAINT_TEXTS = {
    "short_weight": "Received less than the entitled quantity; dealer refused to re-weigh.",
    "shop_closed": "Shop found closed during notified distribution hours.",
    "overcharging": "Dealer charged above the notified issue price.",
    "quality": "Grain issued was of poor quality and partly spoiled.",
    "epos_failure": "ePoS machine reported failure but the entitlement was marked issued.",
    "refused_entitlement": "Entitlement refused despite a valid ration card.",
}

DEALER_FIRST = ["Ram", "Shyam", "Anil", "Sunita", "Kamla", "Rakesh", "Vinod", "Meena", "Suresh"]
DEALER_LAST = ["Verma", "Singh", "Yadav", "Gupta", "Mishra", "Pandey", "Sharma", "Rastogi"]


# ---------------------------------------------------------------------------
# Fixture shops — hardcoded to docs/contract/fixtures.md. Do not "improve".
# ---------------------------------------------------------------------------

# ration_cards is chosen so that txn_card_ratio lands exactly on the fixture
# value with a whole number of transacting cards (e.g. 0.88 * 1200 = 1056).
FIXTURES = [
    {
        "id": "4521",
        "name": "FPS Sitapur-12",
        "block": "Sitapur",
        "district": "Sitapur",
        "lat": 27.57,
        "lng": 80.68,
        "ration_cards": 1200,
        "dealer_name": "Ram Verma",
        "allocated_kg": 12000.0,
        "dispatched_kg": 12000.0,
        "weighed_kg": 11015.0,  # -8.21% against dispatch
        "dispensed_kg": 10980.0,  # -0.32% against receipt
        "delivery_gap_hours": 61,
        "gps_deviation_km": 3.4,
        "gps_available": True,
        "txn_card_ratio": 0.88,
        "hour_violations_month": 1,
        "complaints_in_window": 7,
        "complaints_outside_window": 2,  # proves the 14-day window is applied
    },
    {
        "id": "4102",
        "name": "FPS Barabanki-7",
        "block": "Barabanki",
        "district": "Barabanki",
        "lat": 26.93,
        "lng": 81.19,
        "ration_cards": 900,
        "dealer_name": "Sunita Singh",
        "allocated_kg": 8000.0,
        "dispatched_kg": 8000.0,
        "weighed_kg": 7512.0,  # -6.10%
        "dispensed_kg": 7490.0,  # -0.29%
        "delivery_gap_hours": 52,
        "gps_deviation_km": None,  # no GPS unit fitted -> gps_deviation skipped
        "gps_available": False,
        "txn_card_ratio": 0.71,
        "hour_violations_month": 1,
        "complaints_in_window": 2,  # below min_complaints, bonus must not fire
        "complaints_outside_window": 1,
    },
    {
        "id": "4788",
        "name": "FPS Hargaon-3",
        "block": "Hargaon",
        "district": "Sitapur",
        "lat": 27.65,
        "lng": 80.55,
        "ration_cards": 1000,
        "dealer_name": "Rakesh Yadav",
        "allocated_kg": 9000.0,
        "dispatched_kg": 9000.0,
        "weighed_kg": 8970.0,  # -0.33%
        "dispensed_kg": 8190.0,  # -8.70%, counter skim
        "delivery_gap_hours": 44,
        "gps_deviation_km": 0.8,
        "gps_available": True,
        "txn_card_ratio": 0.55,
        "hour_violations_month": 4,
        "complaints_in_window": 6,
        "complaints_outside_window": 0,
    },
]


def make_generated_shops(count: int) -> list[dict]:
    """57 shops with plausible values across four archetypes.

    Kept deliberately below the fixture archetypes: a generated shop may fire
    one or two rules, but the combination that produces #4521's 87 is reserved
    for the fixture so the ranked list opens on the demo case.
    """
    taken_ids = {f["id"] for f in FIXTURES}
    used_names: set[str] = set()
    shops: list[dict] = []

    for _ in range(count):
        shop_id = str(random.randint(4000, 4999))
        while shop_id in taken_ids:
            shop_id = str(random.randint(4000, 4999))
        taken_ids.add(shop_id)

        district = random.choice(["Sitapur", "Sitapur", "Barabanki"])
        block = random.choice(BLOCKS[district])
        name = f"FPS {block}-{random.randint(1, 40)}"
        while name in used_names:
            name = f"FPS {block}-{random.randint(1, 40)}"
        used_names.add(name)

        # Sitapur sits around 27.57N 80.68E; Barabanki around 26.93N 81.19E.
        base_lat, base_lng = (27.57, 80.68) if district == "Sitapur" else (26.93, 81.19)

        ration_cards = random.randrange(400, 1600, 50)
        allocated = float(random.randrange(4000, 14000, 500))

        # Paper diversion at the depot is rare; dispatch usually matches the
        # allocation order exactly.
        dispatched = allocated if random.random() > 0.10 else allocated - random.randrange(50, 300, 25)

        archetype = random.choices(
            ["clean", "transport", "counter", "sloppy"],
            weights=[62, 14, 14, 10],
        )[0]

        if archetype == "transport":
            receipt_pct = random.uniform(-9.0, -5.2)
            counter_pct = random.uniform(-0.6, -0.05)
            gap_hours = random.randint(49, 72)
            gps_km = round(random.uniform(2.1, 4.5), 1)
        elif archetype == "counter":
            receipt_pct = random.uniform(-1.0, -0.05)
            counter_pct = random.uniform(-9.5, -5.2)
            gap_hours = random.randint(18, 47)
            gps_km = round(random.uniform(0.1, 1.8), 1)
        elif archetype == "sloppy":
            # Nothing leaks; the shop is just badly run. Exercises the low-
            # severity rules without inflating the score.
            receipt_pct = random.uniform(-1.5, -0.1)
            counter_pct = random.uniform(-1.5, -0.1)
            gap_hours = random.randint(20, 47)
            gps_km = round(random.uniform(0.1, 1.9), 1)
        else:
            receipt_pct = random.uniform(-0.9, 0.2)
            counter_pct = random.uniform(-0.9, 0.1)
            gap_hours = random.randint(8, 44)
            gps_km = round(random.uniform(0.0, 1.6), 1)

        weighed = round(dispatched * (1 + receipt_pct / 100), 1)
        dispensed = round(weighed * (1 + counter_pct / 100), 1)

        # F5 coverage: a scale that failed to report, and vehicles with no GPS
        # unit. Both must degrade coverage rather than read as compliant.
        scale_offline = random.random() < 0.05
        gps_available = random.random() > 0.12

        if archetype == "sloppy":
            hour_violations = random.randint(3, 7)
            txn_ratio = round(random.uniform(0.45, 0.62), 2)
        else:
            hour_violations = random.randint(0, 2)
            txn_ratio = round(random.uniform(0.62, 0.96), 2)

        if archetype == "clean":
            complaints_in = random.randint(0, 2)
        else:
            complaints_in = random.randint(1, 5)

        shops.append(
            {
                "id": shop_id,
                "name": name,
                "block": block,
                "district": district,
                "lat": round(base_lat + random.uniform(-0.35, 0.35), 4),
                "lng": round(base_lng + random.uniform(-0.35, 0.35), 4),
                "ration_cards": ration_cards,
                "dealer_name": f"{random.choice(DEALER_FIRST)} {random.choice(DEALER_LAST)}",
                "allocated_kg": allocated,
                "dispatched_kg": float(dispatched),
                "weighed_kg": None if scale_offline else weighed,
                "dispensed_kg": None if scale_offline else dispensed,
                "delivery_gap_hours": gap_hours,
                "gps_deviation_km": gps_km if gps_available else None,
                "gps_available": gps_available,
                "txn_card_ratio": txn_ratio,
                "hour_violations_month": hour_violations,
                "complaints_in_window": complaints_in,
                "complaints_outside_window": random.randint(0, 2),
            }
        )

    return shops


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def write_shop(db, spec: dict) -> Shop:
    opens_hour = 9
    closes_hour = 17
    shop = Shop(
        id=spec["id"],
        name=spec["name"],
        block=spec["block"],
        district=spec["district"],
        lat=spec["lat"],
        lng=spec["lng"],
        ration_cards=spec["ration_cards"],
        opens_hour=opens_hour,
        closes_hour=closes_hour,
        dealer_name=spec["dealer_name"],
        created_at=datetime(2024, 4, 1),
    )
    db.add(shop)
    return shop


def write_scored_cycle(db, spec: dict) -> Cycle:
    """The 2026-08 cycle — the one the engine will score."""
    start = PERIOD_START[SCORED_PERIOD]
    cycle = Cycle(
        shop_id=spec["id"],
        period=SCORED_PERIOD,
        allocated_kg=spec["allocated_kg"],
        dispatched_kg=spec["dispatched_kg"],
        weighed_kg=spec["weighed_kg"],
        dispensed_kg=spec["dispensed_kg"],
        hour_violations_month=spec["hour_violations_month"],
        opened_on=start,
        closed_on=start + timedelta(days=27),
    )
    db.add(cycle)
    db.flush()  # need cycle.id for deliveries and transactions
    return cycle


def write_history_cycles(db, spec: dict) -> None:
    """Two prior cycles so the CaseDetail trend chart has something to plot.

    Prior months run close to clean for every shop — the demo narrative is a
    shop that has just started leaking, not one that always has.
    """
    for period in HISTORY_PERIODS:
        start = PERIOD_START[period]
        allocated = spec["allocated_kg"]
        weighed = round(allocated * (1 + random.uniform(-1.2, -0.05) / 100), 1)
        dispensed = round(weighed * (1 + random.uniform(-1.0, -0.05) / 100), 1)
        cycle = Cycle(
            shop_id=spec["id"],
            period=period,
            allocated_kg=allocated,
            dispatched_kg=allocated,
            weighed_kg=weighed,
            dispensed_kg=dispensed,
            hour_violations_month=random.randint(0, 2),
            opened_on=start,
            closed_on=start + timedelta(days=27),
        )
        db.add(cycle)
        db.flush()

        dispatch_ts = start + timedelta(days=4, hours=6)
        db.add(
            Delivery(
                cycle_id=cycle.id,
                shop_id=spec["id"],
                vehicle_no=vehicle_no(),
                route_id=f"R-{spec['block'][:3].upper()}-{random.randint(1, 9)}",
                dispatch_ts=dispatch_ts,
                arrival_ts=dispatch_ts + timedelta(hours=random.randint(10, 40)),
                gps_deviation_km=round(random.uniform(0.0, 1.5), 1),
                gps_available=True,
            )
        )


def write_delivery(db, spec: dict, cycle: Cycle) -> None:
    """The transport leg for the scored cycle.

    delivery_gap_hours is not stored as a number: it is arrival_ts minus
    dispatch_ts, so the trace can quote the two timestamps an officer would
    check against the consignment note.
    """
    dispatch_ts = PERIOD_START[SCORED_PERIOD] + timedelta(days=4, hours=6)
    db.add(
        Delivery(
            cycle_id=cycle.id,
            shop_id=spec["id"],
            vehicle_no=vehicle_no(),
            route_id=f"R-{spec['block'][:3].upper()}-{random.randint(1, 9)}",
            dispatch_ts=dispatch_ts,
            arrival_ts=dispatch_ts + timedelta(hours=spec["delivery_gap_hours"]),
            gps_deviation_km=spec["gps_deviation_km"],
            gps_available=spec["gps_available"],
        )
    )


def write_transactions(db, spec: dict, cycle: Cycle) -> int:
    """One collection per transacting card, for the scored cycle only.

    Distinct card count over shop.ration_cards is txn_card_ratio, so the count
    is derived from the target ratio rather than stored as a number.
    Quantities sum to exactly dispensed_kg — the ladder's fourth rung is the
    sum of what crossed the counter, and the two must not drift apart.
    """
    dispensed = cycle.dispensed_kg
    if dispensed is None:
        # ePoS data unavailable for this cycle: no rows, and the counter rules
        # will be skipped rather than passed.
        return 0

    n_txn = int(round(spec["txn_card_ratio"] * spec["ration_cards"]))
    if n_txn <= 0:
        return 0

    per_txn = round(dispensed / n_txn, 3)
    start = PERIOD_START[SCORED_PERIOD]
    outside_hours_left = spec["hour_violations_month"]

    rows = []
    running = 0.0
    for i in range(n_txn):
        # Last row absorbs the rounding remainder so the total is exact.
        qty = per_txn if i < n_txn - 1 else round(dispensed - running, 3)
        running = round(running + qty, 3)

        outside = outside_hours_left > 0 and random.random() < 0.02
        if outside:
            outside_hours_left -= 1
            hour = random.choice([6, 7, 8, 18, 19, 20])
        else:
            hour = random.randint(9, 16)

        rows.append(
            {
                "cycle_id": cycle.id,
                "shop_id": spec["id"],
                "card_id": f"UP{spec['id']}{i:05d}",
                "txn_ts": start
                + timedelta(days=random.randint(1, 25), hours=hour, minutes=random.randint(0, 59)),
                "quantity_kg": qty,
                "auth_mode": random.choices(
                    ["biometric", "otp", "manual_override"], weights=[88, 9, 3]
                )[0],
                "outside_hours": outside,
            }
        )

    db.bulk_insert_mappings(Transaction, rows)
    return len(rows)


def write_complaints(db, spec: dict) -> int:
    """Grievances against the shop.

    Complaints inside the 14-day window before ANCHOR are what F4 can count.
    Some shops also carry older complaints: they exist to prove the window is
    actually applied, not decorative.
    """
    rows = []
    for _ in range(spec["complaints_in_window"]):
        filed_at = ANCHOR - timedelta(
            days=random.randint(0, 13), hours=random.randint(0, 23), minutes=random.randint(0, 59)
        )
        rows.append(complaint_row(spec["id"], filed_at))

    for _ in range(spec["complaints_outside_window"]):
        filed_at = ANCHOR - timedelta(days=random.randint(20, 90), hours=random.randint(0, 23))
        rows.append(complaint_row(spec["id"], filed_at))

    for row in rows:
        db.add(Complaint(**row))
    return len(rows)


def complaint_row(shop_id: str, filed_at: datetime) -> dict:
    category = random.choice(COMPLAINT_CATEGORIES)
    return {
        "shop_id": shop_id,
        "filed_at": filed_at,
        "source": random.choice(COMPLAINT_SOURCES),
        "category": category,
        "text": COMPLAINT_TEXTS[category],
        "status": random.choices(["open", "closed"], weights=[70, 30])[0],
        "linked_case_id": None,  # engine/complaints.py links these, not seed
    }


def vehicle_no() -> str:
    return f"UP{random.randint(30, 42)}{random.choice('ABCDEFGHJK')}{random.randint(1000, 9999)}"


def write_rulebook_version(db) -> str:
    """Record the rulebook text in force at seed time.

    The YAML file stays the runtime source of truth; this row exists so a
    score can be re-derived against the exact text that produced it.
    """
    yaml_text = RULES_PATH.read_text(encoding="utf-8")
    parsed = yaml.safe_load(yaml_text)
    db.add(
        RulebookVersion(
            version=parsed["version"],
            updated_by=parsed["updated_by"],
            yaml_text=yaml_text,
            checksum=hashlib.sha256(yaml_text.encode("utf-8")).hexdigest(),
            loaded_at=ANCHOR - timedelta(days=30),
            is_active=True,
        )
    )
    return parsed["version"]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def seed() -> None:
    # A rerun rebuilds the file from scratch: same seed, same 60 shops.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    specs = FIXTURES + make_generated_shops(57)

    db = SessionLocal()
    try:
        version = write_rulebook_version(db)

        n_txn = 0
        n_complaints = 0
        for spec in specs:
            write_shop(db, spec)
            db.flush()
            write_history_cycles(db, spec)
            cycle = write_scored_cycle(db, spec)
            write_delivery(db, spec, cycle)
            n_txn += write_transactions(db, spec, cycle)
            n_complaints += write_complaints(db, spec)

        db.commit()

        shops = db.query(Shop).count()
        cycles = db.query(Cycle).count()
        deliveries = db.query(Delivery).count()

        print(f"rulebook version : {version}")
        print(f"shops            : {shops}")
        print(f"cycles           : {cycles}")
        print(f"deliveries       : {deliveries}")
        print(f"transactions     : {n_txn}")
        print(f"complaints       : {n_complaints}")
        print("cases/rule_hits/audit_log left empty - derived by engine/, not seeded")

        assert shops == 60, f"expected 60 shops, got {shops}"
    finally:
        db.close()


if __name__ == "__main__":
    seed()
```

### 3.2 Seed facts, stated explicitly

**Random seed value: `random.seed(4521)`** — set at module import (line 44),
before any generation call. There is exactly one seeding call in the file.

**Rows created per table by `seed()`:**

| Table | Rows written by seed.py | How |
|---|---:|---|
| `rulebook_versions` | 1 | `write_rulebook_version()` — one snapshot of rules.yaml |
| `shops` | 60 | 3 hardcoded `FIXTURES` + `make_generated_shops(57)` |
| `cycles` | 180 | 3 per shop: 2 history (2026-06, 2026-07) + 1 scored (2026-08) |
| `deliveries` | 180 | 1 per cycle — 2 in `write_history_cycles`, 1 in `write_delivery` |
| `transactions` | 42,958 | scored cycle only; `round(txn_card_ratio × ration_cards)` per shop, 0 if `dispensed_kg is None` |
| `complaints` | 175 | `complaints_in_window + complaints_outside_window` per shop |
| `cases` | **0** | left empty on purpose — derived at runtime |
| `rule_hits` | **0** | left empty on purpose |
| `audit_log` | **0** | left empty on purpose |

`seed()` begins with `Base.metadata.drop_all()` then `create_all()`. A rerun
destroys the whole file including any cases/rule_hits/audit rows the API wrote.

**Value ranges and distributions used for the 57 generated shops:**

| Quantity | Distribution |
|---|---|
| `shop_id` | `random.randint(4000, 4999)`, resampled on collision |
| `district` | `random.choice(["Sitapur", "Sitapur", "Barabanki"])` → ~2:1 Sitapur |
| `block` | `random.choice(BLOCKS[district])`; Sitapur has 8 blocks, Barabanki 5 |
| `name` | `f"FPS {block}-{randint(1,40)}"`, resampled until unique |
| `lat` / `lng` | district base (27.57/80.68 or 26.93/81.19) + `uniform(-0.35, 0.35)`, 4 dp |
| `ration_cards` | `randrange(400, 1600, 50)` |
| `allocated_kg` | `randrange(4000, 14000, 500)` |
| `dispatched_kg` | equal to `allocated` with p=0.90; else `allocated − randrange(50, 300, 25)` |
| archetype | `random.choices(["clean","transport","counter","sloppy"], weights=[62,14,14,10])` |
| `weighed_kg` | `dispatched × (1 + receipt_pct/100)`, 1 dp |
| `dispensed_kg` | `weighed × (1 + counter_pct/100)`, 1 dp |
| scale offline | `random.random() < 0.05` → both `weighed_kg` and `dispensed_kg` set to `None` |
| GPS fitted | `random.random() > 0.12` → ~12% get `gps_available=False`, `gps_deviation_km=None` |
| `hour_violations_month` | sloppy: `randint(3, 7)`; else `randint(0, 2)` |
| `txn_card_ratio` | sloppy: `uniform(0.45, 0.62)` 2 dp; else `uniform(0.62, 0.96)` 2 dp |
| `complaints_in_window` | clean: `randint(0, 2)`; else `randint(1, 5)` |
| `complaints_outside_window` | `randint(0, 2)` |
| history `weighed_kg` | `allocated × (1 + uniform(-1.2, -0.05)/100)` |
| history `dispensed_kg` | `weighed × (1 + uniform(-1.0, -0.05)/100)` |
| history `hour_violations` | `randint(0, 2)` |
| history delivery gap | `randint(10, 40)` h; GPS always available, deviation `uniform(0.0, 1.5)` |
| complaint `filed_at` (in window) | `ANCHOR − timedelta(days=randint(0,13), hours=randint(0,23), minutes=randint(0,59))` |
| complaint `filed_at` (outside) | `ANCHOR − timedelta(days=randint(20,90), hours=randint(0,23))` |
| complaint `category` | `random.choice` of 6 |
| complaint `source` | `random.choice(["portal","helpline","walk_in"])` |
| complaint `status` | `random.choices(["open","closed"], weights=[70,30])` |
| `auth_mode` | `random.choices(["biometric","otp","manual_override"], weights=[88,9,3])` |
| `outside_hours` on a txn | `outside_hours_left > 0 and random.random() < 0.02` |
| txn hour | outside: `choice([6,7,8,18,19,20])`; else `randint(9,16)` |
| `vehicle_no` | `f"UP{randint(30,42)}{choice('ABCDEFGHJK')}{randint(1000,9999)}"` |
| `route_id` | `f"R-{block[:3].upper()}-{randint(1,9)}"` |
| `card_id` | `f"UP{shop_id}{i:05d}"` — deterministic, not random |

Archetype variance bands — the mechanism that decides which rules fire:

```
transport : receipt_pct uniform(-9.0, -5.2)   counter_pct uniform(-0.6, -0.05)
            gap_hours randint(49, 72)         gps_km uniform(2.1, 4.5)
counter   : receipt_pct uniform(-1.0, -0.05)  counter_pct uniform(-9.5, -5.2)
            gap_hours randint(18, 47)         gps_km uniform(0.1, 1.8)
sloppy    : receipt_pct uniform(-1.5, -0.1)   counter_pct uniform(-1.5, -0.1)
            gap_hours randint(20, 47)         gps_km uniform(0.1, 1.9)
clean     : receipt_pct uniform(-0.9,  0.2)   counter_pct uniform(-0.9, 0.1)
            gap_hours randint(8, 44)          gps_km uniform(0.0, 1.6)
```

The `transport` band crosses all three of the high-weight thresholds
(−5.0%, 48 h, 2.0 km) by construction, which is why 4 of 60 shops reach 87.

**How the three demo fixtures reach their locked scores.** They are not
anomalies injected into a distribution — they are three fully hardcoded dicts in
`FIXTURES` whose raw readings were chosen so the rulebook produces the wanted
number. No score, variance, coverage or gap_hop is stored anywhere:

- **#4521 → 87, HIGH, coverage 100, gap `dispatch_to_receipt`.**
  `dispatched 12000 / weighed 11015` = −8.21% → fires `weighing_variance` (30).
  `delivery_gap_hours 61` > 48 → fires `delivery_gap` (25).
  `gps_deviation_km 3.4` > 2.0 → fires `gps_deviation` (22).
  `weighed 11015 / dispensed 10980` = −0.32% → passes.
  `txn_card_ratio 0.88` → passes. `hour_violations 1` → passes.
  7 complaints in the window ≥ 3 → bonus +10. **30+25+22+10 = 87.**
  `ration_cards 1200` is chosen so `0.88 × 1200 = 1056` transacting cards exactly.
- **#4102 → 55, MEDIUM, coverage 83, gap `dispatch_to_receipt`.**
  −6.10% fires 30; 52 h fires 25; `gps_available=False` makes
  `gps_deviation_km` **None**, so that rule is *skipped*, not passed → 5 of 6
  rules evaluated → `round(5/6 × 100) = 83`. 2 complaints < 3 → no bonus.
  **30+25 = 55.** `900 × 0.71 = 639` cards.
- **#4788 → 53, MEDIUM, coverage 100, gap `receipt_to_counter`.**
  −0.33% passes; 44 h passes; 0.8 km passes; −8.70% fires `counter_variance`
  (20); `txn_card_ratio 0.55` < 0.6 fires `transaction_mismatch` (15);
  `hour_violations 4` ≥ 3 fires `operating_hours` (8); 6 complaints ≥ 3 → +10.
  **20+15+8+10 = 53.** `1000 × 0.55 = 550` cards.

The out-of-window complaints (#4521: 2, #4102: 1, #4788: 0) exist solely so a
broken window filter fails a test instead of passing quietly.

### 3.3 The committed database

`backend/leakproof.db` **is** in the working tree and is explicitly un-ignored by
`.gitignore` ("`backend/leakproof.db` is NOT ignored. It is committed on
purpose"). Because the repository has zero commits, it is currently untracked
like every other file. Size: **5,574,656 bytes**.

Row counts, read with `SELECT COUNT(*)` over a read-only connection:

| Table | Rows |
|---|---:|
| audit_log | 161 |
| cases | 60 |
| complaints | 175 |
| cycles | 180 |
| deliveries | 180 |
| rule_hits | 360 |
| rulebook_versions | 1 |
| shops | 60 |
| transactions | 42,958 |

`cases`, `rule_hits` and `audit_log` are populated, so this file has been through
at least one API request since it was seeded — `ensure_cases()` writes them
lazily on the first request. `audit_log` by `event_type`:

| event_type | count |
|---|---:|
| CASE_OPENED | 60 |
| COMPLAINT_LINKED | 53 |
| RULE_FIRED | 44 |
| NOTE_ADDED | 2 |
| SCORE_RECOMPUTED | 2 |

The two `NOTE_ADDED` and two `SCORE_RECOMPUTED` rows are residue from manual
demo or testing against the committed file, not from seeding.

Case-level facts in the committed DB:

| case_id | shop | score | severity | coverage | gap_hop | complaints | z_score | z_confirms |
|---|---|---:|---|---:|---|---:|---:|---|
| C-0041 | 4521 | 87 | HIGH | 100 | dispatch_to_receipt | 7 | 1.66 | 0 (false) |
| C-0010 | 4102 | 55 | MEDIUM | 83 | dispatch_to_receipt | 2 | 1.0 | 0 (false) |
| C-0047 | 4788 | 53 | MEDIUM | 100 | receipt_to_counter | 6 | 1.82 | 0 (false) |

Ranked-list head, showing the tie-break at work:

```
C-0041  shop 4521  score 87  complaints 7  coverage 100
C-0056  shop 4910  score 87  complaints 4  coverage 100
C-0018  shop 4219  score 87  complaints 3  coverage 100
C-0032  shop 4458  score 87  complaints 3  coverage 100
C-0049  shop 4798  score 77  complaints 2  coverage 100
C-0001  shop 4012  score 77  complaints 1  coverage 100
```

Severity distribution over the 60 cases: **HIGH 7, MEDIUM 3, LOW 50**.
Cases with `coverage_pct < 100`: **8**.

`rulebook_versions` single row: version `1.0.0`, updated_by
`District Supply Office, Sitapur`, checksum
`3419eeca1c4ec225d1bf9946bc67e023b594742c8ae956a5cb42613bcdf8ddb7`,
loaded_at `2026-07-15 09:12:00`, is_active `1`.

---

## 4. Detection engine

All seven engine modules are under 150 lines, so every one is reproduced in
full. `backend/app/engine/__init__.py` is included too because its docstring is
stale (see §10).

### 4.0 `backend/app/engine/__init__.py` (5 lines, verbatim)

```python
"""Detection engine: reconcile (F1), rulebook (F2), score (F3/F5),
complaints (F4), memo, audit (F6).

F1, F2, F3/F5 and the memo template are implemented. complaints.py (F4) and
audit.py (F6) are still stubs."""
```

### 4.1 `backend/app/engine/reconcile.py` (125 lines, verbatim)

```python
"""F1 — Four-hop reconciliation ladder.

allocated_kg -> dispatched_kg -> weighed_kg -> dispensed_kg

Two variances, two places grain can go:
  dispatched -> weighed    transport-leg diversion
  weighed    -> dispensed  counter skimming at the shop

reconcile() turns one cycle's raw readings into the flat feature dict the
rulebook evaluates. locate_gap() names the worse of the two hops, which is the
sentence an officer actually acts on: "985 kg opened between dispatch and
receipt — not the dealer, the transport leg."

F5 runs through this whole module: a reading we do not have is None, never 0.
A missing shop scale must degrade coverage, not report a 100% shortfall.
"""

DISPATCH_TO_RECEIPT = "dispatch_to_receipt"
RECEIPT_TO_COUNTER = "receipt_to_counter"


def _field(obj, name):
    """Read one field off a SQLAlchemy row, a SimpleNamespace or a dict.

    The engine is fed ORM rows in the app and plain objects in the tests; it
    should not care which, and should never explode on a shape it has not met.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _variance_pct(before, after):
    """Percentage change from one hop to the next, negative when grain is lost.

    Returns None — not 0.0 — when either reading is missing or the earlier hop
    is zero. "We could not measure this hop" and "this hop was clean" are
    different findings and the rest of the pipeline depends on telling them
    apart.
    """
    if before is None or after is None or before == 0:
        return None
    return round((after - before) / before * 100, 2)


def reconcile(cycle, delivery, txns, shop):
    """Derive the feature dict for one shop-cycle from its raw readings.

    Nothing here is stored precomputed: seed.py writes readings, this function
    derives, and it is the only place the variances come from.
    """
    dispatched_kg = _field(cycle, "dispatched_kg")
    weighed_kg = _field(cycle, "weighed_kg")
    dispensed_kg = _field(cycle, "dispensed_kg")

    return {
        "shop_id": _field(shop, "id"),
        "variance_dispatch_to_receipt": _variance_pct(dispatched_kg, weighed_kg),
        "variance_receipt_to_counter": _variance_pct(weighed_kg, dispensed_kg),
        "delivery_gap_hours": _delivery_gap_hours(delivery),
        "gps_deviation_km": _gps_deviation_km(delivery),
        "txn_card_ratio": _txn_card_ratio(txns, shop),
        "hour_violations_month": _field(cycle, "hour_violations_month"),
    }


def _delivery_gap_hours(delivery):
    """Hours between depot dispatch and shop arrival.

    None when the consignment is still in transit or its arrival scan never
    landed — an unrecorded arrival is not an instant delivery.
    """
    dispatch_ts = _field(delivery, "dispatch_ts")
    arrival_ts = _field(delivery, "arrival_ts")
    if dispatch_ts is None or arrival_ts is None:
        return None
    return round((arrival_ts - dispatch_ts).total_seconds() / 3600, 2)


def _gps_deviation_km(delivery):
    """Max distance off the registered route, or None if no GPS unit is fitted.

    gps_available is checked before the reading precisely so that "no device"
    stays distinguishable from "device reported 0.0 km" — the second is a
    passing rule, the first is a rule we could not evaluate at all.
    """
    if not _field(delivery, "gps_available"):
        return None
    return _field(delivery, "gps_deviation_km")


def _txn_card_ratio(txns, shop):
    """Distinct cards that collected, over cards attached to the shop.

    Distinct, not transaction count: one card collecting five times is one
    beneficiary served, and a shop can pad its transaction log.
    """
    ration_cards = _field(shop, "ration_cards")
    if txns is None or not ration_cards:
        return None
    distinct_cards = {_field(t, "card_id") for t in txns}
    distinct_cards.discard(None)
    return round(len(distinct_cards) / ration_cards, 2)


def locate_gap(features):
    """Name the hop where the most grain went missing.

    Whichever variance is more negative wins. A hop we could not measure is not
    a candidate — it is not "0% loss", it is unknown — so a case with only one
    measurable hop localises to that hop, and a case with neither returns None.

    Ties go to the earlier hop: if both hops lost the same share, the grain was
    already short when it reached the shop.
    """
    candidates = [
        (features.get("variance_dispatch_to_receipt"), DISPATCH_TO_RECEIPT),
        (features.get("variance_receipt_to_counter"), RECEIPT_TO_COUNTER),
    ]
    measurable = [c for c in candidates if c[0] is not None]
    if not measurable:
        return None
    return min(measurable, key=lambda c: c[0])[1]
```

### 4.2 `backend/app/engine/rulebook.py` (113 lines, verbatim)

```python
"""F2 — Versioned YAML rulebook.

The rulebook is read from app/rules.yaml at runtime, every time. It is never
mirrored into Python constants: an officer edits the YAML, the next evaluation
uses it, and no code changes. That is the whole point of the feature — the
thresholds belong to the district supply office, not to us.

evaluate() returns one trace row per rule, in rulebook order, with three
possible states:

  fired    the condition was met                 contributes the rule's weight
  passed   we checked and it was within tolerance contributes 0
  skipped  the input was unavailable             contributes 0

"skipped" is not a polite "passed". A rule we could not evaluate is not a rule
that passed, and conflating the two is how audit systems lose credibility.
"""

from pathlib import Path

import yaml

# app/rules.yaml — the officer-editable file, one directory up from engine/.
RULES_PATH = Path(__file__).resolve().parent.parent / "rules.yaml"

# The comparisons the rulebook may express. Deliberately small: a rule an
# officer can read is worth more than an expression language they cannot.
OPERATORS = {
    "lt": lambda value, threshold: value < threshold,
    "lte": lambda value, threshold: value <= threshold,
    "gt": lambda value, threshold: value > threshold,
    "gte": lambda value, threshold: value >= threshold,
    "eq": lambda value, threshold: value == threshold,
}


def load(path=None):
    """Parse rules.yaml into a dict. No caching — see the module docstring."""
    path = Path(path) if path else RULES_PATH
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _with_unit(text, unit):
    """Attach the unit the way the frozen contract prints it: '-8.21%', '61 hrs'."""
    if not unit:
        return text
    return f"{text}{unit}" if unit == "%" else f"{text} {unit}"


def _format_raw_value(value, unit):
    """Render a measurement the way the trace should quote it.

    Percentages carry two decimals because that is the precision the ladder is
    reconciled at (-8.21%, not -8.2%). Everything else prints as measured, with
    a whole number staying whole: a 61.0-hour gap reads "61 hrs".
    """
    if unit == "%":
        return _with_unit(f"{value:.2f}", unit)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return _with_unit(str(value), unit)


def _format_threshold(threshold, unit):
    """Render a threshold verbatim as it stands in rules.yaml.

    Not reformatted to match the raw value: the trace should show the officer
    the number they actually typed ("-5.0%"), so that reading the row and
    reading the rulebook give the same answer.
    """
    return _with_unit(str(threshold), unit)


def evaluate(features, rulebook):
    """Evaluate every rule against one feature dict. Returns the full trace.

    Every rule produces a row, including the ones that passed and the ones we
    could not check — the trace is a record of what was examined, not a list of
    accusations.
    """
    return [_evaluate_rule(rule, features) for rule in rulebook.get("rules", [])]


def _evaluate_rule(rule, features):
    operator = rule["operator"]
    if operator not in OPERATORS:
        raise ValueError(
            f"rules.yaml rule '{rule['id']}' uses unknown operator '{operator}'. "
            f"Supported: {', '.join(sorted(OPERATORS))}."
        )

    unit = rule.get("unit")
    value = features.get(rule["field"])
    hit = {
        "rule_id": rule["id"],
        "label": rule["label"],
        "raw_value": None,
        "threshold": _format_threshold(rule["threshold"], unit),
        "contribution": 0,
        "severity": rule["severity"],
        "status": "skipped",
    }

    # Absent and None are the same finding: there was no reading to check.
    if value is None:
        return hit

    fired = OPERATORS[operator](value, rule["threshold"])
    hit["raw_value"] = _format_raw_value(value, unit)
    hit["status"] = "fired" if fired else "passed"
    hit["contribution"] = rule["weight"] if fired else 0
    return hit
```

### 4.3 `backend/app/engine/score.py` (93 lines, verbatim)

```python
"""F3 + F5 — Composite score, reasoning trace, coverage.

compute() is the single derivation path: features in, a scored case with its
full trace out. Nothing upstream precomputes a score, so a case opened today
and a case re-derived in six months run through this same function.

Invariants this module is answerable for:
  * #4521 scores EXACTLY 87 (30 + 25 + 22 + 10). Not 86, not 88.
  * Weights total 120 and the bonus adds 10, so 130 is arithmetically
    possible. The DISPLAY caps at 100; the raw total is kept as score_raw.
    Do not renormalise the weights to make the cap disappear.
  * A skipped rule contributes 0 and pulls coverage_pct down. It is never
    counted as passed, and its weight is never redistributed to the rules we
    could evaluate — that would quietly inflate a case built on less evidence.
  * The z-score is a confirming badge and contributes ZERO. It is not read
    here, and adding it to the feature dict must not move the score.
"""

from .memo import build_memo
from .reconcile import locate_gap
from .rulebook import evaluate


def compute(features, rulebook, complaints_count):
    """Score one shop-cycle against the rulebook. Returns the whole case body."""
    rule_hits = evaluate(features, rulebook)
    complaint_bonus = _complaint_bonus(rulebook, complaints_count)

    fired_total = sum(hit["contribution"] for hit in rule_hits if hit["status"] == "fired")
    score_raw = fired_total + complaint_bonus["contribution"]
    # Display cap. score_raw is preserved so an auditor can see that a case at
    # 100 was a 130 and not a bare pass of the band.
    score = min(score_raw, 100)

    severity = _severity(score, rulebook)
    shop_id = features.get("shop_id")

    return {
        "score": score,
        "score_raw": score_raw,
        "severity": severity,
        "coverage_pct": _coverage_pct(rule_hits),
        "gap_hop": locate_gap(features),
        "rulebook_version": rulebook.get("version"),
        "rule_hits": rule_hits,
        "complaint_bonus": complaint_bonus,
        "memo": build_memo(shop_id, score, severity, rule_hits, complaint_bonus),
    }


def _complaint_bonus(rulebook, complaints_count):
    """F4's corroboration bonus, read off the rulebook rather than hardcoded.

    complaints_count is the count ALREADY narrowed to the window by
    engine/complaints.py; window_days is echoed here so the case body can show
    what "recent" meant on the day it was scored.
    """
    config = rulebook.get("corroboration", {}).get("complaint_bonus", {})
    min_complaints = config.get("min_complaints", 0)
    weight = config.get("weight", 0)
    count = complaints_count or 0
    return {
        "count": count,
        "window_days": config.get("window_days"),
        "contribution": weight if count >= min_complaints else 0,
    }


def _coverage_pct(rule_hits):
    """Share of rules we were actually able to evaluate.

    Counted per rule, not per weight: coverage answers "how much of the
    rulebook did we get to run?", which is a question about checks performed,
    not about points available. #4102 misses one rule of six and reads 83%.
    """
    if not rule_hits:
        return 100
    evaluated = [hit for hit in rule_hits if hit["status"] != "skipped"]
    return round(len(evaluated) / len(rule_hits) * 100)


def _severity(score, rulebook):
    """HIGH / MEDIUM / LOW, with the band edges taken from rules.yaml.

    Banded on the displayed score: the officer's triage decision should follow
    the number printed on the case sheet.
    """
    bands = rulebook.get("severity_bands", {})
    if score >= bands.get("high", 75):
        return "HIGH"
    if score >= bands.get("medium", 50):
        return "MEDIUM"
    return "LOW"
```

### 4.4 `backend/app/engine/complaints.py` (81 lines, verbatim)

```python
"""F4 — Complaint auto-linking and the corroboration bonus.

Public grievances are the one signal in LEAKPROOF that does not come from a
machine. They are not evidence of diversion on their own, which is why they add
a bounded +10 rather than a rule weight: they corroborate a case the ladder
already built, they do not create one.

Thresholds (window_days, min_complaints, weight) come from rules.yaml, never
from constants in this module — an officer widening the window edits the YAML.
"""

from datetime import datetime, timedelta

from ..models import Complaint
from .rulebook import load

# The demo is frozen to a moment in time: this is when the case opens, and the
# window is measured backwards from here.
#
# Deliberately NOT datetime.now(). The seeded complaints sit at fixed offsets
# behind this instant, so a wall-clock anchor would quietly slide them out of
# the window as real days pass and #4521 would stop scoring 87 — a demo that
# decays overnight. Real deployments would pass the case's opened_at instead,
# which is exactly what the `anchor` argument is for.
ANCHOR = datetime(2026, 8, 14, 9, 12, 0)


def _bonus_config(rulebook=None):
    rulebook = rulebook if rulebook is not None else load()
    return rulebook.get("corroboration", {}).get("complaint_bonus", {})


def complaints_in_window(session, shop_id, anchor=None, window_days=None, rulebook=None):
    """Complaints filed against this shop inside the window, newest first.

    window_days defaults to the rulebook's value (currently 14) rather than to
    a literal here, so the YAML stays the single place the window is set.
    """
    if window_days is None:
        window_days = _bonus_config(rulebook).get("window_days", 14)
    anchor = anchor or ANCHOR
    opens = anchor - timedelta(days=window_days)

    return (
        session.query(Complaint)
        .filter(
            Complaint.shop_id == shop_id,
            Complaint.filed_at >= opens,
            Complaint.filed_at <= anchor,
        )
        .order_by(Complaint.filed_at.desc())
        .all()
    )


def link(session, shop_id, window_days=None, anchor=None, case_id=None, rulebook=None):
    """Match complaints to a case's window and return the count.

    The return value is exactly what score.compute() takes as complaints_count:
    F4 decides WHICH complaints are in scope, F3 decides what they are worth.

    Passing case_id attaches the matched complaints to that case. Complaints
    outside the window keep linked_case_id null — null means unlinked, not
    unexamined, and the ones we looked at and rejected stay in the table where
    an auditor can see the window did something.

    The caller commits. This function does not, so that linking a case and
    writing its audit rows land in one transaction or neither does.
    """
    matched = complaints_in_window(session, shop_id, anchor, window_days, rulebook)

    if case_id is not None:
        for complaint in matched:
            complaint.linked_case_id = case_id

    return len(matched)


def bonus_threshold(rulebook=None):
    """Minimum complaints the rulebook requires before the bonus applies."""
    return _bonus_config(rulebook).get("min_complaints", 3)
```

### 4.5 `backend/app/engine/stats.py` (79 lines, verbatim)

```python
"""Statistical confirmation layer — a BADGE, and only a badge.

Invariant 5: this module contributes ZERO to the score. engine/score.py does
not import it, does not know it exists, and must never learn. The score is
fired rule weights plus the complaint bonus; everything here is a second
opinion an officer can read next to that number, not a term inside it.

What it answers: "is this shop unusual, or is this just what the district looks
like?" A rulebook threshold says a shop crossed a line. A z-score says how far
from its peers it stands. The two disagree often, and when they do, the
disagreement is worth showing rather than resolving.

Moved here from routers/cases.py: engine/ holds domain computation, routers/
holds endpoints. The logic is unchanged — same population, same exclusions,
same rounding.
"""

from statistics import mean, pstdev

# A z-score at or beyond this is called "confirming". Not tuned to the demo:
# #4521 lands at 1.66 against it and its badge reads "does not confirm".
Z_CONFIRMS_AT = 2.0


def worst_variance(features):
    """The variance at the located gap — how much this shop lost at its worst hop."""
    measured = [
        v
        for v in (
            features.get("variance_dispatch_to_receipt"),
            features.get("variance_receipt_to_counter"),
        )
        if v is not None
    ]
    return min(measured) if measured else None


def z_scores(worst_by_shop: dict):
    """How far each shop's worst hop sits from the district-wide norm.

    Signed so that a WORSE shop scores higher: variances are negative, so the
    distance is measured as (population mean - this shop), which puts an
    unusually large shortfall at a positive z.

    Shops with no measurable variance are excluded from the population rather
    than counted as zero — F5 again. A shop whose scale was offline is not a
    shop with no shortfall, and folding it in as 0.0% would drag the mean
    toward clean and inflate everyone else's z. It gets None back and does not
    vote on where the norm sits.

    Confirming badge only. Nothing here reaches the score.
    """
    values = [v for v in worst_by_shop.values() if v is not None]
    if len(values) < 2:
        return {shop_id: None for shop_id in worst_by_shop}

    population_mean = mean(values)
    spread = pstdev(values)
    if not spread:
        return {shop_id: None for shop_id in worst_by_shop}

    return {
        shop_id: (round((population_mean - value) / spread, 2) if value is not None else None)
        for shop_id, value in worst_by_shop.items()
    }


def z_scores_from_features(features_by_shop: dict):
    """z-score per shop, straight from the feature dicts reconcile() produced."""
    return z_scores({shop_id: worst_variance(f) for shop_id, f in features_by_shop.items()})


def confirms(z_score):
    """Does the statistical layer back the rulebook up on this case?

    None is not confirmation. A shop we could not place against its peers is
    unconfirmed, the same way an unevaluated rule is not a passed rule.
    """
    return z_score is not None and z_score >= Z_CONFIRMS_AT
```

### 4.6 `backend/app/engine/audit.py` (84 lines, verbatim)

```python
"""F6 — Append-only audit trail and reproducibility.

Insert is the only operation this module performs. There is no helper here to
edit a row and none to remove one, and there must never be: a trail that can be
rewritten proves nothing, and the whole claim LEAKPROOF makes to an auditor is
that a score can be re-derived months later from what was written on the day.

Events: CASE_OPENED, RULE_FIRED (one row per fired rule), COMPLAINT_LINKED,
NOTE_ADDED, SCORE_RECOMPUTED.

recompute() is an observation, not a correction. It re-derives from the stored
inputs, records what it found next to what was stored, and leaves the stored
case exactly as it was. If the two disagree, that disagreement is the finding —
quietly overwriting the old score would destroy the evidence that anything
moved.

CLAUDE.md section 6 asks for a grep over audit code before any commit that
touches this file. The forbidden patterns are not spelled out here, because
this docstring would match them and the check would never come back clean.
tests/test_audit.py runs the same check automatically.
"""

import json
from datetime import datetime

from ..models import AuditLog

# The fields compared when a case is re-derived. Kept narrow on purpose: these
# are the numbers an officer acted on and an auditor would challenge.
COMPARED_FIELDS = ("score", "severity", "coverage_pct", "gap_hop", "rulebook_version")


def log(session, case_id, actor, action, detail=None, rulebook_version=None, at=None):
    """Append one event to the trail. The caller commits.

    detail is JSON-encoded rather than spread across columns so that an event
    written today stays readable after the payload shape of its event type has
    moved on — an old row must never need a migration to be understood.
    """
    row = AuditLog(
        case_id=case_id,
        event_type=action,
        actor_role=actor,
        payload=json.dumps(detail, default=str) if detail is not None else None,
        rulebook_version=rulebook_version,
        created_at=at or datetime.utcnow(),
    )
    session.add(row)
    return row


def summarise(case_or_result):
    """The comparable shape of a case, from either a stored row or a fresh derivation."""
    if isinstance(case_or_result, dict):
        return {field: case_or_result.get(field) for field in COMPARED_FIELDS}
    return {field: getattr(case_or_result, field, None) for field in COMPARED_FIELDS}


def recompute(session, case, recomputed, actor="auditor"):
    """Compare a stored case against a fresh derivation and record the result.

    Returns {stored, recomputed, identical}. Writes a SCORE_RECOMPUTED row and
    nothing else — the stored case is left standing whatever the comparison
    says. The caller commits.
    """
    stored_summary = summarise(case)
    fresh_summary = summarise(recomputed)
    identical = stored_summary == fresh_summary

    outcome = {
        "stored": stored_summary,
        "recomputed": fresh_summary,
        "identical": identical,
    }

    log(
        session,
        case.id,
        actor,
        "SCORE_RECOMPUTED",
        outcome,
        rulebook_version=fresh_summary.get("rulebook_version"),
    )
    return outcome
```

### 4.7 `backend/app/engine/memo.py` (100 lines, verbatim)

```python
"""Plain-language memo.

THIS IS A TEMPLATE, NOT AN LLM. Nothing in this module calls a model or an
external API; it is a dict of f-string phrasings joined into a sentence. The
honest answer to "what generates the memo?" is "a template" — "template now,
LLM later" is a declared scoping decision, and the code stays truthful about it.

The memo says three things, in the order an officer needs them:
  1. what fired, each with its raw value and the threshold it crossed
  2. whether the public corroborated it
  3. what we could NOT check — F5 in prose, so the gap in the evidence is on
     the page next to the score rather than buried in a coverage badge
"""

# One phrasing per rule in rules.yaml, keyed by rule_id. A rule an officer adds
# to the YAML still gets a sentence (see _clause) — it just gets a generic one,
# because the rulebook is theirs to edit and the memo must not block on us.
PHRASINGS = {
    "weighing_variance": (
        lambda value, threshold: f"weighing shortfall of {abs(value):.1f}% "
        f"against a {abs(threshold):.0f}% tolerance"
    ),
    "delivery_gap": (
        lambda value, threshold: f"a {value:.0f}-hour delivery gap "
        f"against a {threshold:.0f}-hour limit"
    ),
    "gps_deviation": lambda value, threshold: f"a {value:g} km route deviation",
    "counter_variance": (
        lambda value, threshold: f"a counter shortfall of {abs(value):.1f}% "
        f"against a {abs(threshold):.0f}% tolerance"
    ),
    "transaction_mismatch": (
        lambda value, threshold: f"a transaction-to-card ratio of {value:.2f} "
        f"against a {threshold:g} floor"
    ),
    "operating_hours": (
        lambda value, threshold: f"{value:.0f} out-of-hours counter sessions "
        f"against a limit of {threshold:.0f}"
    ),
}


def _number(text):
    """Pull the number back out of a trace string: '-8.21%' -> -8.21, '61 hrs' -> 61.0."""
    if text is None:
        return None
    try:
        return float(text.split()[0].rstrip("%"))
    except (ValueError, IndexError):
        return None


def _clause(hit):
    value = _number(hit["raw_value"])
    threshold = _number(hit["threshold"])
    phrasing = PHRASINGS.get(hit["rule_id"])
    if phrasing is None or value is None or threshold is None:
        # Officer-added rule, or a rule whose value is not numeric: quote the
        # trace row verbatim rather than say nothing.
        return f"{hit['label'].lower()} ({hit['raw_value']} against {hit['threshold']})"
    return phrasing(value, threshold)


def _join(parts):
    """'A', 'A and B', 'A, B, and C' — read aloud in a hearing, not parsed."""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def build_memo(shop_id, score, severity, rule_hits, complaint_bonus):
    """One paragraph an officer can act on and an auditor can re-derive."""
    subject = f"Shop #{shop_id}" if shop_id else "This shop"

    fired = [hit for hit in rule_hits if hit["status"] == "fired"]
    findings = _join([_clause(hit) for hit in fired]) if fired else "no rules fired"
    memo = f"{subject} flagged {severity} ({score}/100): {findings}."

    count = complaint_bonus.get("count", 0)
    if complaint_bonus.get("contribution"):
        plural = "" if count == 1 else "s"
        memo += (
            f" Corroborated by {count} complaint{plural} in the preceding "
            f"{complaint_bonus.get('window_days')} days."
        )

    skipped = [hit for hit in rule_hits if hit["status"] == "skipped"]
    if skipped:
        # Named, not counted. "We could not check the vehicle's route" is a
        # different sentence from "the vehicle's route was fine", and the memo
        # is where that distinction has to survive being read out loud.
        # Phrased as "Not evaluated: <label>" rather than "<label> could not be
        # checked", because a rule label is an assertion ("Vehicle deviated from
        # registered route") and must not read as a finding we never made.
        labels = _join([hit["label"] for hit in skipped])
        memo += f" Not evaluated: {labels} — the reading was unavailable."

    return memo
```

### 4.8 Question 1 — the rulebook file `backend/app/rules.yaml` (65 lines, verbatim)

```yaml
version: "1.0.0"
updated_by: "District Supply Office, Sitapur"

severity_bands:
  high: 75
  medium: 50

rules:
  - id: weighing_variance
    label: Weighing shortfall beyond tolerance
    field: variance_dispatch_to_receipt
    operator: lt
    threshold: -5.0
    unit: "%"
    severity: high
    weight: 30

  - id: delivery_gap
    label: Delivery-to-dispatch gap exceeded
    field: delivery_gap_hours
    operator: gt
    threshold: 48
    unit: "hrs"
    severity: high
    weight: 25

  - id: gps_deviation
    label: Vehicle deviated from registered route
    field: gps_deviation_km
    operator: gt
    threshold: 2.0
    unit: "km"
    severity: high
    weight: 22

  - id: counter_variance
    label: Shortfall between shop receipt and counter dispensing
    field: variance_receipt_to_counter
    operator: lt
    threshold: -5.0
    unit: "%"
    severity: high
    weight: 20

  - id: transaction_mismatch
    label: Transactions inconsistent with ration-card count
    field: txn_card_ratio
    operator: lt
    threshold: 0.6
    severity: medium
    weight: 15

  - id: operating_hours
    label: Irregular shop operating hours
    field: hour_violations_month
    operator: gte
    threshold: 3
    severity: low
    weight: 8

corroboration:
  complaint_bonus:
    min_complaints: 3
    window_days: 14
    weight: 10
```

### 4.9 Question 2 — the exact grammar of a rule in `rules.yaml`

**Top-level keys of the document** (all four are read somewhere):

| Key | Type | Read by |
|---|---|---|
| `version` | string | `score.compute()` → `rulebook.get("version")`; `seed.write_rulebook_version()`; served raw by `/api/rulebook` |
| `updated_by` | string | `seed.write_rulebook_version()`; served raw by `/api/rulebook`; rendered on the Rulebook page |
| `severity_bands` | mapping with keys `high`, `medium` | `score._severity()` |
| `rules` | list of rule mappings | `rulebook.evaluate()` |
| `corroboration.complaint_bonus` | mapping with `min_complaints`, `window_days`, `weight` | `score._complaint_bonus()`, `complaints._bonus_config()` |

**Keys of one rule.** Seven, of which six are mandatory in practice:

| Key | Required | Type | Used how |
|---|---|---|---|
| `id` | yes | string | `hit["rule_id"]`; also the key into `memo.PHRASINGS`; also `RuleHit.rule_id` |
| `label` | yes | string | copied verbatim into `hit["label"]` |
| `field` | yes | string | **the feature-dict key to look up** — `features.get(rule["field"])` |
| `operator` | yes | string | one of five, see below; unknown → `ValueError` |
| `threshold` | yes | number | right-hand side of the comparison |
| `unit` | **optional** | string | display only; `rule.get("unit")`, absent on `transaction_mismatch` and `operating_hours` |
| `severity` | yes | string | copied into `hit["severity"]`; only ever `high`/`medium`/`low` in the current file, but **not validated anywhere in Python** |
| `weight` | yes | int | added to the score when the rule fires |

`id`, `label`, `field`, `operator`, `threshold`, `severity` and `weight` are all
accessed with `rule["..."]` (hard `KeyError` if missing). Only `unit` uses
`.get()`.

**Supported operators — exactly five, and nothing else.** From
`backend/app/engine/rulebook.py`:

```python
OPERATORS = {
    "lt":  lambda value, threshold: value <  threshold,
    "lte": lambda value, threshold: value <= threshold,
    "gt":  lambda value, threshold: value >  threshold,
    "gte": lambda value, threshold: value >= threshold,
    "eq":  lambda value, threshold: value == threshold,
}
```

There is no `AND`, no `OR`, no `NOT`, no nesting, no arithmetic, no ranges, no
multi-field conditions, and no way for one rule to reference another. A rule is
strictly `one field OP one scalar threshold`. An unrecognised operator raises:

```python
    operator = rule["operator"]
    if operator not in OPERATORS:
        raise ValueError(
            f"rules.yaml rule '{rule['id']}' uses unknown operator '{operator}'. "
            f"Supported: {', '.join(sorted(OPERATORS))}."
        )
```

**Field names a rule may reference.** The lookup itself is **generic**: it is a
plain dict `.get()` against whatever `reconcile()` returned. It is not a
match/case, not an if-chain, not a registry of handlers. The exact resolving
line is:

```python
    unit = rule.get("unit")
    value = features.get(rule["field"])
```

So the grammar accepts *any* string as `field`. What constrains it is that only
`engine/reconcile.py` builds the feature dict, and it hardcodes exactly seven
keys (one of which, `shop_id`, is not a numeric feature):

```python
    return {
        "shop_id": _field(shop, "id"),
        "variance_dispatch_to_receipt": _variance_pct(dispatched_kg, weighed_kg),
        "variance_receipt_to_counter": _variance_pct(weighed_kg, dispensed_kg),
        "delivery_gap_hours": _delivery_gap_hours(delivery),
        "gps_deviation_km": _gps_deviation_km(delivery),
        "txn_card_ratio": _txn_card_ratio(txns, shop),
        "hour_violations_month": _field(cycle, "hour_violations_month"),
    }
```

Therefore the *effective* allowed field set for a rule is:

```
variance_dispatch_to_receipt   float | None
variance_receipt_to_counter    float | None
delivery_gap_hours             float | None
gps_deviation_km               float | None
txn_card_ratio                 float | None
hour_violations_month          int   | None
(shop_id                       str   — present but never referenced by a rule)
```

A rule naming a field that does not exist in the dict is **silently reported as
`skipped`**, not as a configuration error — `features.get()` returns `None`, and
`None` is the "no reading" branch. `tests/test_rulebook.py::test_a_field_absent_from_features_is_skipped`
asserts exactly this behaviour.

**Consequence for a domain pivot:** the rulebook is genuinely data-driven on the
comparison side, but the *feature vocabulary* is hardcoded in Python in one
function (`reconcile()`), and each feature's derivation is bespoke
(`_variance_pct`, `_delivery_gap_hours`, `_gps_deviation_km`, `_txn_card_ratio`).
There is no generic "read column X from table Y" mechanism.

### 4.10 Question 3 — the exact data structure of one reasoning-trace entry

Produced by `rulebook._evaluate_rule()`. Always exactly these seven keys, in this
insertion order, for every rule, in every state:

```python
    hit = {
        "rule_id": rule["id"],
        "label": rule["label"],
        "raw_value": None,
        "threshold": _format_threshold(rule["threshold"], unit),
        "contribution": 0,
        "severity": rule["severity"],
        "status": "skipped",
    }

    # Absent and None are the same finding: there was no reading to check.
    if value is None:
        return hit

    fired = OPERATORS[operator](value, rule["threshold"])
    hit["raw_value"] = _format_raw_value(value, unit)
    hit["status"] = "fired" if fired else "passed"
    hit["contribution"] = rule["weight"] if fired else 0
    return hit
```

`test_rulebook.py::test_every_rule_produces_exactly_one_trace_row` asserts the
key set is exactly `{rule_id, label, raw_value, threshold, contribution,
severity, status}`.

Real examples, taken from `docs/contract/case_detail.json` (which the API is
asserted equal to, key for key):

*fired*
```json
{
  "rule_id": "weighing_variance",
  "label": "Weighing shortfall beyond tolerance",
  "raw_value": "-8.21%",
  "threshold": "-5.0%",
  "contribution": 30,
  "severity": "high",
  "status": "fired"
}
```

*passed*
```json
{
  "rule_id": "operating_hours",
  "label": "Irregular shop operating hours",
  "raw_value": "1",
  "threshold": "3",
  "contribution": 0,
  "severity": "low",
  "status": "passed"
}
```

*skipped* (as produced for shop #4102, asserted in
`test_rulebook.py::test_4102_missing_gps_is_skipped_never_passed`)
```json
{
  "rule_id": "gps_deviation",
  "label": "Vehicle deviated from registered route",
  "raw_value": null,
  "threshold": "2.0 km",
  "contribution": 0,
  "severity": "high",
  "status": "skipped"
}
```

Note that `raw_value` and `threshold` are **display strings carrying their
units**, not numbers. Formatting rules:

```python
def _with_unit(text, unit):
    """Attach the unit the way the frozen contract prints it: '-8.21%', '61 hrs'."""
    if not unit:
        return text
    return f"{text}{unit}" if unit == "%" else f"{text} {unit}"


def _format_raw_value(value, unit):
    if unit == "%":
        return _with_unit(f"{value:.2f}", unit)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return _with_unit(str(value), unit)


def _format_threshold(threshold, unit):
    return _with_unit(str(threshold), unit)
```

So `%` closes up (`-8.21%`), every other unit is space-separated (`61 hrs`,
`3.4 km`), a whole-number float prints without its `.0`, and the threshold is
printed exactly as typed in the YAML (`-5.0%`, not `-5.00%`). `engine/memo.py`
then has to parse the number back out of these strings with `_number()`.

The dict is spread straight into the ORM row in `routers/cases.py`:
`db.add(RuleHit(case_id=case_id, **hit))` — so the trace dict keys and the
`rule_hits` column names are the same seven names by construction.

### 4.11 Question 4 — "skipped / couldn't check", and signal coverage

**Representation.** `"skipped"` is one of three values of the `status` string on
a trace row. It is produced in exactly one place, and it is the *default* state
of the dict, not an exception path — the row is built as skipped and only
upgraded once a reading exists:

```python
        "status": "skipped",
    }

    # Absent and None are the same finding: there was no reading to check.
    if value is None:
        return hit
```

A skipped row keeps `raw_value: None` and `contribution: 0`, but still shows its
`threshold`, so the trace says *what* could not be checked.

The `None` that triggers it originates upstream in `reconcile.py`, which is
careful never to substitute a zero:

```python
def _variance_pct(before, after):
    if before is None or after is None or before == 0:
        return None
    return round((after - before) / before * 100, 2)


def _delivery_gap_hours(delivery):
    dispatch_ts = _field(delivery, "dispatch_ts")
    arrival_ts = _field(delivery, "arrival_ts")
    if dispatch_ts is None or arrival_ts is None:
        return None
    return round((arrival_ts - dispatch_ts).total_seconds() / 3600, 2)


def _gps_deviation_km(delivery):
    if not _field(delivery, "gps_available"):
        return None
    return _field(delivery, "gps_deviation_km")


def _txn_card_ratio(txns, shop):
    ration_cards = _field(shop, "ration_cards")
    if txns is None or not ration_cards:
        return None
    distinct_cards = {_field(t, "card_id") for t in txns}
    distinct_cards.discard(None)
    return round(len(distinct_cards) / ration_cards, 2)
```

**Coverage percentage.** Computed in `engine/score.py`, rule-count based, not
weight-based:

```python
def _coverage_pct(rule_hits):
    """Share of rules we were actually able to evaluate.

    Counted per rule, not per weight: coverage answers "how much of the
    rulebook did we get to run?", which is a question about checks performed,
    not about points available. #4102 misses one rule of six and reads 83%.
    """
    if not rule_hits:
        return 100
    evaluated = [hit for hit in rule_hits if hit["status"] != "skipped"]
    return round(len(evaluated) / len(rule_hits) * 100)
```

`round(5 / 6 * 100)` = `round(83.33…)` = **83**. Note the empty-list case returns
**100**, not 0. But `compute({}, rulebook, 0)` returns coverage **0**, because an
empty *feature* dict still produces six skipped rows —
`test_score.py::test_a_skipped_rule_never_contributes` asserts that.

A skipped rule's weight is **never redistributed** to the rules that did run;
the docstring in `score.py` states this as an invariant.

Related: `stats.z_scores()` applies the same discipline — a shop with no
measurable variance is excluded from the population rather than counted as 0.0.

### 4.12 Question 5 — composite score, cap, and severity bands

The whole of `compute()`:

```python
def compute(features, rulebook, complaints_count):
    """Score one shop-cycle against the rulebook. Returns the whole case body."""
    rule_hits = evaluate(features, rulebook)
    complaint_bonus = _complaint_bonus(rulebook, complaints_count)

    fired_total = sum(hit["contribution"] for hit in rule_hits if hit["status"] == "fired")
    score_raw = fired_total + complaint_bonus["contribution"]
    # Display cap. score_raw is preserved so an auditor can see that a case at
    # 100 was a 130 and not a bare pass of the band.
    score = min(score_raw, 100)

    severity = _severity(score, rulebook)
    shop_id = features.get("shop_id")

    return {
        "score": score,
        "score_raw": score_raw,
        "severity": severity,
        "coverage_pct": _coverage_pct(rule_hits),
        "gap_hop": locate_gap(features),
        "rulebook_version": rulebook.get("version"),
        "rule_hits": rule_hits,
        "complaint_bonus": complaint_bonus,
        "memo": build_memo(shop_id, score, severity, rule_hits, complaint_bonus),
    }
```

So: **score = sum of fired weights + complaint bonus, then `min(…, 100)`.**
`score_raw` keeps the uncapped total (max 130) but is never persisted.

The bonus:

```python
def _complaint_bonus(rulebook, complaints_count):
    config = rulebook.get("corroboration", {}).get("complaint_bonus", {})
    min_complaints = config.get("min_complaints", 0)
    weight = config.get("weight", 0)
    count = complaints_count or 0
    return {
        "count": count,
        "window_days": config.get("window_days"),
        "contribution": weight if count >= min_complaints else 0,
    }
```

It is all-or-nothing: 3 complaints and 300 complaints both add exactly 10.

**Severity band thresholds.** They live in `rules.yaml` under `severity_bands`
(`high: 75`, `medium: 50`), and are read at evaluation time — but with **hard-coded
Python fallbacks of the same numbers**:

```python
def _severity(score, rulebook):
    """HIGH / MEDIUM / LOW, with the band edges taken from rules.yaml.

    Banded on the displayed score: the officer's triage decision should follow
    the number printed on the case sheet.
    """
    bands = rulebook.get("severity_bands", {})
    if score >= bands.get("high", 75):
        return "HIGH"
    if score >= bands.get("medium", 50):
        return "MEDIUM"
    return "LOW"
```

So 75 and 50 appear in two places: `backend/app/rules.yaml` lines 5–6, and
`backend/app/engine/score.py` lines 89 and 91 as `.get()` defaults. There is no
third copy in the backend. The frontend does not band anything itself — it
renders `severity` as received, and the Rulebook page renders
`book.severity_bands.high` / `.medium` from the API.

Banding is applied to the **capped** score, so a raw 130 bands the same as a raw
101 or a bare 100.

Other numeric constants that participate in scoring, and where they live:

| Constant | Value | Location |
|---|---|---|
| rule weights | 30, 25, 22, 20, 15, 8 | `rules.yaml` only |
| rule thresholds | −5.0, 48, 2.0, −5.0, 0.6, 3 | `rules.yaml` only |
| complaint bonus weight | 10 | `rules.yaml`; `score._complaint_bonus` defaults to 0 |
| min complaints | 3 | `rules.yaml`; `score` defaults to 0, `complaints.bonus_threshold` defaults to 3 |
| window days | 14 | `rules.yaml`; `complaints.complaints_in_window` defaults to 14 |
| display cap | 100 | `score.py` hardcoded `min(score_raw, 100)` |
| HIGH band | 75 | `rules.yaml` + `score.py` fallback |
| MEDIUM band | 50 | `rules.yaml` + `score.py` fallback |
| z confirming threshold | 2.0 | `stats.Z_CONFIRMS_AT` — Python constant, **not** in YAML |
| complaint window anchor | `datetime(2026, 8, 14, 9, 12, 0)` | `complaints.ANCHOR` and `seed.ANCHOR` (duplicated) |
| scored period | `"2026-08"` | `routers/cases.SCORED_PERIOD` and `seed.SCORED_PERIOD` (duplicated) |
| pinned demo case id | `{"4521": "C-0041"}` | `routers/cases.PINNED_CASE_IDS` |

### 4.13 Question 6 — is the audit trail hash-chained, signed, or just append-only?

**Just append-only rows. There is no hash chain and no signature.**

`AuditLog` has no `prev_hash`, no `hash`, no `signature` and no sequence column
beyond the autoincrement `id`. Nothing computes a digest of a row. The only
sha256 in the backend is in `seed.write_rulebook_version()`, over the rules.yaml
*text*, and that value is never verified afterwards.

The entire write path is one function:

```python
def log(session, case_id, actor, action, detail=None, rulebook_version=None, at=None):
    """Append one event to the trail. The caller commits.

    detail is JSON-encoded rather than spread across columns so that an event
    written today stays readable after the payload shape of its event type has
    moved on — an old row must never need a migration to be understood.
    """
    row = AuditLog(
        case_id=case_id,
        event_type=action,
        actor_role=actor,
        payload=json.dumps(detail, default=str) if detail is not None else None,
        rulebook_version=rulebook_version,
        created_at=at or datetime.utcnow(),
    )
    session.add(row)
    return row
```

`session.add()` and nothing else. The module exposes `log`, `summarise`,
`recompute`, `COMPARED_FIELDS`, `AuditLog`, `json`, `datetime` — no update or
delete helper. `routers/audit.py` exposes one GET and no other verb.

The append-only property is enforced by *convention plus two tests*, not by the
database. There is no SQLite trigger, no `WITHOUT ROWID` immutability trick, no
revoked permission — a stray `session.delete()` anywhere would work. The tests
that stand in for enforcement:

```python
FORBIDDEN_CALLS = ("".join((".dele", "te(")), "".join(("UPD", "ATE")))
AUDITED_SOURCES = (APP_DIR / "engine" / "audit.py", APP_DIR / "routers" / "audit.py")

def test_audit_code_contains_no_mutation_calls():
    for source in AUDITED_SOURCES:
        text = source.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_CALLS:
            assert pattern not in text, f"{source.name} contains '{pattern}'"

def test_audit_module_exposes_no_mutation_helper():
    from app.engine import audit
    exported = [name for name in dir(audit) if not name.startswith("_")]
    for name in exported:
        assert "remov" not in name.lower()
        assert "purge" not in name.lower()
        assert "edit" not in name.lower()
```

Note this grep-in-a-test only covers two files, whereas CLAUDE.md invariant 6
asks for the whole of `backend/`.

**What "re-derivable" concretely means in code.** It means: take the case's own
stored `cycle`, `delivery` and `transactions` rows and its `opened_at`, run the
*current* `rules.yaml` through the same `compute()`, and compare five fields.
Nothing is fetched from outside the database and nothing is rewritten:

```python
COMPARED_FIELDS = ("score", "severity", "coverage_pct", "gap_hop", "rulebook_version")


def summarise(case_or_result):
    if isinstance(case_or_result, dict):
        return {field: case_or_result.get(field) for field in COMPARED_FIELDS}
    return {field: getattr(case_or_result, field, None) for field in COMPARED_FIELDS}


def recompute(session, case, recomputed, actor="auditor"):
    stored_summary = summarise(case)
    fresh_summary = summarise(recomputed)
    identical = stored_summary == fresh_summary

    outcome = {"stored": stored_summary, "recomputed": fresh_summary, "identical": identical}

    log(session, case.id, actor, "SCORE_RECOMPUTED", outcome,
        rulebook_version=fresh_summary.get("rulebook_version"))
    return outcome
```

and the router that feeds it:

```python
    _, result = _derive(db, shop, cycle, load_rulebook(), case.opened_at)
    outcome = recompute_case(db, case, result)
    db.commit()
    return outcome
```

Two consequences worth stating plainly:

1. The re-derivation uses **`load_rulebook()` — the current file on disk**, not
   the `yaml_text` snapshot stored in `rulebook_versions`. Editing `rules.yaml`
   and pressing Recompute will report a divergence; the system detects that, but
   it cannot reproduce the *old* rulebook, even though the text is sitting in a
   table. `rulebook_versions` is written and never read.
2. `rule_hits` are **not** compared. Only the five scalar fields are. A trace
   could differ row-for-row while `identical` still reports `true`.

### 4.14 Question 7 — any machine learning?

**No.**

No model training, no forecasting, no clustering, no inference, no model
artifacts, no feature store, no train/test split. `backend/requirements.txt`
pins seven packages — `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pydantic`,
`pyyaml`, `pytest`, `httpx` — and none of `numpy`, `pandas`, `scipy`,
`scikit-learn`, `statsmodels`, `torch` or `tensorflow` appears in it or in any
import in `backend/app/`, `backend/seed.py` or `backend/tests/`. (Grepping the
whole of `backend/` does hit those words, but only inside `.venv/` — pip's
vendored code and pytest's optional numpy support.)

The only statistics import in the entire application is:

```python
from statistics import mean, pstdev
```

in `backend/app/engine/stats.py`, from the Python standard library.

**Every statistical function actually implemented**, in full:

| Function | File | What it computes |
|---|---|---|
| `worst_variance(features)` | `stats.py` | `min()` over the two measurable hop variances; `None` if neither is measurable |
| `z_scores(worst_by_shop)` | `stats.py` | population mean and population SD (`pstdev`) over shops with a measurable worst variance, then `(mean − value) / sd` rounded to 2 dp per shop. Returns all-`None` if fewer than 2 measurable values or if SD is 0 |
| `z_scores_from_features(features_by_shop)` | `stats.py` | thin wrapper: `worst_variance` per shop, then `z_scores` |
| `confirms(z_score)` | `stats.py` | `z_score is not None and z_score >= 2.0` |
| `_variance_pct(before, after)` | `reconcile.py` | `(after − before) / before × 100`, 2 dp — arithmetic, not statistics |
| `_coverage_pct(rule_hits)` | `score.py` | a ratio of counts |
| `_txn_card_ratio(txns, shop)` | `reconcile.py` | distinct-card count ÷ ration_cards |

That is the whole of it. The z-score is a **badge**: `engine/score.py` does not
import `stats` at all, and `test_score.py::test_zscore_is_not_an_input_to_the_score`
asserts that adding a `z_score` key to the feature dict does not move the score.
The `Z_CONFIRMS_AT = 2.0` threshold is a Python module constant, not a YAML
setting, and in the committed data **no case confirms** — the three fixtures sit
at z 1.66, 1.00 and 1.82, all below 2.0, and `z_confirms` is `0` for all three.

---

## 5. API surface

### 5.1 `backend/app/main.py` (42 lines, verbatim)

```python
"""FastAPI application entrypoint.

App, CORS, /health, and the three routers. Every route lives under /api; the
prefix is applied here rather than repeated in each router so the contract in
PROJECT-BRIEF.md has exactly one place it can drift from.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (import registers tables on Base.metadata)
from .db import Base, engine
from .routers import audit, cases, rulebook

app = FastAPI(
    title="LEAKPROOF",
    description="Diversion detection for India's Public Distribution System.",
    version="0.1.0",
)

# Vite dev server only. No wildcard: the demo runs on one known origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Safe on an already-seeded file: create_all only creates what is missing.
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    """Liveness probe. Returns ok as soon as the app is importable."""
    return {"status": "ok", "service": "leakproof", "version": app.version}


app.include_router(cases.router, prefix="/api")
app.include_router(rulebook.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
```

### 5.2 `backend/app/db.py` (38 lines, verbatim)

```python
"""SQLAlchemy engine, session factory and declarative Base.

Single SQLite file at backend/leakproof.db. It is committed on purpose so a
judge can clone the repo and see the same 60 shops we demo with.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# backend/app/db.py -> backend/leakproof.db
BACKEND_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BACKEND_DIR / "leakproof.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False: FastAPI serves requests from a threadpool, and a
# SQLite connection is otherwise pinned to its creating thread.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for every table in models.py."""


def get_db():
    """FastAPI dependency: one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 5.3 `backend/app/schemas.py` (198 lines, verbatim)

```python
"""Pydantic v2 response shapes.

These mirror docs/contract/case_detail.json key for key. The frontend builds
against that static file until Stage 3, so the two move together or not at all:
renaming a key here without renaming it there breaks the UI silently. If a
change looks necessary, flag it — do not do it on one side only.

The trace list is deliberately a flat list of rule hits including the ones that
passed and the ones we could not evaluate. A rule we could not check is not a
rule that passed, and the response must be able to say so.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["HIGH", "MEDIUM", "LOW"]
RuleSeverity = Literal["high", "medium", "low"]
RuleStatus = Literal["fired", "passed", "skipped"]
GapHop = Literal["allocation_to_dispatch", "dispatch_to_receipt", "receipt_to_counter"]


class ShopRef(BaseModel):
    """Just enough shop to render the case header and drop a map pin."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    block: str
    lat: float
    lng: float


class CycleSummary(BaseModel):
    """The four-hop ladder and the two variances the officer reads off it.

    Variances are percentages against the previous hop, rounded to 2 dp for
    display. Null on either kg field means the reading was unavailable, which
    is what makes the corresponding rule "skipped".
    """

    model_config = ConfigDict(from_attributes=True)

    allocated_kg: float
    dispatched_kg: float
    weighed_kg: float | None = None
    dispensed_kg: float | None = None
    variance_dispatch_to_receipt: float | None = None
    variance_receipt_to_counter: float | None = None


class RuleHitOut(BaseModel):
    """One trace row. raw_value carries its unit so the row reads as evidence.

    raw_value is null only when status is "skipped" — there was no reading to
    quote.
    """

    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    label: str
    raw_value: str | None = None
    threshold: str
    contribution: int
    severity: RuleSeverity
    status: RuleStatus


class ComplaintBonus(BaseModel):
    """F4 corroboration: complaints inside the window, and what they added."""

    model_config = ConfigDict(from_attributes=True)

    count: int
    window_days: int
    contribution: int


class ComplaintOut(BaseModel):
    """One grievance matched into the case's window by F4.

    Added to the contract alongside the same key in case_detail.json — the two
    moved together. PROJECT-BRIEF describes GET /api/cases/{case_id} as
    "case + trace + linked complaints", and the original contract file simply
    had no field for the third of those.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    filed_at: datetime
    source: str
    category: str
    text: str
    status: str


class Statistical(BaseModel):
    """Confirming badge only. `confirms` never moves the score."""

    model_config = ConfigDict(from_attributes=True)

    z_score: float | None = None
    confirms: bool


class CaseDetail(BaseModel):
    """GET /api/cases/{case_id} — the canonical response.

    Frozen shape: docs/contract/case_detail.json is the worked example for
    shop #4521 and is the authority on key names and ordering.
    """

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    shop: ShopRef
    # Display score, capped at 100 even though 130 is arithmetically possible.
    score: int
    severity: Severity
    status: str
    opened_at: datetime
    cycle: CycleSummary
    gap_hop: GapHop | None = None
    # Share of rule weight actually evaluated; skipped rules pull it down.
    coverage_pct: int
    rulebook_version: str
    rule_hits: list[RuleHitOut]
    complaint_bonus: ComplaintBonus
    # The complaints the bonus was counted from, so the officer can read the
    # grievances rather than take the count on trust.
    complaints: list[ComplaintOut] = []
    statistical: Statistical
    # engine/memo.py f-string template output. Not AI-generated.
    memo: str


class CaseListItem(BaseModel):
    """Row in the ranked list on the Officer and Inspector screens."""

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    shop: ShopRef
    score: int
    severity: Severity
    status: str
    opened_at: datetime
    gap_hop: GapHop | None = None
    coverage_pct: int


# ---------------------------------------------------------------------------
# Operational shapes. NOT part of the frozen case-detail contract: these carry
# requests and the trail, and docs/contract/case_detail.json says nothing about
# them, so they are free to change without invariant 8 applying.
# ---------------------------------------------------------------------------


class NoteIn(BaseModel):
    """POST /api/cases/{case_id}/notes — an inspector's field note.

    There is no notes table. A note IS an audit event: writing it anywhere else
    would create a second place the case's history lives.
    """

    text: str
    actor_role: str = "inspector"


class AuditEventOut(BaseModel):
    """One row of the append-only trail."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    event_type: str
    actor_role: str
    # Decoded from the stored JSON text so the client does not parse twice.
    payload: dict | None = None
    rulebook_version: str | None = None
    created_at: datetime


class RecomputeOut(BaseModel):
    """POST /api/cases/{case_id}/recompute — stored vs freshly re-derived.

    `identical` is the claim being made: the same inputs and the same rulebook
    still produce the same score. A false here is a finding, not an error.
    """

    stored: dict
    recomputed: dict
    identical: bool
```

### 5.4 `backend/app/routers/__init__.py` (1 lines, verbatim)

```python
"""API routers: cases, rulebook, audit. All stubs until Stage 2."""
```

### 5.5 `backend/app/routers/cases.py` (364 lines, verbatim)

```python
"""Case endpoints: the ranked list, the case sheet, notes and recompute.

Cases are DERIVED, never seeded. seed.py writes raw readings and stops; the
first request to this router opens every case by running the engine over those
readings. That gives the project exactly one derivation path — the score a
judge sees on screen and the score an auditor re-derives six months later come
out of the same function, because there is no second place a score is made.

Re-running seed.py drops the cases table, and the next request rebuilds it.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..engine import complaints as complaints_engine
from ..engine import stats
from ..engine.audit import log, recompute as recompute_case
from ..engine.reconcile import reconcile
from ..engine.rulebook import load as load_rulebook
from ..engine.score import compute
from ..models import Case, Complaint, Cycle, Delivery, RuleHit, Shop, Transaction
from ..schemas import CaseDetail, CaseListItem, NoteIn, RecomputeOut

router = APIRouter(prefix="/cases", tags=["cases"])

# The cycle the demo scores. Earlier cycles exist for trend, but a case is
# opened against one allocation month.
SCORED_PERIOD = "2026-08"

# #4521 is C-0041 in docs/contract/case_detail.json and on the deck. Case ids
# are otherwise assigned in shop order; the demo case keeps the id already in
# print rather than the one its position would give it.
PINNED_CASE_IDS = {"4521": "C-0041"}


# ---------------------------------------------------------------------------
# Derivation. This router orchestrates the engine and assembles responses; the
# computation lives in engine/ — reconcile (F1), rulebook (F2), score (F3/F5),
# complaints (F4), stats (badge). Nothing is calculated inline here.
# ---------------------------------------------------------------------------


def _stored_inputs(db: Session, cycle: Cycle):
    """Everything the engine needs for one cycle, read back from the database.

    Transactions come back as distinct card ids only. reconcile() wants a
    sequence it can count distinct cards from, and pulling 40,000 full rows to
    count them would be the same answer at a hundred times the cost.
    """
    delivery = db.query(Delivery).filter(Delivery.cycle_id == cycle.id).first()
    txns = db.query(Transaction.card_id).filter(Transaction.cycle_id == cycle.id).distinct().all()
    return delivery, txns


def _derive(db: Session, shop: Shop, cycle: Cycle, rulebook: dict, anchor):
    """Run the full engine over one shop-cycle's stored inputs."""
    delivery, txns = _stored_inputs(db, cycle)
    features = reconcile(cycle, delivery, txns, shop)
    complaints_count = complaints_engine.link(db, shop.id, anchor=anchor, rulebook=rulebook)
    return features, compute(features, rulebook, complaints_count)


def _assign_case_ids(shop_ids):
    """C-0001, C-0002, ... in shop order, with the pinned demo id reserved."""
    reserved = set(PINNED_CASE_IDS.values())
    assigned = {}
    counter = 1
    for shop_id in shop_ids:
        if shop_id in PINNED_CASE_IDS:
            assigned[shop_id] = PINNED_CASE_IDS[shop_id]
            continue
        candidate = f"C-{counter:04d}"
        while candidate in reserved:
            counter += 1
            candidate = f"C-{counter:04d}"
        assigned[shop_id] = candidate
        counter += 1
    return assigned


def ensure_cases(db: Session) -> None:
    """Open a case for every shop's scored cycle, once, if none exist yet.

    Writes the case, its full trace (fired, passed AND skipped rows), the
    complaint links, and the audit events that make the case re-derivable.
    """
    if db.query(Case).count() > 0:
        return

    rulebook = load_rulebook()
    anchor = complaints_engine.ANCHOR
    version = rulebook.get("version")

    shops = db.query(Shop).order_by(Shop.id).all()
    cycles = {
        cycle.shop_id: cycle
        for cycle in db.query(Cycle).filter(Cycle.period == SCORED_PERIOD).all()
    }

    # Pass 1: derive everything, so the z-score has a population to compare
    # against before any case is written.
    derived = []
    for shop in shops:
        cycle = cycles.get(shop.id)
        if cycle is None:
            continue
        features, result = _derive(db, shop, cycle, rulebook, anchor)
        derived.append((shop, cycle, features, result))

    z_by_shop = stats.z_scores_from_features(
        {shop.id: features for shop, _, features, _ in derived}
    )
    case_ids = _assign_case_ids([shop.id for shop, _, _, _ in derived])

    # Pass 2: write.
    for shop, cycle, features, result in derived:
        case_id = case_ids[shop.id]
        bonus = result["complaint_bonus"]
        z_score = z_by_shop.get(shop.id)

        db.add(
            Case(
                id=case_id,
                shop_id=shop.id,
                cycle_id=cycle.id,
                score=result["score"],
                severity=result["severity"],
                status="OPEN",
                opened_at=anchor,
                gap_hop=result["gap_hop"],
                coverage_pct=result["coverage_pct"],
                rulebook_version=result["rulebook_version"],
                complaint_count=bonus["count"],
                complaint_window_days=bonus["window_days"],
                complaint_contribution=bonus["contribution"],
                z_score=z_score,
                z_confirms=stats.confirms(z_score),
                memo=result["memo"],
            )
        )

        for hit in result["rule_hits"]:
            db.add(RuleHit(case_id=case_id, **hit))

        log(
            db,
            case_id,
            "system",
            "CASE_OPENED",
            {
                "shop_id": shop.id,
                "period": cycle.period,
                "score": result["score"],
                "severity": result["severity"],
                "coverage_pct": result["coverage_pct"],
                "gap_hop": result["gap_hop"],
            },
            rulebook_version=version,
            at=anchor,
        )

        for hit in result["rule_hits"]:
            if hit["status"] != "fired":
                continue
            log(
                db,
                case_id,
                "system",
                "RULE_FIRED",
                {
                    "rule_id": hit["rule_id"],
                    "raw_value": hit["raw_value"],
                    "threshold": hit["threshold"],
                    "contribution": hit["contribution"],
                },
                rulebook_version=version,
                at=anchor,
            )

        # Attaches the matched complaints to this case. The count was already
        # derived in pass 1; this call is what writes the link.
        linked = complaints_engine.link(
            db, shop.id, anchor=anchor, case_id=case_id, rulebook=rulebook
        )
        if linked:
            log(
                db,
                case_id,
                "system",
                "COMPLAINT_LINKED",
                {
                    "count": linked,
                    "window_days": bonus["window_days"],
                    "contribution": bonus["contribution"],
                },
                rulebook_version=version,
                at=anchor,
            )

    db.commit()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def _shop_ref(shop: Shop) -> dict:
    return {
        "id": shop.id,
        "name": shop.name,
        "block": shop.block,
        "lat": shop.lat,
        "lng": shop.lng,
    }


@router.get("", response_model=list[CaseListItem])
def list_cases(
    db: Session = Depends(get_db),
    severity: str | None = Query(default=None),
    district: str | None = Query(default=None),
):
    """The ranked case list. Highest score first — that IS the triage order."""
    ensure_cases(db)

    query = db.query(Case, Shop).join(Shop, Case.shop_id == Shop.id)
    if severity:
        query = query.filter(Case.severity == severity.upper())
    if district:
        query = query.filter(Shop.district == district)

    # Ties are broken by corroborating complaints, then by coverage. Two cases
    # on the same score are not equally urgent: the one the public has already
    # complained about seven times is the one to send an inspector to first,
    # and between two of those, the one we could evaluate more fully is the one
    # whose score we can stand behind.
    rows = query.order_by(
        Case.score.desc(),
        Case.complaint_count.desc(),
        Case.coverage_pct.desc(),
        Case.id,
    ).all()
    return [
        CaseListItem(
            case_id=case.id,
            shop=_shop_ref(shop),
            score=case.score,
            severity=case.severity,
            status=case.status,
            opened_at=case.opened_at,
            gap_hop=case.gap_hop,
            coverage_pct=case.coverage_pct,
        )
        for case, shop in rows
    ]


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, db: Session = Depends(get_db)):
    """One case sheet: ladder, trace, coverage, complaints and memo.

    The score and trace are the STORED ones — what was decided on the day. Only
    the ladder's variances are re-derived here, and those are direct arithmetic
    on the stored readings, not a second scoring path.
    """
    ensure_cases(db)

    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"No case {case_id}")

    shop = db.get(Shop, case.shop_id)
    cycle = db.get(Cycle, case.cycle_id)
    delivery, txns = _stored_inputs(db, cycle)
    features = reconcile(cycle, delivery, txns, shop)

    hits = db.query(RuleHit).filter(RuleHit.case_id == case_id).order_by(RuleHit.id).all()
    linked = (
        db.query(Complaint)
        .filter(Complaint.linked_case_id == case_id)
        .order_by(Complaint.filed_at.desc())
        .all()
    )

    return CaseDetail(
        case_id=case.id,
        shop=_shop_ref(shop),
        score=case.score,
        severity=case.severity,
        status=case.status,
        opened_at=case.opened_at,
        cycle={
            "allocated_kg": cycle.allocated_kg,
            "dispatched_kg": cycle.dispatched_kg,
            "weighed_kg": cycle.weighed_kg,
            "dispensed_kg": cycle.dispensed_kg,
            "variance_dispatch_to_receipt": features["variance_dispatch_to_receipt"],
            "variance_receipt_to_counter": features["variance_receipt_to_counter"],
        },
        gap_hop=case.gap_hop,
        coverage_pct=case.coverage_pct,
        rulebook_version=case.rulebook_version,
        rule_hits=hits,
        complaint_bonus={
            "count": case.complaint_count,
            "window_days": case.complaint_window_days,
            "contribution": case.complaint_contribution,
        },
        complaints=linked,
        statistical={"z_score": case.z_score, "confirms": bool(case.z_confirms)},
        memo=case.memo or "",
    )


@router.post("/{case_id}/notes", status_code=201)
def add_note(case_id: str, note: NoteIn, db: Session = Depends(get_db)):
    """An inspector's field note. It lands in the audit trail and nowhere else."""
    ensure_cases(db)

    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"No case {case_id}")

    text = note.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="A note needs text")

    row = log(
        db,
        case_id,
        note.actor_role,
        "NOTE_ADDED",
        {"text": text},
        rulebook_version=case.rulebook_version,
    )
    db.commit()
    db.refresh(row)
    return {"id": row.id, "case_id": case_id, "event_type": row.event_type, "text": text}


@router.post("/{case_id}/recompute", response_model=RecomputeOut)
def recompute(case_id: str, db: Session = Depends(get_db)):
    """Re-derive the case from its STORED inputs and report what changed.

    Stored inputs only: the same cycle readings, the same delivery, the same
    complaints in the same window measured from the same anchor. Nothing is
    re-read from a live source and nothing about the case is rewritten — the
    answer is a comparison, and the comparison is written to the trail.
    """
    ensure_cases(db)

    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"No case {case_id}")

    shop = db.get(Shop, case.shop_id)
    cycle = db.get(Cycle, case.cycle_id)
    _, result = _derive(db, shop, cycle, load_rulebook(), case.opened_at)

    outcome = recompute_case(db, case, result)
    db.commit()
    return outcome
```

### 5.6 `backend/app/routers/audit.py` (58 lines, verbatim)

```python
"""Audit endpoint — F6 surface.

Read-only, and permanently so. There is one route here and it returns rows.
No route in this file may ever offer an edit or a removal of an audit row: the
trail is the one thing in LEAKPROOF that a magistrate is entitled to assume
nobody in this codebase can touch.

Ordered oldest first — the trail is read as a narrative of what happened to the
case, and a narrative runs forwards.
"""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditLog
from ..schemas import AuditEventOut
from .cases import ensure_cases

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{case_id}", response_model=list[AuditEventOut])
def get_trail(case_id: str, db: Session = Depends(get_db)):
    """Every event written against this case, oldest first.

    An empty list is a real answer: it means nothing has happened to this case
    yet, not that the case is missing.

    Cases are opened here too. Reaching the trail first on a cold database
    would otherwise show an auditor an empty history for a case that simply had
    not been derived yet — the most misleading screen in the app.
    """
    ensure_cases(db)

    rows = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case_id)
        .order_by(AuditLog.created_at, AuditLog.id)
        .all()
    )

    return [
        AuditEventOut(
            id=row.id,
            case_id=row.case_id,
            event_type=row.event_type,
            actor_role=row.actor_role,
            # Stored as text so an old row survives a payload shape change;
            # decoded here so the client does not have to parse twice.
            payload=json.loads(row.payload) if row.payload else None,
            rulebook_version=row.rulebook_version,
            created_at=row.created_at,
        )
        for row in rows
    ]
```

### 5.7 `backend/app/routers/rulebook.py` (24 lines, verbatim)

```python
"""Rulebook endpoint — F2 surface.

Reads through engine/rulebook.load() at request time, so an officer editing
rules.yaml sees the change on the next refresh without a restart and without a
code change. That is the feature, not a convenience: the thresholds belong to
the district supply office.

The parsed YAML is returned as-is rather than through a response model. A
response model would pin the rulebook's shape in Python, which is exactly the
coupling this feature exists to avoid — add a field to the YAML and it should
reach the screen on its own.
"""

from fastapi import APIRouter

from ..engine.rulebook import load

router = APIRouter(prefix="/rulebook", tags=["rulebook"])


@router.get("")
def get_rulebook():
    """The rulebook in force: version, updated_by, severity bands and rules."""
    return load()
```

### 5.8 Endpoint table

Every route. `/api` is applied once in `main.py` at `include_router` time; the
routers add their own `/cases`, `/audit`, `/rulebook` prefixes.

| METHOD | Path | Path params | Query params | Request body | Response model | Engine functions called |
|---|---|---|---|---|---|---|
| GET | `/health` | — | — | — | none (plain dict) | none |
| GET | `/api/cases` | — | `severity: str \| None`, `district: str \| None` | — | `list[CaseListItem]` | `ensure_cases` → on a cold DB: `rulebook.load`, `reconcile.reconcile`, `complaints.link`, `score.compute` (→ `rulebook.evaluate`, `reconcile.locate_gap`, `memo.build_memo`), `stats.z_scores_from_features`, `stats.confirms`, `audit.log` |
| GET | `/api/cases/{case_id}` | `case_id: str` | — | — | `CaseDetail` | `ensure_cases`; then `reconcile.reconcile` (for the ladder variances only) |
| POST | `/api/cases/{case_id}/notes` | `case_id: str` | — | `NoteIn` — `{text: str, actor_role: str = "inspector"}` | none (plain dict, status 201) | `ensure_cases`; `audit.log` |
| POST | `/api/cases/{case_id}/recompute` | `case_id: str` | — | — (empty) | `RecomputeOut` | `ensure_cases`; `rulebook.load`, `reconcile.reconcile`, `complaints.link`, `score.compute`, `audit.recompute` (→ `audit.summarise`, `audit.log`) |
| GET | `/api/audit/{case_id}` | `case_id: str` | — | — | `list[AuditEventOut]` | `ensure_cases` (imported from `routers.cases`) |
| GET | `/api/rulebook` | — | — | — | **none — raw parsed YAML** | `rulebook.load` |

Notes on the table:

- `severity` is upper-cased before comparison (`Case.severity == severity.upper()`).
  `district` is matched against `Shop.district` exactly, with no normalisation.
  Neither is validated against an enum — an unknown value returns an empty list.
- `GET /api/rulebook` deliberately has **no** `response_model`, so the YAML shape
  reaches the client unfiltered. The docstring says this is the point of F2.
- `POST .../notes` returns a hand-built dict `{"id", "case_id", "event_type",
  "text"}`, which does **not** match `AuditEventOut`.
- Every case-touching route calls `ensure_cases(db)` first, including the audit
  route, so the first request of any kind against a freshly seeded database
  writes all 60 cases, 360 rule_hits and ~161 audit rows.
- Error responses: 404 `{"detail": "No case C-9999"}` for an unknown case on
  detail / notes / recompute; 422 `{"detail": "A note needs text"}` for a
  whitespace-only note. There is no 404 on `/api/audit/{case_id}` — an unknown
  case returns `[]`.

**`GET /api/shops/{shop_id}` — ABSENT.** `PROJECT-BRIEF.md` lists it in the
frozen contract ("shop profile + cycle history") and it does not exist. There is
no `routers/shops.py`, no `/shops` route on any router, and no frontend call to
it. The two prior cycles seeded for the trend chart are therefore unreachable
over the API, and the CaseDetail "trend" element named in
`PROJECT-BRIEF.md → Screens` is not built.

### 5.9 How responses are built

**Mixed — Pydantic schemas for the case-shaped routes, hand-built dicts for the
rest.**

Built from Pydantic v2 models (`schemas.py`, all with
`ConfigDict(from_attributes=True)`):

- `GET /api/cases` → constructs `CaseListItem(...)` per row explicitly. The
  nested `shop` is a hand-built dict from `_shop_ref()` that Pydantic coerces
  into `ShopRef`.
- `GET /api/cases/{case_id}` → constructs one `CaseDetail(...)`. Within it,
  `cycle`, `complaint_bonus` and `statistical` are passed as **hand-built
  dicts**, while `rule_hits` and `complaints` are passed as **raw ORM rows** and
  coerced by `from_attributes`.
- `POST .../recompute` → `RecomputeOut`, whose `stored` and `recomputed` fields
  are typed as bare `dict`, so nothing inside them is validated.
- `GET /api/audit/{case_id}` → constructs `AuditEventOut(...)` per row, decoding
  `payload` from JSON text into a `dict` in the router.

Hand-built plain dicts, with no schema at all:

- `GET /health` → `{"status", "service", "version"}`
- `GET /api/rulebook` → whatever `yaml.safe_load` returned
- `POST /api/cases/{case_id}/notes` → `{"id", "case_id", "event_type", "text"}`

The `CaseDetail` shape is pinned to `docs/contract/case_detail.json` by
`test_api.py::test_case_detail_matches_the_frozen_contract`, which asserts the
live response equals the file exactly. That test is the only mechanical
enforcement of CLAUDE.md invariant 8.


### 5.10 `docs/contract/case_detail.json` (frozen contract)



`docs/contract/case_detail.json` (149 lines, verbatim)

```json
{
  "case_id": "C-0041",
  "shop": {
    "id": "4521",
    "name": "FPS Sitapur-12",
    "block": "Sitapur",
    "lat": 27.57,
    "lng": 80.68
  },
  "score": 87,
  "severity": "HIGH",
  "status": "OPEN",
  "opened_at": "2026-08-14T09:12:00",
  "cycle": {
    "allocated_kg": 12000.0,
    "dispatched_kg": 12000.0,
    "weighed_kg": 11015.0,
    "dispensed_kg": 10980.0,
    "variance_dispatch_to_receipt": -8.21,
    "variance_receipt_to_counter": -0.32
  },
  "gap_hop": "dispatch_to_receipt",
  "coverage_pct": 100,
  "rulebook_version": "1.0.0",
  "rule_hits": [
    {
      "rule_id": "weighing_variance",
      "label": "Weighing shortfall beyond tolerance",
      "raw_value": "-8.21%",
      "threshold": "-5.0%",
      "contribution": 30,
      "severity": "high",
      "status": "fired"
    },
    {
      "rule_id": "delivery_gap",
      "label": "Delivery-to-dispatch gap exceeded",
      "raw_value": "61 hrs",
      "threshold": "48 hrs",
      "contribution": 25,
      "severity": "high",
      "status": "fired"
    },
    {
      "rule_id": "gps_deviation",
      "label": "Vehicle deviated from registered route",
      "raw_value": "3.4 km",
      "threshold": "2.0 km",
      "contribution": 22,
      "severity": "high",
      "status": "fired"
    },
    {
      "rule_id": "counter_variance",
      "label": "Shortfall between shop receipt and counter dispensing",
      "raw_value": "-0.32%",
      "threshold": "-5.0%",
      "contribution": 0,
      "severity": "high",
      "status": "passed"
    },
    {
      "rule_id": "transaction_mismatch",
      "label": "Transactions inconsistent with ration-card count",
      "raw_value": "0.88",
      "threshold": "0.6",
      "contribution": 0,
      "severity": "medium",
      "status": "passed"
    },
    {
      "rule_id": "operating_hours",
      "label": "Irregular shop operating hours",
      "raw_value": "1",
      "threshold": "3",
      "contribution": 0,
      "severity": "low",
      "status": "passed"
    }
  ],
  "complaint_bonus": {
    "count": 7,
    "window_days": 14,
    "contribution": 10
  },
  "complaints": [
    {
      "id": 1,
      "filed_at": "2026-08-10T21:10:00",
      "source": "portal",
      "category": "epos_failure",
      "text": "ePoS machine reported failure but the entitlement was marked issued.",
      "status": "closed"
    },
    {
      "id": 5,
      "filed_at": "2026-08-09T19:33:00",
      "source": "walk_in",
      "category": "epos_failure",
      "text": "ePoS machine reported failure but the entitlement was marked issued.",
      "status": "open"
    },
    {
      "id": 4,
      "filed_at": "2026-08-03T22:40:00",
      "source": "portal",
      "category": "shop_closed",
      "text": "Shop found closed during notified distribution hours.",
      "status": "closed"
    },
    {
      "id": 2,
      "filed_at": "2026-08-03T15:14:00",
      "source": "walk_in",
      "category": "refused_entitlement",
      "text": "Entitlement refused despite a valid ration card.",
      "status": "open"
    },
    {
      "id": 3,
      "filed_at": "2026-08-03T12:42:00",
      "source": "helpline",
      "category": "short_weight",
      "text": "Received less than the entitled quantity; dealer refused to re-weigh.",
      "status": "open"
    },
    {
      "id": 7,
      "filed_at": "2026-08-03T12:30:00",
      "source": "portal",
      "category": "quality",
      "text": "Grain issued was of poor quality and partly spoiled.",
      "status": "open"
    },
    {
      "id": 6,
      "filed_at": "2026-07-31T13:48:00",
      "source": "portal",
      "category": "epos_failure",
      "text": "ePoS machine reported failure but the entitlement was marked issued.",
      "status": "open"
    }
  ],
  "statistical": {
    "z_score": 1.66,
    "confirms": false
  },
  "memo": "Shop #4521 flagged HIGH (87/100): weighing shortfall of 8.2% against a 5% tolerance, a 61-hour delivery gap against a 48-hour limit, and a 3.4 km route deviation. Corroborated by 7 complaints in the preceding 14 days."
}
```

### 5.11 Auth, sessions, users, server-side role enforcement

**None of it exists. The README is accurate.**

- **No user table.** The nine models contain no `User`, `Account`, `Session`,
  `Role`, `Permission` or `Token` table. The only user-shaped column anywhere is
  `audit_log.actor_role`, a free string with default `"system"`.
- **No authentication.** No password hashing, no JWT, no OAuth, no API key, no
  `Depends(get_current_user)`. `requirements.txt` contains no auth library
  (no `python-jose`, `passlib`, `bcrypt`, `authlib`, `fastapi-users`).
- **No session.** No cookie is set or read; `SessionLocal` is a SQLAlchemy
  database session, unrelated to a user session. CORS is configured with
  `allow_credentials=True` but nothing ever sends a credential.
- **No server-side role enforcement.** No route reads a role from the request in
  order to decide anything. The only place a role reaches the server is the
  optional `actor_role` field in the notes body, which is written verbatim into
  the audit row and never checked:

  ```python
  class NoteIn(BaseModel):
      text: str
      actor_role: str = "inspector"
  ```

  A client can post `actor_role: "auditor"`, or any other string, and it is
  stored as given.
- **No row-level security and no role-scoped queries.** CLAUDE.md says the
  correct description is "role-scoped queries at the API layer" — in the code as
  it stands there are not even those. `list_cases` filters only on `severity` and
  `district`; every role receives identical rows.
- The only network-level restriction is CORS pinned to the Vite dev origin:

  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

  This restricts browser origins only; `curl` is unaffected.

Client-side, `frontend/src/roles.js` and `Layout.jsx` do redirect a role away
from another role's workspace screen, and both files carry comments saying
plainly that this is wayfinding rather than access control.

---

## 6. Frontend

### 6.1 Core modules, verbatim

#### `frontend/src/api.js` (42 lines, verbatim)

```javascript
// Single fetch wrapper. Every network call in the app goes through apiFetch()
// so that flipping USE_MOCK is the only change needed to move the whole
// frontend from the frozen contract file onto the live backend.

import caseDetail from '@contract/case_detail.json'

// The engine, the routers and the derivation path all exist now, so the app
// reads the real backend. The mock path is kept, not deleted: it is the only
// way to open the UI when the API is down, and docs/contract/case_detail.json
// is still the shape both sides are held to.
export const USE_MOCK = false

const API_BASE = 'http://localhost:8000'

// The only fixture the contract currently freezes is one case detail.
// Anything else has to fail loudly rather than return a plausible-looking
// empty object — a silent {} is how a page ends up rendering fake zeros.
function resolveMock(path) {
  if (/^\/api\/cases\/[^/]+$/.test(path)) return caseDetail
  throw new Error(
    `No mock fixture for ${path}. Add it to docs/contract/ or set USE_MOCK = false.`,
  )
}

export async function apiFetch(path, options = {}) {
  if (USE_MOCK) {
    // Structured-cloned so a page mutating the response cannot corrupt the
    // fixture for every later read in the same session.
    return structuredClone(resolveMock(path))
  }

  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`${options.method ?? 'GET'} ${path} failed: ${response.status}`)
  }

  return response.json()
}
```

#### `frontend/src/ui.js` (142 lines, verbatim)

```javascript
// Shared control and surface classes.
//
// One radius token and one shadow depth, per CLAUDE.md's UI conventions: every
// surface in the app is `rounded` (4px) and `shadow-card`, and there is no
// second option to reach for. Keeping the strings here rather than in each
// page is what stops a fifth button from inventing a sixth style.
//
// Colour discipline (docs/design/REDESIGN-SPEC.md): nothing in this file sets
// navy except the primary tier, whose whole job is to be the one navy control
// on a screen. Everything else carries ink text on surface, bordered with the
// warm `border` tokens. Navy stays reserved for headings, the score-display
// number, and that single primary action.
//
// Focus rings are NOT here — they live in index.css as a global
// :focus-visible rule so that native controls (select, textarea) get one
// without every page having to remember.

export const CARD = 'rounded border border-border bg-surface shadow-card'

// The one motion setting in the app. 150ms ease-out is fast enough that a
// control feels answered rather than animated — long enough to read as a
// response, short enough that a demo clicking quickly never waits on it.
// `transition` (not transition-all) covers colour, background, border, shadow
// and transform, which is exactly the set the states below move.
//
// Exported because CARD_OPTION inverts on hover: the card changes ground and
// its contents change colour with it, and a child that does not carry the same
// timing would snap while the card around it eases.
export const MOTION = 'transition duration-150 ease-out'

// The lift. One pixel of translate plus the app's ONE shadow token appearing
// from nothing — that is how a control gains elevation here without a second
// shadow depth existing to reach for. `disabled:hover:` unwinds it, so a
// disabled button stays flat under the cursor; those stacked variants carry
// two pseudo-classes and therefore outrank the plain hover rules.
const LIFT =
  'hover:-translate-y-px hover:shadow-card active:translate-y-0 active:shadow-none ' +
  'disabled:hover:translate-y-0 disabled:hover:shadow-none'

// ---------------------------------------------------------------------------
// Buttons, in three tiers. Every clickable thing in the app is one of these.
// ---------------------------------------------------------------------------

// TIER 1 — primary. Solid navy, white text. At most one per screen: the action
// the screen exists for. Recompute on Auditor, Record note on Inspector, and
// the role choices on the sign-in screen, which are the only thing that page
// does. Hover darkens the fill and lifts; active drops it back down.
export const BUTTON_PRIMARY =
  'inline-block rounded border border-navy bg-navy px-4 py-2 text-body-secondary font-medium text-white ' +
  `${MOTION} ${LIFT} ` +
  'hover:border-navy/90 hover:bg-navy/90 active:bg-navy ' +
  'disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-navy'

// TIER 2 — secondary. Outlined, ink text, surface fill. The ordinary controls:
// Open case, Field note, back links, and anything else a screen offers
// alongside its primary action. Hover fills faintly with surface-sunk and
// lifts, so the tier is distinguished by weight rather than by another colour.
export const BUTTON =
  'inline-block rounded border border-border-strong bg-surface px-4 py-2 text-body-secondary font-medium text-ink ' +
  `${MOTION} ${LIFT} ` +
  'hover:border-ink-secondary hover:bg-surface-sunk active:bg-surface-sunk ' +
  'disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-border-strong ' +
  'disabled:hover:bg-surface'

// TIER 3 — tertiary. Text only: no border, no fill, ink-secondary, underlined
// on hover. For minor actions that must not compete with the two tiers above.
// The sortable column heads are the only ones in the build, and they are
// styled through SORT_HEAD below because a table header keeps its own type
// size whatever else it is.
const TERTIARY = `${MOTION} underline-offset-2 hover:underline`

// A sortable column head: the tertiary tier at table-header size. The colour
// is left to the caller rather than baked in, because the active state has to
// swap it — and `text-ink` and `text-ink-secondary` on one element are two
// utilities of equal specificity, resolved by stylesheet order rather than by
// the order they are written in. `text-ink` is emitted first, so the muted one
// wins and an active header silently stays muted. Exactly one colour class
// reaches this element, so that cannot happen.
export const SORT_HEAD = `text-table-header uppercase ${TERTIARY}`

// ---------------------------------------------------------------------------

// A card that goes somewhere. Same lift vocabulary as the buttons, and
// deliberately NOT applied to informational panels: a hover response on a card
// that cannot be clicked promises a click that never happens.
//
// No border-colour change here on purpose — the Officer and Inspector rows
// carry their severity as a coloured left-border, and a hover rule setting all
// four border colours would wipe it out under the cursor.
export const CARD_INTERACTIVE =
  `${CARD} ${MOTION} hover:-translate-y-px hover:bg-surface-sunk ` +
  'active:translate-y-0 active:bg-surface-sunk'

// A selection card: one of a small set of choices, each carrying a label and a
// line of description, where the whole surface is the target.
//
// AT REST IT IS NOT NAVY, and that is the point. The primary tier's solid navy
// was written for an inline button that IS the action — one per screen, so the
// fill reads as emphasis. Three of them stacked full-width stop reading as
// three things to choose between and start reading as a filled table, because
// nothing distinguishes one row from the next. So the card rests as a bordered
// surface, the way a set of options should, and the navy arrives on
// interaction — hover and keyboard focus both invert it. The weight lands
// where the reader is actually pointing rather than on all three at once.
//
// `group` is part of the token: the contents invert with the card, and they
// key off this class.
export const CARD_OPTION =
  `group rounded border border-border-strong bg-surface shadow-card ${MOTION} ` +
  'hover:-translate-y-px hover:border-navy hover:bg-navy ' +
  'focus-visible:border-navy focus-visible:bg-navy ' +
  'active:translate-y-0 active:bg-navy'

export const FIELD =
  'rounded border border-border-strong bg-surface px-4 py-2 text-body-secondary text-ink ' +
  // Filters sit in the secondary tier, but a select that lifted off the page
  // when the cursor crossed it would be motion for its own sake. It gets the
  // border response and nothing else.
  `${MOTION} hover:border-ink-secondary`

// The meta-label style: 12px, uppercase, tracked, ink-secondary. Used for
// field labels and for the small caps above a figure.
export const LABEL = 'mb-1 block text-meta-label uppercase text-ink-secondary'

// Table headers share the meta-label style so they read as structure rather
// than as another row of data — smaller, tracked and muted against the cells.
export const COLUMN_HEAD = 'text-table-header uppercase text-ink-secondary'

// Every table and list carries one of these: a plain-language line saying what
// the reader is looking at, sitting under the section heading.
export const CAPTION = 'mt-1 text-body-secondary text-ink-secondary'

// Body copy and the standard table cell. Numeric cells add `num` for
// tabular figures and `text-right` for alignment.
export const BODY = 'text-body text-ink'
export const CELL = 'text-table-cell text-ink'
export const CELL_MUTED = 'text-table-cell text-ink-secondary'
export const CELL_NUM = 'num text-table-cell text-ink text-right'

// Row padding for list/table views: 16px vertical. Dense enough to read as a
// data product, not so dense it reads as a spreadsheet.
export const ROW = 'px-4 py-4'
```

#### `frontend/src/severity.js` (86 lines, verbatim)

```javascript
// Severity and trace-state styling, in one place so a row on the Officer list
// and a row in the trace table can never disagree about what coral means.
//
// Tailwind classes are written out in full rather than composed at runtime:
// the JIT scans source text, so a class built as `border-${colour}` would be
// absent from the stylesheet and the row would silently lose its border.
//
// TWO severity patterns exist and they never mix on one element:
//   (1) coloured left-border on a full data row — SEVERITY_BORDER below,
//       used by the Officer list, the Inspector list and the case header
//   (2) the rectangular Tag component — components/Tag.jsx, used for compact
//       inline status (Rulebook severities, complaint status, note outcomes)
// Where a row carries the left-border, its severity TEXT is plain ink: the
// border is already the colour signal, and colouring the word as well would
// be encoding the same fact twice. There is deliberately no severity-to-text-
// colour map here any more — a bare coloured word is never the right answer,
// because colour alone is not a label.

export const SEVERITY_BORDER = {
  HIGH: 'border-l-coral',
  MEDIUM: 'border-l-gold',
  LOW: 'border-l-green',
}

// Rulebook comparisons, written the way an officer reads them rather than the
// way YAML stores them.
export const OPERATOR_SYMBOL = {
  lt: '<',
  lte: '≤',
  gt: '>',
  gte: '≥',
  eq: '=',
}

// What a located gap tells an inspector to go and do. Derived from gap_hop,
// which is the one field on a case that names a place rather than a number.
export const HOP_ACTION = {
  allocation_to_dispatch:
    'Short before it left the depot. Check the dispatch order against the weighbridge slip.',
  dispatch_to_receipt:
    'Lost on the transport leg. Check the consignment note, the vehicle log and the route.',
  receipt_to_counter:
    'Lost at the counter. Check the stock register against the ePoS dispensing record.',
}

// The three trace-row states. A skipped rule is greyed and italic — it must
// never be mistaken for a rule that passed, so it is the one state that
// changes the type style and not just the colour.
export const TRACE_ROW = {
  fired: {
    border: 'border-l-coral',
    row: 'bg-surface text-ink',
    label: 'Fired',
    labelClass: 'text-coral font-medium',
  },
  passed: {
    border: 'border-l-green',
    row: 'bg-surface text-ink',
    label: 'Passed',
    labelClass: 'text-green',
  },
  skipped: {
    border: 'border-l-border-strong',
    row: 'bg-surface-sunk text-ink-muted italic',
    label: 'Skipped',
    labelClass: 'text-ink-muted',
  },
}

const KG = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })

export function formatKg(value) {
  return value === null || value === undefined ? null : KG.format(value)
}

export function formatPct(value) {
  // Two decimals, matching the precision the ladder is reconciled at. Nulls
  // stay null: an unmeasured hop is not a 0.00% hop.
  return value === null || value === undefined ? null : `${value.toFixed(2)}%`
}

export const HOP_LABEL = {
  allocation_to_dispatch: 'Allocation to dispatch',
  dispatch_to_receipt: 'Dispatch to receipt',
  receipt_to_counter: 'Receipt to counter',
}
```

#### `frontend/src/hooks/useApi.js` (84 lines, verbatim)

```javascript
import { useCallback, useEffect, useState } from 'react'

import { apiFetch } from '../api.js'

// One fetch hook for every page. Before this existed each page carried its own
// useEffect with its own loading and error handling, and they had already
// started to disagree about what "loading" meant.
//
// `path` of null means "nothing to fetch yet" — an unselected case is not a
// failed request, and the caller gets idle:true rather than a spurious error.
//
// WHY THIS SHAPE, and not three useStates. An earlier version stored data,
// error and loading as three independent pieces of state and flipped them by
// hand. Nothing kept them consistent, and the combination that broke the UI was
// `loading: true` alongside a data value left over from the PREVIOUS request:
// every page renders its skeleton on `loading` and its content on `data` as two
// separate tests, so both appeared at once — grey placeholder bars stacked on
// top of a fully drawn table. It showed up wherever a second request followed a
// first: the Auditor's case dropdown changing the path, or reload() after a
// note was posted.
//
// So the three are no longer independent. One piece of state holds the settled
// response TOGETHER WITH the request it belongs to, and `loading` is derived by
// comparing that against the request currently being asked for. This makes the
// invariant structural rather than something each page has to remember:
//
//     loading === true  implies  data === null && error === null
//
// There is therefore no ordering of effects, no double-invoked StrictMode mount
// and no mid-flight path change that can produce a frame showing a skeleton and
// real content together — not because the flags are set in the right order, but
// because the state that would have to exist to render both cannot be spelled.
//
// It also fixes a correctness bug that mattered more than the cosmetics: while
// a new case's audit trail was in flight, the PREVIOUS case's events stayed on
// screen under the new case's heading. An append-only trail that shows the
// wrong case's rows, however briefly, is worse than one that shows nothing.
export function useApi(path) {
  // The request identity. nonce is part of it so reload() re-fetches the same
  // path and is correctly treated as a new request rather than as one already
  // answered. nonce is a number and every path begins with "/", so the space
  // joining them cannot be ambiguous.
  const [nonce, setNonce] = useState(0)
  const key = path ? `${nonce} ${path}` : null

  // The settled response and the key it answers. Never read directly — read
  // through the derivations below, which discard it unless it matches.
  const [settled, setSettled] = useState({ key: null, data: null, error: null })

  const answered = settled.key === key
  const data = answered ? settled.data : null
  const error = answered ? settled.error : null
  // Derived, not stored: there is a request and it has not been answered yet.
  // Because it is derived during render, a path change already reads as
  // "loading" on the very first render after the change — before any effect has
  // run — which is the frame the old version rendered stale content in.
  const loading = key !== null && !answered

  useEffect(() => {
    if (!key) return undefined

    let live = true

    apiFetch(path)
      .then((result) => {
        if (live) setSettled({ key, data: result, error: null })
      })
      .catch((err) => {
        // data goes to null on failure. A page shows either an error or a
        // result, never an error above the stale rows it replaced.
        if (live) setSettled({ key, data: null, error: err.message })
      })

    // A page can be navigated away from mid-request; without this the response
    // lands on an unmounted component and React warns.
    return () => {
      live = false
    }
  }, [key, path])

  const reload = useCallback(() => setNonce((n) => n + 1), [])

  return { data, error, loading, idle: !path, reload }
}
```

`frontend/src/roles.js` is not in the requested list but is load-bearing for
routing and role behaviour, so it is included:

#### `frontend/src/roles.js` (53 lines, verbatim)

```javascript
// The role model, in one place so the sign-in screen, the top bar's switcher
// and the sidebar cannot disagree about what a role is offered.
//
// WHAT THIS IS NOT. This is wayfinding. It decides which screens a person is
// shown links to and which screen they land on. It is not access control and
// nothing here protects anything: the API answers the same rows whichever
// role is set, every page remains reachable by typing its address, and the
// role itself is picked from a list with no password. Declared limitation 4
// in PROJECT-BRIEF.md — roles are a switcher, not authentication.

export const ROLES = ['Officer', 'Inspector', 'Auditor']

// Where each role starts, and where it is sent back to if it ends up on
// another role's screen. Sign-in and the top-bar switcher both read this, so
// choosing Inspector at the door and choosing Inspector mid-session land in
// exactly the same place.
export const ROLE_HOME = {
  Officer: '/',
  Inspector: '/inspector',
  Auditor: '/auditor',
}

// The sidebar, per role: one workspace screen, then the two screens everybody
// reads. Case Detail is on all three lists because every role opens cases. So
// is the Rulebook — it is the document the scores are derived from, and an
// officer, an inspector and an auditor all have reason to check what a case
// was measured against. Filtering it out of the nav would leave F2, the
// editable rulebook, reachable only by typing its address.
const SHARED = [
  { to: '/cases/C-0041', label: 'Case Detail', end: false },
  { to: '/rulebook', label: 'Rulebook', end: false },
]

export const ROLE_NAV = {
  Officer: [{ to: '/', label: 'Officer', end: true }, ...SHARED],
  Inspector: [{ to: '/inspector', label: 'Inspector', end: false }, ...SHARED],
  Auditor: [{ to: '/auditor', label: 'Auditor', end: false }, ...SHARED],
}

// The three workspace screens and who owns each. A role standing on another
// role's screen is sent home; everything absent from this map — Case Detail,
// the Rulebook, the 404 — belongs to no role and nobody is moved off it.
const OWNER = {
  '/': 'Officer',
  '/inspector': 'Inspector',
  '/auditor': 'Auditor',
}

// Returns the path to send this role to, or null to leave them where they are.
export function redirectFor(role, pathname) {
  const owner = OWNER[pathname]
  return owner && owner !== role ? ROLE_HOME[role] : null
}
```


### 6.2 Build and shell files, verbatim

#### `frontend/package.json` (25 lines, verbatim)

```json
{
  "name": "leakproof-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@fontsource/fraunces": "^5.0.20",
    "@fontsource/inter": "^5.0.20",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.2"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.13",
    "vite": "^5.4.8"
  }
}
```

#### `frontend/vite.config.js` (23 lines, verbatim)

```javascript
import { fileURLToPath, URL } from 'node:url'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// docs/contract/ lives above the Vite root. We alias into it rather than copy
// case_detail.json in, because CLAUDE.md invariant 8 says the contract and the
// code that reads it move together — a copy inside src/ would drift silently.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@contract': fileURLToPath(new URL('../docs/contract', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    fs: {
      allow: ['..'],
    },
  },
})
```

#### `frontend/tailwind.config.js` (124 lines, verbatim)

```javascript
/** @type {import('tailwindcss').Config} */

// The five brand colours are locked and unchanged since Stage 0. What the
// redesign pass adds is the set of text/border/surface tokens that were
// previously being faked with navy at an opacity (text-navy/60, border-navy/10,
// bg-navy/5). Those opacity tricks are why the hierarchy read flat: heading
// colour and paragraph colour were the same hue, so they carried the same
// weight of importance. See docs/design/REDESIGN-SPEC.md.
//
// THE RULE THAT BREAKS MOST OFTEN: navy is for headings and the score-display
// number ONLY. Body text is `ink`. Meta/captions are `ink-secondary`.
//
// TYPE SCALE — the named fontSize keys below carry size, line-height, tracking
// and weight together, so `text-page-title` is the whole style and there is no
// way to apply half of it:
//
//   text-score-display    48/1.0   serif semibold  navy   (the 87 itself)
//   text-page-title       28/1.2   serif semibold  navy
//   text-section-heading  18/1.3   serif semibold  navy
//   text-body             15/1.5   Inter regular   ink
//   text-body-secondary   14/1.5   Inter regular   ink-secondary
//   text-meta-label       12/1.4   Inter medium    ink-secondary, uppercase
//   text-table-header     12/1.4   Inter medium    ink-secondary, uppercase
//   text-table-cell       14/1.5   Inter regular   ink, tabular-nums
//
// Colour and uppercase are NOT baked into the fontSize keys — Tailwind's
// fontSize tuple cannot express them — so those stay as companion classes.
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    // `spacing` is REPLACED, not extended. Only 4/8/16/24/32/48 exist, so an
    // off-scale class like p-3 (12px) silently produces nothing and the drift
    // shows up on screen instead of hiding in a diff.
    spacing: {
      0: '0px',
      px: '1px',
      1: '4px',
      2: '8px',
      4: '16px',
      6: '24px',
      8: '32px',
      12: '48px',
    },
    // One radius, the same way there is one shadow depth. Cards, controls,
    // tags and the role switcher all round by 4px so nothing looks borrowed
    // from a different design system.
    //
    // `full` is deliberately ABSENT, not merely unused: rounded-full pills are
    // the badge-soup tell the redesign is correcting, and deleting the token
    // means `rounded-full` silently produces nothing instead of quietly
    // working the next time someone reaches for it.
    borderRadius: {
      none: '0px',
      DEFAULT: '4px',
    },
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      white: '#FFFFFF',

      // Brand — locked since Stage 0, unchanged.
      bg: '#FAF8F4',
      navy: '#132A47',
      green: '#2E7D5B',
      gold: '#C8952B',
      coral: '#D4573D',

      // Text. Near-black rather than navy, so a paragraph stops competing
      // with the heading above it.
      ink: '#14171A',
      'ink-secondary': '#5B6169',
      'ink-muted': '#94989E',

      // Borders, warm-toned to sit on the #FAF8F4 ground rather than reading
      // as a cool grey imported from somewhere else.
      border: '#DDD9D0',
      'border-strong': '#C7C2B6',

      // Surfaces. surface-sunk names what was previously bg-navy/5 — the
      // skipped-row ground and code-like blocks.
      surface: '#FFFFFF',
      'surface-sunk': '#F3F0EA',
    },
    extend: {
      // Named type styles. Extended rather than replaced so the pass can move
      // page by page without the whole app losing its type at once; the named
      // keys are what new work should use.
      fontSize: {
        'score-display': ['48px', { lineHeight: '1', fontWeight: '600' }],
        'page-title': ['28px', { lineHeight: '1.2', fontWeight: '600' }],
        'section-heading': ['18px', { lineHeight: '1.3', fontWeight: '600' }],
        body: ['15px', { lineHeight: '1.5' }],
        'body-secondary': ['14px', { lineHeight: '1.5' }],
        'meta-label': ['12px', { lineHeight: '1.4', letterSpacing: '0.04em', fontWeight: '500' }],
        'table-header': ['12px', { lineHeight: '1.4', letterSpacing: '0.04em', fontWeight: '500' }],
        'table-cell': ['14px', { lineHeight: '1.5' }],
      },
      fontFamily: {
        // Fraunces carries the display voice; Inter carries everything read
        // at body size, including every number in a table.
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      // Layout dimensions, not spacing. Kept off the spacing scale on purpose
      // so nobody reaches for w-sidebar as a padding value.
      width: {
        sidebar: '240px',
      },
      height: {
        topbar: '64px',
      },
      // Defines the content region on a page that has no content yet, so the
      // shell reads as a page waiting to be filled rather than a card adrift.
      minHeight: {
        region: '320px',
      },
      // One shadow depth for the whole app. See CLAUDE.md UI conventions.
      boxShadow: {
        card: '0 1px 2px rgba(19, 42, 71, 0.06)',
      },
    },
  },
  plugins: [],
}
```

#### `frontend/postcss.config.js` (6 lines, verbatim)

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

#### `frontend/src/index.css` (52 lines, verbatim)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  /* The app's inherited text colour is ink, NOT navy. This one line is the
     checklist's first rule made structural: anything that forgets to set a
     colour now falls back to body text instead of to heading colour, so a
     missed class reads as a small mistake rather than as another navy
     paragraph flattening the hierarchy. Navy is applied deliberately, per
     heading, and never inherited. */
  body {
    @apply bg-bg font-sans text-ink antialiased;
  }

  /* One focus ring, defined once, for every focusable thing in the app —
     including the native <select> and <textarea>, which cannot be reached by
     a utility class on a wrapper. :focus-visible rather than :focus so a
     mouse click does not leave a ring behind, but every keyboard tab does.

     Navy at 2px with a 2px offset reads clearly on both the bg cream and the
     white cards, and on the navy sidebar the offset lets the ring sit against
     the dark ground. No page may override this with focus:outline-none. */
  :focus-visible {
    outline: 2px solid theme('colors.navy');
    outline-offset: 2px;
    border-radius: theme('borderRadius.DEFAULT');
  }

  /* The sidebar is navy on navy, so the ring switches to white there. */
  aside :focus-visible {
    outline-color: theme('colors.white');
  }

  /* Tabular figures everywhere a number is read as data rather than as prose.
     Scores, variances, kilograms and timestamps all sit in columns that a
     reader compares vertically; proportional digits make 11,015 and 10,980
     different widths and the comparison stops working. Applied globally here
     so no page has to remember it. */
  table,
  th,
  td,
  time,
  output,
  meter,
  progress,
  .num,
  [data-numeric] {
    font-variant-numeric: tabular-nums;
    font-feature-settings: 'tnum' 1;
  }
}
```

#### `frontend/src/App.jsx` (39 lines, verbatim)

```jsx
import { useState } from 'react'
import { Route, Routes } from 'react-router-dom'

import Layout from './components/Layout.jsx'
import Auditor from './pages/Auditor.jsx'
import CaseDetail from './pages/CaseDetail.jsx'
import Inspector from './pages/Inspector.jsx'
import NotFound from './pages/NotFound.jsx'
import Officer from './pages/Officer.jsx'
import Rulebook from './pages/Rulebook.jsx'
import SignIn from './pages/SignIn.jsx'

export default function App() {
  // Role was local to Layout until the sign-in screen existed. It has to live
  // above the router's outlet now because two things set it — the sign-in
  // screen, which is outside the shell, and the top bar's dropdown, which is
  // inside it — and both have to be moving the same piece of state.
  //
  // null means "nobody has chosen a view yet", and it is the only thing
  // standing between a visitor and the app. That is a front door, not
  // authentication: declared limitation 4 still holds, nothing is verified and
  // nothing is stored, so a refresh drops back to the sign-in screen.
  const [role, setRole] = useState(null)

  return (
    <Routes>
      <Route path="/sign-in" element={<SignIn onSelect={setRole} />} />

      <Route element={<Layout role={role} onRoleChange={setRole} />}>
        <Route index element={<Officer />} />
        <Route path="cases/:caseId" element={<CaseDetail />} />
        <Route path="rulebook" element={<Rulebook />} />
        <Route path="inspector" element={<Inspector />} />
        <Route path="auditor" element={<Auditor />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
```

#### `frontend/src/main.jsx` (26 lines, verbatim)

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

// Self-hosted via @fontsource so the demo renders identically on a conference
// wifi that cannot reach Google Fonts. Only the weights we actually use.
import '@fontsource/fraunces/400.css'
import '@fontsource/fraunces/600.css'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'

import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* Opting into the v7 behaviours now keeps the demo console clean — an
        officer or a judge looking over a shoulder should see no warnings. */}
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

#### `frontend/index.html` (12 lines, verbatim)

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>LEAKPROOF</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

### 6.3 Pages — one row per file

| File | Lines | Props | API endpoints called | State held | What it renders |
|---|---:|---|---|---|---|
| `pages/Officer.jsx` | 242 | none (route element) | `GET /api/cases` via `useApi` | `district` (string, default `'All districts'`), `severity` (string, default `'All severities'`), `sort` (`'score' \| 'shop' \| 'coverage'`, default `'score'`); memoised `districts`, `visible` | The ranked case list as a grid "table": two `<select>` filters, a caption with counts, a sortable header row, then one `<Link>` card per case carrying a severity-coloured 4px left border, shop name/id/block/case id, gap-hop label, coverage %, score and severity word. Empty and error states included. |
| `pages/CaseDetail.jsx` | 243 | none; reads `caseId` from `useParams()` | `GET /api/cases/{caseId}` via `useApi` | none of its own — four render branches on `error` / `loading` / `!detail` / data | The case sheet: page header, a "← All cases" button, a headline card (48px navy score, severity, gap located at, `CoverageBadge`), `<Ladder>`, `<TraceTable>`, a linked-complaints list with `StatusTag`, and the memo card with the "Not generated by a language model" caption. |
| `pages/Inspector.jsx` | 299 | none | `GET /api/cases` via `useApi`; inner `Notes` uses `GET /api/audit/{caseId}` via `useApi` and `POST /api/cases/{caseId}/notes` via `apiFetch` | `district`, `openCase` (case_id or null); inner `Notes`: `text`, `status` (`{ok, detail}` or null), `saving` (bool) | The same ranked cases as a visit list, each row leading with the `HOP_ACTION` instruction for its gap hop, plus Open-case and Field-note buttons. Expanding a row reveals a note textarea, a primary submit, an outcome `Tag`, and the case's existing `NOTE_ADDED` events read back from the audit trail. |
| `pages/Auditor.jsx` | 301 | none | `GET /api/cases` (for the dropdown) and `GET /api/audit/{caseId}` via `useApi`; `POST /api/cases/{caseId}/recompute` via `apiFetch` | `caseId` (default `'C-0041'`), `result` (recompute outcome or null), `running` (bool), `failure` (string or null) | A case `<select>`, a "Recompute from stored inputs" primary button, an optional `RecomputeResult` band (stored vs re-derived score, Identical ✓ / Mismatch, and a four-field comparison list), and the append-only event trail as a grid with timestamp, actor, a neutral `Tag` for event type, and a per-event-type English sentence from `describe()`. |
| `pages/Rulebook.jsx` | 218 | none | `GET /api/rulebook` via `useApi` | none; derives `ruleTotal` by summing rule weights | The rulebook as served: a provenance card (version, maintained by, severity bands with `SeverityTag`s), the scoring-rules table (label, id, field read, operator symbol + threshold, severity tag, weight), the corroboration row, and a closing card stating 120 + 10 = 130 possible with the cap and the "back-solved, not learned" disclosure. |
| `pages/SignIn.jsx` | 176 | `onSelect` (function — sets the role in `App`) | none | none; uses `useNavigate()` | The front door outside the app shell: `LogoMark` at 64px, the LEAKPROOF wordmark, the "Public Distribution System · Uttar Pradesh · cycle 2026-08" line, three role cards (each with an inline SVG icon, name and one-line description) that invert to navy on hover/focus, the "No password required" line, and the "Synthetic data, seed 4521" footer. |
| `pages/NotFound.jsx` | 32 | none | none | none | A styled 404 using the same `PageHeader`, `CARD` and `BUTTON` tokens as every other screen, plus a link back to the case list. |

### 6.4 Components — one row per file

| File | Lines | Props | API endpoints called | State held | What it renders |
|---|---:|---|---|---|---|
| `components/Layout.jsx` | 53 | `role` (string or null), `onRoleChange` (function) | none | none; reads `useLocation()` | The app shell. Redirects to `/sign-in` when `role` is null, and to `ROLE_HOME[role]` when the current path belongs to another role. Otherwise renders `Sidebar` + `TopBar` + `<Outlet context={{role}}/>`. |
| `components/Sidebar.jsx` | 59 | `role` (string) | none | none | The fixed 240px navy rail: `Logo`, the role's three `NavLink`s from `ROLE_NAV` (active state = green left border + green/15 ground), and the "Synthetic data, seed 4521 / Demo build" footer. |
| `components/TopBar.jsx` | 69 | `role`, `onRoleChange` | none | none | A 64px white bar: the "Public Distribution System · Uttar Pradesh · cycle 2026-08" context line on the left, and a "Viewing as" `<select>` over `ROLES` with a hand-drawn SVG chevron on the right. |
| `components/PageHeader.jsx` | 22 | `title` (node), `note` (node, optional) | none | none | The page title band: navy 28px serif `<h1>`, an optional ink-secondary note, a bottom hairline, and `bg-bg` so the page motif cannot run behind the text. |
| `components/SectionHeading.jsx` | 26 | `title` (node), `children` (caption node, optional) | none | none | A navy 18px serif `<h2>` plus its one-line caption, plated together on `bg-bg` so the motif cannot show between them. |
| `components/Ladder.jsx` | 128 | `cycle` (the `CycleSummary` object), `gapHop` (string or null) | none | none | The four-hop reconciliation ladder: four `Node` cards (Allocated / Dispatched / Received / Dispensed, each with its instrument caption) separated by three `Connector` blocks showing Δkg and Δ%, with the located hop drawn in coral and labelled "gap located". A missing reading renders "not reported" in italic ink-muted. |
| `components/TraceTable.jsx` | 79 | `hits` (array of rule-hit objects) | none | none | The reasoning trace as a 5-column grid: rule label + id, reading, threshold, weight (`+30` or `—`), status word. Row style comes from `TRACE_ROW[hit.status]` — coral edge for fired, green for passed, grey edge + sunk ground + muted italic for skipped. |
| `components/Tag.jsx` | 66 | `Tag`: `tone` (default `'neutral'`), `children`, `className`. `SeverityTag`: `severity`, `className`. `StatusTag`: `status`, `className` | none | none | A rectangular 4px-radius tag: tinted background at 15% of the signal colour, solid-colour text, always with a text label. Strings are sentence-cased and underscores replaced with spaces. |
| `components/Skeleton.jsx` | 56 | `SkeletonRows`: `rows` (default 5). `SkeletonPanel`: `lines` (default 3). `LoadingRegion`: `label`, `children` | none | none | Pulse-animated placeholder bars shaped like the real rows/panel, plus an `aria-live` region carrying a screen-reader sentence. No spinner anywhere. |
| `components/EmptyState.jsx` | 32 | `EmptyState`: `title`, `children`. `ErrorState`: `error` (string), `children` | none | none | A plain hairline card with a bold line saying what is not there and a secondary line saying why / what to do. `ErrorState` uses a coral heading, deliberately not a coloured left border. |
| `components/Logo.jsx` | 63 | `LogoMark`: `size` (default 32), `className`. `Logo`: `className` | none | none | An inline SVG emblem — a square frame containing a twice-stepped descending line over a solid baseline — drawn on a 32-unit grid in `currentColor`, plus the mark-and-wordmark lockup used by the sidebar. |
| `components/PageMotif.jsx` | 182 | `variant` (`'officer' \| 'case' \| 'rulebook' \| 'inspector' \| 'auditor' \| 'signin'`) | none | none | A full-bleed decorative background layer at `-z-10`: five SVG tiling patterns (ruled register / four-node chain / stacked clauses / dotted route / timeline scale) at opacity 0.10, plus the logo mark at 720px and opacity 0.08 for sign-in. Tiling variants are masked to fade in over the first 200px. |

### 6.5 Route table

Declared in `frontend/src/App.jsx`:

| Path | Component | Notes |
|---|---|---|
| `/sign-in` | `SignIn` | Outside the `Layout` shell. Receives `onSelect={setRole}`. |
| `/` (index) | `Officer` | Inside `Layout`. Owned by role Officer. |
| `/cases/:caseId` | `CaseDetail` | Inside `Layout`. Owned by no role. |
| `/rulebook` | `Rulebook` | Inside `Layout`. Owned by no role. |
| `/inspector` | `Inspector` | Inside `Layout`. Owned by role Inspector. |
| `/auditor` | `Auditor` | Inside `Layout`. Owned by role Auditor. |
| `*` | `NotFound` | Inside `Layout`. Owned by no role. |

Role → landing path (`ROLE_HOME` in `roles.js`): Officer → `/`,
Inspector → `/inspector`, Auditor → `/auditor`. `redirectFor(role, pathname)`
moves a role off another role's workspace screen; the `OWNER` map covers only
`/`, `/inspector` and `/auditor`.

Sidebar nav per role (`ROLE_NAV`): that role's own screen, then the two shared
links `Case Detail → /cases/C-0041` (**the demo case id is hardcoded in the
nav**) and `Rulebook → /rulebook`.

`role` lives in `App`'s `useState(null)`. Nothing is persisted, so a browser
refresh drops back to `/sign-in`.

### 6.6 Every design token in `ui.js`, verbatim

Class strings, exported names as written:

```js
export const CARD = 'rounded border border-border bg-surface shadow-card'

export const MOTION = 'transition duration-150 ease-out'

const LIFT =
  'hover:-translate-y-px hover:shadow-card active:translate-y-0 active:shadow-none ' +
  'disabled:hover:translate-y-0 disabled:hover:shadow-none'

export const BUTTON_PRIMARY =
  'inline-block rounded border border-navy bg-navy px-4 py-2 text-body-secondary font-medium text-white ' +
  `${MOTION} ${LIFT} ` +
  'hover:border-navy/90 hover:bg-navy/90 active:bg-navy ' +
  'disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-navy'

export const BUTTON =
  'inline-block rounded border border-border-strong bg-surface px-4 py-2 text-body-secondary font-medium text-ink ' +
  `${MOTION} ${LIFT} ` +
  'hover:border-ink-secondary hover:bg-surface-sunk active:bg-surface-sunk ' +
  'disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-border-strong ' +
  'disabled:hover:bg-surface'

const TERTIARY = `${MOTION} underline-offset-2 hover:underline`

export const SORT_HEAD = `text-table-header uppercase ${TERTIARY}`

export const CARD_INTERACTIVE =
  `${CARD} ${MOTION} hover:-translate-y-px hover:bg-surface-sunk ` +
  'active:translate-y-0 active:bg-surface-sunk'

export const CARD_OPTION =
  `group rounded border border-border-strong bg-surface shadow-card ${MOTION} ` +
  'hover:-translate-y-px hover:border-navy hover:bg-navy ' +
  'focus-visible:border-navy focus-visible:bg-navy ' +
  'active:translate-y-0 active:bg-navy'

export const FIELD =
  'rounded border border-border-strong bg-surface px-4 py-2 text-body-secondary text-ink ' +
  `${MOTION} hover:border-ink-secondary`

export const LABEL = 'mb-1 block text-meta-label uppercase text-ink-secondary'

export const COLUMN_HEAD = 'text-table-header uppercase text-ink-secondary'

export const CAPTION = 'mt-1 text-body-secondary text-ink-secondary'

export const BODY = 'text-body text-ink'
export const CELL = 'text-table-cell text-ink'
export const CELL_MUTED = 'text-table-cell text-ink-secondary'
export const CELL_NUM = 'num text-table-cell text-ink text-right'

export const ROW = 'px-4 py-4'
```

`LIFT` and `TERTIARY` are module-private (not exported). Note that the actual
colour and size values are **not** in `ui.js` — they are Tailwind theme keys
defined in `tailwind.config.js`:

```
colors: transparent, current, white #FFFFFF,
        bg #FAF8F4, navy #132A47, green #2E7D5B, gold #C8952B, coral #D4573D,
        ink #14171A, ink-secondary #5B6169, ink-muted #94989E,
        border #DDD9D0, border-strong #C7C2B6,
        surface #FFFFFF, surface-sunk #F3F0EA

spacing (REPLACED, not extended): 0 0px · px 1px · 1 4px · 2 8px · 4 16px ·
        6 24px · 8 32px · 12 48px

borderRadius (REPLACED): none 0px · DEFAULT 4px      ('full' deliberately absent)

fontSize (extended):
  score-display    48px / 1     weight 600
  page-title       28px / 1.2   weight 600
  section-heading  18px / 1.3   weight 600
  body             15px / 1.5
  body-secondary   14px / 1.5
  meta-label       12px / 1.4   tracking 0.04em, weight 500
  table-header     12px / 1.4   tracking 0.04em, weight 500
  table-cell       14px / 1.5

fontFamily: display = Fraunces, Georgia, serif
            sans    = Inter, system-ui, sans-serif

width.sidebar 240px · height.topbar 64px · minHeight.region 320px
boxShadow.card '0 1px 2px rgba(19, 42, 71, 0.06)'
```

Severity/status maps live in `severity.js`, not `ui.js`:
`SEVERITY_BORDER` (HIGH → `border-l-coral`, MEDIUM → `border-l-gold`,
LOW → `border-l-green`), `TRACE_ROW` (fired / passed / skipped styling),
`OPERATOR_SYMBOL` (`lt <`, `lte ≤`, `gt >`, `gte ≥`, `eq =`), `HOP_LABEL`,
`HOP_ACTION`, plus `formatKg` (`Intl.NumberFormat('en-IN')`, 0 dp) and
`formatPct` (2 dp, null-preserving). Tag tones are in `Tag.jsx`:
`high` coral/15, `medium` gold/15, `low` green/15, `open` gold/15,
`closed` green/15, `neutral` surface-sunk + ink-secondary.

### 6.7 Library questions

| Category | Present? | Detail |
|---|---|---|
| **Charting / visualisation library** | **No** | `package.json` dependencies are exactly `@fontsource/fraunces`, `@fontsource/inter`, `react`, `react-dom`, `react-router-dom`. Dev deps: `@vitejs/plugin-react`, `autoprefixer`, `postcss`, `tailwindcss`, `vite`. **Recharts is named in CLAUDE.md's fixed stack and in the README tech table but is NOT installed and NOT imported anywhere.** No chart of any kind is rendered; the "trend" element promised in PROJECT-BRIEF's CaseDetail screen description does not exist. |
| **Map library** | **No** | No Leaflet, Mapbox, react-map-gl, Google Maps, or any tile source. `shops.lat`/`lng` are carried through `ShopRef` into the API response and into every case row, and are never rendered — `schemas.py` says "drop a map pin", but nothing does. |
| **Table library** | **No** | No TanStack Table, react-table, AG Grid or DataTables. Every "table" is a hand-built CSS-grid layout: a header `<div>` and a `<ul>`/`<ol>` of rows sharing a `GRID` class string. Sorting on the Officer page is a hand-rolled `SORTS` map plus `Array.prototype.sort`. |
| **Component library** | **No** | No MUI, Chakra, shadcn, Radix, Headless UI. All controls are native elements styled with the `ui.js` token strings. |
| **State library** | **No** | No Redux, Zustand, Jotai, React Query, SWR. State is `useState` plus one shared `useApi` hook. |
| **Icons** | Inline SVG only | The logo mark, the three role icons on SignIn, the TopBar chevron and all five page motifs are hand-written SVG in JSX. |
| **Fonts** | Self-hosted | `@fontsource/fraunces` (400, 600) and `@fontsource/inter` (400, 500, 600), imported in `main.jsx`, explicitly so the demo does not depend on venue wifi reaching Google Fonts. |

### 6.8 Backend base URL

**Hardcoded. Not from an environment variable.** `frontend/src/api.js`, line 13:

```js
const API_BASE = 'http://localhost:8000'
```

It is a module-private `const` — not exported, not read from `import.meta.env`,
with no `.env` file anywhere in the repo and no `VITE_` variable referenced in
any source file. Every network call in the app goes through the single
`apiFetch()` wrapper in this file, so this one line is the only place the origin
appears.

The same file carries a mock switch, currently off:

```js
import caseDetail from '@contract/case_detail.json'

export const USE_MOCK = false
```

`@contract` is a Vite alias to `../docs/contract` (`vite.config.js`), so the
frozen contract file is imported directly from `docs/` rather than copied into
`src/`. When `USE_MOCK` is true, only `/api/cases/{id}` resolves — every other
path throws by design rather than returning a plausible empty object.

The dev server is pinned in `vite.config.js` to port 5173 with
`strictPort: true` and `fs.allow: ['..']`, which is what lets the alias reach
above the Vite root. That port matches the CORS allow-list in `backend/app/main.py`.

---

## 7. Tests

### 7.1 Full recursive listing of `backend/tests/`

```
backend/tests/
├── .gitkeep            1 line
├── __init__.py         2 lines
├── conftest.py       215 lines
├── test_api.py       150 lines
├── test_audit.py     182 lines
├── test_complaints.py 88 lines
├── test_memo.py       72 lines
├── test_reconcile.py  98 lines
├── test_rulebook.py  169 lines
└── test_score.py     167 lines
```

Total 944 lines across 8 Python files, 60 test functions (one of which is
parametrised four ways, giving 63 collected cases).

There is **no** `pytest.ini`, `setup.cfg`, `pyproject.toml` or `tox.ini` anywhere
in `backend/` — pytest runs on defaults, and `backend/tests/__init__.py` plus
running from `backend/` is what makes `import app...` resolve.
`backend/.pytest_cache/` exists (with `lastfailed`, `nodeids`, `stepwise`), and
so does a stray `frontend/.pytest_cache/`, which is inert — there are no Python
tests under `frontend/`.


### 7.2 Every test file, verbatim

#### `backend/tests/__init__.py` (2 lines, verbatim)

```python
"""pytest suite. Fixture expectations live in docs/contract/fixtures.md and
are asserted before each engine function is implemented."""
```

#### `backend/tests/conftest.py` (215 lines, verbatim)

```python
"""Raw inputs for the three contract fixtures.

These are RAW INPUTS only — the same columns seed.py writes. Variances,
fired rules, coverage_pct, gap_hop and score are never hardcoded here; the
tests derive them through engine/ so that a wrong derivation fails a test
instead of being handed the right answer.

Source of truth: docs/contract/fixtures.md.

SimpleNamespace stands in for a SQLAlchemy row on purpose — the engine reads
these by attribute, exactly as it will read a real Cycle/Delivery/Shop.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.engine import rulebook as rulebook_mod
from app.models import Complaint, Shop

# Case open time, and the anchor every complaint window is measured back from
# (docs/contract/fixtures.md).
CASE_OPENED_AT = datetime(2026, 8, 14, 9, 12, 0)

DISPATCH_TS = datetime(2026, 8, 10, 6, 0, 0)


def _cycle(shop_id, allocated, dispatched, weighed, dispensed, hour_violations):
    return SimpleNamespace(
        id=1,
        shop_id=shop_id,
        period="2026-08",
        allocated_kg=allocated,
        dispatched_kg=dispatched,
        weighed_kg=weighed,
        dispensed_kg=dispensed,
        hour_violations_month=hour_violations,
        opened_on=datetime(2026, 8, 1, 0, 0, 0),
        closed_on=None,
    )


def _delivery(shop_id, gap_hours, gps_deviation_km, gps_available):
    return SimpleNamespace(
        id=1,
        cycle_id=1,
        shop_id=shop_id,
        vehicle_no="UP32-AB-0001",
        route_id="R-01",
        dispatch_ts=DISPATCH_TS,
        arrival_ts=DISPATCH_TS + timedelta(hours=gap_hours),
        gps_deviation_km=gps_deviation_km,
        gps_available=gps_available,
    )


def _txns(shop_id, distinct_cards, duplicates=5):
    """distinct_cards distinct card_ids, plus repeat visits by the first few.

    The duplicates matter: txn_card_ratio counts DISTINCT cards, so a naive
    len(txns) implementation has to fail here rather than pass by luck.
    """
    rows = [
        SimpleNamespace(
            id=i,
            cycle_id=1,
            shop_id=shop_id,
            card_id=f"{shop_id}-CARD-{i:05d}",
            txn_ts=DISPATCH_TS + timedelta(hours=i % 72),
            quantity_kg=5.0,
            auth_mode="biometric",
            outside_hours=False,
        )
        for i in range(distinct_cards)
    ]
    rows.extend(
        SimpleNamespace(
            id=10_000 + i,
            cycle_id=1,
            shop_id=shop_id,
            card_id=f"{shop_id}-CARD-{i:05d}",
            txn_ts=DISPATCH_TS + timedelta(hours=i),
            quantity_kg=5.0,
            auth_mode="manual",
            outside_hours=False,
        )
        for i in range(duplicates)
    )
    return rows


def _shop(shop_id, name, block, ration_cards):
    return SimpleNamespace(
        id=shop_id,
        name=name,
        block=block,
        district="Sitapur",
        lat=27.57,
        lng=80.68,
        ration_cards=ration_cards,
        opens_hour=9,
        closes_hour=17,
        dealer_name=None,
    )


# --- #4521 Sitapur — transport diversion, everything available ---------------
RAW_4521 = {
    "shop": _shop("4521", "FPS Sitapur-12", "Sitapur", 1200),
    "cycle": _cycle("4521", 12000, 12000, 11015, 10980, 1),
    "delivery": _delivery("4521", 61, 3.4, True),
    "txns": _txns("4521", 1056),
    "complaints_in_window": 7,
}

# --- #4102 Barabanki — transport diversion, GPS unit not fitted -------------
RAW_4102 = {
    "shop": _shop("4102", "FPS Barabanki-07", "Barabanki", 900),
    "cycle": _cycle("4102", 8000, 8000, 7512, 7490, 1),
    # gps_available False, so gps_deviation_km must degrade to None -> skipped.
    "delivery": _delivery("4102", 52, None, False),
    "txns": _txns("4102", 639),
    "complaints_in_window": 2,
}

# --- #4788 Hargaon — counter skimming at the shop ---------------------------
RAW_4788 = {
    "shop": _shop("4788", "FPS Hargaon-03", "Hargaon", 1000),
    "cycle": _cycle("4788", 9000, 9000, 8970, 8190, 4),
    "delivery": _delivery("4788", 44, 0.8, True),
    "txns": _txns("4788", 550),
    "complaints_in_window": 6,
}


@pytest.fixture
def rulebook():
    """The real app/rules.yaml, loaded at runtime — never mirrored here."""
    return rulebook_mod.load()


@pytest.fixture
def raw_4521():
    return RAW_4521


@pytest.fixture
def raw_4102():
    return RAW_4102


@pytest.fixture
def raw_4788():
    return RAW_4788


# --- A throwaway database, not backend/leakproof.db --------------------------
#
# In-memory and rebuilt per test: the committed SQLite file is the demo's
# evidence, and a test suite that writes to it would leave the demo in a state
# nobody chose. Complaint timings mirror seed.py — some inside the window, some
# deliberately outside it, so a window check that silently matches everything
# fails a test instead of passing quietly.

COMPLAINTS_IN_WINDOW = {"4521": 7, "4102": 2, "4788": 6}
COMPLAINTS_OUTSIDE_WINDOW = {"4521": 2, "4102": 1, "4788": 0}


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, future=True)()

    for raw in (RAW_4521, RAW_4102, RAW_4788):
        shop = raw["shop"]
        session.add(
            Shop(
                id=shop.id,
                name=shop.name,
                block=shop.block,
                district=shop.district,
                lat=shop.lat,
                lng=shop.lng,
                ration_cards=shop.ration_cards,
                opens_hour=shop.opens_hour,
                closes_hour=shop.closes_hour,
                dealer_name=shop.dealer_name,
            )
        )
        for n in range(COMPLAINTS_IN_WINDOW[shop.id]):
            session.add(_complaint(shop.id, CASE_OPENED_AT - timedelta(days=n % 13, hours=1)))
        for n in range(COMPLAINTS_OUTSIDE_WINDOW[shop.id]):
            # 20+ days back: outside any 14-day window, by a wide margin.
            session.add(_complaint(shop.id, CASE_OPENED_AT - timedelta(days=20 + n * 10)))

    session.commit()
    yield session
    session.close()


def _complaint(shop_id, filed_at):
    return Complaint(
        shop_id=shop_id,
        filed_at=filed_at,
        source="portal",
        category="short_weight",
        text="Received less than the entitled quantity.",
        status="open",
        linked_case_id=None,
    )
```

#### `backend/tests/test_reconcile.py` (98 lines, verbatim)

```python
"""F1 — four-hop reconciliation ladder, asserted against docs/contract/fixtures.md.

Written before engine/reconcile.py had any logic. Every number below is copied
from the fixture table, not from a run of the code.
"""

from app.engine.reconcile import locate_gap, reconcile


def test_4521_variances(raw_4521):
    f = reconcile(raw_4521["cycle"], raw_4521["delivery"], raw_4521["txns"], raw_4521["shop"])
    assert f["variance_dispatch_to_receipt"] == -8.21
    assert f["variance_receipt_to_counter"] == -0.32


def test_4102_variances(raw_4102):
    f = reconcile(raw_4102["cycle"], raw_4102["delivery"], raw_4102["txns"], raw_4102["shop"])
    assert f["variance_dispatch_to_receipt"] == -6.10
    assert f["variance_receipt_to_counter"] == -0.29


def test_4788_variances(raw_4788):
    f = reconcile(raw_4788["cycle"], raw_4788["delivery"], raw_4788["txns"], raw_4788["shop"])
    assert f["variance_dispatch_to_receipt"] == -0.33
    assert f["variance_receipt_to_counter"] == -8.70


def test_delivery_gap_hours(raw_4521, raw_4102, raw_4788):
    for raw, expected in ((raw_4521, 61), (raw_4102, 52), (raw_4788, 44)):
        f = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
        assert f["delivery_gap_hours"] == expected


def test_txn_card_ratio_counts_distinct_cards(raw_4521, raw_4102, raw_4788):
    for raw, expected in ((raw_4521, 0.88), (raw_4102, 0.71), (raw_4788, 0.55)):
        f = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
        assert f["txn_card_ratio"] == expected


def test_hour_violations_passed_through(raw_4521, raw_4102, raw_4788):
    for raw, expected in ((raw_4521, 1), (raw_4102, 1), (raw_4788, 4)):
        f = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
        assert f["hour_violations_month"] == expected


def test_gps_available_reports_the_reading(raw_4521, raw_4788):
    assert (
        reconcile(raw_4521["cycle"], raw_4521["delivery"], raw_4521["txns"], raw_4521["shop"])[
            "gps_deviation_km"
        ]
        == 3.4
    )
    assert (
        reconcile(raw_4788["cycle"], raw_4788["delivery"], raw_4788["txns"], raw_4788["shop"])[
            "gps_deviation_km"
        ]
        == 0.8
    )


def test_gps_unavailable_is_none_not_zero(raw_4102):
    """F5: 'no device fitted' must not read as 'device reported 0.0 km'."""
    f = reconcile(raw_4102["cycle"], raw_4102["delivery"], raw_4102["txns"], raw_4102["shop"])
    assert f["gps_deviation_km"] is None
    assert f["gps_deviation_km"] != 0


def test_locate_gap_picks_the_more_negative_hop(raw_4521, raw_4102, raw_4788):
    for raw, expected in (
        (raw_4521, "dispatch_to_receipt"),
        (raw_4102, "dispatch_to_receipt"),
        (raw_4788, "receipt_to_counter"),
    ):
        f = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
        assert locate_gap(f) == expected


def test_missing_weighed_kg_degrades_rather_than_zeroes(raw_4521):
    """An offline shop scale yields None variances, never a 100% shortfall."""
    cycle = raw_4521["cycle"]
    offline = type(cycle)(**{**vars(cycle), "weighed_kg": None})
    f = reconcile(offline, raw_4521["delivery"], raw_4521["txns"], raw_4521["shop"])
    assert f["variance_dispatch_to_receipt"] is None
    assert f["variance_receipt_to_counter"] is None


def test_missing_arrival_scan_leaves_gap_unknown(raw_4521):
    delivery = raw_4521["delivery"]
    in_transit = type(delivery)(**{**vars(delivery), "arrival_ts": None})
    f = reconcile(raw_4521["cycle"], in_transit, raw_4521["txns"], raw_4521["shop"])
    assert f["delivery_gap_hours"] is None


def test_locate_gap_returns_none_when_neither_hop_is_measurable():
    assert (
        locate_gap({"variance_dispatch_to_receipt": None, "variance_receipt_to_counter": None})
        is None
    )
```

#### `backend/tests/test_rulebook.py` (169 lines, verbatim)

```python
"""F2 — versioned YAML rulebook, asserted against docs/contract/fixtures.md
and the frozen trace rows in docs/contract/case_detail.json.

Written before engine/rulebook.py had any logic.
"""

import pytest

from app.engine.reconcile import reconcile
from app.engine.rulebook import evaluate, load


def _hits_by_id(features, rulebook):
    return {h["rule_id"]: h for h in evaluate(features, rulebook)}


def _features(raw):
    return reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])


def test_load_reads_the_yaml_file_at_runtime(rulebook):
    assert rulebook["version"] == "1.0.0"
    assert rulebook["updated_by"] == "District Supply Office, Sitapur"
    assert rulebook["severity_bands"] == {"high": 75, "medium": 50}
    assert [r["id"] for r in rulebook["rules"]] == [
        "weighing_variance",
        "delivery_gap",
        "gps_deviation",
        "counter_variance",
        "transaction_mismatch",
        "operating_hours",
    ]
    assert rulebook["corroboration"]["complaint_bonus"] == {
        "min_complaints": 3,
        "window_days": 14,
        "weight": 10,
    }


def test_weights_total_120_and_bonus_is_10(rulebook):
    """Invariant 3: 120 + 10 = 130 possible. Do not renormalise to 100."""
    assert sum(r["weight"] for r in rulebook["rules"]) == 120
    assert rulebook["corroboration"]["complaint_bonus"]["weight"] == 10


def test_load_from_explicit_path_matches_default(rulebook):
    from app.engine import rulebook as rulebook_mod

    assert load(rulebook_mod.RULES_PATH) == rulebook


def test_every_rule_produces_exactly_one_trace_row(raw_4521, rulebook):
    hits = evaluate(_features(raw_4521), rulebook)
    assert len(hits) == len(rulebook["rules"])
    assert [h["rule_id"] for h in hits] == [r["id"] for r in rulebook["rules"]]
    for hit in hits:
        assert set(hit) == {
            "rule_id",
            "label",
            "raw_value",
            "threshold",
            "contribution",
            "severity",
            "status",
        }


def test_4521_trace_matches_the_frozen_contract(raw_4521, rulebook):
    """The three fired rows are copied from docs/contract/case_detail.json."""
    hits = _hits_by_id(_features(raw_4521), rulebook)

    assert hits["weighing_variance"] == {
        "rule_id": "weighing_variance",
        "label": "Weighing shortfall beyond tolerance",
        "raw_value": "-8.21%",
        "threshold": "-5.0%",
        "contribution": 30,
        "severity": "high",
        "status": "fired",
    }
    assert hits["delivery_gap"] == {
        "rule_id": "delivery_gap",
        "label": "Delivery-to-dispatch gap exceeded",
        "raw_value": "61 hrs",
        "threshold": "48 hrs",
        "contribution": 25,
        "severity": "high",
        "status": "fired",
    }
    assert hits["gps_deviation"] == {
        "rule_id": "gps_deviation",
        "label": "Vehicle deviated from registered route",
        "raw_value": "3.4 km",
        "threshold": "2.0 km",
        "contribution": 22,
        "severity": "high",
        "status": "fired",
    }


def test_4521_non_firing_rules_are_passed_and_contribute_zero(raw_4521, rulebook):
    hits = _hits_by_id(_features(raw_4521), rulebook)
    for rule_id, raw_value in (
        ("counter_variance", "-0.32%"),
        ("transaction_mismatch", "0.88"),
        ("operating_hours", "1"),
    ):
        assert hits[rule_id]["status"] == "passed"
        assert hits[rule_id]["contribution"] == 0
        assert hits[rule_id]["raw_value"] == raw_value


def test_4102_fires_two_rules(raw_4102, rulebook):
    hits = _hits_by_id(_features(raw_4102), rulebook)
    fired = {rid: h["contribution"] for rid, h in hits.items() if h["status"] == "fired"}
    assert fired == {"weighing_variance": 30, "delivery_gap": 25}


def test_4102_missing_gps_is_skipped_never_passed(raw_4102, rulebook):
    """Invariant 4. A rule we could not evaluate is not a rule that passed."""
    hit = _hits_by_id(_features(raw_4102), rulebook)["gps_deviation"]
    assert hit["status"] == "skipped"
    assert hit["status"] != "passed"
    assert hit["contribution"] == 0
    assert hit["raw_value"] is None
    # The threshold still shows, so the trace says WHAT we could not check.
    assert hit["threshold"] == "2.0 km"


def test_4788_fires_the_counter_skim_rules(raw_4788, rulebook):
    hits = _hits_by_id(_features(raw_4788), rulebook)
    fired = {rid: h["contribution"] for rid, h in hits.items() if h["status"] == "fired"}
    assert fired == {
        "counter_variance": 20,
        "transaction_mismatch": 15,
        "operating_hours": 8,
    }
    assert hits["counter_variance"]["raw_value"] == "-8.70%"
    assert hits["transaction_mismatch"]["raw_value"] == "0.55"
    assert hits["operating_hours"]["raw_value"] == "4"


def test_gte_operator_fires_exactly_on_the_threshold(rulebook):
    """operating_hours is `gte 3`: 3 fires, 2 does not."""
    features = {"hour_violations_month": 3}
    assert _hits_by_id(features, rulebook)["operating_hours"]["status"] == "fired"
    features = {"hour_violations_month": 2}
    assert _hits_by_id(features, rulebook)["operating_hours"]["status"] == "passed"


def test_lt_operator_does_not_fire_exactly_on_the_threshold(rulebook):
    """weighing_variance is `lt -5.0`: -5.0 itself is within tolerance."""
    features = {"variance_dispatch_to_receipt": -5.0}
    assert _hits_by_id(features, rulebook)["weighing_variance"]["status"] == "passed"
    features = {"variance_dispatch_to_receipt": -5.01}
    assert _hits_by_id(features, rulebook)["weighing_variance"]["status"] == "fired"


def test_a_field_absent_from_features_is_skipped(rulebook):
    """Absent and None are the same thing: we could not check."""
    for hit in evaluate({}, rulebook):
        assert hit["status"] == "skipped"
        assert hit["contribution"] == 0


def test_unknown_operator_is_refused_loudly(rulebook):
    broken = {**rulebook, "rules": [{**rulebook["rules"][0], "operator": "approximately"}]}
    with pytest.raises(ValueError):
        evaluate({"variance_dispatch_to_receipt": -8.21}, broken)
```

#### `backend/tests/test_score.py` (167 lines, verbatim)

```python
"""F3 + F5 — composite score, reasoning trace, coverage.

These are the acceptance criteria. Every expected number comes from
docs/contract/fixtures.md; none of them is a recording of what the code did.

Invariant 1: #4521 scores EXACTLY 87 (30 + 25 + 22 + 10). If a change makes
it 86 or 88, the change is wrong, not the 87.
"""

import pytest

from app.engine.reconcile import locate_gap, reconcile
from app.engine.score import compute


def _features(raw):
    return reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])


def _result(raw, rulebook):
    return compute(_features(raw), rulebook, raw["complaints_in_window"])


# --- Acceptance: #4521 Sitapur ----------------------------------------------


def test_4521_scores_exactly_87(raw_4521, rulebook):
    assert _result(raw_4521, rulebook)["score"] == 87


def test_4521_is_high_with_full_coverage(raw_4521, rulebook):
    result = _result(raw_4521, rulebook)
    assert result["severity"] == "HIGH"
    assert result["coverage_pct"] == 100
    assert result["gap_hop"] == "dispatch_to_receipt"


def test_4521_score_is_the_sum_of_fired_rules_plus_the_bonus(raw_4521, rulebook):
    result = _result(raw_4521, rulebook)
    fired = [h["contribution"] for h in result["rule_hits"] if h["status"] == "fired"]
    assert sorted(fired, reverse=True) == [30, 25, 22]
    assert result["complaint_bonus"] == {"count": 7, "window_days": 14, "contribution": 10}
    assert sum(fired) + result["complaint_bonus"]["contribution"] == 87


# --- Acceptance: #4102 Barabanki --------------------------------------------


def test_4102_scores_exactly_55(raw_4102, rulebook):
    assert _result(raw_4102, rulebook)["score"] == 55


def test_4102_is_medium_with_reduced_coverage(raw_4102, rulebook):
    result = _result(raw_4102, rulebook)
    assert result["severity"] == "MEDIUM"
    assert result["coverage_pct"] == 83
    assert result["gap_hop"] == "dispatch_to_receipt"


def test_4102_gps_deviation_is_none(raw_4102):
    assert _features(raw_4102)["gps_deviation_km"] is None


def test_4102_bonus_does_not_fire_below_three_complaints(raw_4102, rulebook):
    assert _result(raw_4102, rulebook)["complaint_bonus"] == {
        "count": 2,
        "window_days": 14,
        "contribution": 0,
    }


def test_4102_coverage_counts_the_skipped_rule_not_the_weight(raw_4102, rulebook):
    """5 of 6 rules evaluated -> 83%. Skipped weight is not redistributed."""
    result = _result(raw_4102, rulebook)
    skipped = [h for h in result["rule_hits"] if h["status"] == "skipped"]
    assert [h["rule_id"] for h in skipped] == ["gps_deviation"]
    assert result["coverage_pct"] == round(5 / 6 * 100)


# --- Acceptance: #4788 Hargaon ----------------------------------------------


def test_4788_scores_exactly_53(raw_4788, rulebook):
    assert _result(raw_4788, rulebook)["score"] == 53


def test_4788_is_medium_and_localises_the_counter(raw_4788, rulebook):
    result = _result(raw_4788, rulebook)
    assert result["severity"] == "MEDIUM"
    assert result["gap_hop"] == "receipt_to_counter"
    assert result["coverage_pct"] == 100


def test_4788_fires_the_counter_ladder_plus_bonus(raw_4788, rulebook):
    result = _result(raw_4788, rulebook)
    fired = [h["contribution"] for h in result["rule_hits"] if h["status"] == "fired"]
    assert sorted(fired, reverse=True) == [20, 15, 8]
    assert result["complaint_bonus"]["contribution"] == 10


# --- Shape, bands and the display cap ---------------------------------------


def test_result_carries_the_full_trace_and_rulebook_version(raw_4521, rulebook):
    result = _result(raw_4521, rulebook)
    assert result["rulebook_version"] == "1.0.0"
    assert len(result["rule_hits"]) == len(rulebook["rules"])
    assert isinstance(result["memo"], str) and result["memo"]


def test_severity_bands(rulebook):
    """HIGH >= 75, MEDIUM >= 50, else LOW — read from rules.yaml."""
    bands = [
        (-90.0, 61, 3.4, 0.5, 10, 7, "HIGH"),  # everything fires
        (-6.0, 52, 0.1, 0.9, 0, 0, "MEDIUM"),  # 30 + 25 = 55
        (-1.0, 10, 0.1, 0.9, 0, 0, "LOW"),  # nothing fires
    ]
    for d2r, gap, gps, ratio, hours, complaints, expected in bands:
        features = {
            "variance_dispatch_to_receipt": d2r,
            "variance_receipt_to_counter": -0.1,
            "delivery_gap_hours": gap,
            "gps_deviation_km": gps,
            "txn_card_ratio": ratio,
            "hour_violations_month": hours,
        }
        assert compute(features, rulebook, complaints)["severity"] == expected


def test_display_score_caps_at_100_but_the_raw_total_survives(rulebook):
    """Invariant 3: 130 is arithmetically possible. Cap the display, keep the raw."""
    everything = {
        "variance_dispatch_to_receipt": -40.0,
        "variance_receipt_to_counter": -40.0,
        "delivery_gap_hours": 96,
        "gps_deviation_km": 9.9,
        "txn_card_ratio": 0.1,
        "hour_violations_month": 9,
    }
    result = compute(everything, rulebook, 7)
    assert result["score"] == 100
    assert result["score_raw"] == 130


def test_a_skipped_rule_never_contributes(rulebook):
    result = compute({}, rulebook, 0)
    assert result["score"] == 0
    assert result["coverage_pct"] == 0
    assert all(h["status"] == "skipped" for h in result["rule_hits"])


def test_zscore_is_not_an_input_to_the_score(raw_4521, rulebook):
    """Invariant 5: the statistical layer is a confirming badge, worth ZERO."""
    features = _features(raw_4521)
    baseline = compute(features, rulebook, 7)["score"]
    louder = compute({**features, "z_score": 9.9}, rulebook, 7)["score"]
    assert baseline == louder == 87


@pytest.mark.parametrize(
    "count,expected",
    [(0, 0), (2, 0), (3, 10), (7, 10)],
)
def test_bonus_threshold_is_three_complaints(rulebook, count, expected):
    result = compute({}, rulebook, count)
    assert result["complaint_bonus"]["contribution"] == expected
    assert result["complaint_bonus"]["window_days"] == 14
```

#### `backend/tests/test_complaints.py` (88 lines, verbatim)

```python
"""F4 — complaint window matching and the corroboration bonus.

Fixture expectations (docs/contract/fixtures.md): #4521 has 7 complaints in the
window, #4102 has 2 (below the minimum, so no bonus), #4788 has 6. #4521 and
#4102 also carry older complaints that must NOT be counted.
"""

from datetime import timedelta

from app.engine.complaints import ANCHOR, complaints_in_window, link
from app.engine.score import compute
from app.models import Complaint


def test_counts_match_the_fixture_table(db):
    assert link(db, "4521") == 7
    assert link(db, "4102") == 2
    assert link(db, "4788") == 6


def test_older_complaints_are_excluded(db):
    """The window is applied, not decorative — #4521 has 9 complaints in all."""
    assert db.query(Complaint).filter(Complaint.shop_id == "4521").count() == 9
    assert link(db, "4521") == 7


def test_window_days_comes_from_the_rulebook(db):
    """Default window is whatever rules.yaml says, currently 14 days."""
    from app.engine.rulebook import load

    assert load()["corroboration"]["complaint_bonus"]["window_days"] == 14
    # Widening the window past the older complaints picks them up.
    assert link(db, "4521", window_days=120) == 9


def test_a_narrow_window_counts_fewer(db):
    assert link(db, "4521", window_days=1) < 7


def test_complaints_in_window_returns_rows_newest_first(db):
    rows = complaints_in_window(db, "4521")
    assert len(rows) == 7
    assert [r.filed_at for r in rows] == sorted((r.filed_at for r in rows), reverse=True)
    assert all(r.filed_at >= ANCHOR - timedelta(days=14) for r in rows)


def test_link_attaches_the_case_id_to_matched_complaints_only(db):
    link(db, "4521", case_id="C-0041")
    db.commit()

    linked = db.query(Complaint).filter(Complaint.linked_case_id == "C-0041").all()
    assert len(linked) == 7
    assert all(c.shop_id == "4521" for c in linked)

    # Null means unlinked, not unexamined — the older two stay null.
    unlinked = (
        db.query(Complaint)
        .filter(Complaint.shop_id == "4521", Complaint.linked_case_id.is_(None))
        .count()
    )
    assert unlinked == 2


def test_link_without_a_case_id_counts_without_writing(db):
    assert link(db, "4521") == 7
    assert db.query(Complaint).filter(Complaint.linked_case_id.isnot(None)).count() == 0


def test_the_count_feeds_compute_directly(db, rulebook, raw_4521):
    """F4's output is exactly what compute() already takes as complaints_count."""
    from app.engine.reconcile import reconcile

    features = reconcile(
        raw_4521["cycle"], raw_4521["delivery"], raw_4521["txns"], raw_4521["shop"]
    )
    result = compute(features, rulebook, link(db, "4521"))
    assert result["complaint_bonus"] == {"count": 7, "window_days": 14, "contribution": 10}
    assert result["score"] == 87


def test_4102_stays_below_the_bonus_threshold(db, rulebook):
    result = compute({}, rulebook, link(db, "4102"))
    assert result["complaint_bonus"]["count"] == 2
    assert result["complaint_bonus"]["contribution"] == 0


def test_unknown_shop_has_no_complaints(db):
    assert link(db, "9999") == 0
```

#### `backend/tests/test_memo.py` (72 lines, verbatim)

```python
"""Plain-language memo.

The memo is an f-string template. It is not AI-generated and no test here
should ever be read as implying that it is — "template now, LLM later" is a
declared scoping decision.

The #4521 memo is asserted byte-for-byte against docs/contract/case_detail.json,
and the expected string is READ FROM that file rather than copied into this
module — the contract and the engine output cannot drift apart without this
test failing.
"""

import json
from pathlib import Path

from app.engine.memo import build_memo
from app.engine.reconcile import reconcile
from app.engine.score import compute

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs" / "contract" / "case_detail.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _result(raw, rulebook):
    features = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
    return compute(features, rulebook, raw["complaints_in_window"])


def test_4521_memo_matches_the_frozen_contract_exactly(raw_4521, rulebook):
    assert _result(raw_4521, rulebook)["memo"] == CONTRACT["memo"]


def test_4521_memo_records_the_corroborating_complaints(raw_4521, rulebook):
    memo = _result(raw_4521, rulebook)["memo"]
    assert "7 complaints" in memo
    assert "14 days" in memo


def test_4102_memo_names_what_could_not_be_checked(raw_4102, rulebook):
    """F5 in prose: the officer must see the gap in the evidence, not just the score."""
    memo = _result(raw_4102, rulebook)["memo"]
    assert memo.startswith("Shop #4102 flagged MEDIUM (55/100):")
    assert "weighing shortfall of 6.1%" in memo
    assert "52-hour delivery gap" in memo
    assert "Not evaluated: Vehicle deviated from registered route" in memo
    assert "the reading was unavailable" in memo
    # No bonus fired, so no corroboration claim may appear.
    assert "complaints" not in memo


def test_4788_memo_describes_the_counter_skim(raw_4788, rulebook):
    memo = _result(raw_4788, rulebook)["memo"]
    assert memo.startswith("Shop #4788 flagged MEDIUM (53/100):")
    assert "counter shortfall of 8.7%" in memo
    assert "6 complaints" in memo


def test_memo_with_nothing_fired_says_so_plainly():
    memo = build_memo(
        shop_id="4999",
        score=0,
        severity="LOW",
        rule_hits=[],
        complaint_bonus={"count": 0, "window_days": 14, "contribution": 0},
    )
    assert memo == "Shop #4999 flagged LOW (0/100): no rules fired."


def test_memo_never_claims_to_be_generated(raw_4521, rulebook):
    memo = _result(raw_4521, rulebook)["memo"].lower()
    for overclaim in ("ai", "generated", "model", "llm"):
        assert overclaim not in memo.split()
```

#### `backend/tests/test_audit.py` (182 lines, verbatim)

```python
"""F6 — append-only audit trail and reproducibility.

Invariant 6: audit_log is insert-only. No in-place edit, no removal, no helper
anywhere that could perform either. CLAUDE.md asks for a grep before any commit
that touches audit code; test_audit_code_contains_no_mutation_calls runs that
same check automatically so it cannot be forgotten.
"""

import json
from datetime import datetime
from pathlib import Path

from app.engine.audit import log, recompute
from app.models import AuditLog, Case, Cycle

APP_DIR = Path(__file__).resolve().parents[1] / "app"

# The two patterns from CLAUDE.md section 6, assembled from fragments so that
# this file — which lives at a path containing "audit" — does not itself match
# the grep it exists to enforce.
#
# Joined with str.join rather than with +: the compiler folds adjacent string
# literals into one constant, which would put the whole pattern back into
# __pycache__ and trip the grep on a build artifact instead of on real code.
FORBIDDEN_CALLS = ("".join((".dele", "te(")), "".join(("UPD", "ATE")))

AUDITED_SOURCES = (APP_DIR / "engine" / "audit.py", APP_DIR / "routers" / "audit.py")


def _case(db, case_id="C-0041", score=87):
    cycle = Cycle(
        shop_id="4521",
        period="2026-08",
        allocated_kg=12000.0,
        dispatched_kg=12000.0,
        weighed_kg=11015.0,
        dispensed_kg=10980.0,
        hour_violations_month=1,
        opened_on=datetime(2026, 8, 1),
    )
    db.add(cycle)
    db.flush()
    case = Case(
        id=case_id,
        shop_id="4521",
        cycle_id=cycle.id,
        score=score,
        severity="HIGH",
        status="OPEN",
        opened_at=datetime(2026, 8, 14, 9, 12),
        gap_hop="dispatch_to_receipt",
        coverage_pct=100,
        rulebook_version="1.0.0",
        complaint_count=7,
        complaint_window_days=14,
        complaint_contribution=10,
    )
    db.add(case)
    db.commit()
    return case


def test_log_inserts_one_row(db):
    _case(db)
    log(db, "C-0041", "officer", "CASE_OPENED", {"score": 87})
    db.commit()

    rows = db.query(AuditLog).all()
    assert len(rows) == 1
    assert rows[0].case_id == "C-0041"
    assert rows[0].event_type == "CASE_OPENED"
    assert rows[0].actor_role == "officer"
    assert json.loads(rows[0].payload) == {"score": 87}


def test_log_appends_and_leaves_earlier_rows_untouched(db):
    _case(db)
    log(db, "C-0041", "system", "CASE_OPENED", {"score": 87})
    db.commit()
    first = db.query(AuditLog).one()
    first_id, first_payload, first_at = first.id, first.payload, first.created_at

    for rule_id in ("weighing_variance", "delivery_gap", "gps_deviation"):
        log(db, "C-0041", "system", "RULE_FIRED", {"rule_id": rule_id})
    db.commit()

    rows = db.query(AuditLog).order_by(AuditLog.id).all()
    assert len(rows) == 4
    assert rows[0].id == first_id
    assert rows[0].payload == first_payload
    assert rows[0].created_at == first_at
    assert [r.event_type for r in rows[1:]] == ["RULE_FIRED"] * 3


def test_log_records_the_rulebook_in_force(db):
    _case(db)
    log(db, "C-0041", "system", "CASE_OPENED", {"score": 87}, rulebook_version="1.0.0")
    db.commit()
    assert db.query(AuditLog).one().rulebook_version == "1.0.0"


def test_recompute_reports_identical_when_nothing_moved(db):
    case = _case(db)
    result = recompute(
        db,
        case,
        {
            "score": 87,
            "severity": "HIGH",
            "coverage_pct": 100,
            "gap_hop": "dispatch_to_receipt",
            "rulebook_version": "1.0.0",
        },
    )
    db.commit()

    assert result["identical"] is True
    assert result["stored"]["score"] == 87
    assert result["recomputed"]["score"] == 87


def test_recompute_reports_a_divergence_without_rewriting_the_case(db):
    """A recompute is an observation, not a correction. The stored case stands."""
    case = _case(db)
    result = recompute(
        db,
        case,
        {
            "score": 55,
            "severity": "MEDIUM",
            "coverage_pct": 83,
            "gap_hop": "dispatch_to_receipt",
            "rulebook_version": "1.0.0",
        },
    )
    db.commit()

    assert result["identical"] is False
    assert result["stored"]["score"] == 87
    assert result["recomputed"]["score"] == 55
    assert db.query(Case).one().score == 87


def test_recompute_writes_a_new_row_rather_than_touching_an_old_one(db):
    case = _case(db)
    log(db, "C-0041", "system", "CASE_OPENED", {"score": 87})
    db.commit()
    before = db.query(AuditLog).count()

    derived = {
        "score": 87,
        "severity": "HIGH",
        "coverage_pct": 100,
        "gap_hop": "dispatch_to_receipt",
        "rulebook_version": "1.0.0",
    }
    recompute(db, case, derived)
    db.commit()

    rows = db.query(AuditLog).order_by(AuditLog.id).all()
    assert len(rows) == before + 1
    assert rows[-1].event_type == "SCORE_RECOMPUTED"
    assert json.loads(rows[-1].payload)["identical"] is True
    assert rows[0].event_type == "CASE_OPENED"


def test_audit_code_contains_no_mutation_calls():
    """Invariant 6, enforced in the suite rather than only in a pre-commit grep."""
    for source in AUDITED_SOURCES:
        text = source.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_CALLS:
            assert pattern not in text, f"{source.name} contains '{pattern}'"


def test_audit_module_exposes_no_mutation_helper():
    from app.engine import audit

    exported = [name for name in dir(audit) if not name.startswith("_")]
    for name in exported:
        assert "remov" not in name.lower()
        assert "purge" not in name.lower()
        assert "edit" not in name.lower()
```

#### `backend/tests/test_api.py` (150 lines, verbatim)

```python
"""The API surface: ranked list, case sheet, notes, recompute, trail, rulebook.

Every test here runs against a COPY of backend/leakproof.db. The committed file
is the demo's evidence and a test run must not leave it in a state nobody chose
— least of all the audit trail, which cannot be tidied up afterwards.

test_case_detail_matches_the_frozen_contract turns CLAUDE.md invariant 8 from a
promise into a check: the contract file and the live response are compared key
for key, so neither can move without the other.
"""

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import get_db
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]
CONTRACT_PATH = BACKEND_DIR.parent / "docs" / "contract" / "case_detail.json"


@pytest.fixture
def client(tmp_path):
    scratch = tmp_path / "leakproof.db"
    shutil.copy(BACKEND_DIR / "leakproof.db", scratch)

    engine = create_engine(
        f"sqlite:///{scratch}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, autoflush=False, future=True)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_case_detail_matches_the_frozen_contract(client):
    """Invariant 8, enforced: schemas.py and case_detail.json move together."""
    live = client.get("/api/cases/C-0041").json()
    frozen = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert live == frozen


def test_demo_case_scores_87_from_the_live_api(client):
    detail = client.get("/api/cases/C-0041").json()
    assert detail["score"] == 87
    assert detail["severity"] == "HIGH"
    assert detail["coverage_pct"] == 100
    assert detail["gap_hop"] == "dispatch_to_receipt"


def test_ranked_list_opens_on_the_demo_case(client):
    cases = client.get("/api/cases").json()
    assert len(cases) == 60
    assert cases[0]["case_id"] == "C-0041"
    assert [c["score"] for c in cases] == sorted((c["score"] for c in cases), reverse=True)


def test_the_three_fixtures_land_where_the_table_says(client):
    by_shop = {c["shop"]["id"]: c for c in client.get("/api/cases").json()}
    assert (by_shop["4521"]["score"], by_shop["4521"]["severity"]) == (87, "HIGH")
    assert (by_shop["4102"]["score"], by_shop["4102"]["coverage_pct"]) == (55, 83)
    assert by_shop["4788"]["gap_hop"] == "receipt_to_counter"


def test_severity_and_district_filters(client):
    high = client.get("/api/cases?severity=HIGH").json()
    assert high and all(c["severity"] == "HIGH" for c in high)

    barabanki = client.get("/api/cases?district=Barabanki").json()
    assert barabanki and len(barabanki) < 60

    both = client.get("/api/cases?severity=MEDIUM&district=Sitapur").json()
    assert all(c["severity"] == "MEDIUM" for c in both)


def test_trace_carries_all_three_row_states(client):
    """#4102 is the shop with a skipped rule; the trace must show all six rules."""
    hits = client.get("/api/cases/C-0010").json()["rule_hits"]
    assert len(hits) == 6
    statuses = {h["status"] for h in hits}
    assert statuses == {"fired", "passed", "skipped"}
    skipped = [h for h in hits if h["status"] == "skipped"]
    assert skipped[0]["rule_id"] == "gps_deviation"
    assert skipped[0]["raw_value"] is None


def test_unknown_case_is_404(client):
    assert client.get("/api/cases/C-9999").status_code == 404
    assert client.post("/api/cases/C-9999/recompute").status_code == 404


def test_opening_a_case_writes_the_trail(client):
    trail = client.get("/api/audit/C-0041").json()
    events = [row["event_type"] for row in trail]
    assert events[0] == "CASE_OPENED"
    assert events.count("RULE_FIRED") == 3  # one per fired rule
    assert "COMPLAINT_LINKED" in events
    assert [row["created_at"] for row in trail] == sorted(row["created_at"] for row in trail)


def test_note_appends_a_row_and_returns_201(client):
    before = len(client.get("/api/audit/C-0041").json())
    response = client.post(
        "/api/cases/C-0041/notes",
        json={"text": "Dealer absent at 11:40; stock register not produced.", "actor_role": "inspector"},
    )
    assert response.status_code == 201

    trail = client.get("/api/audit/C-0041").json()
    assert len(trail) == before + 1
    assert trail[-1]["event_type"] == "NOTE_ADDED"
    assert trail[-1]["actor_role"] == "inspector"
    assert "Dealer absent" in trail[-1]["payload"]["text"]


def test_empty_note_is_rejected(client):
    assert client.post("/api/cases/C-0041/notes", json={"text": "   "}).status_code == 422


def test_recompute_reproduces_the_score_from_stored_inputs(client):
    result = client.post("/api/cases/C-0041/recompute").json()
    assert result["identical"] is True
    assert result["stored"]["score"] == result["recomputed"]["score"] == 87

    trail = client.get("/api/audit/C-0041").json()
    assert trail[-1]["event_type"] == "SCORE_RECOMPUTED"
    # The case itself is untouched: a recompute observes, it does not correct.
    assert client.get("/api/cases/C-0041").json()["score"] == 87


def test_rulebook_endpoint_serves_the_yaml(client):
    book = client.get("/api/rulebook").json()
    assert book["version"] == "1.0.0"
    assert book["updated_by"] == "District Supply Office, Sitapur"
    assert len(book["rules"]) == 6
    assert sum(rule["weight"] for rule in book["rules"]) == 120
```

### 7.3 Test → assertion → hardcoded numeric constants

`conftest.py` itself hardcodes the raw inputs; those constants are listed once
here rather than repeated per test.

**`conftest.py` constants:** `CASE_OPENED_AT = datetime(2026, 8, 14, 9, 12, 0)`;
`DISPATCH_TS = datetime(2026, 8, 10, 6, 0, 0)`;
`COMPLAINTS_IN_WINDOW = {"4521": 7, "4102": 2, "4788": 6}`;
`COMPLAINTS_OUTSIDE_WINDOW = {"4521": 2, "4102": 1, "4788": 0}`;
`RAW_4521` cycle `12000/12000/11015/10980`, hours 1, gap 61 h, gps 3.4 available,
1056 distinct cards over 1200 ration_cards;
`RAW_4102` cycle `8000/8000/7512/7490`, hours 1, gap 52 h, gps None unavailable,
639 cards over 900;
`RAW_4788` cycle `9000/9000/8970/8190`, hours 4, gap 44 h, gps 0.8 available,
550 cards over 1000. `_txns(..., duplicates=5)` adds 5 repeat card_ids so a
`len(txns)` implementation cannot pass by luck.

#### `test_reconcile.py` (12 tests)

| Test | Asserts | Hardcoded constants |
|---|---|---|
| `test_4521_variances` | both hop variances for #4521 | `-8.21`, `-0.32` |
| `test_4102_variances` | both hop variances for #4102 | `-6.10`, `-0.29` |
| `test_4788_variances` | both hop variances for #4788 | `-0.33`, `-8.70` |
| `test_delivery_gap_hours` | `arrival − dispatch` in hours per fixture | `61`, `52`, `44` |
| `test_txn_card_ratio_counts_distinct_cards` | distinct-card ratio per fixture | `0.88`, `0.71`, `0.55` |
| `test_hour_violations_passed_through` | the raw column reaches the feature dict | `1`, `1`, `4` |
| `test_gps_available_reports_the_reading` | the reading passes through when fitted | `3.4`, `0.8` |
| `test_gps_unavailable_is_none_not_zero` | F5: `is None` **and** `!= 0` | `0` (the value it must not be) |
| `test_locate_gap_picks_the_more_negative_hop` | worst-hop selection per fixture | strings `"dispatch_to_receipt"` ×2, `"receipt_to_counter"` |
| `test_missing_weighed_kg_degrades_rather_than_zeroes` | both variances go `None` when `weighed_kg` is None | none (None only) |
| `test_missing_arrival_scan_leaves_gap_unknown` | gap is `None` when `arrival_ts` is None | none |
| `test_locate_gap_returns_none_when_neither_hop_is_measurable` | `locate_gap` returns None | none |

#### `test_rulebook.py` (11 tests)

| Test | Asserts | Hardcoded constants |
|---|---|---|
| `test_load_reads_the_yaml_file_at_runtime` | version, updated_by, bands, the ordered rule-id list, bonus config | `"1.0.0"`, `"District Supply Office, Sitapur"`, `{"high": 75, "medium": 50}`, six rule ids in order, `{"min_complaints": 3, "window_days": 14, "weight": 10}` |
| `test_weights_total_120_and_bonus_is_10` | invariant 3 arithmetic | `120`, `10` |
| `test_load_from_explicit_path_matches_default` | explicit path == default path | none |
| `test_every_rule_produces_exactly_one_trace_row` | one row per rule, same order, exact 7-key set | the 7 key names |
| `test_4521_trace_matches_the_frozen_contract` | three fired rows byte-for-byte | `"-8.21%"/"-5.0%"/30`, `"61 hrs"/"48 hrs"/25`, `"3.4 km"/"2.0 km"/22`, severity `"high"` |
| `test_4521_non_firing_rules_are_passed_and_contribute_zero` | passed status, 0 contribution, exact display strings | `"-0.32%"`, `"0.88"`, `"1"`, `0` |
| `test_4102_fires_two_rules` | exact fired map | `{"weighing_variance": 30, "delivery_gap": 25}` |
| `test_4102_missing_gps_is_skipped_never_passed` | invariant 4; threshold still shown | `0`, `None`, `"2.0 km"` |
| `test_4788_fires_the_counter_skim_rules` | exact fired map and display strings | `{"counter_variance": 20, "transaction_mismatch": 15, "operating_hours": 8}`, `"-8.70%"`, `"0.55"`, `"4"` |
| `test_gte_operator_fires_exactly_on_the_threshold` | `gte 3`: 3 fires, 2 passes | `3`, `2` |
| `test_lt_operator_does_not_fire_exactly_on_the_threshold` | `lt -5.0`: −5.0 passes, −5.01 fires | `-5.0`, `-5.01` |
| `test_a_field_absent_from_features_is_skipped` | empty features → all skipped, 0 | `0` |
| `test_unknown_operator_is_refused_loudly` | `ValueError` on an unknown operator | none |

#### `test_score.py` (14 test functions, 17 cases with the parametrisation)

| Test | Asserts | Hardcoded constants |
|---|---|---|
| `test_4521_scores_exactly_87` | **invariant 1** | `87` |
| `test_4521_is_high_with_full_coverage` | severity, coverage, gap hop | `"HIGH"`, `100`, `"dispatch_to_receipt"` |
| `test_4521_score_is_the_sum_of_fired_rules_plus_the_bonus` | the arithmetic itself | `[30, 25, 22]`, `{"count": 7, "window_days": 14, "contribution": 10}`, `87` |
| `test_4102_scores_exactly_55` | invariant 2 | `55` |
| `test_4102_is_medium_with_reduced_coverage` | severity, coverage, gap hop | `"MEDIUM"`, `83`, `"dispatch_to_receipt"` |
| `test_4102_gps_deviation_is_none` | F5 at the feature level | none |
| `test_4102_bonus_does_not_fire_below_three_complaints` | exact bonus dict | `{"count": 2, "window_days": 14, "contribution": 0}` |
| `test_4102_coverage_counts_the_skipped_rule_not_the_weight` | coverage is rule-count based | `["gps_deviation"]`, `round(5/6*100)` = `83` |
| `test_4788_scores_exactly_53` | invariant 2 | `53` |
| `test_4788_is_medium_and_localises_the_counter` | severity, gap hop, coverage | `"MEDIUM"`, `"receipt_to_counter"`, `100` |
| `test_4788_fires_the_counter_ladder_plus_bonus` | fired weights and bonus | `[20, 15, 8]`, `10` |
| `test_result_carries_the_full_trace_and_rulebook_version` | version string, trace length, memo non-empty | `"1.0.0"` |
| `test_severity_bands` | three synthetic feature sets band correctly | inputs `(-90.0, 61, 3.4, 0.5, 10, 7)`, `(-6.0, 52, 0.1, 0.9, 0, 0)`, `(-1.0, 10, 0.1, 0.9, 0, 0)`; outputs `"HIGH"`, `"MEDIUM"`, `"LOW"`; comment `30 + 25 = 55` |
| `test_display_score_caps_at_100_but_the_raw_total_survives` | **invariant 3** | inputs `-40.0, -40.0, 96, 9.9, 0.1, 9`; outputs `score == 100`, `score_raw == 130` |
| `test_a_skipped_rule_never_contributes` | empty features → 0 score, 0 coverage, all skipped | `0`, `0` |
| `test_zscore_is_not_an_input_to_the_score` | **invariant 5** | `9.9` injected, `87` unchanged |
| `test_bonus_threshold_is_three_complaints` (parametrised ×4) | bonus step function | `(0,0)`, `(2,0)`, `(3,10)`, `(7,10)`, plus `window_days == 14` |

#### `test_complaints.py` (9 tests) — uses the in-memory `db` fixture

| Test | Asserts | Hardcoded constants |
|---|---|---|
| `test_counts_match_the_fixture_table` | window counts per shop | `7`, `2`, `6` |
| `test_older_complaints_are_excluded` | total rows vs in-window rows for #4521 | `9`, `7` |
| `test_window_days_comes_from_the_rulebook` | YAML window is 14; widening to 120 picks up the old ones | `14`, `120`, `9` |
| `test_a_narrow_window_counts_fewer` | `window_days=1` yields `< 7` | `1`, `7` |
| `test_complaints_in_window_returns_rows_newest_first` | count, descending order, all inside 14 days | `7`, `14` |
| `test_link_attaches_the_case_id_to_matched_complaints_only` | 7 linked, 2 left null | `"C-0041"`, `7`, `2` |
| `test_link_without_a_case_id_counts_without_writing` | counting does not write links | `7`, `0` |
| `test_the_count_feeds_compute_directly` | F4 output feeds F3 and yields 87 | `{"count": 7, "window_days": 14, "contribution": 10}`, `87` |
| `test_4102_stays_below_the_bonus_threshold` | count 2, contribution 0 | `2`, `0` |
| `test_unknown_shop_has_no_complaints` | shop `"9999"` → 0 | `"9999"`, `0` |

#### `test_memo.py` (6 tests)

| Test | Asserts | Hardcoded constants |
|---|---|---|
| `test_4521_memo_matches_the_frozen_contract_exactly` | memo string == `case_detail.json["memo"]`, read from the file | none inline — the whole sentence is read from the contract |
| `test_4521_memo_records_the_corroborating_complaints` | substrings present | `"7 complaints"`, `"14 days"` |
| `test_4102_memo_names_what_could_not_be_checked` | prefix, two clauses, the F5 sentence, and absence of any corroboration claim | `"Shop #4102 flagged MEDIUM (55/100):"`, `"weighing shortfall of 6.1%"`, `"52-hour delivery gap"`, `"Not evaluated: Vehicle deviated from registered route"`, `"the reading was unavailable"`, `"complaints"` must be absent |
| `test_4788_memo_describes_the_counter_skim` | prefix and clauses | `"Shop #4788 flagged MEDIUM (53/100):"`, `"counter shortfall of 8.7%"`, `"6 complaints"` |
| `test_memo_with_nothing_fired_says_so_plainly` | exact string for an empty trace | `"Shop #4999 flagged LOW (0/100): no rules fired."`, `14`, `0` |
| `test_memo_never_claims_to_be_generated` | honesty rule enforced in the suite | words `"ai"`, `"generated"`, `"model"`, `"llm"` must not appear as tokens |

#### `test_audit.py` (8 tests) — uses the in-memory `db` fixture

| Test | Asserts | Hardcoded constants |
|---|---|---|
| `test_log_inserts_one_row` | one row, correct case/event/actor/payload | `1`, `"C-0041"`, `{"score": 87}` |
| `test_log_appends_and_leaves_earlier_rows_untouched` | first row's id, payload and timestamp unchanged after 3 more inserts | `4`, `3` |
| `test_log_records_the_rulebook_in_force` | version column written | `"1.0.0"` |
| `test_recompute_reports_identical_when_nothing_moved` | `identical is True` | `87`, `"HIGH"`, `100`, `"dispatch_to_receipt"`, `"1.0.0"` |
| `test_recompute_reports_a_divergence_without_rewriting_the_case` | `identical is False`, stored case still 87 | `55`, `"MEDIUM"`, `83`, `87` |
| `test_recompute_writes_a_new_row_rather_than_touching_an_old_one` | count grows by exactly 1, last row is `SCORE_RECOMPUTED`, first is still `CASE_OPENED` | `before + 1`, `87`, `100` |
| `test_audit_code_contains_no_mutation_calls` | **invariant 6** — greps `engine/audit.py` and `routers/audit.py` for `.delete(` and `UPDATE` | the two obfuscated patterns |
| `test_audit_module_exposes_no_mutation_helper` | no public name containing `remov` / `purge` / `edit` | those three substrings |

The `_case()` helper hardcodes a full #4521-shaped case:
`12000/12000/11015/10980`, hours 1, score 87, HIGH, coverage 100,
gap `dispatch_to_receipt`, rulebook `1.0.0`, complaints 7 / 14 days / +10.

#### `test_api.py` (11 tests) — runs against a `shutil.copy` of `backend/leakproof.db` into `tmp_path`

| Test | Asserts | Hardcoded constants |
|---|---|---|
| `test_case_detail_matches_the_frozen_contract` | **invariant 8** — live `GET /api/cases/C-0041` equals `case_detail.json` exactly | `"C-0041"`; the whole contract file |
| `test_demo_case_scores_87_from_the_live_api` | score/severity/coverage/gap over HTTP | `87`, `"HIGH"`, `100`, `"dispatch_to_receipt"` |
| `test_ranked_list_opens_on_the_demo_case` | 60 rows, first is C-0041, scores descending | `60`, `"C-0041"` |
| `test_the_three_fixtures_land_where_the_table_says` | the fixture table over HTTP | `(87, "HIGH")`, `(55, 83)`, `"receipt_to_counter"` |
| `test_severity_and_district_filters` | both query filters narrow correctly | `"HIGH"`, `"Barabanki"`, `60`, `"MEDIUM"`, `"Sitapur"` |
| `test_trace_carries_all_three_row_states` | six rows, all three statuses, gps skipped with null reading | **`"C-0010"`**, `6`, `"gps_deviation"` |
| `test_unknown_case_is_404` | 404 on GET detail and POST recompute | `"C-9999"`, `404` |
| `test_opening_a_case_writes_the_trail` | first event, exactly 3 RULE_FIRED, COMPLAINT_LINKED present, chronological | `3` |
| `test_note_appends_a_row_and_returns_201` | 201, trail grows by 1, actor and text stored | `201`, `"inspector"`, `"Dealer absent"` |
| `test_empty_note_is_rejected` | whitespace-only note → 422 | `"   "`, `422` |
| `test_recompute_reproduces_the_score_from_stored_inputs` | identical, both 87, last event is SCORE_RECOMPUTED, case untouched | `87` |
| `test_rulebook_endpoint_serves_the_yaml` | version, maintainer, 6 rules, weights sum 120 | `"1.0.0"`, `"District Supply Office, Sitapur"`, `6`, `120` |

`test_trace_carries_all_three_row_states` is the one test that depends on a case
id that is **assigned by shop-ordering at runtime** rather than pinned:
`C-0010` happens to be shop 4102 under the current 60-shop set. Any change to the
shop id set moves it.

### 7.4 Command to run them

```bash
cd backend
pytest -v
```

(from `backend/`, with `.venv` activated so `app` is importable; there is no
pytest config file, so `rootdir` and `sys.path` come from
`backend/tests/__init__.py` and the working directory).

### 7.5 Which tests break under three hypothetical changes

*Determined by reading the assertions; the suite was not run.*

#### (a) If `rules.yaml` weights changed

Direct failures — these assert weights or weight-derived totals:

- `test_rulebook.py::test_weights_total_120_and_bonus_is_10` (asserts `120`)
- `test_rulebook.py::test_4521_trace_matches_the_frozen_contract` (30/25/22 inside the row dicts)
- `test_rulebook.py::test_4102_fires_two_rules` (`{weighing_variance: 30, delivery_gap: 25}`)
- `test_rulebook.py::test_4788_fires_the_counter_skim_rules` (`{20, 15, 8}`)
- `test_score.py::test_4521_scores_exactly_87`
- `test_score.py::test_4521_score_is_the_sum_of_fired_rules_plus_the_bonus` (`[30,25,22]` and `87`)
- `test_score.py::test_4102_scores_exactly_55`
- `test_score.py::test_4788_scores_exactly_53`
- `test_score.py::test_4788_fires_the_counter_ladder_plus_bonus` (`[20,15,8]`)
- `test_score.py::test_display_score_caps_at_100_but_the_raw_total_survives` (`score_raw == 130`)
- `test_score.py::test_zscore_is_not_an_input_to_the_score` (`== 87`)
- `test_score.py::test_severity_bands` (the middle band case is built assuming 30 + 25 = 55)
- `test_complaints.py::test_the_count_feeds_compute_directly` (`score == 87`)
- `test_memo.py::test_4521_memo_matches_the_frozen_contract_exactly` (the memo embeds "(87/100)")
- `test_memo.py::test_4102_memo_names_what_could_not_be_checked` ("(55/100)")
- `test_memo.py::test_4788_memo_describes_the_counter_skim` ("(53/100)")
- `test_api.py::test_demo_case_scores_87_from_the_live_api`
- `test_api.py::test_the_three_fixtures_land_where_the_table_says`
- `test_api.py::test_recompute_reproduces_the_score_from_stored_inputs`
- `test_api.py::test_rulebook_endpoint_serves_the_yaml` (asserts sum `120`)
- `test_api.py::test_case_detail_matches_the_frozen_contract` (contribution values are in the contract)
- `test_api.py::test_severity_and_district_filters` — likely, since it asserts `high` is non-empty and `MEDIUM` rows exist
- `test_api.py::test_ranked_list_opens_on_the_demo_case` — likely, since C-0041 leads on score
- `test_audit.py` — only if weights were changed such that a re-derivation moved; the audit tests feed literal dicts, so `test_recompute_reports_identical_when_nothing_moved` and friends would still pass

Unaffected: all of `test_reconcile.py` (it never touches the rulebook), and the
operator-edge tests in `test_rulebook.py` (they assert status, not weight) —
unless the *thresholds* moved too, in which case `test_gte_operator_...` and
`test_lt_operator_...` break as well.

Note the frozen contract file `docs/contract/case_detail.json` would also have to
change, or `test_case_detail_matches_the_frozen_contract` fails regardless.

#### (b) If the DB schema gained a table

Adding a *new* table alone breaks **nothing**:

- `conftest.py`'s `db` fixture calls `Base.metadata.create_all(bind=engine)`
  against a fresh in-memory SQLite, so a new model is simply created and ignored.
- `main.py` calls `Base.metadata.create_all(bind=engine)` at import, which
  "creates only what is missing" — so `test_api.py`, running against a copied
  `leakproof.db`, would have the new (empty) table created in the copy.
- No test asserts a table count or enumerates `Base.metadata.tables`.
- `models.py`'s docstring says "The nine LEAKPROOF tables" and CLAUDE.md's repo
  map says "9 SQLAlchemy tables" — both are prose, neither is asserted.

Failure would only follow if the new table came with changes to an *existing*
one: a new non-nullable column on `cases`, `rule_hits`, `cycles`, `shops`,
`deliveries`, `complaints` or `audit_log` would break `test_api.py` immediately,
because that suite copies the pre-existing `leakproof.db` and `create_all` does
not alter existing tables — every query touching the new column would raise
`OperationalError: no such column`. `test_case_detail_matches_the_frozen_contract`
would also fail if the new column reached a Pydantic response model, since the
live JSON would gain a key the contract file lacks.

#### (c) If the seed changed

Anything that changes the generated 57 shops (a different `random.seed`, changed
archetype bounds, a different shop count) breaks the suite in two distinct ways.

Immediately, without even re-running `seed.py` — because `test_api.py` reads the
**committed** `leakproof.db`, a seed change only matters after that file is
regenerated. Once it is:

- `test_api.py::test_ranked_list_opens_on_the_demo_case` — asserts exactly `60`
  rows and `cases[0]["case_id"] == "C-0041"`. The tie-break is score, then
  complaint count; #4521 leads on 7 complaints today. A reseed that gave another
  87-scoring shop 8+ complaints would flip the top row.
- `test_api.py::test_trace_carries_all_three_row_states` — **hardcodes `C-0010`**
  as shop 4102. Case ids are assigned by `_assign_case_ids()` walking shops in
  `ORDER BY Shop.id`, so any change to the generated id set renumbers everything
  except the pinned `C-0041`. This is the most fragile assertion in the suite.
- `test_api.py::test_severity_and_district_filters` — asserts the HIGH list is
  non-empty and the Barabanki list is shorter than 60. Both depend on the
  generated population.
- `test_api.py::test_case_detail_matches_the_frozen_contract` — the `complaints`
  array in the contract carries seven specific ids, timestamps, categories,
  sources and statuses (e.g. id 1 at `2026-08-10T21:10:00`, `epos_failure`,
  `closed`). All of those are drawn from the RNG stream, so **any** change to the
  seed — including one that leaves the score at 87 — breaks this test.
- `test_api.py::test_demo_case_scores_87_from_the_live_api`,
  `test_the_three_fixtures_land_where_the_table_says`,
  `test_opening_a_case_writes_the_trail`,
  `test_note_appends_a_row_and_returns_201`,
  `test_recompute_reproduces_the_score_from_stored_inputs` — these depend only on
  the three hardcoded `FIXTURES` dicts, so they survive a change to the
  *generated* shops but fail if a fixture's raw inputs move.

Unaffected by a seed change entirely: `test_reconcile.py`, `test_rulebook.py`,
`test_score.py`, `test_complaints.py`, `test_memo.py` and `test_audit.py` — all
six build their own data from `conftest.py`'s `SimpleNamespace` fixtures and an
in-memory database, and never open `leakproof.db`.

---

## 8. Domain-coupling scan

Method: case-insensitive `grep -rniI` for each term over `backend/app`,
`backend/seed.py`, `backend/tests`, `frontend/src` and
`docs/contract/case_detail.json` (the frozen contract is included because §5
requires it and a rename must move it in lockstep). Extensions searched:
`.py .js .jsx .yaml .json .css .html`. `.venv`, `node_modules`, `__pycache__`
and `dist` are excluded.

Classification key used in every table below:

- **(i)** Python/JS identifier — variable, function, parameter, class, dict key, constant
- **(ii)** DB column or table name (a `mapped_column`, `__tablename__`, or an ORM attribute reference)
- **(iii)** User-visible UI string — text that renders on screen
- **(iv)** Comment or docstring
- **(v)** YAML key or value
- **(vi)** JSON contract key or value

A single line can carry more than one class; where it does, the dominant one is
given with the other in parentheses.

**Two terms are pure substring noise and are marked as such**: `ration` also
matches *migration / generation / duration / corroboration / iteration /
decoration*, and `kg` also matches *background*. Those rows are listed for
completeness and flagged `FALSE POSITIVE` — they carry no domain meaning and
must not be counted toward rename cost.

### Summary of totals

| Term | Hits | True domain hits | Notes |
|---|---:|---:|---|
| PDS | 0 | 0 | ABSENT as a bare token (the expansion appears — see `diversion`, and §5 `main.py`) |
| ration | 47 | 22 | 25 are `corroboration` / `migration` / `generation` / `duration` / `decoration` |
| grain | 8 | 8 | |
| foodgrain | 0 | 0 | ABSENT |
| shop | 245 | 245 | **the single most coupled token in the codebase** |
| fair-price | 1 | 1 | |
| fps | 11 | 11 | |
| depot | 6 | 6 | |
| FCI | 2 | 2 | |
| weighbridge | 3 | 3 | |
| ePoS / epos | 8 | 8 | |
| beneficiary | 2 | 2 | |
| dispatch | 84 | 84 | |
| dispensed | 28 | 28 | |
| allocated | 22 | 22 | |
| weighed | 30 | 30 | |
| kg | 94 | 83 | 11 are `background` |
| quintal | 0 | 0 | ABSENT |
| consignment | 5 | 5 | |
| NFSA | 0 | 0 | ABSENT |
| leakproof / LEAKPROOF | 18 | 18 | |
| diversion | 7 | 7 | |
| complaint | 203 | 203 | second most coupled |
| GPS / gps | 56 | 56 | |

### PDS — 0 hits

**ABSENT.** The acronym does not appear in any scanned source file. The
expansion "Public Distribution System" appears three times and is caught under
other terms: `backend/app/main.py:17` (API description), `frontend/src/components/TopBar.jsx:37`
and `frontend/src/pages/SignIn.jsx:107` (both the UI context line). It also
appears throughout `README.md`, `CLAUDE.md` and `PROJECT-BRIEF.md`, which are
outside the scanned set.

### foodgrain — 0 hits · quintal — 0 hits · NFSA — 0 hits

**ABSENT** from all scanned source. `foodgrain` and `NFSA` appear only in
`README.md` / `PROJECT-BRIEF.md` / `CLAUDE.md`. `quintal` appears nowhere in the
repository at all — quantities are always kilograms.

### ration — 47 hits (22 true, 25 false positives)

**True domain hits — all of them are the column `ration_cards` or the phrase
"ration card":**

| File | Line | Class | Line content |
|---|---:|---|---|
| backend/app/engine/reconcile.py | 100 | (i) | `    ration_cards = _field(shop, "ration_cards")` |
| backend/app/engine/reconcile.py | 101 | (i) | `    if txns is None or not ration_cards:` |
| backend/app/engine/reconcile.py | 105 | (i) | `    return round(len(distinct_cards) / ration_cards, 2)` |
| backend/app/models.py | 47 | **(ii)** | `    ration_cards: Mapped[int] = mapped_column(Integer, nullable=False)` |
| backend/app/models.py | 133 | (iv) | `    # Distinct card_id count over shop.ration_cards gives txn_card_ratio.` |
| backend/app/rules.yaml | 46 | **(v)** | `    label: Transactions inconsistent with ration-card count` |
| backend/seed.py | 88 | (i)(iii) | `    "refused_entitlement": "Entitlement refused despite a valid ration card.",` |
| backend/seed.py | 99 | (iv) | `# ration_cards is chosen so that txn_card_ratio lands exactly on the fixture` |
| backend/seed.py | 109 | (i) | `        "ration_cards": 1200,` |
| backend/seed.py | 130 | (i) | `        "ration_cards": 900,` |
| backend/seed.py | 151 | (i) | `        "ration_cards": 1000,` |
| backend/seed.py | 195 | (i) | `        ration_cards = random.randrange(400, 1600, 50)` |
| backend/seed.py | 258 | (i) | `                "ration_cards": ration_cards,` |
| backend/seed.py | 292 | (i)(ii) | `        ration_cards=spec["ration_cards"],` |
| backend/seed.py | 386 | (iv) | `    Distinct card count over shop.ration_cards is txn_card_ratio, so the count` |
| backend/seed.py | 397 | (i) | `    n_txn = int(round(spec["txn_card_ratio"] * spec["ration_cards"]))` |
| backend/tests/conftest.py | 96 | (i) | `def _shop(shop_id, name, block, ration_cards):` |
| backend/tests/conftest.py | 104 | (i) | `        ration_cards=ration_cards,` |
| backend/tests/conftest.py | 189 | (i)(ii) | `                ration_cards=shop.ration_cards,` |
| docs/contract/case_detail.json | 64 | **(vi)** | `      "label": "Transactions inconsistent with ration-card count",` |
| docs/contract/case_detail.json | 116 | (vi) | `      "text": "Entitlement refused despite a valid ration card.",` |

Plus `backend/app/engine/reconcile.py:98` (`beneficiary served, and a shop can
pad its transaction log.`) is counted under `beneficiary`, not here.

**FALSE POSITIVE rows** (substring only, no domain meaning): `audit.py:3`
("operation"), `audit.py:38` ("migration"), `complaints.py:1,30`
("corroboration"), `score.py:52,58` ("corroboration"), `schemas.py:73,157`
("corroboration"/"Operational"), `seed.py:10,43` ("generation"),
`test_complaints.py:1,31`, `test_memo.py:47`, `test_rulebook.py:33,43`
(all "corroboration"), `Tag.jsx:41` and `ui.js:29` ("duration"),
`CaseDetail.jsx:155`, `Rulebook.jsx:109,152,154,170,171,182,194,195`
("Corroboration"), `SignIn.jsx:65` ("decoration").

Note that "corroboration" **is** a real domain concept here (the complaint
bonus) — it is just not the word "ration". It is inventoried under `complaint`.

### grain — 8 hits (all true)

| File | Line | Class | Line content |
|---|---:|---|---|
| backend/app/engine/reconcile.py | 5 | (iv) | `Two variances, two places grain can go:` |
| backend/app/engine/reconcile.py | 36 | (iv) | `    """Percentage change from one hop to the next, negative when grain is lost.` |
| backend/app/engine/reconcile.py | 109 | (iv) | `    """Name the hop where the most grain went missing.` |
| backend/app/engine/reconcile.py | 115 | (iv) | `    Ties go to the earlier hop: if both hops lost the same share, the grain was` |
| backend/seed.py | 86 | (i)(iii) | `    "quality": "Grain issued was of poor quality and partly spoiled.",` |
| frontend/src/components/Ladder.jsx | 10 | (iv) | `// the point is that these are four readings of the SAME grain, and the story` |
| frontend/src/components/Ladder.jsx | 15 | (iv) | `// the one connector where the grain actually went — colour as signal, spent` |
| frontend/src/components/Logo.jsx | 6 | (iv) | `// four-hop ladder of readings that steps down where grain left the chain, and` |

Seven of eight are comments. Only `seed.py:86` is a value that reaches a screen
(via `complaints.text`), and it is mirrored at
`docs/contract/case_detail.json:132`.

### shop — 245 hits (all true)

The heaviest coupling in the codebase. Grouped by file with line numbers; the
class is uniform within each group unless noted.

**`backend/app/models.py` — (ii) table/column/relationship, (iv) prose**

| Line | Class | Content |
|---:|---|---|
| 33 | (i) | `class Shop(Base):` |
| 34 | (iv) | `    """A fair-price shop (FPS). The unit an officer inspects."""` |
| 36 | **(ii)** | `    __tablename__ = "shops"` |
| 46 | (iv) | `    # Denominator of txn_card_ratio: cards attached to this shop.` |
| 56 | (i) | `    cycles: Mapped[list["Cycle"]] = relationship(back_populates="shop")` |
| 57 | (i) | `    complaints: Mapped[list["Complaint"]] = relationship(back_populates="shop")` |
| 58 | (i) | `    cases: Mapped[list["Case"]] = relationship(back_populates="shop")` |
| 62 | (iv) | `    """One monthly allocation cycle for one shop — the four-hop ladder.` |
| 68 | **(ii)** | `    __table_args__ = (UniqueConstraint("shop_id", "period", name="uq_cycle_shop_period"),)` |
| 71 | **(ii)** | `    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)` |
| 80 | (iv) | `    # Hop 3: shop-side weighing scale at receipt. Nullable — a scale can be` |
| 92 | (i) | `    shop: Mapped["Shop"] = relationship(back_populates="cycles")` |
| 99 | (iv) | `    """The transport leg: depot dispatch to shop arrival, with GPS."""` |
| 105 | **(ii)** | `    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)` |
| 131 | **(ii)** | `    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)` |
| 133 | (iv) | `    # Distinct card_id count over shop.ration_cards gives txn_card_ratio.` |
| 141 | (iv) | `    # True when the sale happened outside the shop's licensed hours.` |
| 148 | (iv) | `    """A public grievance filed against a shop. Feeds the F4 bonus."""` |
| 153 | **(ii)** | `    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)` |
| 165 | (i) | `    shop: Mapped["Shop"] = relationship(back_populates="complaints")` |
| 169 | (iv) | `    """A scored, openable case. One cycle of one shop, evaluated once."""` |
| 175 | **(ii)** | `    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)` |
| 208 | (i) | `    shop: Mapped["Shop"] = relationship(back_populates="cases")` |

**`backend/app/engine/` — (i) identifiers, (iv) prose**

| File:Line | Class | Content |
|---|---|---|
| complaints.py:33 | (i) | `def complaints_in_window(session, shop_id, anchor=None, window_days=None, rulebook=None):` |
| complaints.py:34 | (iv) | `    """Complaints filed against this shop inside the window, newest first.` |
| complaints.py:47 | (i)(ii) | `            Complaint.shop_id == shop_id,` |
| complaints.py:56 | (i) | `def link(session, shop_id, window_days=None, anchor=None, case_id=None, rulebook=None):` |
| complaints.py:70 | (i) | `    matched = complaints_in_window(session, shop_id, anchor, window_days, rulebook)` |
| memo.py:73 | (i) | `def build_memo(shop_id, score, severity, rule_hits, complaint_bonus):` |
| memo.py:75 | (i)**(iii)** | `    subject = f"Shop #{shop_id}" if shop_id else "This shop"` |
| reconcile.py:7 | (iv) | `  weighed    -> dispensed  counter skimming at the shop` |
| reconcile.py:15 | (iv) | `A missing shop scale must degrade coverage, not report a 100% shortfall.` |
| reconcile.py:48 | (i) | `def reconcile(cycle, delivery, txns, shop):` |
| reconcile.py:49 | (iv) | `    """Derive the feature dict for one shop-cycle from its raw readings.` |
| reconcile.py:59 | **(i)** | `        "shop_id": _field(shop, "id"),` |
| reconcile.py:64 | (i) | `        "txn_card_ratio": _txn_card_ratio(txns, shop),` |
| reconcile.py:70 | (iv) | `    """Hours between depot dispatch and shop arrival.` |
| reconcile.py:94 | (i) | `def _txn_card_ratio(txns, shop):` |
| reconcile.py:95 | (iv) | `    """Distinct cards that collected, over cards attached to the shop.` |
| reconcile.py:98 | (iv) | `    beneficiary served, and a shop can pad its transaction log.` |
| reconcile.py:100 | (i) | `    ration_cards = _field(shop, "ration_cards")` |
| reconcile.py:116 | (iv) | `    already short when it reached the shop.` |
| score.py:25 | (iv) | `    """Score one shop-cycle against the rulebook. Returns the whole case body."""` |
| score.py:36 | (i) | `    shop_id = features.get("shop_id")` |
| score.py:47 | (i) | `        "memo": build_memo(shop_id, score, severity, rule_hits, complaint_bonus),` |
| stats.py:8 | (iv) | `What it answers: "is this shop unusual, or is this just what the district looks` |
| stats.py:9 | (iv) | `like?" A rulebook threshold says a shop crossed a line. A z-score says how far` |
| stats.py:26 | (iv) | `    """The variance at the located gap — how much this shop lost at its worst hop."""` |
| stats.py:38 | (i) | `def z_scores(worst_by_shop: dict):` |
| stats.py:39 | (iv) | `    """How far each shop's worst hop sits from the district-wide norm.` |
| stats.py:41 | (iv) | `    Signed so that a WORSE shop scores higher: variances are negative, so the` |
| stats.py:42 | (iv) | `    distance is measured as (population mean - this shop), which puts an` |
| stats.py:45 | (iv) | `    Shops with no measurable variance are excluded from the population rather` |
| stats.py:46 | (iv) | `    than counted as zero — F5 again. A shop whose scale was offline is not a` |
| stats.py:47 | (iv) | `    shop with no shortfall, and folding it in as 0.0% would drag the mean` |
| stats.py:53 | (i) | `    values = [v for v in worst_by_shop.values() if v is not None]` |
| stats.py:55 | (i) | `        return {shop_id: None for shop_id in worst_by_shop}` |
| stats.py:60 | (i) | `        return {shop_id: None for shop_id in worst_by_shop}` |
| stats.py:63 | (i) | `        shop_id: (round((population_mean - value) / spread, 2) if value is not None else None)` |
| stats.py:64 | (i) | `        for shop_id, value in worst_by_shop.items()` |
| stats.py:68 | (i) | `def z_scores_from_features(features_by_shop: dict):` |
| stats.py:69 | (iv) | `    """z-score per shop, straight from the feature dicts reconcile() produced."""` |
| stats.py:70 | (i) | `    return z_scores({shop_id: worst_variance(f) for shop_id, f in features_by_shop.items()})` |
| stats.py:76 | (iv) | `    None is not confirmation. A shop we could not place against its peers is` |

**`backend/app/routers/cases.py` — (i)/(ii)**

Lines 22, 32(iv), 56, 57(iv), 59, 60, 64, 65(iv), 69, 70, 71, 77, 83(iv), 95,
97, 104, 105, 108, 109, 111, 112, 114, 117, 118, 120, 125, 152, 184, 209, 211,
212, 213, 214, 215, 228, 232, 248, 256, 274, 277, 289, 358, 360. The
load-bearing ones:

| Line | Class | Content |
|---:|---|---|
| 22 | (i) | `from ..models import Case, Complaint, Cycle, Delivery, RuleHit, Shop, Transaction` |
| 95 | (i)(ii) | `    shops = db.query(Shop).order_by(Shop.id).all()` |
| 97 | (i)(ii) | `        cycle.shop_id: cycle` |
| 125 | (i)(ii) | `                shop_id=shop.id,` |
| 152 | **(i)** | `                "shop_id": shop.id,` (audit payload key) |
| 209 | (i) | `def _shop_ref(shop: Shop) -> dict:` |
| 211-215 | **(i)/(vi)** | the `ShopRef` dict: `"id"`, `"name"`, `"block"`, `"lat"`, `"lng"` |
| 228 | (i)(ii) | `    query = db.query(Case, Shop).join(Shop, Case.shop_id == Shop.id)` |
| 232 | (i)(ii) | `        query = query.filter(Shop.district == district)` |
| 248 | **(vi)** | `            shop=_shop_ref(shop),` — the `shop` key of the JSON contract |
| 289 | **(vi)** | `        shop=_shop_ref(shop),` |

**`backend/app/rules.yaml` — (v), user-visible via the API**

| Line | Class | Content |
|---:|---|---|
| 37 | **(v)(iii)** | `    label: Shortfall between shop receipt and counter dispensing` |
| 54 | **(v)(iii)** | `    label: Irregular shop operating hours` |

**`backend/app/schemas.py` — (i)/(vi)**

| Line | Class | Content |
|---:|---|---|
| 24 | (i) | `class ShopRef(BaseModel):` |
| 25 | (iv) | `    """Just enough shop to render the case header and drop a map pin."""` |
| 114 | (iv) | `    shop #4521 and is the authority on key names and ordering.` |
| 120 | **(vi)** | `    shop: ShopRef` (in `CaseDetail`) |
| 147 | **(vi)** | `    shop: ShopRef` (in `CaseListItem`) |

**`backend/seed.py`** — lines 1(iv), 22(iv), 39, 76, 84, 96(iv), 168, 169(iv),
171(iv), 177, 180, 181, 182, 183, 188, 189, 191, 193(iv), 194, 195, 196, 197,
198, 200, 201, 202(iv), 203(iv), 204, 205, 206, 207(iv), 208, 209(iv), 210(iv),
211, 212, 213(iv), 214, 215, 216, 217, 218, 274, 282, 285, 298, 299, 306, 324,
325, 333, 350, 372, 386, 422, 439, 442, 461, 464, 505, 509, 518, 528, 533, 540.
The two user-visible strings among them:

| Line | Class | Content |
|---:|---|---|
| 76 | (i)(vi) | `    "shop_closed",` — a complaint category value |
| 84 | (iii)(vi) | `    "shop_closed": "Shop found closed during notified distribution hours.",` |

**`backend/tests/`** — conftest.py lines 11, 23, 32, 35, 47, 51, 61, 71, 72, 84,
85, 96, 98, 113, 122, 130, 132, 180, 182-192, 195-199, 206, 208;
test_api.py 73, 74, 75, 76, 91; test_audit.py 32, 45; test_complaints.py 23, 53,
58, 74, 87; test_memo.py 25, 42, 53, 60, 66; test_reconcile.py 11, 17, 23, 30,
36, 42, 48, 54, 63, 74, 79, 82, 90; test_rulebook.py 18; test_score.py 17.
All class (i) except the memo assertions, which assert **(iii)** user-visible
text: `"Shop #4102 flagged MEDIUM (55/100):"`, `"Shop #4788 flagged MEDIUM
(53/100):"`, `"Shop #4999 flagged LOW (0/100): no rules fired."`.

**`frontend/src/` — mostly (iii) user-visible, some (i)**

| File:Line | Class | Content |
|---|---|---|
| components/Ladder.jsx:21 | **(iii)** | `  { key: 'weighed_kg', label: 'Received', source: 'Shop weighing scale' },` |
| pages/Auditor.jsx:52 | **(iii)** | `` return `Shop #${p.shop_id}, cycle ${p.period}. Scored ${p.score} (${p.severity}), coverage ${p.coverage_pct}%, gap at ${p.gap_hop ?? 'none located'}.` `` |
| pages/Auditor.jsx:120 | (i)(iii) | `cases ?? [{ case_id: DEFAULT_CASE, shop: { id: '4521', name: 'FPS Sitapur-12' } }]` |
| pages/Auditor.jsx:123 | (i) | `{item.case_id} — {item.shop.name}` |
| pages/CaseDetail.jsx:85 | (i) | `const { shop, complaint_bonus: bonus } = detail` |
| pages/CaseDetail.jsx:90 | (i) | `title={shop.name}` |
| pages/CaseDetail.jsx:91 | **(iii)** | `` note={`Case ${detail.case_id} · Shop #${shop.id} · ${shop.block} · opened ...`} `` |
| pages/CaseDetail.jsx:159 | **(iii)** | `Grievances filed against this shop inside the {bonus.window_days}-day window before the` |
| pages/CaseDetail.jsx:169 | **(iii)** | `Nothing was filed against this shop in the {bonus.window_days} days before the case` |
| pages/Inspector.jsx:46 | (i) | `() => (cases ? [...new Set(cases.map((c) => c.shop.block))].sort() : []),` |
| pages/Inspector.jsx:53 | (i) | `() => (cases ?? []).filter((c) => district === 'All districts' \|\| c.shop.block === district),` |
| pages/Inspector.jsx:114 | **(iii)** | `<span className={COLUMN_HEAD}>Shop · what to look at</span>` |
| pages/Inspector.jsx:135 | (i) | `<p className="text-body font-medium text-ink">{item.shop.name}</p>` |
| pages/Inspector.jsx:137 | **(iii)** | `Shop #<span className="num">{item.shop.id}</span> · {item.shop.block} ·` |
| pages/Inspector.jsx:182 | **(iii)** | `Every case in this district has been closed, or no shop there has been scored for` |
| pages/Officer.jsx:35 | (i) | `shop: (a, b) => a.shop.name.localeCompare(b.shop.name),` |
| pages/Officer.jsx:75 | (i) | `() => (cases ? [...new Set(cases.map((c) => c.shop.block))].sort() : []),` |
| pages/Officer.jsx:82 | (i) | `.filter((c) => district === 'All districts' \|\| c.shop.block === district)` |
| pages/Officer.jsx:135 | **(iii)** | `<span className="num">{cases.length}</span> shops, ranked by evidence. Severity is` |
| pages/Officer.jsx:143 | **(iii)** | `<SortHeader label="Shop" field="shop" sort={sort} onSort={setSort} />` |
| pages/Officer.jsx:177 | (i) | `{item.shop.name}` |
| pages/Officer.jsx:180 | **(iii)** | `Shop #<span className="num">{item.shop.id}</span> · {item.shop.block} ·` |
| pages/Rulebook.jsx:22 | (iv) | `// cases: nothing on this page is a thing that happened to a shop, so a row of` |

**`docs/contract/case_detail.json` — (vi)**

| Line | Class | Content |
|---:|---|---|
| 3 | **(vi) key** | `  "shop": {` |
| 55 | (vi) value | `      "label": "Shortfall between shop receipt and counter dispensing",` |
| 73 | (vi) value | `      "label": "Irregular shop operating hours",` |
| 107 | (vi) value | `      "category": "shop_closed",` |
| 108 | (vi) value | `      "text": "Shop found closed during notified distribution hours.",` |
| 148 | (vi) value | the memo, beginning `"Shop #4521 flagged HIGH (87/100): ..."` |

### fair-price — 1 hit

| File | Line | Class | Content |
|---|---:|---|---|
| backend/app/models.py | 34 | (iv) | `    """A fair-price shop (FPS). The unit an officer inspects."""` |

### fps — 11 hits

| File | Line | Class | Content |
|---|---:|---|---|
| backend/app/models.py | 34 | (iv) | `    """A fair-price shop (FPS). The unit an officer inspects."""` |
| backend/app/models.py | 38 | (iv) | `    # Real FPS codes are strings, not counters — #4521 stays "4521".` |
| backend/seed.py | 104 | **(iii)** | `        "name": "FPS Sitapur-12",` |
| backend/seed.py | 125 | **(iii)** | `        "name": "FPS Barabanki-7",` |
| backend/seed.py | 146 | **(iii)** | `        "name": "FPS Hargaon-3",` |
| backend/seed.py | 187 | **(iii)** | `        name = f"FPS {block}-{random.randint(1, 40)}"` |
| backend/seed.py | 189 | **(iii)** | `            name = f"FPS {block}-{random.randint(1, 40)}"` |
| backend/tests/conftest.py | 113 | (i) | `    "shop": _shop("4521", "FPS Sitapur-12", "Sitapur", 1200),` |
| backend/tests/conftest.py | 122 | (i) | `    "shop": _shop("4102", "FPS Barabanki-07", "Barabanki", 900),` |
| backend/tests/conftest.py | 132 | (i) | `    "shop": _shop("4788", "FPS Hargaon-03", "Hargaon", 1000),` |
| frontend/src/pages/Auditor.jsx | 120 | (iii) | the fallback dropdown row `name: 'FPS Sitapur-12'` |
| docs/contract/case_detail.json | 5 | **(vi)** | `    "name": "FPS Sitapur-12",` |

The `FPS ` prefix is a **data value**, not an identifier — it is baked into every
one of the 60 seeded shop names and therefore into the committed database.

### depot — 6 hits

| File | Line | Class | Content |
|---|---:|---|---|
| backend/app/engine/reconcile.py | 70 | (iv) | `    """Hours between depot dispatch and shop arrival.` |
| backend/app/models.py | 78 | (iv) | `    # Hop 2: FCI depot weighbridge at dispatch.` |
| backend/app/models.py | 99 | (iv) | `    """The transport leg: depot dispatch to shop arrival, with GPS."""` |
| backend/seed.py | 198 | (iv) | `        # Paper diversion at the depot is rare; dispatch usually matches the` |
| frontend/src/components/Ladder.jsx | 20 | **(iii)** | `  { key: 'dispatched_kg', label: 'Dispatched', source: 'FCI depot weighbridge' },` |
| frontend/src/severity.js | 39 | **(iii)** | `    'Short before it left the depot. Check the dispatch order against the weighbridge slip.',` |

### FCI — 2 hits

| File | Line | Class | Content |
|---|---:|---|---|
| backend/app/models.py | 78 | (iv) | `    # Hop 2: FCI depot weighbridge at dispatch.` |
| frontend/src/components/Ladder.jsx | 20 | **(iii)** | `  { key: 'dispatched_kg', label: 'Dispatched', source: 'FCI depot weighbridge' },` |

### weighbridge — 3 hits

| File | Line | Class | Content |
|---|---:|---|---|
| backend/app/models.py | 78 | (iv) | `    # Hop 2: FCI depot weighbridge at dispatch.` |
| frontend/src/components/Ladder.jsx | 20 | **(iii)** | `  { key: 'dispatched_kg', label: 'Dispatched', source: 'FCI depot weighbridge' },` |
| frontend/src/severity.js | 39 | **(iii)** | `    'Short before it left the depot. Check the dispatch order against the weighbridge slip.',` |

### ePoS / epos — 8 hits in code, 14 lines including the contract

| File | Line | Class | Content |
|---|---:|---|---|
| backend/app/models.py | 83 | (iv) | `    # Hop 4: sum of ePoS counter dispensing. Nullable for the same reason.` |
| backend/app/models.py | 125 | (iv) | `    """One beneficiary collection at the ePoS counter."""` |
| backend/app/models.py | 138 | (iv) | `    # ePoS auth mode, kept because a spike in manual overrides is the kind of` |
| backend/seed.py | 79 | **(i)(vi)** | `    "epos_failure",` — a complaint category **value** |
| backend/seed.py | 87 | **(iii)** | `    "epos_failure": "ePoS machine reported failure but the entitlement was marked issued.",` |
| backend/seed.py | 393 | (iv) | `        # ePoS data unavailable for this cycle: no rows, and the counter rules` |
| frontend/src/components/Ladder.jsx | 22 | **(iii)** | `  { key: 'dispensed_kg', label: 'Dispensed', source: 'ePoS counter total' },` |
| frontend/src/severity.js | 43 | **(iii)** | `    'Lost at the counter. Check the stock register against the ePoS dispensing record.',` |
| docs/contract/case_detail.json | 91, 99, 139 | (vi) | `      "category": "epos_failure",` ×3 |
| docs/contract/case_detail.json | 92, 100, 140 | (vi) | `      "text": "ePoS machine reported failure but the entitlement was marked issued.",` ×3 |

`epos_failure` is a stored **data value** in `complaints.category` across the
committed database, not just a source-code string.

### beneficiary — 2 hits

| File | Line | Class | Content |
|---|---:|---|---|
| backend/app/engine/reconcile.py | 98 | (iv) | `    beneficiary served, and a shop can pad its transaction log.` |
| backend/app/models.py | 125 | (iv) | `    """One beneficiary collection at the ePoS counter."""` |

Both are comments. Nothing beneficiary-facing exists — PROJECT-BRIEF lists it as
deliberately excluded.

### dispatch — 84 hits (all true)

The token appears in four distinct forms, and a pivot has to move all four:
the column `dispatched_kg`, the column `dispatch_ts`, the hop id
`dispatch_to_receipt` / `allocation_to_dispatch`, and the feature key
`variance_dispatch_to_receipt`.

**backend/app/engine/reconcile.py**

| Line | Class | Content |
|---:|---|---|
| 3 | (iv) | `allocated_kg -> dispatched_kg -> weighed_kg -> dispensed_kg` |
| 6 | (iv) | `  dispatched -> weighed    transport-leg diversion` |
| 11 | (iv) | `sentence an officer actually acts on: "985 kg opened between dispatch and` |
| 18 | **(i)** | `DISPATCH_TO_RECEIPT = "dispatch_to_receipt"` |
| 54 | (i)(ii) | `    dispatched_kg = _field(cycle, "dispatched_kg")` |
| 60 | **(i)** | `        "variance_dispatch_to_receipt": _variance_pct(dispatched_kg, weighed_kg),` |
| 70 | (iv) | `    """Hours between depot dispatch and shop arrival.` |
| 75 | (i)(ii) | `    dispatch_ts = _field(delivery, "dispatch_ts")` |
| 77 | (i) | `    if dispatch_ts is None or arrival_ts is None:` |
| 79 | (i) | `    return round((arrival_ts - dispatch_ts).total_seconds() / 3600, 2)` |
| 119 | (i) | `        (features.get("variance_dispatch_to_receipt"), DISPATCH_TO_RECEIPT),` |

**backend/app/engine/stats.py:30** (i) — `features.get("variance_dispatch_to_receipt"),`

**backend/app/models.py**

| Line | Class | Content |
|---:|---|---|
| 64 | (iv) | `    allocated_kg -> dispatched_kg -> weighed_kg -> dispensed_kg` |
| 78 | (iv) | `    # Hop 2: FCI depot weighbridge at dispatch.` |
| 79 | **(ii)** | `    dispatched_kg: Mapped[float] = mapped_column(Float, nullable=False)` |
| 99 | (iv) | `    """The transport leg: depot dispatch to shop arrival, with GPS."""` |
| 110 | (iv) | `    # delivery_gap_hours = arrival_ts - dispatch_ts. arrival_ts is nullable:` |
| 112 | **(ii)** | `    dispatch_ts: Mapped[datetime] = mapped_column(DateTime, nullable=False)` |
| 185-186 | (iv) | `    # Worst hop from locate_gap(): dispatch_to_receipt \| receipt_to_counter \| allocation_to_dispatch.` |

**backend/app/routers/cases.py**

| Line | Class | Content |
|---:|---|---|
| 296 | **(vi)** | `            "dispatched_kg": cycle.dispatched_kg,` |
| 299 | **(vi)** | `            "variance_dispatch_to_receipt": features["variance_dispatch_to_receipt"],` |

**backend/app/rules.yaml**

| Line | Class | Content |
|---:|---|---|
| 11 | **(v)** | `    field: variance_dispatch_to_receipt` |
| 19 | **(v)(iii)** | `    label: Delivery-to-dispatch gap exceeded` |

**backend/app/schemas.py**

| Line | Class | Content |
|---:|---|---|
| 21 | **(i)(vi)** | `GapHop = Literal["allocation_to_dispatch", "dispatch_to_receipt", "receipt_to_counter"]` |
| 47 | **(vi)** | `    dispatched_kg: float` |
| 50 | **(vi)** | `    variance_dispatch_to_receipt: float \| None = None` |

**backend/seed.py** — 112, 113(iv), 133, 154, 198(iv), 200, 230, 261, 309, 336,
346, 353, 354, 365(iv), 368, 375, 376. All (i) or (ii); the hardcoded fixture
values are `"dispatched_kg": 12000.0 / 8000.0 / 9000.0`.

**backend/tests/** — conftest.py 29 (`DISPATCH_TS = datetime(2026, 8, 10, 6, 0, 0)`),
32, 38, 54, 55, 73, 86; test_api.py 62; test_audit.py 35, 51, 111, 132, 154;
test_reconcile.py 12, 18, 24, 70, 71, 83, 96; test_rulebook.py 83, 153, 155, 169;
test_score.py 35, 57, 120, 133. All (i), asserting the hop-id strings and the
feature key.

**frontend/src/**

| File:Line | Class | Content |
|---|---|---|
| components/Ladder.jsx:6 | (iv) | `// allocated -> dispatched -> weighed -> dispensed, with what was lost between` |
| components/Ladder.jsx:20 | **(iii)** | `  { key: 'dispatched_kg', label: 'Dispatched', source: 'FCI depot weighbridge' },` |
| components/Ladder.jsx:29 | **(i)** | `  { id: 'allocation_to_dispatch', from: 'allocated_kg', to: 'dispatched_kg', variance: null },` |
| components/Ladder.jsx:31-34 | **(i)** | the `dispatch_to_receipt` hop object, `from: 'dispatched_kg'`, `variance: 'variance_dispatch_to_receipt'` |
| pages/Rulebook.jsx:17 | (iv) | `// row as a sentence ("Weighing shortfall · variance_dispatch_to_receipt ·` |
| severity.js:38-39 | **(i)(iii)** | `allocation_to_dispatch:` → `'Short before it left the depot. Check the dispatch order against the weighbridge slip.'` |
| severity.js:40 | **(i)** | `dispatch_to_receipt:` (HOP_ACTION key) |
| severity.js:83 | **(i)(iii)** | `allocation_to_dispatch: 'Allocation to dispatch',` |
| severity.js:84 | **(i)(iii)** | `dispatch_to_receipt: 'Dispatch to receipt',` |

**docs/contract/case_detail.json** — 16 `"dispatched_kg": 12000.0`,
19 `"variance_dispatch_to_receipt": -8.21`, 22 `"gap_hop": "dispatch_to_receipt"`,
37 `"label": "Delivery-to-dispatch gap exceeded"`. All (vi).

### dispensed — 28 hits (all true)

| File | Line | Class | Content |
|---|---:|---|---|
| engine/reconcile.py | 3 | (iv) | ladder line |
| engine/reconcile.py | 7 | (iv) | `  weighed    -> dispensed  counter skimming at the shop` |
| engine/reconcile.py | 56 | (i)(ii) | `    dispensed_kg = _field(cycle, "dispensed_kg")` |
| engine/reconcile.py | 61 | (i) | `        "variance_receipt_to_counter": _variance_pct(weighed_kg, dispensed_kg),` |
| models.py | 10 | (iv) | `  dispensed_kg) rather than as a zero or a magic number. F5 depends on being` |
| models.py | 64 | (iv) | ladder line |
| models.py | 84 | **(ii)** | `    dispensed_kg: Mapped[float \| None] = mapped_column(Float)` |
| routers/cases.py | 298 | **(vi)** | `            "dispensed_kg": cycle.dispensed_kg,` |
| schemas.py | 49 | **(vi)** | `    dispensed_kg: float \| None = None` |
| seed.py | 114 | (i) | `        "dispensed_kg": 10980.0,  # -0.32% against receipt` |
| seed.py | 135 | (i) | `        "dispensed_kg": 7490.0,  # -0.29%` |
| seed.py | 156 | (i) | `        "dispensed_kg": 8190.0,  # -8.70%, counter skim` |
| seed.py | 231 | (i) | `        dispensed = round(weighed * (1 + counter_pct / 100), 1)` |
| seed.py | 263 | (i) | `                "dispensed_kg": None if scale_offline else dispensed,` |
| seed.py | 311 | (i)(ii) | `        dispensed_kg=spec["dispensed_kg"],` |
| seed.py | 331 | (i) | `        dispensed = round(weighed * (1 + random.uniform(-1.0, -0.05) / 100), 1)` |
| seed.py | 338 | (i)(ii) | `            dispensed_kg=dispensed,` |
| seed.py | 388 | (iv) | `    Quantities sum to exactly dispensed_kg — the ladder's fourth rung is the` |
| seed.py | 391 | (i)(ii) | `    dispensed = cycle.dispensed_kg` |
| seed.py | 392 | (i) | `    if dispensed is None:` |
| seed.py | 401 | (i) | `    per_txn = round(dispensed / n_txn, 3)` |
| seed.py | 409 | (i) | `        qty = per_txn if i < n_txn - 1 else round(dispensed - running, 3)` |
| tests/conftest.py | 32, 40 | (i) | `_cycle(... dispensed ...)`, `dispensed_kg=dispensed` |
| tests/test_audit.py | 37 | (i) | `        dispensed_kg=10980.0,` |
| frontend Ladder.jsx | 6 | (iv) | ladder comment |
| frontend Ladder.jsx | 22 | **(iii)** | `  { key: 'dispensed_kg', label: 'Dispensed', source: 'ePoS counter total' },` |
| frontend Ladder.jsx | 39 | (i) | `    to: 'dispensed_kg',` |
| case_detail.json | 18 | **(vi)** | `    "dispensed_kg": 10980.0,` |

Also `frontend/src/severity.js:43` uses the word "dispensing" in the
`receipt_to_counter` action string, and `rules.yaml:37` / `case_detail.json:55`
use "dispensing" in the `counter_variance` label.

### allocated — 22 hits (all true)

| File | Line | Class | Content |
|---|---:|---|---|
| engine/reconcile.py | 3 | (iv) | ladder line |
| models.py | 64 | (iv) | ladder line |
| models.py | 77 | **(ii)** | `    allocated_kg: Mapped[float] = mapped_column(Float, nullable=False)` |
| routers/cases.py | 295 | **(vi)** | `            "allocated_kg": cycle.allocated_kg,` |
| schemas.py | 46 | **(vi)** | `    allocated_kg: float` |
| seed.py | 111, 132, 153 | (i) | `"allocated_kg": 12000.0 / 8000.0 / 9000.0` |
| seed.py | 196 | (i) | `        allocated = float(random.randrange(4000, 14000, 500))` |
| seed.py | 200 | (i) | `        dispatched = allocated if random.random() > 0.10 else allocated - random.randrange(50, 300, 25)` |
| seed.py | 260, 308, 329, 335, 336 | (i)(ii) | assignments of `allocated_kg` |
| seed.py | 330 | (i) | `        weighed = round(allocated * (1 + random.uniform(-1.2, -0.05) / 100), 1)` |
| tests/conftest.py | 32, 37 | (i) | `_cycle(shop_id, allocated, ...)`, `allocated_kg=allocated` |
| tests/test_audit.py | 34 | (i) | `        allocated_kg=12000.0,` |
| frontend Ladder.jsx | 6 | (iv) | ladder comment |
| frontend Ladder.jsx | 19 | **(iii)** | `  { key: 'allocated_kg', label: 'Allocated', source: 'Government allocation order' },` |
| frontend Ladder.jsx | 29 | (i) | `  { id: 'allocation_to_dispatch', from: 'allocated_kg', to: 'dispatched_kg', variance: null },` |
| case_detail.json | 15 | **(vi)** | `    "allocated_kg": 12000.0,` |

Also `frontend/src/components/Ladder.jsx:103` renders "from allocation order to
counter", and `severity.js:83` renders "Allocation to dispatch".

### weighed — 30 hits (all true)

| File | Line | Class | Content |
|---|---:|---|---|
| engine/reconcile.py | 3, 6, 7 | (iv) | ladder lines |
| engine/reconcile.py | 55 | (i)(ii) | `    weighed_kg = _field(cycle, "weighed_kg")` |
| engine/reconcile.py | 60, 61 | (i) | both `_variance_pct(...)` calls |
| models.py | 9 | (iv) | `* "Unavailable" is modelled explicitly (gps_available, nullable weighed_kg /` |
| models.py | 64 | (iv) | ladder line |
| models.py | 82 | **(ii)** | `    weighed_kg: Mapped[float \| None] = mapped_column(Float)` |
| routers/cases.py | 297 | **(vi)** | `            "weighed_kg": cycle.weighed_kg,` |
| schemas.py | 48 | **(vi)** | `    weighed_kg: float \| None = None` |
| seed.py | 113, 134, 155 | (i) | `"weighed_kg": 11015.0 / 7512.0 / 8970.0` |
| seed.py | 230, 231, 262, 310, 330, 331, 337 | (i)(ii) | derivations and assignments |
| tests/conftest.py | 32, 39 | (i) | |
| tests/test_audit.py | 36 | (i) | `        weighed_kg=11015.0,` |
| tests/test_reconcile.py | 78 | (i) | `def test_missing_weighed_kg_degrades_rather_than_zeroes(raw_4521):` |
| tests/test_reconcile.py | 81 | (i) | `    offline = type(cycle)(**{**vars(cycle), "weighed_kg": None})` |
| frontend Ladder.jsx | 6 | (iv) | ladder comment |
| frontend Ladder.jsx | 21 | **(iii)** | `  { key: 'weighed_kg', label: 'Received', source: 'Shop weighing scale' },` |
| frontend Ladder.jsx | 33, 38 | (i) | `to: 'weighed_kg'`, `from: 'weighed_kg'` |
| case_detail.json | 17 | **(vi)** | `    "weighed_kg": 11015.0,` |

Note the UI label for `weighed_kg` is **"Received"**, not "Weighed" — the column
name and its screen label already diverge.

Related: the rule id `weighing_variance` and the label
`Weighing shortfall beyond tolerance` (rules.yaml:9-10, case_detail.json:27-28,
test_rulebook.py:73, memo.py:19-20, and the memo string
"weighing shortfall of 8.2%").

### kg — 94 hits (83 true, 11 `background` false positives)

**True hits** are the four ladder columns (`allocated_kg`, `dispatched_kg`,
`weighed_kg`, `dispensed_kg`, already inventoried above), plus:

| File | Line | Class | Content |
|---|---:|---|---|
| engine/reconcile.py | 11 | (iv) | `sentence an officer actually acts on: "985 kg opened between dispatch and` |
| models.py | 136 | **(ii)** | `    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)` |
| schemas.py | 40 | (iv) | `    display. Null on either kg field means the reading was unavailable, which` |
| seed.py | 426 | (i) | `                "quantity_kg": qty,` |
| tests/conftest.py | 74, 87 | (i) | `            quantity_kg=5.0,` |
| frontend/src/severity.js | 70 | (i) | `const KG = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })` |
| frontend/src/severity.js | 72-73 | (i) | `export function formatKg(value) { ... KG.format(value) }` |
| frontend/src/components/Ladder.jsx | 1 | (i) | `import { formatKg, formatPct } from '../severity.js'` |
| frontend/src/components/Ladder.jsx | 13 | (iv) | `// The kg figures are ink, not navy: they are data, and navy is reserved for` |
| frontend/src/components/Ladder.jsx | 58 | **(iii)** | `{formatKg(value)} <span className="text-body-secondary text-ink-secondary">kg</span>` |
| frontend/src/components/Ladder.jsx | 74 | (iv) | `  // kg is exact subtraction of two stored readings. The percentage is the` |
| frontend/src/components/Ladder.jsx | 77 | (i) | `  const deltaKg = measurable ? to - from : null` |
| frontend/src/components/Ladder.jsx | 86 | **(iii)** | `` {measurable ? `${deltaKg > 0 ? '+' : ''}${formatKg(deltaKg)} kg` : '—'} `` |

Kilograms are also the implicit unit of every ladder number rendered on
CaseDetail, and `en-IN` locale grouping is applied to them
(`1,00,000`-style Indian digit grouping, not `100,000`).

**FALSE POSITIVE rows** — the substring in "background": `PageMotif.jsx:30, 31,
42, 62`, `SectionHeading.jsx:13`, `Tag.jsx:4`, `TraceTable.jsx:48, 51`,
`CaseDetail.jsx:26`, `Officer.jsx:89`, `SignIn.jsx:30`, `ui.js:23`.

### consignment — 5 hits

| File | Line | Class | Content |
|---|---:|---|---|
| engine/reconcile.py | 72 | (iv) | `    None when the consignment is still in transit or its arrival scan never` |
| models.py | 111 | (iv) | `    # a consignment can be in transit or its arrival scan can be missing.` |
| seed.py | 366 | (iv) | `    check against the consignment note.` |
| frontend/src/components/Ladder.jsx | 103 | **(iii)** | `Four readings of the same consignment, from allocation order to counter. The gap is where` |
| frontend/src/severity.js | 41 | **(iii)** | `    'Lost on the transport leg. Check the consignment note, the vehicle log and the route.',` |

### leakproof / LEAKPROOF — 18 hits

| File | Line | Class | Content |
|---|---:|---|---|
| backend/app/db.py | 3 | (iv) | `Single SQLite file at backend/leakproof.db. It is committed on purpose so a` |
| backend/app/db.py | 12 | (iv) | `# backend/app/db.py -> backend/leakproof.db` |
| backend/app/db.py | 14 | **(i)** | `DB_PATH = BACKEND_DIR / "leakproof.db"` — **the filename on disk** |
| backend/app/engine/audit.py | 5 | (iv) | `rewritten proves nothing, and the whole claim LEAKPROOF makes to an auditor is` |
| backend/app/engine/complaints.py | 3 | (iv) | `Public grievances are the one signal in LEAKPROOF that does not come from a` |
| backend/app/main.py | 16 | **(iii)** | `    title="LEAKPROOF",` — the OpenAPI/Swagger title |
| backend/app/main.py | 37 | **(iii)** | `    return {"status": "ok", "service": "leakproof", "version": app.version}` |
| backend/app/models.py | 1 | (iv) | `"""The nine LEAKPROOF tables.` |
| backend/app/routers/audit.py | 5 | (iv) | `trail is the one thing in LEAKPROOF that a magistrate is entitled to assume` |
| backend/app/__init__.py | 1 | (iv) | `"""LEAKPROOF backend application package."""` |
| backend/seed.py | 1 | (iv) | `"""Synthetic data for LEAKPROOF. 60 shops: 3 fixtures + 57 generated.` |
| backend/tests/conftest.py | 161 | (iv) | `# --- A throwaway database, not backend/leakproof.db ---` |
| backend/tests/test_api.py | 3 | (iv) | `Every test here runs against a COPY of backend/leakproof.db. The committed file` |
| backend/tests/test_api.py | 30 | (i) | `    scratch = tmp_path / "leakproof.db"` |
| backend/tests/test_api.py | 31 | (i) | `    shutil.copy(BACKEND_DIR / "leakproof.db", scratch)` |
| frontend/src/components/Logo.jsx | 31 | (iv) | `      // Decorative in every placement: the word LEAKPROOF is always beside it` |
| frontend/src/components/Logo.jsx | 60 | **(iii)** | `      <span className="font-display text-section-heading tracking-wide">LEAKPROOF</span>` |
| frontend/src/pages/SignIn.jsx | 103 | **(iii)** | `          <h1 ...>LEAKPROOF</h1>` |

Also outside this grep's file set: `frontend/index.html:6`
`<title>LEAKPROOF</title>` and `frontend/package.json:2`
`"name": "leakproof-frontend"`.

### diversion — 7 hits

| File | Line | Class | Content |
|---|---:|---|---|
| engine/complaints.py | 4 | (iv) | `machine. They are not evidence of diversion on their own, which is why they add` |
| engine/reconcile.py | 6 | (iv) | `  dispatched -> weighed    transport-leg diversion` |
| app/main.py | 17 | **(iii)** | `    description="Diversion detection for India's Public Distribution System.",` |
| seed.py | 198 | (iv) | `        # Paper diversion at the depot is rare; dispatch usually matches the` |
| tests/conftest.py | 111 | (iv) | `# --- #4521 Sitapur — transport diversion, everything available ---` |
| tests/conftest.py | 120 | (iv) | `# --- #4102 Barabanki — transport diversion, GPS unit not fitted ---` |
| frontend/src/pages/Rulebook.jsx | 155 | **(iii)** | `available once. Public complaints are not evidence of diversion on their own: they` |

### complaint — 203 hits (all true)

Second-heaviest coupling. It appears as a table, a model class, five columns,
two YAML keys, a JSON contract key, an audit event type, and a large amount of
UI copy.

**backend/app/engine/complaints.py** — the whole module. Lines 1(iv), 8(iv),
14 (`from ..models import Complaint`), 20(iv), 30
(`rulebook.get("corroboration", {}).get("complaint_bonus", {})`), 33
(`def complaints_in_window(...)`), 34(iv), 45, 47, 48, 49, 51 (ORM query on
`Complaint`), 56 (`def link(...)`), 57(iv), 59-60(iv), 62(iv), 70, 73, 74
(`complaint.linked_case_id = case_id`), 80(iv), 81
(`.get("min_complaints", 3)`).

**backend/app/engine/memo.py**

| Line | Class | Content |
|---:|---|---|
| 73 | (i) | `def build_memo(shop_id, score, severity, rule_hits, complaint_bonus):` |
| 81 | (i) | `    count = complaint_bonus.get("count", 0)` |
| 82 | (i) | `    if complaint_bonus.get("contribution"):` |
| 85 | **(iii)** | `` f" Corroborated by {count} complaint{plural} in the preceding " `` |
| 86 | **(iii)** | `` f"{complaint_bonus.get('window_days')} days." `` |

**backend/app/engine/score.py** — 24 (`def compute(features, rulebook,
complaints_count)`), 27, 30, 46 (`"complaint_bonus": complaint_bonus`), 47, 51
(`def _complaint_bonus(...)`), 54-55(iv), 58, 59 (`min_complaints`), 61, 65.
All (i), with `"complaint_bonus"` at line 46 also being a **(vi)** contract key.

**backend/app/engine/audit.py:8** (iv) — `COMPLAINT_LINKED` named in the docstring.
**backend/app/engine/stats.py:5** (iv) — "fired rule weights plus the complaint bonus".
**backend/app/engine/__init__.py:2, 4** (iv) — module inventory (stale, see §10).

**backend/app/models.py**

| Line | Class | Content |
|---:|---|---|
| 57 | (i) | `    complaints: Mapped[list["Complaint"]] = relationship(back_populates="shop")` |
| 147 | (i) | `class Complaint(Base):` |
| 150 | **(ii)** | `    __tablename__ = "complaints"` |
| 161 | (iv) | `    # Set by engine/complaints.py when a complaint falls inside a case window.` |
| 165 | (i) | `    shop: Mapped["Shop"] = relationship(back_populates="complaints")` |
| 196 | **(ii)** | `    complaint_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)` |
| 197 | **(ii)** | `    complaint_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)` |
| 198 | **(ii)** | `    complaint_contribution: Mapped[int] = mapped_column(Integer, nullable=False, default=0)` |
| 240 | (iv) | `    Events: CASE_OPENED, RULE_FIRED, COMPLAINT_LINKED, NOTE_ADDED,` |

**backend/app/routers/cases.py** — 16
(`from ..engine import complaints as complaints_engine`), 22 (`Complaint` import),
40(iv), 60, 61, 86(iv), 92, 119, 134, 135, 136 (writing the three case columns),
181(iv), 183, 191 (**the audit event type string `"COMPLAINT_LINKED"`**),
234(iv), 241 (`Case.complaint_count.desc()` in the tie-break ORDER BY), 262(iv),
281, 282, 283 (the linked-complaints query), 306-309 (`complaint_bonus` response
dict), 311 (`complaints=linked` — **(vi)** contract key), 348(iv).

**backend/app/rules.yaml**

| Line | Class | Content |
|---:|---|---|
| 62 | **(v)** | `  complaint_bonus:` |
| 63 | **(v)** | `    min_complaints: 3` |

(`window_days: 14` and `weight: 10` sit under the same key at lines 64-65.)

**backend/app/schemas.py** — 72 (`class ComplaintBonus(BaseModel)`), 73(iv),
82 (`class ComplaintOut(BaseModel)`), 87(iv), 132
(`    complaint_bonus: ComplaintBonus` — **(vi)**), 133-134(iv), 135
(`    complaints: list[ComplaintOut] = []` — **(vi)**).

**backend/seed.py** — 35 (`Complaint` import), 47(iv), 73
(`COMPLAINT_SOURCES = ["portal", "helpline", "walk_in"]`), 74
(`COMPLAINT_CATEGORIES = [...]`), 82 (`COMPLAINT_TEXTS = {...}`), 120, 121, 141,
142, 162, 163 (the fixture `complaints_in_window` / `complaints_outside_window`
values 7/2, 2/1, 6/0), 246, 248, 269, 270, 438
(`def write_complaints(db, spec)`), 441-442(iv), 446, 450, 452, 454, 457
(`db.add(Complaint(**row))`), 461 (`def complaint_row(...)`), 462, 466, 468, 470,
516, 524, 537.

**backend/tests/** — conftest.py 23, 25(iv), 117, 127, 136, 165(iv), 169, 170,
195, 196, 197, 199, 206, 207; test_api.py 111; test_audit.py 54, 55, 56;
test_complaints.py 1(iv), 3(iv), 5(iv), 10, 12, 21, 22(iv), 23, 31, 32(iv), 40,
41, 47, 51, 57, 58, 66, 70(iv), 77, 83, 84, 87; test_memo.py 26, 33, 35, 48, 55,
64; test_rulebook.py 33, 34, 43; test_score.py 21, 42, 43, 64, 65, 98, 118, 127,
164, 166, 167.

**frontend/src/**

| File:Line | Class | Content |
|---|---|---|
| components/Tag.jsx:12 | (iv) | `// table, a complaint's open/closed state, an audit event's type. It is NOT for` |
| pages/Auditor.jsx:55 | **(i)** | `    case 'COMPLAINT_LINKED':` |
| pages/Auditor.jsx:56 | **(iii)** | `` return `${p.count} complaint${p.count === 1 ? '' : 's'} inside the ${p.window_days}-day window. Bonus ${...}.` `` |
| pages/CaseDetail.jsx:85 | (i) | `  const { shop, complaint_bonus: bonus } = detail` |
| pages/CaseDetail.jsx:158 | **(iii)** | `<SectionHeading title="Linked complaints">` |
| pages/CaseDetail.jsx:166 | (i) | `{detail.complaints.length === 0 ? (` |
| pages/CaseDetail.jsx:168 | **(iii)** | `<EmptyState title="No complaints inside the window">` |
| pages/CaseDetail.jsx:170 | **(iii)** | `opened. Older complaints, if any, are outside the window and were not counted.` |
| pages/CaseDetail.jsx:175-191 | (i)/(iii) | the complaint list rows: `complaint.category`, `.source`, `.filed_at`, `.status`, `.text` |
| pages/Officer.jsx:29 | (iv) | `// and its tie-break reads complaint_count, which this row does not carry.` |
| pages/Rulebook.jsx:154 | (i)(iii) | `{book.corroboration.complaint_bonus.weight}` |
| pages/Rulebook.jsx:155 | **(iii)** | `available once. Public complaints are not evidence of diversion on their own: they` |
| pages/Rulebook.jsx:162 | **(iii)** | `Complaints corroborate the case` |
| pages/Rulebook.jsx:164 | **(iii)** | `<span className={...}>complaint_bonus</span>` — the YAML key rendered on screen |
| pages/Rulebook.jsx:167 | **(iii)** | `<span className={...}>complaints in window</span>` |
| pages/Rulebook.jsx:170-171 | (i)(iii) | `≥ {…min_complaints} in {…window_days} days` |
| pages/Rulebook.jsx:182, 194 | (i) | `+{book.corroboration.complaint_bonus.weight}` |
| severity.js:12 | (iv) | `//       inline status (Rulebook severities, complaint status, note outcomes)` |

**docs/contract/case_detail.json**

| Line | Class | Content |
|---:|---|---|
| 81 | **(vi) key** | `  "complaint_bonus": {` |
| 86 | **(vi) key** | `  "complaints": [` |
| 148 | (vi) value | the memo, containing `"Corroborated by 7 complaints in the preceding 14 days."` |

### GPS / gps — 56 hits (all true)

| File | Line | Class | Content |
|---|---:|---|---|
| engine/memo.py | 27 | **(i)(iii)** | `    "gps_deviation": lambda value, threshold: f"a {value:g} km route deviation",` |
| engine/reconcile.py | 63 | **(i)** | `        "gps_deviation_km": _gps_deviation_km(delivery),` |
| engine/reconcile.py | 82 | (i) | `def _gps_deviation_km(delivery):` |
| engine/reconcile.py | 83 | (iv) | `    """Max distance off the registered route, or None if no GPS unit is fitted.` |
| engine/reconcile.py | 85 | (iv) | `    gps_available is checked before the reading precisely so that "no device"` |
| engine/reconcile.py | 89 | (i)(ii) | `    if not _field(delivery, "gps_available"):` |
| engine/reconcile.py | 91 | (i)(ii) | `    return _field(delivery, "gps_deviation_km")` |
| models.py | 9 | (iv) | `* "Unavailable" is modelled explicitly (gps_available, nullable weighed_kg /` |
| models.py | 99 | (iv) | `    """The transport leg: depot dispatch to shop arrival, with GPS."""` |
| models.py | 116 | **(ii)** | `    gps_deviation_km: Mapped[float \| None] = mapped_column(Float)` |
| models.py | 117 | (iv) | `    # False when the vehicle has no working GPS unit fitted. Keeps "no device"` |
| models.py | 119 | **(ii)** | `    gps_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)` |
| rules.yaml | 27 | **(v)** | `  - id: gps_deviation` |
| rules.yaml | 29 | **(v)** | `    field: gps_deviation_km` |
| seed.py | 116, 117 | (i) | `"gps_deviation_km": 3.4,` / `"gps_available": True,` |
| seed.py | 137, 138 | (i) | `"gps_deviation_km": None,  # no GPS unit fitted -> gps_deviation skipped` / `"gps_available": False,` |
| seed.py | 158, 159 | (i) | `"gps_deviation_km": 0.8,` / `"gps_available": True,` |
| seed.py | 211, 216, 223, 228 | (i) | the four archetype `gps_km = round(random.uniform(...), 1)` draws |
| seed.py | 233 | (iv) | `        # F5 coverage: a scale that failed to report, and vehicles with no GPS` |
| seed.py | 236 | (i) | `        gps_available = random.random() > 0.12` |
| seed.py | 265, 266 | (i) | `"gps_deviation_km": gps_km if gps_available else None,` / `"gps_available": gps_available,` |
| seed.py | 355, 356 | (i)(ii) | history-cycle delivery GPS |
| seed.py | 377, 378 | (i)(ii) | scored-cycle delivery GPS |
| tests/conftest.py | 47, 56, 57 | (i) | `_delivery(shop_id, gap_hours, gps_deviation_km, gps_available)` |
| tests/conftest.py | 120, 124 | (iv) | `# --- #4102 Barabanki — transport diversion, GPS unit not fitted ---` |
| tests/test_api.py | 97 | (i) | `    assert skipped[0]["rule_id"] == "gps_deviation"` |
| tests/test_audit.py | 83 | (i) | `    for rule_id in ("weighing_variance", "delivery_gap", "gps_deviation"):` |
| tests/test_reconcile.py | 46, 49, 55, 61, 64, 65 | (i) | the two GPS availability tests |
| tests/test_rulebook.py | 28, 90, 91, 119, 121 | (i) | the rule-id assertions and the skipped-row test |
| tests/test_score.py | 60, 61, 76, 118, 123, 136 | (i) | feature-key assertions |
| case_detail.json | 45 | **(vi)** | `      "rule_id": "gps_deviation",` |

Also user-visible: `rules.yaml:28` /
`case_detail.json:46` label `Vehicle deviated from registered route`, and
`case_detail.json:47` `"raw_value": "3.4 km"`.

### What §8 implies for rename cost — factual summary

Counted, not estimated:

- **`shop` is embedded in one table name (`shops`), one class (`Shop`), one
  Pydantic model (`ShopRef`), four foreign-key columns (`cycles.shop_id`,
  `deliveries.shop_id`, `transactions.shop_id`, `complaints.shop_id`,
  `cases.shop_id` — five in total), one feature-dict key (`shop_id`), one JSON
  contract key (`shop`), one audit-payload key (`shop_id`), and roughly 30
  user-visible strings.**
- **`complaint` is embedded in one table (`complaints`), one class
  (`Complaint`), three `cases` columns (`complaint_count`,
  `complaint_window_days`, `complaint_contribution`), one FK
  (`complaints.linked_case_id`), one YAML key (`corroboration.complaint_bonus`
  with `min_complaints`), two JSON contract keys (`complaint_bonus`,
  `complaints`), one audit event type (`COMPLAINT_LINKED`), and an engine module
  filename (`engine/complaints.py`).**
- The **four ladder column names** (`allocated_kg`, `dispatched_kg`,
  `weighed_kg`, `dispensed_kg`) each appear in: `models.py`, `schemas.py`,
  `routers/cases.py`, `seed.py`, `conftest.py`, `test_audit.py`,
  `Ladder.jsx` and `case_detail.json` — eight files per name.
- The **three hop ids** (`allocation_to_dispatch`, `dispatch_to_receipt`,
  `receipt_to_counter`) appear in `reconcile.py` (as constants), `schemas.py`
  (as a `Literal`), `models.py` (comment), `rules.yaml` (inside the two variance
  field names), `severity.js` (twice — `HOP_ACTION` and `HOP_LABEL`),
  `Ladder.jsx` (the `HOPS` array), `case_detail.json`, and six test files.
- The **six rule ids** are simultaneously YAML keys, `rule_hits.rule_id` values
  stored in the committed database, keys of `memo.PHRASINGS`, and assertion
  literals in three test files.
- Domain vocabulary that exists **only** in comments and can be reworded freely:
  `grain` (7 of 8), `beneficiary` (2 of 2), `fair-price` (1 of 1),
  `consignment` (3 of 5).
- Domain vocabulary baked into **stored data** in `leakproof.db`, so a rename
  requires a reseed and invalidates the committed file: the `FPS ` name prefix
  on all 60 shops, the six `complaints.category` values (`short_weight`,
  `shop_closed`, `overcharging`, `quality`, `epos_failure`,
  `refused_entitlement`), the six complaint text strings, the six
  `rule_hits.rule_id` and `rule_hits.label` values across 360 rows, the three
  `cases.gap_hop` values, and the full `rules.yaml` text plus its sha256 in
  `rulebook_versions`.

---

## 9. Environment

### 9.1 `backend/requirements.txt` (7 lines, verbatim)

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
pydantic==2.10.4
pyyaml==6.0.2
pytest==8.3.4
httpx==0.28.1
```

### 9.2 `.gitignore` (12 lines, verbatim)

```gitignore
# backend/leakproof.db is NOT ignored. It is committed on purpose so a clone
# demos the same 60 shops without running seed.py first.

.venv/
__pycache__/
*.py[cod]
.pytest_cache/

node_modules/
frontend/dist/

.DS_Store
```

### 9.3 Runtime versions

| Thing | Version | How determined |
|---|---|---|
| Python | **3.11.9** | `python --version` in the session shell |
| Node | **v24.19.0** | `node --version` (README says "expect v20.x") |
| npm | **11.16.0** | `npm --version` |
| OS | **Windows 11 Home Single Language, 10.0.26200 (win32)** | session environment |
| Shell used for the scan | Git Bash (POSIX) alongside PowerShell 5.1 | |

### 9.4 Config files

| File | Present? | Contents |
|---|---|---|
| `.env` | **ABSENT** | no `.env` at root, in `backend/`, or in `frontend/` |
| `.env.example` | **ABSENT** | |
| `Dockerfile` / `docker-compose.yml` | **ABSENT** | CLAUDE.md forbids Docker |
| CI workflow (`.github/`, `.gitlab-ci.yml`, etc.) | **ABSENT** | no `.github` directory at all |
| `Makefile` | **ABSENT** | |
| `pytest.ini` / `setup.cfg` / `pyproject.toml` / `tox.ini` | **ABSENT** | pytest runs on defaults |
| `.eslintrc*` / `.prettierrc*` | **ABSENT** | no JS linting or formatting config |
| `.editorconfig` | **ABSENT** | |
| `.nvmrc` | **ABSENT** | |
| `frontend/package-lock.json` | present | 2,750 lines; not reproduced here |
| `.gitignore` | present | reproduced above at §9.2 |

No environment variable is read anywhere in the codebase. `DATABASE_URL` is
built from a path literal in `db.py`; `API_BASE` is a literal in `api.js`; CORS
origins are literals in `main.py`.

### 9.5 Installed state

| Question | Answer |
|---|---|
| Does `frontend/node_modules` exist? | **Yes** — 101 top-level entries; `npm install` has been run |
| Does `backend/.venv` exist? | **Yes** — populated (`.venv/Lib/site-packages` contains fastapi, sqlalchemy, pydantic, pytest, etc.) |
| Is there a build output? | **Yes** — `frontend/dist/` exists (`index.html`, `assets/index-CmAs-zkb.js` 67 lines, `assets/index-CnvqTHBL.css` 1 line). It is gitignored and stale relative to `src/` |
| Are there pytest caches? | **Yes** — `backend/.pytest_cache/` (with `lastfailed`) and a stray `frontend/.pytest_cache/`. Both gitignored |
| Has the DB been through the API? | **Yes** — `cases`, `rule_hits` and `audit_log` are populated in the committed file, including 2 `NOTE_ADDED` and 2 `SCORE_RECOMPUTED` rows |

Commands as documented in CLAUDE.md and README:

```bash
# backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
pytest -v

# frontend
cd frontend
npm install
npm run dev                   # :5173
```

`frontend/package.json` scripts: `dev` → `vite`, `build` → `vite build`,
`preview` → `vite preview`. There is no `test`, `lint` or `format` script.

---

## 10. Honest gap list

Purely factual. No recommendations.

### 10.1 Stubs, `pass`, `TODO`, `FIXME`, or functions returning a constant

A repository-wide grep for `TODO`, `FIXME`, `XXX`, `HACK`, `NotImplemented` and
`stub` over `backend/app`, `backend/seed.py`, `backend/tests` and
`frontend/src` returns **two** hits, both of them stale docstrings rather than
markers on unfinished code:

| File | Line | Content | Reality |
|---|---:|---|---|
| `backend/app/engine/__init__.py` | 4-5 | `F1, F2, F3/F5 and the memo template are implemented. complaints.py (F4) and audit.py (F6) are still stubs."""` | **Stale.** `complaints.py` (81 lines) and `audit.py` (84 lines) are both fully implemented and fully tested. |
| `backend/app/routers/__init__.py` | 1 | `"""API routers: cases, rulebook, audit. All stubs until Stage 2."""` | **Stale.** All three routers are implemented; `cases.py` is 364 lines. |

There are **zero** bare `pass` statements anywhere in `backend/`.

Functions that return a constant, or are otherwise trivially fixed:

| Function | File | What it returns |
|---|---|---|
| `health()` | `app/main.py:35` | `{"status": "ok", "service": "leakproof", "version": app.version}` — a literal dict |
| `_coverage_pct(rule_hits)` | `engine/score.py:69` | returns the literal `100` when `rule_hits` is empty |
| `bonus_threshold(rulebook=None)` | `engine/complaints.py:79` | never called from anywhere in `app/`, `seed.py` or the tests — dead code |
| `worst_variance` / `z_scores` / `z_scores_from_features` / `confirms` | `engine/stats.py` | live code, but their output reaches only two display-only columns (`z_score`, `z_confirms`) and never affects a score |

Declared-but-unused surface:

- `frontend/src/ui.js` exports `BODY` and `CELL_NUM`; neither is imported by any
  page or component.
- `engine/complaints.bonus_threshold()` — unused (above).
- `RulebookVersion` — written by `seed.py`, **never read by anything**. The
  `yaml_text` and `checksum` columns therefore cannot participate in
  re-derivation even though that is the stated reason they exist.
- `Shop.opens_hour`, `Shop.closes_hour`, `Shop.dealer_name`,
  `Delivery.vehicle_no`, `Delivery.route_id`, `Transaction.txn_ts`,
  `Transaction.quantity_kg`, `Transaction.auth_mode`,
  `Transaction.outside_hours`, `Cycle.opened_on`, `Cycle.closed_on` — all
  written by `seed.py`, none read by the engine, the API or the UI.
- `Shop.lat` / `Shop.lng` — carried all the way into every API response via
  `ShopRef` and never rendered; `schemas.py` says "drop a map pin" and no map
  exists.
- `USE_MOCK` in `frontend/src/api.js` is `false`; the `resolveMock` path and the
  `@contract` import are live code kept as a fallback.
- `Case.status` is only ever written as `"OPEN"`; nothing sets it to anything
  else, and there is no close/escalate route.

### 10.2 Hardcoded values that look back-solved for the demo

These are *stated* as scoping decisions in `PROJECT-BRIEF.md` and `CLAUDE.md`,
and they are all present in the code:

| Value | Location | Why it reads as back-solved |
|---|---|---|
| rule weights 30 / 25 / 22 / 20 / 15 / 8 | `rules.yaml` | Sum to 120, and the specific combination 30+25+22+10 = 87 is the number on the deck. PROJECT-BRIEF and the Rulebook page both say "back-solved for the demo case, not learned". |
| complaint bonus 10, min 3, window 14 days | `rules.yaml` | 3 is exactly one below #4102's 2 and well below #4521's 7 — chosen so one fixture fires the bonus and one does not. |
| thresholds −5.0 %, 48 h, 2.0 km, −5.0 %, 0.6, 3 | `rules.yaml` | Each sits just inside the corresponding fixture reading (−8.21 vs −5.0; 61 vs 48; 3.4 vs 2.0; −8.70 vs −5.0; 0.55 vs 0.6; 4 vs 3). |
| `ration_cards` 1200 / 900 / 1000 | `seed.py:109,130,151` | Chosen so `ratio × cards` is a whole number: 0.88×1200 = 1056, 0.71×900 = 639, 0.55×1000 = 550. The comment at `seed.py:99` says so explicitly. |
| `weighed_kg` 11015 / 7512 / 8970 and `dispensed_kg` 10980 / 7490 / 8190 | `seed.py:113-114,134-135,155-156` | Back-solved to land on −8.21 % / −0.32 %, −6.10 % / −0.29 %, −0.33 % / −8.70 % to two decimals. |
| `ANCHOR = datetime(2026, 8, 14, 9, 12, 0)` | `seed.py:48` **and** `engine/complaints.py:25` | Duplicated in two files. Deliberately not `datetime.now()`, with a comment explaining that a wall-clock anchor would slide the complaints out of the window and #4521 would stop scoring 87. |
| `random.seed(4521)` | `seed.py:44` | The seed value is the demo shop id. |
| `PINNED_CASE_IDS = {"4521": "C-0041"}` | `routers/cases.py:34` | One shop is given a fixed case id because C-0041 is already printed in the deck and the contract; every other case id is positional. |
| `SCORED_PERIOD = "2026-08"` | `routers/cases.py:29` **and** `seed.py:49` | Duplicated. A single month is scored; the two history months exist only for a chart that was never built. |
| `DEFAULT_CASE = 'C-0041'` | `frontend/src/pages/Auditor.jsx:24` | The Auditor page opens on the demo case. |
| `{ to: '/cases/C-0041', label: 'Case Detail' }` | `frontend/src/roles.js:30` | The demo case id is hardcoded into the sidebar nav for all three roles. |
| Auditor dropdown fallback `{ case_id: DEFAULT_CASE, shop: { id: '4521', name: 'FPS Sitapur-12' } }` | `frontend/src/pages/Auditor.jsx:120` | A hardcoded demo shop shown when `/api/cases` has not answered. |
| `"C-0010"` | `backend/tests/test_api.py:92` | A positionally-assigned case id hardcoded into an assertion. |
| `Z_CONFIRMS_AT = 2.0` | `engine/stats.py:22` | Documented as *not* tuned — #4521 lands at 1.66 and its badge reads "does not confirm". In the committed data no case at all confirms. |
| Severity bands 75 / 50 | `rules.yaml:5-6` **and** `engine/score.py:89,91` as `.get()` defaults | Duplicated in two places. |
| Display cap `100` | `engine/score.py:33` | The only scoring constant that is not in the YAML. |
| `"Public Distribution System · Uttar Pradesh · cycle 2026-08"` | `TopBar.jsx:37`, `SignIn.jsx:107` | The state and cycle are literal UI strings, duplicated across two files. |
| `"District Supply Office, Sitapur"` | `rules.yaml:2` | The maintainer name is data, rendered on the Rulebook page. |
| `checksum 3419eeca…` | `leakproof.db` `rulebook_versions` | Computed at seed time over the current `rules.yaml`; never verified afterwards. |

### 10.3 README feature table F1–F6 vs. the code

| # | Feature as README states it | Code found? | Evidence |
|---|---|---|---|
| **F1** | Four-hop reconciliation ladder — locates which hop | **Yes, fully** | `engine/reconcile.py` (`reconcile`, `_variance_pct`, `locate_gap`); `components/Ladder.jsx`; 12 tests in `test_reconcile.py`. **One caveat:** the model is named "four-hop" and there are four *rungs* but only **two** measured hops. `locate_gap()` only ever considers `dispatch_to_receipt` and `receipt_to_counter`. The third hop, `allocation_to_dispatch`, is declared in `schemas.GapHop`, in `severity.js` (both `HOP_ACTION` and `HOP_LABEL`), and in `Ladder.jsx`'s `HOPS` array with `variance: null` — but **no code ever computes its variance or returns it as a gap**, even though `seed.py:200` deliberately makes 10 % of generated shops short at that hop. That variance is invisible to the engine. |
| **F2** | Versioned YAML rulebook — officer edits thresholds without a deploy | **Yes** | `rules.yaml`, `engine/rulebook.py` (`load` with no caching, `evaluate`), `routers/rulebook.py` (loads per request, no response model), `pages/Rulebook.jsx`. **Caveat:** "versioned" is only partly true — `rulebook_versions` stores the text and checksum, and nothing ever reads that table, so an old rulebook cannot actually be reconstructed. A recompute always uses the current file on disk. |
| **F3** | Reasoning trace — every rule, value, threshold, contribution | **Yes, fully** | `engine/rulebook._evaluate_rule` produces the 7-key row; `engine/score.compute` returns them; `rule_hits` persists them; `components/TraceTable.jsx` renders all three states. |
| **F4** | Complaint auto-linking — 14-day window corroborates | **Yes, fully** | `engine/complaints.py` (`complaints_in_window`, `link`), `Case.complaint_*` columns, `COMPLAINT_LINKED` audit events, `CaseDetail.jsx` linked-complaints block, `test_complaints.py`. |
| **F5** | Graceful degradation — missing data is "couldn't check" | **Yes, fully** | `None`-preserving derivations in `reconcile.py`; the `"skipped"` default in `_evaluate_rule`; `_coverage_pct` in `score.py`; the greyed italic row in `severity.js`/`TraceTable.jsx`; the coverage badge in `CaseDetail.jsx`; `stats.z_scores` excluding unmeasurable shops. |
| **F6** | Append-only audit trail — every score re-derivable months later | **Yes, with two documented limits** | `engine/audit.py` (`log`, `summarise`, `recompute`), `routers/audit.py` (GET only), `AuditLog`, the Auditor page, `test_audit.py`. **Limit 1:** append-only is enforced by convention and by a source-text grep in a test that covers only two files — there is no database-level constraint. **Limit 2:** "re-derivable" compares five scalar fields (`score`, `severity`, `coverage_pct`, `gap_hop`, `rulebook_version`) against the **current** `rules.yaml`, not against the stored snapshot; `rule_hits` are not compared at all. |

### 10.4 Things named in the governing documents with no corresponding code

| Named where | What | Status |
|---|---|---|
| `PROJECT-BRIEF.md` API contract | `GET /api/shops/{shop_id}` — "shop profile + cycle history" | **ABSENT.** No `routers/shops.py`, no `/shops` route, no frontend caller. The two history cycles per shop are unreachable over the API. |
| `PROJECT-BRIEF.md` → Screens → CaseDetail | "· trend" | **ABSENT.** No chart is rendered anywhere. |
| `CLAUDE.md` → Stack, README → Tech stack | **Recharts** | **ABSENT.** Not in `package.json`, not in `node_modules` usage, not imported anywhere. |
| `PROJECT-BRIEF.md` → Declared limitations #3 | "Escalation is a stub — no email or SMS is sent" | **ABSENT** — there is no escalation code at all, not even a stub function. Nothing in the codebase mentions escalation, email or SMS. |
| `schemas.py:25` | "drop a map pin" | **ABSENT.** `lat`/`lng` reach the client and are never used. |
| `docs/contract/fixtures.md` final paragraph | "no generated shop is built to reach #4521's combination" | **Contradicted by the data.** Four shops score 87 (4521, 4910, 4219, 4458). `PROJECT-BRIEF.md` carries a Stage-4 correction saying so; `fixtures.md` was never updated. |
| `CLAUDE.md` invariant 6 | grep `backend/` for `.delete(` / `UPDATE` near audit | The automated version in `test_audit.py` checks **only** `engine/audit.py` and `routers/audit.py`, not all of `backend/`. |
| `CLAUDE.md` → Honesty rules | "role-scoped queries at the API layer" | **ABSENT.** No query is scoped by role; every role gets identical rows. |
| `CLAUDE.md` repo map / `models.py` docstring | "9 SQLAlchemy tables" / "The nine LEAKPROOF tables" | Accurate — there are exactly nine. |
| README onboarding | clone URL `AI-Based-Public-Distribution-System-Diversion-Detection` | Does not match the configured origin `Gods-Plan-SIH-2026`. |
| README prerequisites | `node --version # expect v20.x` | Installed Node is v24.19.0. |

### 10.5 Other factual observations

- **The repository has no commits.** Every file is untracked; `git log` fails.
  Nothing in `.gitignore` has taken effect yet in a tracked sense.
- `frontend/.pytest_cache/` exists although there are no Python tests under
  `frontend/`.
- `frontend/dist/` contains a stale build (a 67-line JS bundle, i.e. minified
  output from an earlier state of `src/`).
- `engine/complaints.ANCHOR` and `seed.ANCHOR` are two independent literals of
  the same timestamp; likewise `SCORED_PERIOD` in `routers/cases.py` and
  `seed.py`. Nothing keeps either pair in sync.
- `POST /api/cases/{case_id}/notes` returns a shape that does not match
  `AuditEventOut`, and has no `response_model`.
- `ensure_cases()` runs on every request to `/api/cases`, `/api/cases/{id}`,
  `/api/audit/{id}`, `/notes` and `/recompute`. Its guard is
  `if db.query(Case).count() > 0: return`, so on a cold database the first
  request of any kind performs 60 full derivations inside the request.
- The `Case.status` column, the `Complaint.status` column and the `RuleHit.status`
  column all use the name `status` for three unrelated vocabularies
  (`OPEN`; `open`/`closed`; `fired`/`passed`/`skipped`).
- `seed.py` makes ~10 % of generated shops short at `allocation_to_dispatch`
  (line 200), and no rule in `rules.yaml` reads that hop, so those shortfalls
  score zero and are never localised.
- `test_api.py` mutates its copy of the database (it posts a note and runs a
  recompute), but the copy is per-test in `tmp_path`, so the committed file is
  untouched by the suite. The 2 `NOTE_ADDED` / 2 `SCORE_RECOMPUTED` rows in the
  committed file came from manual use, not from `pytest`.

---

*End of REPO-CONTEXT.md.*
