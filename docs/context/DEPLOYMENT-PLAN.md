# NIGRANI — Deployment Plan

**Target:** backend on Render (Free web service), frontend on Vercel (Hobby).
**Repo:** `https://github.com/Nidzz07/Gods-Plan-SIH-2026`
**Audience:** the Antigravity agent. This file is the source of truth for the
implementation plan. Steps marked **[HUMAN]** are done by Nidhi in a browser and
must not be attempted by the agent.

---

## 0. How to run this plan in Antigravity

### 0.1 Mode discipline

- **PLANNING.** Read this file end to end, then read the repo before writing
  anything. Produce `implementation_plan.md` derived from Phases 1–4 below, with
  the actual file paths you found — not a restatement of this document. List the
  files you will create and the files you will modify, one line each. Stop and
  wait for Proceed.
- **EXECUTION.** One phase per task boundary. Do not start Phase 3 before
  Phase 2's checks in section 6 pass. If a step turns out to require changing
  detection or scoring logic, return to PLANNING and ask — do not improvise.
- **VERIFICATION.** Section 6 is the evidence list. Run it, capture output, and
  write `walkthrough.md`. Every checkbox you tick must have a command output or
  screenshot behind it in the artifact.

### 0.2 Command approval policy

Annotate with `// turbo` **only** these, which are read-only or trivially
reversible:

- `pytest`, `git status`, `git check-ignore`, `git ls-files`, `git diff`
- `python -c "import ..."` probes, `pip show`, memory measurement
- `npm run build`, `npm run dev`

**Never `// turbo`, always ask first:**

