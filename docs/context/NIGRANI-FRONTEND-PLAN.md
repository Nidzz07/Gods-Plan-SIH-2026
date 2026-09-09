# NIGRANI — Public landing page and authenticated interface

**Implementation brief for Antigravity.**
Repository: `Gods-Plan-SIH-2026` · Frontend: `frontend/` · Backend: do not touch.

---

## 0. How to use this document

You are rebuilding the presentation layer of a working government-oversight
application. The backend, the detection engine, the ML layer and the API are
finished, tested (645 passing tests) and **out of scope**. Your job is the
interface.

Rules of engagement, in priority order:

1. **Never modify `backend/`.** If a page needs data an endpoint does not
   provide, report it and build the page against what does exist. Do not add
   an endpoint, do not change a response shape, do not "temporarily" mock data
   in a component.
2. **Never invent a number.** Every figure that appears on screen is either
   fetched from the API at runtime, or — for the public landing page, which is
   unauthenticated — taken from the constants table in §12 of this document,
   which are real measured values from the committed corpus. If you find
   yourself writing a plausible-looking statistic, stop.
3. **Read before you write.** `CLAUDE.md`, `frontend/src/ui.js`,
   `frontend/tailwind.config.js`, `frontend/src/severity.js`,
   `frontend/src/roles.js`, `frontend/src/api.js` and every file in
   `frontend/src/pages/` already exist and encode decisions. This document
   extends them; it does not replace them.
4. **`npm run build` must pass after every commit.** `pytest` must stay at 645.
5. Commit messages must not name any assistant, and must not contain the
   string `CLAUDE` — the repository has a literal grep check that this trips.

---

## 1. Subject, audience, and the job of this interface

**Subject.** NIGRANI reads the twelve datasets the MPLADS portal already
publishes and finds where money stalled, where time was lost, and where the
same work appears twice. Every flag it raises carries the rule that fired, the
reading, the threshold, and a citation the officer can open.

**Audience.** Four government authorities with real power and no patience:
a Ministry analyst at MoSPI, a State Nodal officer, a District Authority who
will actually go and inspect the work, and a Member of Parliament looking at
their own constituency. Plus, for the landing page only, a hackathon judge who
has seen forty dashboards today.

**The job.** The interface must make an officer trust a number enough to act on
it. That means the evidence has to be visible next to the claim, always. This
is not a marketing site with a dashboard bolted on; it is an evidence tool with
a front door.

Everything below follows from that. Where a choice is arbitrary, prefer the one
that looks like it was built inside a ministry rather than inside a startup.

---

## 2. Hard constraints — do not change these

These are locked by the existing codebase and by `CLAUDE.md`.

| Constraint | Detail |
|---|---|
| Severity colours are semantic | `coral #D4573D` = HIGH, `gold #C8952B` = MEDIUM, `green #2E7D5B` = LOW. These three may **never** be used decoratively anywhere in the product. |
| Status is never colour alone | Every severity or status indicator carries a text label beside the colour. |
| One border radius | 4px. No second radius token. `rounded-full` does not exist in the Tailwind config and must not be re-added. |
| One shadow depth | `shadow-card`. Do not introduce a second elevation. |
| Numerics are tabular | Every score, amount, percentage, count and date uses `tabular-nums`. Already global in `index.css`. |
| No emoji, ever | Typographic marks only. |
| Focus is visible | The global `:focus-visible` rule in `index.css` stays. Do not add `outline: none` anywhere. |
| Role scoping is server-side | The UI hides what a role cannot use, but the API is what enforces it. Never treat a hidden button as security. |
| Skipped ≠ passed | Wherever a rule could not be evaluated, the interface says so explicitly and shows the reason. Never render an unevaluated rule as a pass, and never render an unpublished value as zero. |
| Token source | `VITE_API_BASE`, JWT in `sessionStorage`, Bearer header via the single `apiFetch` wrapper in `src/api.js`. Do not add a second fetch path. |

---

## 3. What changes, and why

Three deliberate departures from the current build. Each has a reason; do not
extend them further than stated.

**3.1 The page ground moves from cream to institutional white.**
`bg #FAF8F4` is retired as the page background and replaced with `paper
#FFFFFF` over a light neutral `#F4F6F8`. Reason: benchmarked against
india.gov.in, a warm cream ground reads as a design portfolio, not a ministry.
Cream is retained nowhere. The five original brand colours keep their semantic
roles; only the *ground* changes.

**3.2 A deep institutional navy becomes the primary structural colour.**
`#0B2E4F` (new, "portal navy") carries full-bleed section bands, the sticky
header on scroll, and the footer. The existing `navy #132A47` stays as the
heading text colour. Reason: the reference site structures the entire page by
alternating white and saturated full-bleed bands; NIGRANI needs the same rhythm
and cannot use coral or gold for it without breaking rule 2.

**3.3 Display type moves from Fraunces to Source Serif 4.**
`CLAUDE.md` already permits either. Source Serif is quieter and reads
institutional; Fraunces has a wobble in its optical sizing that undercuts
gravitas at large sizes. Body type stays Inter. Add Noto Sans Devanagari for
the Hindi wordmark.

```
npm install @fontsource/source-serif-4 @fontsource/noto-sans-devanagari
```

Nothing else in the token system changes.

---

## 4. Token system

