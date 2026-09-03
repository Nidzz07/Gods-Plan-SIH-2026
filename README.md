# NIGRANI

### Explainable anomaly, fraud and inefficiency detection for MPLADS

*Nigrani* — निगरानी — is the Hindi word for oversight or watch-keeping. That is
the whole product in one word: not an accusation engine, a watch-keeper that
shows its working.

Built for **Smart India Hackathon 2026, problem statement PS 26102**, set by the
Ministry of Statistics and Programme Implementation (MoSPI), Data Informatics
and Innovation Division (DIID), by team **ExploreeTinkerBell**.

---

## The problem

MPLADS gives every Member of Parliament an annual allocation — currently ₹5
crore — to recommend local development works. An MP recommends; a District
Authority sanctions and implements through a government agency; payments run to
vendors; the work is reported complete. Roughly ₹4,000 crore a year moves
through this route, across 543 Lok Sabha and 245 Rajya Sabha members, hundreds
of implementing agencies and tens of thousands of vendors.

MoSPI publishes all of it. The data is public, structured, and effectively
unread. Nobody is systematically asking which sanctions sat for a year before
money moved, which works were paid once and then went silent, which agency
sanctioned the same description 244 times, or which works are reported complete
with no payment ever recorded.

Those questions are answerable today from published data. The hard part is not
detection — it is **detection an officer will act on**: every flag has to be
explainable, re-derivable, and honest about what it does not know.

## What NIGRANI does

It ingests the twelve published MPLADS exports committed in `data/raw/`,
reconstructs each work's fund and lifecycle journey, evaluates it against a
versioned rulebook of ten measured rules, and produces a case carrying a full
reasoning trace: every rule, the value it read, the threshold it compared
against, and the points it contributed.

Four properties separate it from a dashboard:

1. **Every score is arithmetic an officer can re-derive on paper.** No model
   contributes a single point.
2. **Missing data is visible.** A rule that could not be evaluated is marked
   *skipped*, lowers the case's coverage, and is never silently counted as a
   pass.
3. **Every score is reproducible months later.** A case stores the rulebook
   snapshot it was scored under, and a recompute re-derives against *that*
   snapshot rather than against today's rules.
4. **The system reports its own blind spots.** The ablation module measures what
   NIGRANI cannot see and turns it into a specific reporting recommendation back
   to MoSPI — see [`docs/reports/DATA-GAP-RECOMMENDATION.md`](docs/reports/DATA-GAP-RECOMMENDATION.md).

## The data is real, and it is a sample

`data/raw/` holds **118,704 rows across twelve CSV exports** downloaded from
the MPLADS portal on 26 August 2026 and committed on purpose, so a fresh clone
reproduces every figure without re-downloading.

Several of those files stop at suspiciously round numbers — 35,000, 29,000,
8,000 — because the portal caps an export. **These are a large sample of MPLADS,
not the complete national record**, and no figure derived from them is ever
presented as a national total. See [`data/raw/README.md`](data/raw/README.md) for
provenance and [`docs/data/DATA-PROFILE.md`](docs/data/DATA-PROFILE.md) for what
the data actually contains.

## The four personas

Four roles, four scopes. Scoping is enforced **server-side, in the query** — a
District Authority token cannot reach another district's rows by editing a URL,
and the tests prove it by editing URLs rather than by trusting the client.

| Role | What they see | What they do |
| --- | --- | --- |
| **Ministry** | Everything, all states | National patterns, rulebook governance, the ablation report |
| **State Nodal Authority** | All districts in one state | Compare districts, triage escalations |
| **District Authority** | Works in one district | Work the case queue, add notes, recompute, escalate |
| **Member of Parliament** | Own works and own account rollup | See account utilisation and which recommendations stalled — **read-only** |

The MP role is deliberately included and deliberately read-only: MPLADS
criticism routinely lands on the member for a delay that occurred entirely
inside the district administration, and the lifecycle ladder shows exactly where
the time went. The scheme's subject does not adjudicate the scheme's findings.

