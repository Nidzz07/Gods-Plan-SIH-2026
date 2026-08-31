# CLAUDE.md — NIGRANI

## What this is
NIGRANI detects anomalies, fraud and inefficiency in the implementation of
MPLADS — the Members of Parliament Local Area Development Scheme — and explains
every flag in language an officer can act on and an auditor can re-derive months
later.

Smart India Hackathon, problem statement PS 26102, MoSPI / DIID.
Team ExploreeTinkerBell. Two developers, hard deadline.

The project inherits its detection-engine architecture from LEAKPROOF, a PDS
diversion prototype (tag `leakproof-baseline`). The architecture is kept. The
entire domain layer is rebuilt against REAL data downloaded from
mplads.mospi.gov.in and committed in `data/raw/`.

Read, in this order, before your first edit in any session:
  1. `docs/data/DATA-PROFILE.md`   — what the real data contains
  2. `docs/domain/DOMAIN-MODEL.md` — ladders, tables, rulebook
  3. `PROJECT-BRIEF.md`            — features, personas, scope

`docs/data/DATA-PROFILE.md` is the authority for every threshold and every
claim about the data. If code and profile disagree, the profile wins until it is
re-measured.

## Stack — fixed, do not substitute
Backend : Python 3.11 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · PyYAML · SQLite
          · pytest · pandas · numpy · scikit-learn · networkx · rapidfuzz
          · passlib[bcrypt] · python-jose
Frontend: React 18 · Vite · Tailwind · React Router · Recharts · react-leaflet
          · TanStack Table
Node    : pinned to 22.11.0 via nvm, recorded in `.nvmrc` at the repo root.

SQLite is RETAINED deliberately. 118K raw rows, reduced to ~27K work rows with
pre-aggregated agency, vendor and MP-account rollups, fits comfortably in a
single file. Postgres would add a service dependency, a container, and a demo
failure mode, for no benefit a judge can see. The SQLAlchemy URL stays
swappable, so moving to Postgres is a configuration change and not a rewrite.
Say that out loud when asked; do not apologise for it.

Recharts is listed above and, unlike the inherited project, MUST actually be
installed in Phase 8. The inherited repo declared it and never added it.

Do not introduce Postgres, Supabase, Docker, Redis, Celery, an ORM other than
SQLAlchemy, a client state library, a component library, or any LLM API call.
If you think one is needed, say so and stop — do not add it.

## Repo map
```
backend/
  app/
    main.py            FastAPI app, CORS to :5173, router registration
    db.py              engine, SessionLocal, Base
    models.py          SQLAlchemy tables (see DOMAIN-MODEL.md (e))
    schemas.py         Pydantic shapes — MUST mirror docs/contract/case_detail.json
    constants.py       every shared literal, defined once (invariant 7)
    rules.yaml         F2 rulebook, loaded at runtime, never imported as constants
    auth.py            hashing, JWT issuance, get_current_user, require_role
    seed_users.py      the four demo accounts — a build step, run last
    engine/
      reconcile.py     F1  fund ladder (2 hops) + lifecycle ladder (3 lags)
      derive.py        derived feature dictionary (DOMAIN-MODEL.md (f))
      rulebook.py      F2  load() + evaluate()
      score.py         F3+F5 composite score, trace, coverage_pct
      pattern.py       F4  agency pattern-of-conduct corroboration
      memo.py          plain-language memo — template f-string, NOT an LLM
      audit.py         F6  append-only log
      ablation.py      F9  mask a field, re-score, measure coverage delta
    ml/                F7  duplicates, anomaly badge, delay forecast, graph
    routers/
      scoping.py       the role predicate — every WHERE clause, in one place
  ingest/              CSV loaders, canonicalisation, ingest_rejects
  seed.py              labelled synthetic controls only — never bulk fake data
  tests/
frontend/
  src/api.js           single fetch wrapper
  src/pages/           per-persona screens (see PROJECT-BRIEF.md)
  src/components/
data/raw/              the twelve MPLADS exports — COMMITTED on purpose
data/interim/          generated, gitignored
data/processed/        generated, gitignored
docs/data/             DATA-PROFILE.md
docs/domain/           DOMAIN-MODEL.md
docs/contract/         case_detail.json (frozen), fixtures.md
docs/design/           REDESIGN-SPEC.md
```

## Invariants — numbered, non-negotiable
Breaking any of these breaks either the pitch or the honesty of the product.

1. **The score comes only from the rulebook.** The composite score is the sum of
   fired rulebook weights plus the pattern-of-conduct corroboration bonus, and
   nothing else. Anomaly scores, delay forecasts, z-scores and graph centrality
   are badges worth ZERO. A test asserts this per model: perturb the model
   output, assert the score is unchanged.
2. **Missing data is `skipped`, never `passed`.** A skipped rule reduces
   `coverage_pct`. Its weight is never redistributed to the remaining rules.
   "Not published by MoSPI" and "published as zero" are different findings and
   must stay distinguishable end to end — in the derived features, in
   `rule_hits.skip_reason`, in the contract, and on screen.