Add these to `tailwind.config.js` alongside the existing tokens. **Extend, do
not replace** — every existing token stays so the current pages keep working.

### 4.1 Colour

```js
// new
paper:        '#FFFFFF',   // page ground
paper-sunk:   '#F4F6F8',   // alternating section band, table stripe
portal:       '#0B2E4F',   // full-bleed bands, footer, sticky header
portal-deep:  '#071F36',   // footer base, band gradient floor (solid only)
portal-tint:  '#E8EFF5',   // quiet card fill on white
rule:         '#D5DEE6',   // hairline dividers on white
rule-strong:  '#A9BCCB',   // table rules, sidebar dividers
saffron:      '#E07A2F',   // the underline rule under section headings
```

**`saffron` is the one decorative accent in the entire system.** It appears as
a 3px underline beneath section headings and nowhere else. It is deliberately
*not* coral, so it can never be mistaken for a HIGH severity marker. Do not use
it on buttons, links, borders, icons or backgrounds.

Retained and unchanged: `navy #132A47` (heading text), `ink #14171A`,
`ink-secondary #5B6169`, `ink-muted #94989E`, `coral`, `gold`, `green`,
`surface #FFFFFF`, `surface-sunk #F3F0EA`, `border`, `border-strong`.

### 4.2 Type scale

The user asked for larger type and a wider gap between headings and body.
Extend the existing named scale — keep every current key, add the display tier.

```js
fontSize: {
  // NEW — landing page and page heroes
  'hero':            ['64px', { lineHeight: '1.04', fontWeight: '600', letterSpacing: '-0.015em' }],
  'hero-sub':        ['26px', { lineHeight: '1.35', fontWeight: '400' }],
  'band-title':      ['40px', { lineHeight: '1.15', fontWeight: '600' }],
  'section-title':   ['30px', { lineHeight: '1.2',  fontWeight: '600' }],
  'stat':            ['38px', { lineHeight: '1.0',  fontWeight: '600' }],
  'lede':            ['19px', { lineHeight: '1.6',  fontWeight: '400' }],

  // EXISTING — unchanged, still used by the authenticated app
  'score-display':   ['48px', ...],
  'page-title':      ['28px', ...],
  'section-heading': ['18px', ...],
  body:              ['15px', ...],
  'body-secondary':  ['14px', ...],
  'meta-label':      ['12px', ...],
  'table-header':    ['12px', ...],
  'table-cell':      ['14px', ...],
}
```

**Raise the interior-page floor.** On authenticated pages, body text moves from
15px to **16px** and table cells from 14px to **15px**. Section headings move
from 18px to **22px**. This is the "increase the font size" instruction, applied
as a scale shift rather than an ad-hoc bump: change the values behind `body`,
`table-cell` and `section-heading` in the config and every existing page inherits
the change without edits.

Ratio discipline: on any page, the largest heading should be at least **2.2×**
the body size. If a section title is 30px, body is 16px, and that ratio holds.

### 4.3 Font roles

| Role | Family | Where |
|---|---|---|
| Display | Source Serif 4, 600 | hero, band titles, section titles, page titles, the score number |
| Interface | Inter, 400/500/600 | everything else — body, tables, labels, buttons, nav |
| Devanagari | Noto Sans Devanagari, 600 | the निगरानी wordmark only |

Do **not** introduce a monospace face for small data labels. The existing app
uses monospace only for genuine code and hash strings; keep it there. A
monospace label on a stat is a generated-design tell.

### 4.4 Spacing, radius, shadow, containers

- Spacing scale unchanged: 4 / 8 / 16 / 24 / 32 / 48. Section vertical rhythm is
  **72px** top and bottom on desktop (compose as `py-12` twice, or add a
  `section` spacing key of 72px).
- Radius: 4px, single token. Unchanged.
- Shadow: `shadow-card`, single token. Unchanged.
- Content container: `max-width: 1240px`, centred, `padding-inline: 24px`.
  Full-bleed bands run edge to edge; their *contents* sit in the same container.
- Body copy line length: cap at **72 characters** (`max-w-[64ch]` on paragraphs).

---

## 5. Global chrome

### 5.1 Utility strip (top, 36px, `portal-deep`)

Mirrors the reference site's accessibility affordances. Present on every page,
public and authenticated.

Left: `Government of India · Ministry of Statistics and Programme Implementation`
in 12px, `#C9D8E4`.

Right, as icon buttons with visible text labels on hover and always in the
accessible name:

| Control | Behaviour |
|---|---|
| Skip to main content | First focusable element on the page. Jumps to `#main`. Visually hidden until focused, then appears as a solid button. |
| Text size | Cycles A− / A / A+ — sets a root class that scales the type scale by 0.9 / 1.0 / 1.15. Persist in `localStorage`. |
| Contrast | Toggles a high-contrast class (pure black text, white ground, all decorative imagery hidden). Persist. |
| Language | `English / हिन्दी` toggle. **If translations do not exist, do not ship a dead toggle** — omit the control entirely rather than shipping one that does nothing. |

These are not decoration. A government portal without them is immediately
identifiable as a mock.

### 5.2 Masthead (public pages)

Height 88px, `paper` ground, bottom hairline `rule`.

