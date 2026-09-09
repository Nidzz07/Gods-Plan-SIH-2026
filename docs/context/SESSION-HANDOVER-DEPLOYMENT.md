# NIGRANI — Session Handover & Deployment Context

This document captures the complete state, completed tasks, repository configuration, and next steps for continuing NIGRANI deployment in a new Antigravity session.

---

## 1. Project Context & Non-Negotiable Invariants

- **Project**: NIGRANI — Explainable anomaly, fraud, and inefficiency detection for MPLADS (Smart India Hackathon 2026, PS 26102, MoSPI/DIID, Team ExploreeTinkerBell).
- **Target Deployment**:
  - **Backend**: FastAPI on **Render** (Free Web Service tier, 512 MB RAM, ephemeral filesystem).
  - **Frontend**: React 18 + Vite on **Vercel** (Hobby tier).
- **Primary Source of Truth**: [`DEPLOYMENT-PLAN.md`](DEPLOYMENT-PLAN.md) at the repository root.
- **Rules & Voice**: [`CLAUDE.md`](CLAUDE.md), [`README.md`](README.md), and [`AGENTS.md`](AGENTS.md).
- **Core Invariants**:
  1. **No scoring changes**: Weights, thresholds, bands, and rules remain identical.
  2. **Four-tier architecture holds**: Only the rulebook and corroboration bonus score. ML/statistical/graph tiers are zero-point badges.
  3. **Server-side scoping untouched**: Scoping is enforced in SQL queries; District Authority cannot access other districts' data.
  4. **No UI redesign**: Visual design tokens and layout are locked (`REDESIGN-SPEC.md`). The only frontend addition is the cold-start wake affordance in `ServerWakeBanner.jsx`.
  5. **Ephemeral filesystem constraint declared**: Writes on Render Free (notes, escalations, acknowledgements) do not survive instance spin-down; the database resets to the shipped `nigrani.db.gz` artifact on each cold start.
  6. **No autonomous human actions**: Section 8 of `DEPLOYMENT-PLAN.md` (git push, creating cloud services, setting dashboard secrets) is performed by the human operator.

---

## 2. Completed Phases Summary (Phases 1–5)

### Phase 1: Prebuilt Database Artifact
- SQLite database `backend/nigrani.db` was vacuumed (`331.1 MB`) and compressed with gzip (level 9) to **`29.2 MB`** as `backend/nigrani.db.gz`.
- Because `29.2 MB` is well under the 90 MB threshold and GitHub's 100 MB limit, **Path A (plain commit directly in Git)** was executed.
- `.gitignore` rule `*.db` ignores `nigrani.db` while allowing `nigrani.db.gz` to be tracked.
- Created `backend/scripts/__init__.py` and `backend/scripts/restore_db.py`:
  - Decompresses `nigrani.db.gz` via streaming `shutil.copyfileobj` (under 512 MB memory).
  - Skips decompression if `nigrani.db` exists and is newer than the `.gz`.
  - Asserts that `cases` table has non-zero rows (verified: `27,079` cases restored).

### Phase 2: Backend Changes for Render
- **Runtime pin**: Created `backend/.python-version` pinned to `3.11`.
- **Render blueprint**: Created `render.yaml` declaring `nigrani-api` service with build command `pip install -r requirements.txt && python -m scripts.restore_db && python -m app.seed_users` and start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Demo passwords via environment**: Updated `backend/app/seed_users.py` to read `NIGRANI_MINISTRY_PASSWORD`, `NIGRANI_STATE_PASSWORD`, `NIGRANI_DISTRICT_PASSWORD`, and `NIGRANI_MP_PASSWORD`. When set, values are masked in stdout (`[from NIGRANI_*_PASSWORD]`); when unset, random passwords are generated as before. Upsert is idempotent by role.
- **Config via environment**:
  - `backend/app/main.py`: Reads `NIGRANI_CORS_ORIGINS` (comma-separated, defaulting to localhost origins).
  - `backend/app/db.py`: Reads `NIGRANI_DB_PATH` (defaulting to package root `nigrani.db`).
  - `backend/app/auth.py`: Supports `NIGRANI_SECRET_KEY` and `NIGRANI_JWT_SECRET`.
- **Memory & import audit**:
  - Verified no module-level imports of `pandas`, `numpy`, `sklearn`, or `networkx` on `app.main` import.
  - Measured uvicorn resident working set memory at **`4.12 MB`** (comfortably within 512 MB limit).
- **Test suite**: 646 tests passed in `pytest`. (The 1 contract test difference is a pre-existing tie-breaking ordering on `risk_percentile` documented in `CLAUDE.md`).

### Phase 3: Frontend Changes for Vercel
- **SPA Routing**: Created `frontend/vercel.json` rewriting `/(.*)` to `/index.html`.
- **API Base**: Confirmed `frontend/src/api.js` reads `import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'`.
- **Cold-Start Wake Affordance**: Created `frontend/src/components/ServerWakeBanner.jsx` and mounted it in `frontend/src/App.jsx`. Fires unauthenticated `GET /health` on mount; if unresolved after 3s, shows honest notice: *"Waking the server. Free hosting sleeps when idle; this takes up to a minute."* Retries with backoff up to 90s. When backend wakes, clears automatically without page refresh.
- **Build verification**: `npm run build` in `frontend/` succeeds in 3.23s, generating `dist/`.