## The four-tier architecture — exactly one tier scores

| Tier | What it does | Moves the score? |
| --- | --- | --- |
| 1. Reconciliation | Derives both ladders and the feature dictionary | **No** — it produces inputs |
| 2. Rulebook | Ten deterministic rules over those features | **YES — this tier and the corroboration bonus are the only sources of score** |
| 3. Statistical | IsolationForest anomaly badge, delay forecast | **No. Zero points. Badge only** |
| 4. Graph | Agency–vendor bipartite concentration | **No. Zero points. Badge only** |

That boundary is enforced by tests that walk the module imports, not merely
documented. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) draws it.

## Scoring

Ten rules, 144 points of rulebook weight, plus a 10-point agency
pattern-of-conduct bonus. Display is capped at 100; the raw total is retained
and shown alongside, because capping is not renormalisation — weights are never
divided, or the arithmetic an officer re-derives would stop matching.

Severity: **HIGH ≥ 75 · MEDIUM ≥ 50 · LOW below 50**, on the capped score.

Every threshold is drawn from a measured distribution in `DATA-PROFILE.md` and
carries a YAML comment naming the count it fired on. No threshold is back-solved
to make a demo case land on a round number. The full table is in
[`PROJECT-BRIEF.md`](PROJECT-BRIEF.md).

## Running it

Two terminals. Python 3.11, Node 22.11.0 (`.nvmrc`).

### Backend

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
python -m app.alerts_run       # alerts: one per HIGH case, routed by the scope
                               #   its work carries. Idempotent BY CASE, not by
                               #   rebuild - a re-run tops the inbox up and never
                               #   resets an acknowledgement
python -m app.seed_users       # the four demo accounts, one per role, each bound
                               #   to a scope CHOSEN from the derived corpus, with
                               #   generated passwords printed once to stdout

pytest -v
uvicorn app.main:app --reload --port 8000
```

**All five build steps are required, in that order.** The API only reads;
nothing derives a case on the first request. A clone that runs `ingest.run` and
then `uvicorn` gets a working server with zero cases, which is the most
misleading screen the product can show — `/health` reports `awaiting_build`
rather than `ok` for exactly that reason. `pytest` belongs *after* the build:
the corpus tests skip without step 1 and the API tests skip without step 4.

A full rebuild from an empty database takes **under two minutes** and is
deterministic — two runs produce identical scores, identical coverage and an
identical audit hash chain.

`seed_users` prints its generated passwords **once** and stores them nowhere.
Re-run it if you lose them.

### Frontend

```
cd frontend && nvm use && npm install && npm run dev     # :5173
```

`frontend/.env.local` (gitignored, so create it once per machine) points the app
at the loopback address rather than the hostname:

```
VITE_API_BASE=http://127.0.0.1:8000
```

It is worth doing. `src/api.js` defaults to `http://localhost:8000` and stays
that way, because that is the address a reader expects and it works everywhere —
but on Windows, resolving `localhost` costs about 200 ms per connection (it tries
the IPv6 address first and falls back), against about 1.6 ms for `127.0.0.1`.
Measured on the development machine: 0.213 s versus 0.0016 s to connect. A
dashboard issues several requests, so that is a visible stall on every screen of
a live demo, bought for nothing.

Sign in with one of the four accounts `seed_users` printed. Every route under
`/api` requires a bearer token from `POST /api/auth/login`; `/health` does not,
deliberately, because behind a login an outage and a bad password look the same
from outside.

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · PyYAML · SQLite |
| Detection | pandas · numpy · scikit-learn · networkx · rapidfuzz |
| Auth | passlib[bcrypt] · python-jose |
| Frontend | React 18 · Vite · Tailwind · React Router · Recharts · react-leaflet · TanStack Table |
| Tests | pytest — 646 tests |