```
┌───────────────────────────────────────────────────────────────────────┐
│ [emblem] NIGRANI                                                      │
│          निगरानी  ·  MPLADS Oversight    [ nav links ]    [ Sign in ] │
└───────────────────────────────────────────────────────────────────────┘
```

- Emblem: reuse and enlarge the existing `Logo.jsx` stepped-ladder mark. Do not
  use the Indian national emblem — you are not authorised to.
- Nav links: `How it works` · `The finding` · `Data-gap report` · `About`.
  These are in-page anchors except the report, which routes.
- `Sign in` is the only filled button in the masthead: `portal` fill, white text.

On scroll past 200px the masthead collapses to a 60px sticky bar with `portal`
fill and white text, matching the reference site's behaviour. Transition
`background-color 180ms ease-out`, no transform, no shadow animation.

### 5.3 Sidebar (authenticated pages) — **fixed, never scrolls**

This was called out explicitly. The left rail must not move when the main
column scrolls.

```css
/* the rail */
position: sticky;
top: 96px;                       /* utility strip + sticky header */
height: calc(100vh - 96px);
overflow-y: auto;                /* only if its own content overflows */
overscroll-behavior: contain;    /* stops scroll chaining to the page */
flex: 0 0 264px;
```

Structure, following the reference's `Explore : Category` rail:

```
┌──────────────────────────┐
│  Explore                 │   ← 22px display, saffron rule beneath
│  ┌────────────────────┐  │
│  │ 🔍 Filter…         │  │   ← filters the list below, client-side
│  └────────────────────┘  │
│                          │
│  National overview       │   ← current item: 3px left border in
│  State comparison        │      portal, background portal-tint,
│  District queue          │      weight 600. Others: ink-secondary.
│  Member accounts         │
│  ──────────────────────  │
│  Rulebook                │
│  Alerts            (12)  │   ← count badge, rectangular, gold
│  Audit trail             │
│  Data-gap report         │
│  ──────────────────────  │
│  Signed in as            │   ← 12px meta
│  D. M. Jalaun            │
│  District Authority      │
│  Uttar Pradesh · Jalaun  │   ← the scope sentence from /auth/me
│  [ Sign out ]            │
└──────────────────────────┘
```

Items a role cannot reach are **omitted**, not disabled — a disabled link
invites a support question. The scope sentence comes from the server's
`scope.describes` field; never construct it client-side.

### 5.4 Footer

Three tiers, matching the reference.

1. **Standards strip** — `paper-sunk`, 96px. Wordmarks for GOV.UK Design System,
   WCAG 2.1 AA, NIST SP 800-92, OWASP ASVS, MoSPI Open Data. Greyscale at 60%
   opacity, full colour on hover. If a licensed wordmark is unavailable, render
   the name in 14px Inter 600 rather than an approximation of the logo.
2. **Sitemap** — `portal-deep`, five columns: *The system* / *For authorities* /
   *Documentation* / *Data* / *About*. Populate from §11's route map. White
   headings at 15px 600, links at 14px `#C9D8E4`, hover to white with underline.
3. **Colophon** — full width, 13px, `#8FA6B8`:
   > Built for Smart India Hackathon 2026, Problem Statement 26102 (MoSPI,
   > Data Informatics and Innovation Division) by team GOD's Plan. Detection
   > figures are measured on twelve published MPLADS portal exports — a large
   > sample, not the complete national record.
   >
   > **Last reviewed and updated on <date> at <time>.**

That last line is the single most government-authentic detail available to you.
Render it from a build-time constant, not `new Date()` — a timestamp that
changes on every page load is a tell.

---

## 6. The landing page

Route `/`. Public, no token required. If a valid token already exists in
`sessionStorage`, show `Go to your dashboard` in place of `Sign in` — do not
auto-redirect, because a judge arriving on the URL should see the landing page.

Ten sections. The band rhythm alternates `paper` → `portal` → `paper` →
`paper-sunk` → `portal` and so on, so that scrolling has a pulse.

---

### §1 · Hero — `paper` with a masked photographic band

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│   NIGRANI  निगरानी                                                    │
│   ══════                                                              │
│   AI-powered detection of anomalies, fraud and inefficiency           │
│   in the MPLADS scheme                                                │
│                                                                       │
│   Ministry of Statistics and Programme Implementation ·               │
│   Data Informatics and Innovation Division                            │
│                                                                       │
│   ┌───────────────────────────────┬──────────────┬──────────────┐     │
│   │ Work ID, district, agency…    │ All records ▾│   Look up    │     │
│   └───────────────────────────────┴──────────────┴──────────────┘     │
│                                                                       │
│   Jump to:  National overview   District queue   Data-gap report      │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

**Copy — use exactly this, do not rewrite:**

- Wordmark: `NIGRANI` in Source Serif 600 at `hero` (64px), `navy`. Beside it,
  `निगरानी` in Noto Sans Devanagari 600 at 34px, `saffron`, baseline-aligned.
- Line beneath the wordmark: a 4px `saffron` rule, 96px wide, left-aligned to
  the N.
- Subheading (`hero-sub`, 26px, `ink`, max 26 words):
  **"AI-powered detection of anomalies, fraud and inefficiency in the MPLADS
  scheme."**
- Attribution (16px, `ink-secondary`):
  **"Ministry of Statistics and Programme Implementation · Data Informatics and
  Innovation Division"**