3. **Every declared hop and lag is computed.** Any hop or lag named in
   `schemas.py`, in a severity map, or in a ladder component MUST have a
   derivation function in `engine/` and a test. The inherited project declared
   `allocation_to_dispatch` in three files and never computed it once. Do not
   repeat that.
4. **`audit_log` is append-only.** No UPDATE, no DELETE, and no helper capable of
   either, anywhere in `backend/`. The enforcing test greps ALL of `backend/`,
   not only `audit.py`.
5. **Recompute re-derives against the snapshot.** A recompute reads the rulebook
   snapshot stored in `rulebook_versions` for that case, NOT the current
   `rules.yaml`, and compares the full `rule_hits` trace — rule ids, raw values,
   thresholds, contributions, statuses — not just the scalar score.
6. **Thresholds come from measured distributions.** Every threshold is set from
   `docs/data/DATA-PROFILE.md` and carries a YAML comment naming its firing
   count on the profiled sample. Thresholds are NOT back-solved to make a demo
   case land on a round number. If a fixture score looks untidy, the fixture is
   what it is.
7. **Constants appear once and are imported.** No duplicated literals across
   `ingest/`, `engine/` and `derive.py`. The as-of date, the severity cut-offs,
   the weight total and the file-name map all live in `app/constants.py`.
8. **Case ids are deterministic from the work id**, never from positional
   ordering over a query result. Re-running ingest on the same corpus produces
   the same case id for the same work.
9. **`schemas.py` and `docs/contract/case_detail.json` move together or not at
   all.** Renaming a key on one side alone breaks the frontend silently. Flag
   it, do not just do it.
10. **Role scoping is enforced server-side, in the query.** Never by hiding rows
    in the UI. A District Authority token must not be able to fetch another
    district's cases by editing a URL. Every predicate lives in
    `app/routers/scoping.py`; `tests/test_role_scoping.py` asserts it both
    through HTTP and against the compiled SQL, because a response-body test
    alone would also pass against a server that fetched everything and dropped
    rows in Python — which is the failure this invariant names.
11. **Ingestion never silently drops a row.** Every rejected row is written to
    `ingest_rejects` with a reason. Load counts must reconcile:
    loaded + rejected = rows in file, asserted by a test.
12. **Synthetic rows are labelled.** Any synthetic or injected row carries
    `is_synthetic = true`, is labelled as such in the UI, and is excluded from
    every published aggregate. Real and injected data are never mixed silently.

## Working rules
- Test first. For every engine function, write the pytest assertion against the
  fixture in `docs/contract/fixtures.md` before writing the implementation.
- One feature per session. Do not touch F4 while fixing F2.
- Never edit files outside the feature currently being built. If a fix needs a
  change elsewhere, say so and ask.
- Prefer boring, readable code. A judge may read this on screen.
- No new dependencies without asking.
- Comments explain WHY a threshold or weight is what it is, not what the line
  does. A threshold comment names its firing count.
- Never edit anything in `data/raw/`. Defects are handled in ingest, not by
  correcting the source.

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
  file whose imports land in a later commit — a fresh checkout at any point in
  the history should install and build. If a change needs a sibling file to
  work, they go in together.
- `data/raw/` and the regenerated `docs/data/DATA-PROFILE.md` go in the same
  commit. A profile that describes a different download is worse than none.

## Honesty rules — these appear on stage, keep the code truthful
The following are deliberately scoped and are declared to judges as scoping
decisions. Do not write code, comments, copy or captions that overclaim them.

- Memos are **templates**, not generated text. Never describe `memo.py` output
  as AI-generated, LLM-written, or "natural language generation". The honest
  line is "template now, LLM later".
- A rule-based flag is **rule-based**. Never describe a rulebook hit as
  AI-detected. The ML tier is separately labelled and scores zero.
- A duplicate cluster is a **candidate for review, never fraud**. Many repeated
  works — street lights across a constituency, hand pumps across a block — are
  entirely legitimate. The UI word is "review", never "fraud" and never
  "duplicate payment".
- Forecast horizons are **illustrative**. The delay forecast is trained on a
  truncated sample and its horizon is a demonstration, not a commitment.
- The data is a **truncated sample** of the portal, not the national record. No
  figure derived from it is ever presented as a national total.
- Injected controls are **synthetic and labelled**. Say so on the same screen,
  not in a footnote.
- The role switcher is a **dropdown over seeded accounts**, not an identity
  provider. Server-side scoping is real; the login is a demo.
- Escalation delivers to an in-app queue and an audit event. It does not send
  email or SMS. Say "queued for the State Nodal Authority", not "notified".
- Never describe the SQLite setup as row-level security. It is role-scoped
  queries at the API layer.