### Phase 4: Documentation & Agent Rules
- **`README.md`**: Added deployed URL placeholders, demo credentials table with fixed password documentation, amended limitation 5, added limitation 9 (ephemeral filesystem), and added deployment architecture and `nigrani.db.gz` regeneration instructions.
- **`CLAUDE.md`**: Updated repo map with deployment files and added regeneration invariant.
- **`AGENTS.md`**: Created at repo root with core invariants and database artifact rules.

---

## 3. Working Tree & File Status

### Files Modified:
- `README.md`
- `CLAUDE.md`
- `backend/app/main.py`
- `backend/app/db.py`
- `backend/app/auth.py`
- `backend/app/seed_users.py`
- `frontend/src/App.jsx`

### Files Created:
- `render.yaml`
- `AGENTS.md`
- `backend/.python-version`
- `backend/nigrani.db.gz`
- `backend/scripts/__init__.py`
- `backend/scripts/restore_db.py`
- `frontend/vercel.json`
- `frontend/src/components/ServerWakeBanner.jsx`

### Untracked / Ignored Files to Note:
- `backend/nigrani.db` — Gitignored by `*.db` (correct).
- `backend/nigrani.db.gz` — Untracked, ready to stage and commit.
- `.env` and `.env.local` — Gitignored (no secrets tracked).

---

## 4. Immediate Next Steps (Section 8 of DEPLOYMENT-PLAN.md)

These steps are performed by the human operator:

### Step 8.1: Commit and Push
In PowerShell from the repository root:
```powershell
git add -A
git commit -m "Deployment: Render backend, Vercel frontend, shipped database artifact"
git push origin main
```
*Verify on GitHub that `backend/nigrani.db.gz` is present and that no `.env` or `nigrani.db` was committed.*

### Step 8.2: Deploy Backend on Render
1. Go to **render.com** → **New +** → **Web Service** → Connect `Nidzz07/Gods-Plan-SIH-2026`.
2. Render detects `render.yaml`:
   - Root Directory: `backend`
   - Plan: `Free`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt && python -m scripts.restore_db && python -m app.seed_users`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/health`
3. In **Environment Variables**, set:
   - `PYTHON_VERSION`: `3.11`
   - `NIGRANI_SECRET_KEY`: click Generate
   - Choose 4 passwords and record them:
     - `NIGRANI_MINISTRY_PASSWORD`: `<your-ministry-password>`
     - `NIGRANI_STATE_PASSWORD`: `<your-state-password>`
     - `NIGRANI_DISTRICT_PASSWORD`: `<your-district-password>`
     - `NIGRANI_MP_PASSWORD`: `<your-mp-password>`
   - `NIGRANI_CORS_ORIGINS`: leave blank for now.
4. Click **Deploy**. After deployment completes, copy service URL (e.g., `https://nigrani-api.onrender.com`).
5. Open `<render-url>/health` in browser; verify it returns `status: "ok"` and `cases: 27079`.

### Step 8.3: Deploy Frontend on Vercel
1. Go to **vercel.com** → **Add New…** → **Project** → Import `Nidzz07/Gods-Plan-SIH-2026`.
2. Settings:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
   - **Node.js**: `22.x`
3. In **Environment Variables**:
   - `VITE_API_BASE`: `<your-render-url>` (e.g., `https://nigrani-api.onrender.com` with NO trailing slash).
4. Deploy and copy the Vercel URL (e.g., `https://nigrani.vercel.app`).

### Step 8.4: Close the CORS Loop
1. In Render Dashboard → `nigrani-api` → **Environment**.
2. Set `NIGRANI_CORS_ORIGINS`: `<your-vercel-url>` (e.g., `https://nigrani.vercel.app`).
3. Save changes (Render redeploys).

### Step 8.5: Smoke Test & Update Placeholders
1. Open Vercel URL in an Incognito window.
2. Verify cold-start wake banner if server is asleep.
3. Test login with all 4 personas using the passwords set in Render.
4. Verify scoping (editing URL to another district is refused).
5. **Back to Antigravity**: Give the new session the live URLs and passwords to fill in the placeholders in `README.md`.


prompt:
I am continuing work on NIGRANI, an MPLADS fund-oversight system for SIH 2026 (PS 26102, MoSPI/DIID, Team ExploreeTinkerBell).

Please read the following files in order before doing anything:
1. `SESSION-HANDOVER-DEPLOYMENT.md` at the repo root (contains full handover context of what was completed).
2. `DEPLOYMENT-PLAN.md` (source of truth for deployment).
3. `CLAUDE.md` and `AGENTS.md` (project invariants and conventions).

Current state:
- Phases 1 through 5 of `DEPLOYMENT-PLAN.md` have been implemented and verified locally.
- `backend/nigrani.db.gz` (~29.2 MB) is created and ready to be committed alongside `render.yaml`, `backend/scripts/restore_db.py`, `backend/.python-version`, `frontend/vercel.json`, and `frontend/src/components/ServerWakeBanner.jsx`.
- Local test suite has 646 passing tests.

Constraints to observe:
- Section 8 is human-driven: do not push, do not open Render or Vercel, and do not create cloud services autonomously.
- No UI redesign. The only frontend change is the existing cold-start affordance in `ServerWakeBanner.jsx`.
- Invariant 1 holds: no scoring, detection, or role-scoping logic may be altered.
- No passwords, secrets, or tokens in any artifact or log.

Check `git status` to verify the working tree, review the handover document, and confirm your understanding of the current state and next steps.