- Slogan, set apart below the lookup bar in 20px Source Serif italic, `portal`:
  **"Every flag carries its evidence."**

**The lookup bar** sits where the reference site puts its search. It is a real
control, not an ornament: submitting routes to `/sign-in?next=/search&q=…`,
because search requires a scope and therefore a login. Placeholder:
`Search a work ID, district, agency or member`. The dropdown offers
`All records / Works / Districts / Agencies / Members`.

**Do not** put a gradient behind the hero, do not animate the headline word by
word, and do not add a floating device mockup.

**Background treatment.** A single photograph — public infrastructure under
construction, or a district administrative building — occupying the right 45%
of the hero, masked with a left-to-right linear alpha mask so it dissolves into
white before it reaches the text. Maximum 22% opacity. Text never crosses it.
See §9 for sourcing.

---

### §2 · Corpus band — `portal`, full bleed, 140px

Six figures in one row, white on navy, separated by 1px `rgba(255,255,255,.18)`
vertical rules. Each: value in `stat` (38px, Source Serif 600), label beneath in
14px `#C9D8E4`.

| 27,078 | 118,704 | 12 | 638 | 31 | ₹2,107.5 cr |
|---|---|---|---|---|---|
| works scored | rows ingested | portal datasets | implementing agencies | states and UTs | sanctioned in sample |

Count-up animation on first scroll into view, 900ms, ease-out, **once per
session**. Respect `prefers-reduced-motion` by rendering the final value
immediately.

Beneath the row, centred, 14px `#9FB6C8` italic:
**"Measured on twelve published exports from the MPLADS portal. A large sample,
not the complete national record."**

That caveat is not optional. It is the difference between a confident claim and
an overclaim, and this project has held that line throughout.

---

### §3 · The finding — `paper`, asymmetric two-column

This is the memorable moment of the page. **Spend the boldness here and keep
every other section quiet.**

```
┌─────────────────────────────────┬─────────────────────────────────────┐
│                                 │                                     │
│  Recommended                    │  What we found before we built      │
│  ████████████████████████       │  ══════════════                     │
│                                 │                                     │
│  Sanctioned                     │  Across every work where both       │
│  ████████████████████████       │  figures are published, the         │
│                                 │  recommended amount and the         │
│  Identical in 14,831            │  sanctioned amount are the same     │
│  of 14,831 matched works        │  number. Not close — identical.     │
│                                 │                                     │
│                                 │  The portal publishes no revised    │
│                                 │  estimate, so cost overrun cannot   │
│                                 │  be detected from public MPLADS     │
│                                 │  data at all.                       │
│                                 │                                     │
│                                 │  MPLADS data is financially flat    │
│                                 │  and temporally rich. The signal    │
│                                 │  is in time and repetition — and    │
│                                 │  that is what NIGRANI reads.        │
└─────────────────────────────────┴─────────────────────────────────────┘
```

The two bars are the same length, to the pixel. That is the entire point of the
graphic. Bar 1 `portal`, bar 2 `rule-strong`, both 24px tall, 100% of the column
width. Label each bar above it at 15px.

`14,831` is set in `band-title` (40px) `coral` — the one place on the landing
page coral appears, and it is legitimate because it marks a finding, not a
decoration.

Animate the bars drawing left-to-right, 700ms, staggered by 120ms, on scroll
into view, once. Nothing else on this section moves.

---

### §4 · The four authorities — `paper-sunk`

Section title: **"Built for four authorities"**, with the saffron rule.
Lede beneath (19px, `ink-secondary`, max 72ch): **"Each sees only what their
office is responsible for. Scoping is enforced in the database query, not in
the interface."**

Four cards, equal width, `paper` fill, `rule` border. Each card:

| | Ministry | State Nodal | District Authority | Member of Parliament |
|---|---|---|---|---|
| Icon | map | sitemap | magnifier | users |
| Scope line | Unrestricted | One state | One district | Own works |
| Body | National risk map, state league table, and a reporting-gap report on MoSPI's own data format. | District comparison and utilisation trend, so slow districts surface before year-end. | A ranked, evidence-ordered queue that replaces rotation-based inspection. | Own account utilisation and stalled works, read-only. |
| Action | `Sign in as Ministry →` | … | … | … |

Card hover: border darkens to `rule-strong`, background lifts to `portal-tint`,
120ms. **No translate, no shadow change.** Clicking anywhere on the card routes
to `/sign-in` with the role pre-selected in the query string.

---

### §5 · How a case is scored — `paper`, 2×3 grid

Section title: **"How a case is scored"**. Six cards, icon + heading + two-line
body:

1. **Fund ladder** — sanctioned → disbursed → certified. The system names which
   hop the money stalled at.
2. **Lifecycle ladder** — recommended → sanctioned → first payment → completed.
   And which stage the time was lost at.
3. **A rulebook an officer can edit** — ten thresholds in YAML, each carrying
   the count of works it fires on. The Ministry changes them live.
4. **Coverage, stated honestly** — a rule with no reading is reported as not
   published, never as passed. Mean signal coverage today is 58.47%.
5. **Duplicates, cited not accused** — the flag opens both work IDs side by
   side. 447 clusters found; a cluster is a candidate for review.
6. **An append-only trail** — 84,666 hash-chained events. A score re-derives
   months later against the rulebook in force that day.