**SQLite is a deliberate choice, not a shortcut.** 118K raw rows reduce to
~27K work rows with pre-aggregated rollups and fit comfortably in a single file.
Postgres would add a service dependency, a container and a demo failure mode for
no benefit a judge can see. The SQLAlchemy URL stays swappable, so moving to
Postgres is a configuration change and not a rewrite.

Everything runs on localhost. No Docker, no cloud dependency, and **no LLM API
call anywhere in the product** — deliberate, so nothing can fail on venue wifi.

## Declared limitations

Stated proactively, not discovered as gaps. The full list is in
[`PROJECT-BRIEF.md`](PROJECT-BRIEF.md); the ones that most often get overclaimed:

1. **The data is a truncated portal sample**, not the national record.
2. **Memos are templates**, not generated language. Template now, model later.
3. **The certification hop has no public data.** MoSPI publishes no utilisation
   certificate, so it is modelled and tested against a labelled synthetic
   control — which is finding number one in the ablation report.
4. **The delay forecast horizon is illustrative**, trained on a truncated sample.
5. **Login is a demo.** Server-side scoping is real; accounts are seeded, and
   there is no registration, password reset, refresh flow or revocation list.
6. **Escalation queues in-app** and writes an audit event. An SMTP path exists
   and is off unless a mail host is configured; with none configured it composes
   the message, returns it unsent and reports `delivered: false`. The word is
   "queued", never "notified".
7. **A duplicate cluster is a candidate for review, never an accusation.**
   Repeated works — street lights across a constituency, hand pumps across a
   block — are routinely legitimate.
8. **No geospatial precision.** MPLADS publishes no coordinates; maps would join
   at state and district level only and never imply a point-located asset.

## Documentation

| Document | What it is |
| --- | --- |
| [`PROJECT-BRIEF.md`](PROJECT-BRIEF.md) | Scope, features, personas, the scoring table, declared limitations |
| [`CLAUDE.md`](CLAUDE.md) | Conventions, the twelve invariants, the build sequence |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The pipeline and the four-tier boundary, as a diagram |
| [`docs/data/DATA-PROFILE.md`](docs/data/DATA-PROFILE.md) | The authority for every threshold and every claim about the data |
| [`docs/data/INGEST-EXPECTATIONS.md`](docs/data/INGEST-EXPECTATIONS.md) | What a correct ingest run must print, figure by figure |
| [`docs/domain/DOMAIN-MODEL.md`](docs/domain/DOMAIN-MODEL.md) | Ladders, tables, the rulebook, the role-scoping matrix |
| [`docs/contract/case_detail.json`](docs/contract/case_detail.json) | The frozen response shape for one case |
| [`docs/contract/fixtures.md`](docs/contract/fixtures.md) | Three worked cases with full arithmetic |
| [`docs/api/ROLE-SCOPING-PLAN.md`](docs/api/ROLE-SCOPING-PLAN.md) | Endpoint-by-endpoint scoping commitment |
| [`docs/reports/DATA-GAP-RECOMMENDATION.md`](docs/reports/DATA-GAP-RECOMMENDATION.md) | What MoSPI should publish, ranked by unrealised rulebook weight |
| [`docs/design/REDESIGN-SPEC.md`](docs/design/REDESIGN-SPEC.md) | Locked design tokens and UI conventions |

`docs/context/REPO-CONTEXT.md` is a dated snapshot of the **inherited**
LEAKPROOF repository, kept as provenance. It describes what was inherited, not
what NIGRANI is.

## Provenance

NIGRANI inherits its detection-engine architecture from LEAKPROOF, a PDS
diversion prototype by the same team (tag `leakproof-baseline`). The
architecture is kept; the entire domain layer was rebuilt against real MPLADS
data. Where a file still carries PDS vocabulary it is either that snapshot or a
known outstanding item, and `CLAUDE.md`'s repo map says which.

## Team

**ExploreeTinkerBell**
- Nidhi Dhyani — backend, detection engine
- Saumya Singh — frontend, integration