- Headline statistics used in the pitch are drawn from `DATA-PROFILE.md` and
  cited to it, or they are labelled illustrative. There is no third option.

## UI conventions

Reference spec: `docs/design/REDESIGN-SPEC.md` — read this before any styling
work. It extends, not replaces, the tokens below.

Brand palette (unchanged, locked since Stage 0):
  bg #FAF8F4 · navy #132A47 · green #2E7D5B · gold #C8952B · coral #D4573D

Text/surface tokens:
  ink #14171A (body text) · ink-secondary #5B6169 (meta/captions) ·
  ink-muted #94989E (disabled/skipped) · border #DDD9D0 ·
  border-strong #C7C2B6 · surface #FFFFFF · surface-sunk #F3F0EA

Rule: navy is for headings and the score-display number ONLY. Body text,
labels, and captions use ink or ink-secondary. Navy-coloured body text is the
single most common regression — check for it explicitly.

Type    : serif display (headings + score-display) / Inter (everything else),
          tabular-nums on ALL numeric elements. Full scale in REDESIGN-SPEC.md —
          six defined sizes, not two.
Spacing : 8px scale only (4/8/16/24/32/48)
Radius  : one 4px token everywhere, including tags — no second radius
Shadow  : one shadow-card token, no second depth
Severity: TWO valid patterns, do not mix on one element —
  (1) coloured left-border on a full data row (case list, trace table)
  (2) rectangular tag — tinted bg, solid-colour text, sentence case,
      ALWAYS with a text label (rulebook severity, status chips)
Tables  : numeric columns right-aligned + tabular-nums; every table has a
          one-line caption; headers are meta-label style (12px uppercase
          tracked ink-secondary), visually distinct from cells
Charts  : brand palette only — no default Recharts colours, ever. Every chart
          has a one-line caption stating what it shows and over what population.
          Axes are labelled with units. Money is rupees in crore or lakh, never
          raw paise-free integers on an axis. No chart junk, no 3D, no gradient
          fills. A chart that needs a legend of more than five entries is the
          wrong chart.
Maps    : react-leaflet, brand palette for choropleth ramps, always with a
          legend and a caption naming the population. MPLADS publishes no
          coordinates, so maps are state- and district-level joins only — never
          imply point-located assets.
Banned  : gradients, rounded-full badges/pills, emoji in UI, more than one
          shadow depth, more than one border-radius, unstyled browser defaults,
          spinner-only loading states, default chart palettes.

## Commands
Backend
```
cd backend && python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m ingest.run           # data/raw/ -> nigrani.db: 65,270 works and their
                               #   sanctions, payments, completions, accounts,
                               #   plus ingest_rejects and the labelled control
python -m app.ml.run           # ml_findings: the four badge tiers, one row per
                               #   sanctioned work per kind, all worth zero
python -m app.ablation.run     # ablation_findings + the regenerated
                               #   docs/reports/DATA-GAP-RECOMMENDATION.md
python -m app.derive_all       # cases, rule_hits, rulebook_versions, audit_log
                               #   and the rollup tables: one case per sanctioned
                               #   work, its full ten-row trace, its opening
                               #   audit events, and the dashboard aggregates
python -m app.seed_users       # the four demo accounts, one per role, each bound
                               #   to a scope CHOSEN from the derived corpus, with
                               #   generated passwords printed once to stdout

pytest -v
uvicorn app.main:app --reload --port 8000
```
**All four build steps are required.** The API only reads; nothing derives a
case on the first request. A clone that runs `ingest.run` and then `uvicorn`
gets a working server with zero cases, which is the most misleading screen the
product can show — `/health` reports `awaiting_build` rather than `ok` for
exactly that reason. The corpus tests skip without step 1 and `test_api.py`
skips without step 4, so `pytest` belongs after the build and not before it.

`seed_users` is fifth and last. It comes after `derive_all` because it picks
its state, district and member by counting derived cases rather than from a
list written into the script, and refuses to write an account onto a scope with
no cases — a login that opens onto an empty screen is indistinguishable from a
broken one. It is idempotent by email address and prints its generated
passwords once; nothing in the repository stores a password. `ingest.run` drops
`users` along with everything else, so accounts do not survive a re-ingest and
re-running this is how you get them back. The test suite seeds its own accounts
on a copy of the corpus and does not need this step.

Every route under `/api` requires a bearer token from `POST /api/auth/login`.
`/health` does not, deliberately: behind a login, an outage and a bad password
would look the same from outside.

`ingest.run` drops and recreates every table, so it comes first and everything
after it must be re-run. The middle three have no dependency on each other and
may run in any order; each is idempotent by rebuild, so a second run replaces
its own output rather than doubling it. Re-run `app.derive_all` after any edit
to `rules.yaml` — until you do, the stored cases are still scored under the
older snapshot, and `GET /api/rulebook` reports `file_matches_stored_version:
false` to say so.

Frontend
```
cd frontend && nvm use && npm install && npm run dev     # :5173
```