---

### §6 · The wall — `portal`, full bleed

Section title in white: **"Four detection tiers, and the wall between them"**.

Four columns. The first two (`Rulebook`, `Duplicate detection`) sit left of a
2px vertical `coral` rule; the second two (`Anomaly`, `Delay forecast`) sit
right of it. Label the rule vertically: **`SCORES` ← | → `BADGES, WORTH ZERO`**.

Beneath, in `portal-tint` on a darker inset panel, monospace 15px:

```
score = Σ w(fired rules) + corroboration bonus,  capped at 100
anomaly · forecast · centrality  →  contribute 0
```

Closing line, 16px white: **"An automated test walks the import graph and fails
the build if the scoring engine ever imports the machine-learning package. The
number in the corner cannot come from a model."**

---

### §7 · Live signal — `paper`, two columns

Left, **"Recent high-risk cases"**: five rows, each a case ID, district, score,
and the rule that dominated. Right, **"Reporting gaps we found"**: the top three
ablation findings with their coverage deltas.

**This section requires data.** If a public read-only endpoint does not exist,
build it as a static section from the §12 constants and label it
`Sample from the committed corpus` — do not fabricate live-looking rows.

---

### §8 · Documentation directory — `paper-sunk`, five icon tiles

`Rulebook` · `Data profile` · `Data-gap report` · `API reference` ·
`Audit trail`. Tiles are 180px square, icon above, label below. Hover: fill to
`portal`, icon and label invert to white, 120ms. Public tiles route to public
document pages; authenticated ones route to `/sign-in`.

---

### §9 · Standards strip and §10 · Footer

As specified in §5.4.

---

## 7. Interior page template

Every authenticated page uses one template, derived directly from the reference
site's category page.

```
┌─ utility strip ───────────────────────────────────────────────────────┐
├─ sticky header (portal, 60px) ────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐  ┌─────────────────────────────────────────────────┐    │
│  │          │  │ Home  ›  Ministry  ›  National overview          │    │  ← breadcrumb
│  │  FIXED   │  ├─────────────────────────────────────────────────┤    │
│  │  RAIL    │  │                                                 │    │
│  │          │  │  National overview                              │    │  ← page hero
│  │  (§5.3)  │  │  ══════════                                     │    │     paper, watermark
│  │          │  │  27,078 works across 31 states and union        │    │     motif bottom-right
│  │          │  │  territories, scored against rulebook v1.0.0.   │    │
│  │          │  │                                                 │    │
│  │          │  ├─────────────────────────────────────────────────┤    │
│  │          │  │ ███ FULL-BLEED PORTAL BAND ███                  │    │  ← the working section
│  │          │  │                                                 │    │
│  │          │  │  Interactive list  │  Preview panel             │    │
│  │          │  │  ─────────────────┼──────────────────           │    │
│  │          │  │  → Item one       │  ┌──────────┐  Heading      │    │
│  │          │  │  → Item two  ◀────┼──│  image   │  Body copy…   │    │
│  │          │  │  → Item three     │  └──────────┘  [ Open ]     │    │
│  │          │  │                                                 │    │
│  │          │  ├─────────────────────────────────────────────────┤    │
│  │          │  │  Stat strip — four figures with outline icons   │    │
│  │          │  ├─────────────────────────────────────────────────┤    │
│  │          │  │  Charts / tables, full width                    │    │
│  └──────────┘  └─────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────┘
```

### 7.1 The hover-preview list — build this as one shared component

This is the mechanic from reference images 2–4, and it is the most distinctive
interaction on the reference site. Build it once as `<PreviewList>` and reuse it
on five pages.

**Behaviour:**
- A vertical list of rows, each with a leading `→` glyph, separated by hairlines.
- **Hover or keyboard-focus** on a row lifts it to a white pill (`paper` fill,
  4px radius, `shadow-card`) and swaps the preview panel beside it.
- The preview panel shows: an image (left, 42%), a heading, 3–4 lines of body,
  and a filled `Open` button.
- The panel swaps with a **160ms cross-fade only**. Do not slide, do not scale.
- The first row is active on mount.
- The whole row is a link — the pointer is `cursor: pointer` across its full
  width, not just on the text.
- Keyboard: arrow keys move the active row, `Enter` follows it. Every row is a
  real `<a>`; this must work with JavaScript hover disabled.

**Props:** `items: [{ id, label, title, body, image, href }]`, `title`.

### 7.2 Page hero rules

- Page title in `section-title` (30px) Source Serif 600 `navy`, with the 3px
  saffron rule beneath, 72px wide.
- One lede sentence at 19px `ink-secondary`, capped at 72ch, giving the scope
  and the count. Always includes the rulebook version.
- Breadcrumb above at 14px: `Home › <Role home> › <Page>`. Every segment except
  the last is a link.

---

## 8. Page-by-page specification

For each page: what the hero says, what the PreviewList contains, which charts
appear, and where every element routes. **Enlarge every chart to at least 380px
tall** — the current dashboards under-use their vertical space.

### 8.1 `/ministry` — National overview

