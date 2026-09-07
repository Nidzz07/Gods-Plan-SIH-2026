# NIGRANI — Project Continuation Handover

> **Purpose**: Everything a new AI agent needs to continue work on the NIGRANI
> frontend without re-discovering the codebase from scratch.

---

## 1. What is NIGRANI?

NIGRANI detects anomalies, fraud, and inefficiency in **MPLADS** (Members of
Parliament Local Area Development Scheme). It explains every flag in language an
officer can act on and an auditor can re-derive months later.

- **Competition**: Smart India Hackathon 2026, Problem Statement PS 26102, MoSPI / DIID
- **Team**: ExploreeTinkerBell (two developers, hard deadline)
- **Heritage**: Detection-engine architecture inherited from LEAKPROOF (PDS diversion prototype)

---

## 2. Technology Stack (Fixed — Do Not Substitute)

| Layer    | Stack |
|----------|-------|
| Backend  | Python 3.11 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · PyYAML · SQLite · pytest · pandas · numpy · scikit-learn · networkx · rapidfuzz · passlib[bcrypt] · python-jose |
| Frontend | React 18 · Vite 5 · Tailwind CSS 3.4 · React Router 6 · Recharts 2 · react-leaflet · TanStack Table 8 · i18next 26 · react-i18next 17 |
| Node     | Pinned to 22.11.0 (`.nvmrc` at repo root) |
| Fonts    | `@fontsource/fraunces`, `@fontsource/inter`, `@fontsource/noto-sans-devanagari`, `@fontsource/noto-sans-gujarati`, `@fontsource/source-serif-4` |

**Explicitly banned**: Postgres, Supabase, Docker, Redis, Celery, any ORM other than SQLAlchemy, any client state library, any component library, any LLM API call.

---

## 3. Repo Structure