- Anything that writes to or rewrites `backend/nigrani.db` (Step 1.1's `VACUUM`)
- `git add`, `git commit`, `git push` — Nidhi pushes, in section 7
- Anything touching Render or Vercel

### 0.3 Environment

Windows, PowerShell, repo at `C:\Users\NIDHI\Desktop\Gods-Plan-SIH-2026`.
Backend commands run from `backend\`, frontend from `frontend\`. Use PowerShell
syntax — `;` not `&&`, `$env:VAR="x"` not `VAR=x`.

### 0.4 Knowledge and artifacts

Do not write any password, JWT secret or token into `implementation_plan.md`,
`walkthrough.md`, a Knowledge Item, or a screenshot. Refer to them by variable
name. Screenshots of a logged-in dashboard are fine; screenshots of an env var
panel are not.

---

## 1. Non-negotiable invariants

Deployment must not change what the product computes. Before declaring done, all
of the following must still hold:

1. **No scoring change.** No rule weight, threshold, severity band or cap is
   touched. `pytest` must pass with the same count (646) unless tests are added.
2. **The four-tier boundary holds.** Tier 3 and Tier 4 still contribute zero
   points. The import-walking tests that enforce this must still pass.
3. **Server-side scoping is untouched.** No CORS or auth change may widen what a
   role can read. The URL-editing scoping tests must still pass.
4. **`/health` stays unauthenticated** and still reports `awaiting_build` when
   the database has zero cases.
5. **No secret is committed.** No password, JWT secret or token appears in any
   tracked file. `.env` and `.env.local` stay gitignored.
6. **Local development keeps working unchanged.** Every default must be the
   current local behaviour, so `uvicorn app.main:app --reload --port 8000` and
   `npm run dev` behave exactly as `README.md` describes today.
7. **No redesign.** Antigravity's default pull toward premium, animated,
   glassmorphic UI is overridden here. This is a government-oversight dashboard
   with an established visual language. Change no component, no colour, no font,
   no spacing, except the single cold-start affordance specified in 4.3, which
   must match the surrounding style. If you find yourself "improving" a screen,
   stop.
8. **No autonomous deployment.** You do not create Render or Vercel services, do
   not push to `main`, and do not open a PR unless asked. Your output is a
   working tree plus a walkthrough.

Deployment is additive configuration. If a step here appears to require changing
detection logic, stop and ask.

---

## 2. Context you need

- Backend: Python 3.11, FastAPI, SQLAlchemy 2.x, SQLite single file
  `backend/nigrani.db`.
- Frontend: React 18 + Vite, builds to `frontend/dist`, Node 22.11.0 (`.nvmrc`).
- `data/raw/` (twelve MPLADS CSVs) is committed on purpose.
- `backend/nigrani.db` is **335.8 MB** and currently gitignored by the `*.db`
  rule. It is already built and correct.

Read `CLAUDE.md` and `README.md` before planning. They carry the project's
declared limitations and its voice; both matter in Phase 4.

### The constraint that shapes everything

Render's Free tier gives **512 MB RAM and 0.1 CPU**, and its filesystem is
**ephemeral** — free services cannot attach a persistent disk. Two consequences:

- **We do not rebuild the database on Render.** Running `ingest.run` → `ml.run` →
  `ablation.run` → `derive_all` means pandas over 118,704 rows plus an
  IsolationForest fit inside 512 MB. It will likely OOM, and every cold start
  would re-run it. We ship the prebuilt database instead.
- **Runtime writes do not survive a spin-down.** Notes, escalations, alert
  acknowledgements and audit events written during a demo are lost when the free
  instance sleeps (15 minutes idle) and the image is restored. The database
  resets to its shipped state on every cold start. This is acceptable for a demo
  and must be **declared honestly in the README**, in the same voice as the
  existing "Declared limitations" section — not hidden.

---

## 3. Phase 1 — Get the database into the repo

335.8 MB exceeds GitHub's hard 100 MB per-file limit. Git LFS is possible but
GitHub's free LFS tier is only 1 GB storage and **1 GB bandwidth per month** —
at 335.8 MB per clone that is roughly three Render deploys before LFS is
exhausted. So try compression first; it is very likely sufficient, because a
SQLite file of derived rows with repeated text compresses hard.

### Step 1.1 — Vacuum and compress, then report the size

**Ask before running.** `VACUUM` rewrites the database in place. Copy
`nigrani.db` to `nigrani.db.bak` first and say so in chat, so a failure mid-write
is recoverable.

```powershell
cd backend
Copy-Item nigrani.db nigrani.db.bak
python -c "import sqlite3; c=sqlite3.connect('nigrani.db'); c.execute('VACUUM'); c.close()"
python -c "import gzip,shutil; shutil.copyfileobj(open('nigrani.db','rb'), gzip.open('nigrani.db.gz','wb',compresslevel=9))"
Get-ChildItem nigrani.db, nigrani.db.gz | Select-Object Name, @{n='MB';e={[math]::Round($_.Length/1MB,1)}}
```

Report the printed size in chat, then branch:

- **≤ 90 MB** → **Path A** (plain commit). Expected outcome.
- **> 90 MB** → stop, tell Nidhi, and wait. **Path B** (Git LFS) needs a one-time
  human `git lfs install` and carries the bandwidth ceiling above. Do not pick
  Path B on your own.

Delete `nigrani.db.bak` only after Step 6's row-count check passes.

### Path A — commit the compressed database directly

`.gitignore` currently has `*.db`, which does **not** match `nigrani.db.gz`, so no
gitignore change is needed. Verify rather than assume:

```bash
git check-ignore -v backend/nigrani.db.gz   # must print nothing
```

Then create `backend/scripts/restore_db.py`:

- Decompresses `backend/nigrani.db.gz` → `backend/nigrani.db`.
- Streams via `gzip.open` + `shutil.copyfileobj` (never `.read()` the whole file
  — 512 MB ceiling).
- Skips work if `nigrani.db` already exists and is newer than the `.gz`, so local
  developers never clobber a database they just rebuilt.
- Prints the restored row count from `cases` and exits non-zero if it is zero,
  so a corrupt artifact fails the Render build loudly instead of serving an
  empty dashboard.

### Path B — Git LFS (only after Nidhi confirms)

- **[HUMAN]** `git lfs install` once.
- Add `.gitattributes` at repo root: `backend/nigrani.db.gz filter=lfs diff=lfs merge=lfs -text`
- Everything else is identical to Path A.

---

## 4. Phase 2 — Backend changes for Render

All defaults must preserve current local behaviour.

### 4.1 Fixed demo passwords

`backend/app/seed_users.py` currently generates random passwords and prints them
once. Change it to:

- Read each role's password from an environment variable:
  `NIGRANI_MINISTRY_PASSWORD`, `NIGRANI_STATE_PASSWORD`,
  `NIGRANI_DISTRICT_PASSWORD`, `NIGRANI_MP_PASSWORD`.
- If a variable is unset, fall back to the existing random-generate-and-print
  behaviour, so nothing changes for a local developer who has set nothing.
- Make it **idempotent as an upsert**: re-running against a database that already
  has the four accounts must update the password hash and scope rather than
  raising on a unique constraint. This matters because Render re-runs it on every
  build.
- Never log the password value when it came from an environment variable — log
  only which variable supplied it.

### 4.2 Configuration via environment

Audit `backend/app/` for hardcoded values and route each through an env var with
the current value as the default. Use `codebase_search` for the hardcoded strings
rather than assuming this table is complete; report anything you find that is not
listed here.

| Variable | Default (must equal today's behaviour) | Purpose |
| --- | --- | --- |
| `NIGRANI_SECRET_KEY` | current default | JWT signing. Render supplies a real one. |
| `NIGRANI_DB_PATH` | `backend/nigrani.db` resolved from the package root | Must not depend on the current working directory. |
| `NIGRANI_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated. Render adds the Vercel origin. |
| `PORT` | `8000` | Render assigns this; the start command must bind it. |

The CORS change must **add** the Vercel origin to the allow-list, not replace the
allow-list with `*`. Credentials are carried by bearer token, so a wildcard is
both unnecessary and a widening of surface area — see invariant 3.

### 4.3 Keep the API process light

512 MB is the whole container. Audit the import graph reachable from
`app.main` and confirm that **pandas, numpy, scikit-learn and networkx are not
imported at module import time**. They are build-time dependencies; the ML
findings are precomputed rows in `ml_findings`. If any of them is pulled in at
startup, move it behind a lazy import inside the function that needs it. Report
the measured before/after resident memory of the started process, with the
command you used to measure it.

If a runtime code path genuinely needs scikit-learn (e.g. recompute), say so
rather than silently lazy-loading something that will then OOM on first use.

### 4.4 Runtime pins

- Add `backend/.python-version` containing `3.11`.
- In `backend/requirements.txt`, pin `bcrypt` to a version compatible with the
  pinned `passlib` (passlib 1.7.4 breaks against bcrypt ≥ 4.1 with
  `AttributeError: module 'bcrypt' has no attribute '__about__'`). Verify the
  pin by importing and hashing, not by reading version numbers.
- Confirm every dependency in `requirements.txt` has a pinned version. An
  unpinned transitive resolve on Render is how a build that worked yesterday
  fails on demo day.

### 4.5 Render service definition

Add `render.yaml` at repo root so the service is reproducible:

```yaml
services:
  - type: web
    name: nigrani-api
    runtime: python
    plan: free
    rootDir: backend
    buildCommand: "pip install -r requirements.txt && python -m scripts.restore_db && python -m app.seed_users"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: NIGRANI_SECRET_KEY
        generateValue: true
      - key: NIGRANI_CORS_ORIGINS
        sync: false
      - key: NIGRANI_MINISTRY_PASSWORD
        sync: false
      - key: NIGRANI_STATE_PASSWORD
        sync: false
      - key: NIGRANI_DISTRICT_PASSWORD
        sync: false
      - key: NIGRANI_MP_PASSWORD
        sync: false
```

`sync: false` means "set this in the dashboard, do not read it from the repo" —
that is what keeps the passwords out of git.

Note that `restore_db` and `seed_users` run in **build**, not start. Build output
is baked into the image, so the database and the four accounts are present on
every spin-up without re-running anything.

---

## 5. Phase 3 — Frontend changes for Vercel

### 5.1 SPA routing

React Router needs every path served `index.html`, or a judge who refreshes on
`/cases/1234` gets a 404. Add `frontend/vercel.json`:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### 5.2 API base

`src/api.js` keeps its `http://localhost:8000` default — do not change it, the
README explains why that default is deliberate. Vercel supplies `VITE_API_BASE`
as a build-time environment variable pointing at the Render URL. Confirm the
existing code already reads `import.meta.env.VITE_API_BASE`; if it does not,
add that read with the current default preserved.

### 5.3 Cold-start handling — do not skip this

The free Render instance sleeps after 15 minutes and takes **roughly 50–60
seconds** to wake. Right now, the first login after a quiet period will look
like a broken site: a spinner, then a network error.

Add a first-request wake affordance:

- On app mount, fire `GET /health` (unauthenticated, which is why it exists).
- If it does not resolve within ~3 seconds, show an honest message — *"Waking the
  server. Free hosting sleeps when idle; this takes up to a minute."* — and retry
  with backoff for up to 90 seconds.
- Only surface a real error after the retry window expires.

This is a demo-day correctness issue, not polish. Write it in the project's
existing voice and existing component style — plain, no animation, no new design
system. State the constraint plainly rather than pretending it is loading fast.
See invariant 7.

**Verify this with the browser subagent, not by reading the code.** Start the
frontend, stop the backend, load the app, and capture: the wake message
appearing, the retry continuing, and — with the backend restarted — the app
recovering without a manual refresh. Attach the screenshots or recording to the
walkthrough. This is the one part of the plan you can actually prove works before
deployment, so prove it.

---

## 6. Phase 4 — Documentation

Update `README.md`:

1. **Deployed URLs** near the top — leave a clearly marked placeholder, since the
   URLs do not exist until Nidhi finishes section 8.
2. **A "Demo credentials" section** listing the four role logins. Put placeholders
   for the password values, not invented ones; Nidhi fills them in after she picks
   them in 8.2. These are deliberately public — a judge must be able to log in
   from the README. The passwords stay out of *git history* via env vars, but they
   are published here on purpose. Say that explicitly so a reader does not think
   it is a leak.
3. **Amend limitation 5** ("Login is a demo") to add that the deployment's demo
   accounts use fixed published passwords.
4. **Add a new declared limitation** for the ephemeral filesystem: notes,
   escalations, acknowledgements and audit events written on the deployed
   instance are lost when the free instance spins down, and the database resets
   to its shipped state. Local runs persist normally. Write it in the same
   unflinching register as the existing eight.
5. **A "Deployment" section** covering the two-service split, the shipped
   `nigrani.db.gz` artifact and how to regenerate it, and the fact that the
   Render build does **not** run the five-step pipeline.

Update `CLAUDE.md`: add the deployment artifacts to the repo map and record the
rule that `nigrani.db.gz` must be regenerated and re-committed whenever the
rulebook, ingest or derivation changes — otherwise the deployed site silently
serves scores derived under an older rulebook, which would violate the project's
own reproducibility claim.

**Also create or update `AGENTS.md` at repo root** with the same rule, so future
Antigravity sessions inherit it without being told. Keep it short — a repo map
pointer, invariants 1–4 and 7 in one line each, and the `nigrani.db.gz`
regeneration rule. Do not duplicate `CLAUDE.md` wholesale into it.

---

## 7. Phase 5 — Verification before handing back

Run and report, do not assume. Each line needs evidence in `walkthrough.md`.

- [ ] `pytest -v` passes locally, same count as before. Paste the summary line.
- [ ] With no env vars set, `python -m app.seed_users` still generates and prints
      random passwords (local behaviour preserved).
- [ ] With env vars set, it uses them, and running it twice does not error.
      Redact the values in the transcript.
- [ ] `python -m scripts.restore_db` on a clean checkout produces a
      `nigrani.db` whose `cases` count matches the local original exactly. State
      both numbers.
- [ ] `git check-ignore -v` confirms no `.env` and no `.db` is tracked.
- [ ] `git ls-files | Select-String -Pattern "password|secret|\.env"` returns
      nothing unexpected.
- [ ] `git status` shows `nigrani.db.gz` staged-or-untracked and `nigrani.db`
      still ignored.
- [ ] The started API process resident memory is reported, with a judgement on
      whether it fits 512 MB alongside SQLite page cache.
- [ ] `npm run build` in `frontend/` succeeds and `dist/` is produced.
- [ ] Browser evidence for 5.3: wake message, retry, recovery.

`walkthrough.md` must end with: the compressed database size and which path you
took, the measured startup memory, any dependency you had to pin and why, and
anything in sections 1–7 you could not do. Do not tick a box you have not run.

---

## 8. [HUMAN] Deployment steps — agent stops here

Everything below is Nidhi's, done in a browser after the agent's work is reviewed
and pushed. The agent does not perform, simulate, or "helpfully get started on"
any of it.

### 8.1 Push

```powershell
cd C:\Users\NIDHI\Desktop\Gods-Plan-SIH-2026
git add -A
git commit -m "Deployment: Render backend, Vercel frontend, shipped database artifact"
git push origin main
```

Confirm on GitHub that `backend/nigrani.db.gz` is present and that **no** `.env`
file was pushed.

### 8.2 Render — backend

1. render.com → sign in with GitHub → **New** → **Web Service**.
2. Connect `Nidzz07/Gods-Plan-SIH-2026`. Render should detect `render.yaml`; if
   it does not, set Root Directory `backend`, and copy the build and start
   commands from section 4.5 by hand.
3. Instance type: **Free**.
4. **Environment** tab — add the five values left as `sync: false`:
   - `NIGRANI_MINISTRY_PASSWORD`, `NIGRANI_STATE_PASSWORD`,
     `NIGRANI_DISTRICT_PASSWORD`, `NIGRANI_MP_PASSWORD` — pick four fixed
     passwords now and write them down; they go into the README placeholders.
   - `NIGRANI_CORS_ORIGINS` — leave blank for now, you do not have the Vercel URL
     yet. You will come back in 8.4.
5. Deploy. Watch the log: it should install, restore the database, print a
   non-zero case count, seed four users, then start uvicorn.
6. Copy the service URL, e.g. `https://nigrani-api.onrender.com`. Open
   `<url>/health` — it must return `ok`, not `awaiting_build`. If it says
   `awaiting_build`, the database restore failed; read the build log rather than
   redeploying blindly.

### 8.3 Vercel — frontend

1. vercel.com → sign in with GitHub → **Add New** → **Project** → import the same repo.
2. **Root Directory**: `frontend`. Framework preset: Vite. Build `npm run build`,
   output `dist`. Node version: 22.x.
3. **Environment Variables**: `VITE_API_BASE` = your Render URL from 8.2, with no
   trailing slash.
4. Deploy. Copy the resulting URL, e.g. `https://nigrani.vercel.app`.

### 8.4 Close the CORS loop

Back in Render → Environment → set `NIGRANI_CORS_ORIGINS` to your Vercel URL
(comma-separate if you also want a preview domain). Save; Render redeploys.

Until you do this, the frontend loads but every API call fails with a CORS error
in the browser console. This is the single most common place this deployment
gets stuck.

### 8.5 Smoke test

Open the Vercel URL in a private window. Log in as each of the four roles. Check
that scoping still holds by editing a district ID in the URL as a District
Authority — it must refuse.

### 8.6 Optional — stay awake for judging

On demo day, set a free monitor (cron-job.org or UptimeRobot) to hit
`<render-url>/health` every 10 minutes. That keeps the instance warm so judges
never see the wake screen. Render grants 750 free instance hours per calendar
month and an always-on service uses about 730, so run the pinger for the judging
window rather than permanently, or you will exhaust the month's hours.

### 8.7 Back to the agent, afterwards

Once the URLs exist and the passwords are chosen, start a **new** Antigravity
session and ask it to fill in the placeholders from section 6 items 1 and 2. That
is a two-file edit, not a re-plan.