| Element | Content |
|---|---|
| Hero lede | "27,078 works across 31 states and union territories, scored against rulebook v1.0.0. Mean signal coverage 58.47%." |
| PreviewList | The six highest-risk states. Row = state name. Preview = severity split, worst score, sanctioned total, `Open state →` routing to `/state/:state`. |
| Chart 1 | Horizontal bar, states by HIGH count. 420px tall. Recharts. Bars `portal`; the top bar `coral`. |
| Chart 2 | Fund-flow proportion: sanctioned vs. behind an open hop. 380px. |
| Table | State league table, TanStack, sortable: state · cases · HIGH · mean coverage · sanctioned. Row click → `/state/:state`. |
| Stat strip | 37 HIGH · 1,006 MEDIUM · 26,035 LOW · 191 corroborated |
| Ministry-only | `Edit rulebook` and `Open data-gap report` as two prominent cards below the table. |

### 8.2 `/state/:state` — State comparison

Hero lede names the state and its district count. PreviewList = top six
districts, preview shows the district's severity split and worst case, `Open
district →`. Chart: stacked severity by district, 400px. Table: all districts,
sortable, row click → `/district/:state/:district`.

### 8.3 `/district/:state/:district` — The working queue

This is the screen an officer uses all day. It gets the most care.

- Hero lede: case count, HIGH count, mean coverage, implementing-agency count.
- **The queue is the page.** TanStack table, 100 rows, sorted score-descending.
  Columns: severity accent (3px left border, plus a text label) · case ID ·
  work description (truncated at 60ch with a title attribute) · score
  (right-aligned, tabular) · coverage % · gap hop · sanctioned amount.
- Row height 56px minimum. Row hover: `portal-tint` fill, 90ms. Row click →
  `/cases/:caseId`.
- Above the table: filter chips for severity, and a text filter.
- Agency concentration panel beside the queue: horizontal bar of the district's
  agencies by share, 320px.

### 8.4 `/member` — Member account

Hero lede names the member, house and constituency. The account ladder is the
hero graphic: three horizontal bars (allocated → sanctioned → disbursed) per
financial year, **with unpublished years rendered as a dashed outline carrying
the words "not published"** — never as a zero-height bar. Below: the member's
work portfolio as a table. Read-only: no note field, no acknowledge control.

### 8.5 `/cases/:caseId` — The case sheet

The most important screen in the product. Full width, no PreviewList.

```
┌──────────────────────────────────────────────────────────────────────┐
│  Home › District queue › NG-094E347D96                               │
│                                                                      │
│  Construction of interlocking CC road, ward 7          ┌──────────┐  │
│  ══════════════                                        │    92    │  │
│  WS/MP847/2025-2026/160261 · District Magistrate       │   HIGH   │  │
│  Jalaun · Uttar Pradesh · sanctioned ₹19,95,390        │ 79% cov. │  │
│                                                        └──────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│  FUND LADDER              │  LIFECYCLE LADDER                        │
│  sanctioned ──▶ disbursed │  recommended ─▶ sanctioned ─▶ payment ─▶ │
│      ◆ −34.85%            │       ◆ 268 d        136 d       …       │
│  gap located here         │  slowest stage                           │
├──────────────────────────────────────────────────────────────────────┤
│  REASONING TRACE                                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Utilisation shortfall   −34.85%   lt −15   fired      +22      │  │
│  │ Execution delay         —         gt 365   not applicable  0   │  │
│  │ Duplicate work          0.97      ≥ 0.85   fired      +18      │  │
│  │   └ Cited: WS/…/160262, WS/…/160263 · cluster of 15  [Compare] │  │
│  │ …                                                              │  │
│  └────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│  BADGES — none of these affect the score                             │
│  Anomaly 0.42 · Delay risk 71st pct · Vendor share 38.2%   each +0   │
├──────────────────────────────────────────────────────────────────────┤
│  MEMO (generated from a template, not a language model)              │
│  NOTES + RECOMPUTE                                                   │
└──────────────────────────────────────────────────────────────────────┘
```

Requirements:
- Score block: 64px Source Serif, severity tag beneath, coverage beneath that.
- Both ladders drawn as node chains with the gap marker on the failing hop.
  Ladder height at least 120px — the current version is too small to read.
- Trace table rows are colour-accented by status **and** carry the status word.
  Skipped rows show their reason inline (`not published` / `not applicable`),
  greyed and italic.
- The duplicate citation sits **inside its trace row**, indented, with a
  `Compare` button that opens a side-by-side modal of both work descriptions.
- Badges live in their own section under a heading that says they are worth
  zero. This must be visually obvious in a screenshot.

### 8.6 `/rulebook` — Rulebook

PreviewList of the ten rules: row = rule label; preview = field read, operator,
threshold, weight, severity, the measured firing count, and the rationale
sentence. Below: the full rulebook table, plus the version block (`v1.0.0`,
updated by, SHA-256, `file matches stored version: true/false`).

Ministry only: each threshold and weight cell becomes an input, with a
`Propose change` button. Before submission, a panel states in plain words:
**"This creates a new rulebook version. Existing cases keep the score they were
given and are not re-scored until each is recomputed individually."**

### 8.7 `/alerts` — Alert inbox

Table: severity · case · rule · raised · status. Filter chips by status. Row
actions `Acknowledge` and `Escalate` render only for roles that may use them.
The escalate response panel must display the dry-run notice verbatim from the
API — never paraphrase it into something that sounds like an email was sent.

### 8.8 `/reports/data-gap` — Data-gap report

Ministry only. Hero lede states the method in one sentence. Then: the ranked
field table, the coverage before/after column chart (58.47 → 88.91), and the
generated report body rendered from markdown. A `Download report` action.

---

## 9. Background imagery

The instruction was to fill the pages with relevant, low-opacity imagery. Do it
in **two layers**, and never a third.

**Layer A — geometric motif (every page, always).**
`PageMotif.jsx` already exists in the repository with per-page variants. Extend
it, don't replace it. One SVG pattern per page, tiled, at **4% opacity**,
masked so it fades out over the first 240px so it never sits behind the page
title. Motifs by page:

| Page | Motif |
|---|---|
| Ministry | a sparse district-boundary lattice |
| State | stacked horizontal rules, like a register |
| District | the four-node ladder chain, repeated |
| Member | a rupee-column grid |
| Case sheet | the stepped ladder from the logo |
| Rulebook | ruled clause lines |
| Alerts | a diagonal chevron field |

**Layer B — photograph (page hero only, optional).**
A single image, right-aligned, occupying at most 45% of the hero width, at
**18–22% opacity**, with a left-to-right alpha mask so it never reaches the
text column. Behind it, a solid `paper` ground — never a gradient.

Subjects, by page: rural road construction · a district collectorate building ·
a community hall · a school block · a public water tank. Photograph the *works
MPLADS funds*, not stock photos of people pointing at laptops.

**Sourcing.** Use only public-domain or CC0 images, or Government of India open
media. Record the source and licence for each in
`frontend/src/assets/IMAGE-CREDITS.md`. If a licence cannot be confirmed, ship
Layer A alone — a page with only the motif looks deliberate; a page with an
unlicensed photograph is a liability.

**Contrast is non-negotiable.** After adding any background, verify body text
still clears 4.5:1 and large text 3:1 against the *composited* background. The
high-contrast toggle in §5.1 must hide Layer B entirely.

---

## 10. Motion

Restraint is the brief. Scattered fade-up-on-scroll across every section is the
clearest signal of a generated page, and this build must not have it.

**Permitted, and only these:**

| Moment | Spec |
|---|---|
| Corpus stat count-up | Once per session, 900ms ease-out, on first intersection |
| The two identical bars (§3) | Draw left→right, 700ms, 120ms stagger, once |
| Sticky header collapse | `background-color` 180ms ease-out |
| PreviewList panel swap | 160ms cross-fade, opacity only |
| Card and row hover | 90–120ms, colour and border only |
| Modal / drawer open | 180ms, opacity + 8px translate |
| Chart series draw | Recharts default `isAnimationActive`, 600ms, on mount only |

**Forbidden:** parallax, scroll-jacking, section-by-section fade-up, letter or
word staggered headline reveals, animated gradients, count-ups anywhere except
§2, hover translate on cards, spring physics, anything on a loop.

Wrap everything in:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
```