```
Gods-Plan-SIH-2026/
├── CLAUDE.md                          # Master project instructions (READ FIRST)
├── NIGRANI-FRONTEND-PLAN.md           # Implementation spec #1 (frontend presentation layer)
├── NIGRANI-I18N-AND-LAYOUT-PLAN.md    # Implementation spec #2 (i18n + layout overhaul)
├── PROJECT-BRIEF.md                   # Features, personas, scope
├── README.md
├── .nvmrc                             # Node 22.11.0
│
├── backend/                           # ⚠ DO NOT MODIFY — EVER
│   ├── app/
│   │   ├── main.py                    # FastAPI app, CORS to :5173
│   │   ├── db.py                      # SQLAlchemy engine, SessionLocal, Base
│   │   ├── models.py                  # SQLAlchemy tables
│   │   ├── schemas.py                 # Pydantic response shapes
│   │   ├── constants.py               # Shared literals
│   │   ├── rules.yaml                 # F2 rulebook (loaded at runtime)
│   │   ├── auth.py                    # JWT auth, role guards
│   │   ├── notify.py                  # Escalation delivery (DRY RUN)
│   │   └── routers/                   # API endpoints
│   └── tests/                         # 645 passing tests
│
├── data/                              # Real MPLADS data from mplads.mospi.gov.in
│   └── raw/
│
├── docs/
│   ├── data/DATA-PROFILE.md           # Authority for thresholds & data claims
│   ├── domain/DOMAIN-MODEL.md         # Ladders, tables, rulebook
│   └── contract/case_detail.json      # API response shape reference
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js             # Heavily customized tokens
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.jsx                   # Entry point (font imports, i18n init)
        ├── App.jsx                    # React Router routes
        ├── index.css                  # Global styles, fluid typography, Indic line-height
        ├── api.js                     # All backend API calls
        ├── auth.jsx                   # Auth context, JWT handling
        ├── roles.js                   # Navigation structure per role
        ├── severity.js                # Score/severity logic & helpers
        ├── ui.js                      # Shared UI utility classes/functions
        ├── chart.js                   # Recharts config
        │
        ├── data/
        │   └── corpus-facts.js        # CORPUS constants (§12 of NIGRANI-FRONTEND-PLAN)
        │
        ├── i18n/
        │   ├── index.js               # i18next initialization
        │   ├── useLanguage.js          # React hook for language switching
        │   ├── format.js              # Localized number/currency/date formatters
        │   ├── LanguageSwitcher.jsx    # Compact (dropdown) & prominent (pill row) variants
        │   └── locales/
        │       ├── en.json            # English (source of truth)
        │       ├── hi.json            # Hindi
        │       ├── mr.json            # Marathi
        │       └── gu.json            # Gujarati
        │
        ├── hooks/                     # Custom React hooks
        │
        ├── components/
        │   ├── Layout.jsx             # Authenticated dashboard shell (.app-shell + .rail)
        │   ├── Sidebar.jsx            # 288px fixed rail, 3-section flex
        │   ├── TopBar.jsx             # Interior dashboard top bar
        │   ├── UtilityStrip.jsx       # 36px top bar (accessibility + language switcher)
        │   ├── Masthead.jsx           # 88px public masthead with sticky collapse
        │   ├── Footer.jsx             # 3-tier footer (standards, sitemap, colophon)
        │   ├── HeroCarousel.jsx       # Landing filmstrip carousel
        │   ├── PageHero.jsx           # Interior page hero (breadcrumb + title + lede)
        │   ├── PageHeader.jsx         # Legacy page header
        │   ├── PageMotif.jsx          # SVG motif overlays
        │   ├── PreviewList.jsx        # Vertical list with preview panel
        │   ├── Ladder.jsx             # Fund & Lifecycle ladder visualization
        │   ├── ScopedTable.jsx        # Configurable data table
        │   ├── CaseRows.jsx           # Case list row component
        │   ├── CaseActions.jsx        # Case action buttons
        │   ├── TraceTable.jsx         # Reasoning trace display
        │   ├── DuplicateCompareModal.jsx  # Side-by-side duplicate comparison
        │   ├── ZeroPointBadges.jsx    # "+0" badge indicators
        │   ├── StatPair.jsx           # Stat display component
        │   ├── RankedBar.jsx          # Ranked bar chart
        │   ├── SectionHeading.jsx     # Section heading component
        │   ├── Figure.jsx             # Figure wrapper
        │   ├── Tag.jsx                # Tag/chip component
        │   ├── Skeleton.jsx           # Loading skeleton
        │   ├── EmptyState.jsx         # Empty state display
        │   └── Logo.jsx              # NIGRANI logo
        │
        ├── pages/
        │   ├── Landing.jsx            # Public landing (10 sections, §6)
        │   ├── SignIn.jsx             # Authentication page
        │   ├── Ministry.jsx           # Ministry national overview dashboard
        │   ├── StateNodal.jsx         # State overview (/state & /state/:state)
        │   ├── District.jsx           # District working queue (/district & /district/:state/:district)
        │   ├── Member.jsx             # MP member account overview
        │   ├── CaseDetail.jsx         # Universal case sheet
        │   ├── Rulebook.jsx           # Rulebook viewer/editor
        │   ├── Alerts.jsx             # Alert management
        │   ├── DataGapReport.jsx      # /reports/data-gap
        │   ├── SearchPage.jsx         # /search
        │   ├── StaticDocPage.jsx      # /docs/:docId & /audit/:caseId
        │   └── NotFound.jsx           # 404
        │
        └── assets/
            └── IMAGE-CREDITS.md       # Media attribution records
```

---

## 4. Routing Table

| Path | Component | Auth Required | Description |
|------|-----------|--------------|-------------|
| `/` | Landing | No | Public landing page (10 sections) |
| `/sign-in` | SignIn | No | Login page |
| `/reports/data-gap` | DataGapReport | No | Public data gap report |
| `/docs/:docId` | StaticDocPage | No | Public documentation pages |
| `/audit/:caseId` | StaticDocPage | No | Public audit trail pages |
| `/ministry` | Ministry | Yes (ministry) | National overview dashboard |
| `/state` | StateNodal | Yes (state) | State overview |
| `/state/:state` | StateNodal | Yes (state) | State comparison |
| `/district` | District | Yes (district) | District working queue |
| `/district/:state/:district` | District | Yes (district) | Specific district view |
| `/member` | Member | Yes (member) | MP account overview |
| `/cases/:caseId` | CaseDetail | Yes (all roles) | Universal case sheet |
| `/rulebook` | Rulebook | Yes (all roles) | Rulebook viewer |
| `/alerts` | Alerts | Yes (all roles) | Alert management |
| `/search` | SearchPage | Yes (all roles) | Record search |