---

## 11. Route and interaction map

Everything clickable, and where it goes. Nothing on any page may be a dead
element — if a target does not exist, remove the control rather than shipping a
link to nowhere.

| From | Element | To |
|---|---|---|
| `/` | masthead `Sign in` | `/sign-in` |
| `/` | nav `How it works` / `The finding` | in-page anchor |
| `/` | nav `Data-gap report` | `/reports/data-gap` (→ `/sign-in` if no token) |
| `/` | lookup submit | `/sign-in?next=/search&q=…` |
| `/` | any authority card | `/sign-in?role=<role>` |
| `/` | any documentation tile | its route, or `/sign-in` |
| `/sign-in` | submit | role home from `/api/auth/me` |
| any | sidebar item | its route |
| any | sidebar `Sign out` | clears token → `/` |
| any | breadcrumb segment | that ancestor |
| `/ministry` | state row / preview `Open` | `/state/:state` |
| `/ministry` | `Edit rulebook` | `/rulebook` |
| `/ministry` | `Data-gap report` | `/reports/data-gap` |
| `/state/:state` | district row | `/district/:state/:district` |
| `/district/…` | queue row | `/cases/:caseId` |
| `/district/…` | agency bar | filters the queue in place |
| `/member` | portfolio row | `/cases/:caseId` |
| `/cases/:id` | `Compare` on a duplicate | modal, both works side by side |
| `/cases/:id` | cited work ID | `/cases/:otherCaseId` |
| `/cases/:id` | `Recompute` | POST, then result panel in place |
| `/cases/:id` | `View audit trail` | `/audit/:caseId` |
| `/alerts` | alert row | `/cases/:caseId` |
| `/rulebook` | rule row | expands the preview panel |
| footer | any sitemap link | its route |

**Error states.** A 403 renders "This is outside your scope" plus the scope
sentence from the token. A 404 on a case renders "No case with that identifier
in your scope" — worded so it cannot be used to confirm that a case exists
elsewhere. The backend already draws this distinction; the interface must not
undo it.

---

## 12. Constants for the public landing page

The landing page is unauthenticated and cannot call scoped endpoints. These
values are measured from the committed corpus. Put them in
`frontend/src/data/corpus-facts.js` with a comment naming their source, and
import from there — do not scatter them through JSX.