---

## 5. Four Authenticated Roles

| Role | Dashboard | Scope |
|------|-----------|-------|
| `ministry` | `/ministry` | National — sees all states |
| `state` | `/state` | One state — sees all districts within |
| `district` | `/district` | One district — working queue of cases |
| `member` | `/member` | One MP — read-only account view |

Roles are defined in `frontend/src/roles.js`. Navigation items are scoped per role. Unreachable items are **omitted**, not disabled.

---

## 6. Key Architecture Decisions

### i18n (Multilingual)
- **Languages**: English (`en`), Hindi (`hi`), Marathi (`mr`), Gujarati (`gu`)
- **Framework**: i18next + react-i18next
- **Storage**: `localStorage` key `nigrani.lang`
- **HTML sync**: `<html lang="...">` updated on language change
- **Fonts**: Noto Sans Devanagari (hi/mr), Noto Sans Gujarati (gu)
- **Critical rule**: `line-height: 1.65` on `body` for Indic scripts (prevents matra clipping)
- **Number system**: `numberingSystem: 'latn'` enforced — Latin digits in ALL languages
- **Never translate**: proper names, state/district/MP/agency names, work IDs, case IDs, crypto hashes

### Layout
- **Public pages**: `UtilityStrip` (36px) → `Masthead` (88px, collapses to 60px) → content → `Footer`
- **Authenticated pages**: `.app-shell` CSS grid with `.rail` (288px sidebar) + `.app-main` content area
- **Width**: No artificial `max-w` caps. Content flows up to 1920px.
- **Sidebar**: 3-section flex column (fixed head, scrollable nav, pinned footer)

### Formatting Helpers (`src/i18n/format.js`)
- `formatRulebookVersion(v)` — strips double-v prefix, always outputs `v1.0.0`
- `formatNumber(n, lang)` / `formatCurrency(n, lang)` / `formatDate(d, lang)` — locale-aware with Latin digits

### Severity System (`src/severity.js`)
- Centralized score-to-severity mapping
- Used across all dashboards for consistent color coding

---

## 7. Implementation Plans (Specifications)

Two implementation plans were provided and **fully implemented**:

### Plan 1: `NIGRANI-FRONTEND-PLAN.md` (50,981 bytes)
- Complete frontend presentation layer
- 10-section landing page, 4 dashboard overhauls, case sheet, rulebook, alerts
- CORPUS constants, typography tokens, color system
- Components: PreviewList, PageHero, Masthead, Footer, etc.

### Plan 2: `NIGRANI-I18N-AND-LAYOUT-PLAN.md` (36,479 bytes)
- Multilingual architecture (en/hi/mr/gu)
- Landing page hero carousel overhaul
- Dashboard layout standardization (.app-shell/.rail)
- Defect fixes (double-v, pluralization, sidebar clipping)
- Fluid typography, Indic font support

**Both plans are fully implemented.** The codebase is current with all specifications.

---

## 8. Build & Test Status

### Frontend Build ✅
```
npm run build → ✓ built in 2.56s
dist/assets/index-Bp5wwvI5.css    59.19 kB
dist/assets/index-BDmPPvdK.js   842.02 kB
0 errors
```

### Backend Tests ✅
```
pytest → 645 passed, 466 warnings in 78.43s
0 errors, 0 failures
```

### Git Status
- **Latest commit**: `437ed4e Add UI Refinement`
- **Working tree**: Clean (no uncommitted changes)
- All changes are committed.

---

## 9. Setup Instructions for New Environment

```bash
# 1. Navigate to project root
cd Gods-Plan-SIH-2026

# 2. Frontend setup
cd frontend
npm install
npm run dev          # → http://localhost:5173

# 3. Backend setup (separate terminal)
cd backend
pip install -r requirements.txt   # or use existing .venv
uvicorn app.main:app --reload     # → http://localhost:8000

# 4. Verify
npm run build        # Frontend build check
pytest               # Backend test suite (645 tests)
```

---

## 10. Critical Rules for Any Future Agent

1. **NEVER modify anything inside `backend/`.**
2. Do not add, remove, or modify backend API endpoints.
3. Do not change API response structures.
4. Do not invent numbers, statistics, data, or API responses.
5. Do not create mock data to compensate for missing API data.
6. Use the existing frontend API/data flow (`src/api.js`).
7. Preserve all existing working functionality.
8. Reuse existing components where appropriate.
9. Before changing code, **read `CLAUDE.md` first** — it is the master instruction file.
10. Then read `docs/data/DATA-PROFILE.md`, `docs/domain/DOMAIN-MODEL.md`, and `PROJECT-BRIEF.md` in that order.

---

## 11. Key Files to Read Before Making Changes

**In priority order:**
1. `CLAUDE.md` — Master project rules, stack constraints, invariants
2. `frontend/src/api.js` — All API calls and response handling
3. `frontend/src/roles.js` — Role-scoped navigation
4. `frontend/src/severity.js` — Score/severity logic
5. `frontend/src/ui.js` — Shared UI utilities
6. `frontend/tailwind.config.js` — Custom design tokens
7. `frontend/src/index.css` — Global styles, fluid typography
8. `frontend/src/i18n/index.js` — i18n setup
9. `frontend/src/i18n/format.js` — Localized formatters
10. `frontend/src/App.jsx` — Route definitions

---

## 12. Tailwind Token Summary

### Colors
- `paper`: `#FFFFFF`, `paper-sunk`: `#F4F6F8`
- `portal`: `#0B2E4F`, `portal-deep`: `#071F36`, `portal-tint`: `#E8EFF5`
- `rule`: `#D5DEE6`, `rule-strong`: `#A9BCCB`
- `saffron`: `#E07A2F` (accent color for NIGRANI branding)

### Typography Scale
- `hero`: 64px, `hero-sub`: 26px, `band-title`: 40px
- `section-title`: 30px, `stat`: 42px (dashboards) / 38px (landing)
- `page-title`: 38px, `section-heading`: 26px, `lede`: 21px
- `body`: 17px, `table-cell`: 16px

### Layout
- `sidebar`: 288px
- Single radius: 4px
- Single shadow: `shadow-card`

### Fonts
- Display: `Source Serif 4, Georgia, serif`
- Body/UI: `Inter, system-ui, sans-serif`
- Devanagari: `Noto Sans Devanagari`
- Gujarati: `Noto Sans Gujarati`

---

## 13. What Was Done (Summary of All Changes)

### Created Files (frontend/src/):
- `i18n/index.js`, `i18n/useLanguage.js`, `i18n/format.js`, `i18n/LanguageSwitcher.jsx`
- `i18n/locales/en.json`, `hi.json`, `mr.json`, `gu.json`
- `components/HeroCarousel.jsx`, `components/Masthead.jsx`, `components/Footer.jsx`
- `components/UtilityStrip.jsx`, `components/PageHero.jsx`, `components/PreviewList.jsx`
- `components/PageMotif.jsx`, `components/DuplicateCompareModal.jsx`
- `data/corpus-facts.js`
- `pages/DataGapReport.jsx`, `pages/SearchPage.jsx`, `pages/StaticDocPage.jsx`
- `assets/IMAGE-CREDITS.md`

### Modified Files (frontend/):
- `package.json`, `tailwind.config.js`, `src/index.css`, `src/main.jsx`
- `src/App.jsx`, `src/components/Layout.jsx`, `src/components/Sidebar.jsx`, `src/components/TopBar.jsx`
- `src/pages/Landing.jsx`, `src/pages/Ministry.jsx`, `src/pages/StateNodal.jsx`
- `src/pages/District.jsx`, `src/pages/Member.jsx`, `src/pages/CaseDetail.jsx`
- `src/pages/Rulebook.jsx`, `src/pages/Alerts.jsx`

---

## 14. Potential Next Steps

- **Acceptance testing**: Run through all acceptance criteria from both implementation plans
- **Responsive testing**: Verify layouts at 1280px, 1024px, and 390px viewpoints
- **Accessibility audit**: Verify WCAG AA contrast, focus-visible outlines, skip links
- **Performance optimization**: Lazy-load heavy pages, optimize bundle size
- **New features**: Check if the team has additional implementation plans to execute