```js
export const CORPUS = {
  worksScored: 27078,          // real cases; 27,079 including the labelled control
  rowsIngested: 118704,
  datasets: 12,
  agencies: 638,
  vendors: 15245,
  members: 766,
  states: 31,
  sanctionedCrore: 2107.5,
  allocatedCrore: 23242,
  bands: { high: 37, medium: 1006, low: 26035 },
  corroborated: 191,
  meanCoverage: 58.47,
  rules: 10,
  ruleWeight: 144,
  bonusWeight: 10,
  auditRows: 84666,
  tests: 645,
  duplicateClusters: 447,
  duplicateWorks: 3584,
  duplicateCrore: 157.12,
  degeneracy: { matched: 14831, identical: 14831 },
  ablation: {
    expenditureLinkage: { skips: 70647, works: 23549, coverageTo: 88.91, deltaPp: 30.44 },
    assetEvidence:      { skips: 14104, works: 14104, deltaPp: 3.65 },
    zeroFields: 7,
  },
};
```

---

## 13. Anti-patterns — check every page against this before calling it done

These are the specific things that make a page read as generated. Several are
already banned by `CLAUDE.md`; the rest are additions for this work.

**Never:**

1. A cream or warm-beige page ground.
2. A gradient anywhere — text, button, card, band, or overlay.
3. `rounded-full` on anything. Tags are rectangles.
4. A second border radius or a second shadow depth.
5. A tracked-out all-caps eyebrow label above a heading. (Existing table headers
   and meta-labels keep their uppercase — that is a data-table convention, not
   an eyebrow.)
6. `→` appended to the end of link text as decoration. The arrow inside a
   PreviewList row is a leading list glyph and is fine; a trailing arrow on a
   button label is not.
7. Meta strings joined with middle dots as a decorative pattern. Use them only
   where the parts are genuinely peer facts (`District · State`).
8. A monospace face on a statistic or a small label. Monospace is for code,
   hashes, work IDs and YAML only.
9. Numbered markers (01 / 02 / 03) on content that is not a sequence.
10. Fade-up-on-scroll applied to every section.
11. A hero with a big number, a small label and an accent gradient.
12. Emoji, anywhere.
13. Placeholder Latin text, a `#` href, or a `TODO` in shipped markup.
14. A control that does nothing — including a language toggle without
    translations and a search box that does not search.
15. `outline: none` on any focusable element.

**Always:**

16. Every interactive element has a visible hover state *and* a visible focus
    ring, and they are not the same treatment.
17. Every table has a one-line caption above it stating what it shows in plain
    words.
18. Every chart has a caption and an accessible text alternative — a `<figure>`
    with a `<figcaption>`, and the underlying figures reachable as a table or
    in the caption itself.
19. Every numeric column is right-aligned with `tabular-nums`.
20. Every severity or status colour is accompanied by its word.
21. Every "not published" value says so in words; none is rendered as zero, a
    dash alone, or an empty cell.
22. Every page works at 1280px, 1024px and 390px. The fixed sidebar becomes a
    slide-over drawer below 1024px.

---

## 14. Build order

Nine steps. Each ends with `npm run build` green and one commit.

| # | Step | Done when |
|---|---|---|
| 1 | Tokens and fonts — extend the Tailwind config, install Source Serif 4 and Noto Sans Devanagari, raise the interior type floor | Existing pages still render correctly at the new sizes |
| 2 | Global chrome — utility strip, masthead, sticky behaviour, footer | Present on every route, keyboard reachable, skip-link works |
| 3 | Fixed sidebar — rewrite the rail per §5.3 | The rail does not move while the main column scrolls, at every breakpoint |
| 4 | `<PreviewList>` — the shared hover-preview component | Works with pointer, keyboard, and with hover disabled |
| 5 | Landing page — all ten sections | No fabricated data; every control routes somewhere real |
| 6 | Interior template — breadcrumb, page hero, band, stat strip | Applied to one page end-to-end before the rest |
| 7 | Roll the template across Ministry, State, District, Member | Charts at their new sizes; every row click routes |
| 8 | Case sheet, rulebook, alerts, data-gap report | Citations inline; badges visibly separated from the score |
| 9 | Imagery, motion, accessibility pass | §9, §10 and §13 all satisfied |

---

## 15. Acceptance

Before declaring the work finished, verify each of these by doing it, not by
reading the code:

1. `npm run build` passes; `pytest` is still 645.
2. Log in as each of the four roles and walk the full route map. Every link
   resolves. No console errors.
3. Scroll any interior page to the bottom — the sidebar has not moved.
4. Tab through the landing page from the top. The skip link appears first, the
   focus ring is visible on every stop, and the tab order matches the visual
   order.
5. Set `prefers-reduced-motion: reduce` in devtools. Nothing animates; the stat
   band shows its final values immediately.
6. Zoom the browser to 200%. No text is clipped and no layout is broken.
7. Run the page through an automated contrast check with the background imagery
   enabled. No failures on body text.
8. Type a case ID belonging to another district into the URL while signed in as
   District Authority. The page shows the scoped error state, not a crash and
   not another district's data.
9. Screenshot the case sheet. A reader who has never seen the product can tell,
   from that image alone, that the anomaly and forecast badges do not contribute
   to the score.
10. Read every visible string. None of it is placeholder, none of it overclaims,
    and the corpus caveat appears wherever a corpus-wide figure does.
