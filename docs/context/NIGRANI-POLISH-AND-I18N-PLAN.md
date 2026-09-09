# NIGRANI — Motif removal, password visibility, complete translation, and the references strip

**Implementation brief for Antigravity — round four.**
Repository: `Gods-Plan-SIH-2026` · Frontend only · Backend: do not touch.

Deployed at `gods-plan-sih-2026.vercel.app`. Four changes, in this order of
effort: one is trivial, one is small, one is large and unglamorous, one is
content.

---

## 0. Rules of engagement

1. **Never modify `backend/`.** `pytest` stays at 645.
2. **Never invent a number.** Figures come from the API or from
   `frontend/src/data/corpus-facts.js`.
3. **`npm run build` must pass after every commit**, and the Vercel deploy must
   succeed before the branch is merged.
4. Commit messages must not name any assistant and must not contain the string
   `CLAUDE` — the repository has a literal grep check that this trips.
5. Severity colours stay semantic: coral = HIGH, gold = MEDIUM, green = LOW.
   Never decorative.
6. One border radius (4px), one shadow depth, no gradients, no `rounded-full`,
   **no emoji** — including as a placeholder while waiting for an icon.
7. Work on a branch: `git checkout -b feat/i18n-completion-and-polish`.

---

# PART A — Remove the decorative background motif

The faint diamond lattice behind the National overview is the `PageMotif`
layer specified in an earlier round. It has not earned its place: it adds
visual noise behind dense tabular data and it is the kind of texture that reads
as decoration on a page whose whole argument is that nothing here is decorative.

### A1. What to do

1. Locate the component. It is almost certainly
   `frontend/src/components/PageMotif.jsx`, rendered from the authenticated page
   shell or from each dashboard.
2. Remove its render from **every authenticated page** — Ministry, State Nodal,
   District, Member, case sheet, rulebook, alerts, audit trail, data-gap report.
3. If nothing else imports it afterwards, **delete the component file** rather
   than leaving it orphaned. Dead code in a repository a judge may browse is a
   small but real cost.
4. Confirm the page ground is the flat `paper` / `paper-sunk` pair already in
   the token set. Do not introduce a new background colour to replace the
   pattern — the grounds are already correct underneath it.

### A2. What not to touch

The landing page hero carousel is **not** a motif and stays exactly as it is.
So does the scrim behind the sign-in video. This part removes one decorative
SVG layer on authenticated screens, nothing else.

### A3. Check afterwards

Sign in as all four existing roles and confirm every dashboard has a clean flat
ground with no residual pattern, no leftover empty positioned `<div>`, and no
`z-index` artefact where the layer used to sit.

---

# PART B — Password visibility toggle

On `/sign-in`, add a show/hide control inside the password field.

### B1. Behaviour

| Property | Value |
|---|---|
| Position | Inside the field, right-aligned, 12px from the right edge, vertically centred |
| Element | A real `<button type="button">` — **never** a `<div>` with an onClick, and `type="button"` so it cannot submit the form |
| Default state | Hidden. `type="password"` |
| Toggled state | `type="text"` |
| Icon | Inline SVG, two states: an open eye and an eye with a strike-through. 20px. `currentColor` so it inherits and can be recoloured |
| Colour | `ink-secondary` at rest, `ink` on hover and focus |
| Field padding | Add `padding-right: 48px` to the password input so the typed value never runs under the button |
| Hit target | 44 × 44px minimum, even though the icon is 20px |
| Focus | The standard global focus ring. Do not suppress it |
| `aria-label` | Translated. Changes with state: "Show password" / "Hide password" |
| `aria-pressed` | `true` when the password is visible |
| Tab order | Between the password input and the Sign in button |

**Use inline SVG, not an image asset.** Two short paths, no new file to supply,
no network request, and it recolours with the theme. This is one of the few
places where an icon file would be the worse choice.

### B2. Rules

- Reset to hidden on mount. The visible state must never persist across a
  navigation or a reload — a password left visible on a shared district machine
  is exactly the failure this control is otherwise defending against.
- Never log, never store, never put the password in a query string.
- The toggle must work with the keyboard alone: `Tab` to it, `Enter` or `Space`
  to activate.
- Do not add a similar toggle anywhere else. There is one password field in
  this product.

---

# PART C — Complete the translation coverage

The largest part of this round. Four languages are wired up and some strings
change; most do not. This part is the unglamorous sweep that makes the feature
real.

## C1. Find every untranslated string — use a pseudo-locale, not grep

Grepping for quoted strings in JSX will miss placeholders, `aria-label`s, chart
axis labels, `alt` text and anything built by concatenation. Do this instead.

**Build a dev-only pseudo-locale.** Add a fifth locale, `zz`, generated at build
time by transforming every value in `en.json`:

```js
// frontend/src/i18n/pseudo.js  — dev only, never shipped to production
export const makePseudo = (en) =>
  Object.fromEntries(
    Object.entries(en).map(([k, v]) =>
      typeof v === "string" ? [k, `»${v}«`] : [k, makePseudo(v)]
    )
  );
```

Register `zz` only when `import.meta.env.DEV` is true, and expose it in the
switcher only in development.

**Then walk the entire product in `zz`.** Every string wrapped in `»…«` is
translated. **Anything that renders plainly is hard-coded and must be
extracted.** This finds in an afternoon what grep would miss for weeks.

**Walk every page and every state**, not just the happy path:

| Page | States to visit |
|---|---|
| Landing | hero, all sections, footer, the lookup control |
| Sign in | idle, error ("Could not sign in"), field labels, placeholders |
| Ministry | loaded, the preview panel, the league table, every chart |
| State Nodal | loaded, both UP and a low-HIGH state |
| District | loaded, filter chips, empty filter result |
| Member | loaded, the "not published" ladder rows |
| Case sheet | fired / passed / skipped trace rows, the duplicate citation, badges |
| Rulebook | read-only and Ministry edit mode |
| Alerts | all four filter states, empty inbox |
| Data-gap report | loaded |
| Audit trail | loaded |
| Everywhere | 401, 403, 404, loading skeletons, network-error state |

Error and empty states are where hard-coded strings hide, because nobody sees
them during normal development.

## C2. The boundary — what translates and what never does

You asked whether case names should stay in English. **Yes, and the reason
matters more than the rule:** the duplicate-detection similarity scores were
computed on those exact description strings, and an officer cross-checking a
case against the MPLADS portal must see the same text the portal shows. A
translated description is a description that can no longer be matched to its
record.

### Translate — interface chrome, written by us

Page titles · section headings · table column headers · button labels · form
labels and **placeholders** · helper and caption text · empty states · error
messages · the utility strip · sidebar navigation · the scope sentence · chart
axis labels and legends · tooltip text · `aria-label` and `alt` text · date and
unit words · rule **labels** and rule rationale prose · the memo template's
connective phrasing · severity **words** (HIGH → उच्च) while the colour stays.

### Never translate — data, supplied by MoSPI

| Never translate | Why |
|---|---|
| Work descriptions | Verbatim portal text; the similarity scores were computed on these exact strings |
| State, district, constituency names | `BIDAR` is how the record is keyed |
| Member of Parliament names | Proper nouns |
| Implementing agency names | Proper nouns; the canonicalisation ledger keys on the exact string |
| Vendor names | Proper nouns |
| Work IDs (`WS/MP847/2025-2026/160261`) | Identifiers |
| Case IDs (`NG-8F0E3213D8`) | Identifiers |
| Rule IDs (`utilisation_shortfall`) | Keys — but their **labels** are translated |
| Rulebook version strings, SHA-256 digests, audit hashes | Identifiers |
| Email addresses | Identifiers |

Put this table as a comment at the top of `en.json` so the next person adding a
string knows which side of the line it sits on.

## C3. Numbers — a decision, with a recommended default

You asked for numbers to change with the language. There are three separate
things that could mean, and they should be settled separately.

| Aspect | Recommendation |
|---|---|
| **Digit glyphs** (27,078 vs २७,०७८) | **Keep Latin in all four languages.** `numberingSystem: 'latn'` |
| **Grouping** (lakh/crore vs thousands) | Indian grouping in all four — already correct, no change |
| **Unit and adjacent words** (crore, lakh, days, cases, %) | **Translate.** These are prose, not data |

**Why Latin digits.** This product exists so an officer can match a figure on
screen against a government record printed in Latin digits. Devanagari numerals
break that in the one place it matters. They would also sit inconsistently
beside work IDs and case IDs, which stay Latin regardless — a table with
`२७,०७८` in one column and `WS/MP847/2025-2026/160261` in the next reads as a
bug, not as localisation.

**Implement it as a single flag** so the decision is reversible without a
rewrite:

```js
// frontend/src/i18n/format.js
export const USE_NATIVE_DIGITS = false;   // set true to render Devanagari / Gujarati numerals

const opts = USE_NATIVE_DIGITS ? {} : { numberingSystem: "latn" };
export const num = (v, lang) => new Intl.NumberFormat(LOCALE[lang], opts).format(v);
```

Every number in the product goes through this one function. If a component
calls `toLocaleString()` or builds a number string by hand, that is a bug —
find them all and route them through `num()`.

## C4. The things that are always missed

Check each explicitly; these are the usual survivors of an i18n sweep.

1. **Input placeholders** — the lookup bar, the sidebar filter, the queue
   filter, both sign-in fields.
2. **`aria-label` and `alt`** — every icon button, the carousel dots, the
   emblem, the documentation tile icons, the new password toggle.
3. **`title` attributes** — the truncated work descriptions in the queue.
4. **Chart axis labels, tick formatters and legends** — Recharts does not read
   your i18n context on its own. The axis label "cases" is a string like any
   other.
5. **Select and dropdown options** — including "All records" in the hero lookup.
6. **Pluralisation** — use i18next's `_one` / `_other` keys. Never concatenate a
   count and a noun. Hindi, Marathi and Gujarati each need their own forms; do
   not assume the English rule.
7. **Dates** — `Intl.DateTimeFormat(LOCALE[lang], { dateStyle: 'medium' })`.
   Check the "Last reviewed and updated on…" line in the footer.
8. **Interpolated sentences** — "27,078 works across 31 states and union
   territories, scored against rulebook v1.0.0" must be one key with named
   placeholders, not four fragments joined with `+`. Word order differs between
   these languages and concatenation cannot express that.
9. **The `<html lang>` attribute** — must update on every switch.
10. **Toast and inline validation messages**.
11. **The document `<title>`** and any meta description.

## C5. Stop it regressing

Add a check that fails the build when a page renders an untranslated string.

The simplest version that actually works: a small script that walks
`frontend/src/**/*.jsx` and flags string literals passed to JSX text nodes or
to `placeholder` / `aria-label` / `alt` / `title` props, with an allowlist for
genuinely non-translatable values (class names, identifiers, single
punctuation). Wire it into `npm run build` or a `npm run lint:i18n` script that
the team runs before deploying.

It will produce false positives at first. Tune the allowlist rather than
weakening the check.

## C6. Fonts and layout

Already specified in an earlier round, but verify it survived: Devanagari and
Gujarati need more line-height than Latin and will clip matras at the current
heading values. Check every heading, the hero wordmark, the stat card values,
the table headers and the button labels in all four languages at 100% and 200%
zoom.

---

# PART D — The references strip

Replace the five cards under **STANDARDS, BENCHMARKS & OPEN DATA COMPLIANCE**
with four. Keep the existing visual format exactly: a bold title line, a small
grey descriptor beneath, a bordered card, horizontal row.

## D1. The four cards

| # | Title *(not translated)* | Descriptor *(translated)* | Link |
|---|---|---|---|
| 1 | MPLADS Portal, MoSPI | All twelve datasets used in this project | `https://mplads.mospi.gov.in/digigov/dashboard.html` |
| 2 | National Portal of India | Design and status-guidance benchmark | `https://www.india.gov.in/` |
| 3 | MAHAONE Portal | Maharashtra SSO — sign-in page reference | `https://mahaone.maharashtra.gov.in/` |
| 4 | W3C WCAG 2.1 AA | Accessibility conformance reference | `https://www.w3.org/TR/WCAG21/` |

**On card 3:** you supplied two URLs, one carrying `?resid=8019`. That is a
session parameter and will rot. Use the bare domain as the `href`. If it does
not land somewhere sensible, use
`https://mahaone.maharashtra.gov.in/emIDAM/username.html` without the query
string and note it.

## D2. Requirements

- Real `<a>` elements. `target="_blank"` and `rel="noopener noreferrer"`.
- A small external-link glyph after each title, `aria-hidden`, with the
  accessible name carrying "opens in a new tab" from a translated key.
- **Four cards spread the full container width.** Change the grid from five
  columns to four and let them fill — do not leave a fifth column's worth of
  empty space, and do not centre four cards in a five-column grid.
- Card padding follows the global token (`22px 24px`), gap `20px`.
- Hover: the same treatment the current five cards use. Do not invent a new one.
- The component is used in more than one place. Change it once; verify it on
  every page that renders it.

## D3. One thing to decide

The section is headed **"Standards, benchmarks & open data compliance"**, and
the outgoing list (NIST SP 800-92, OWASP ASVS) genuinely were compliance
references. The incoming list is closer to *sources and design references* —
MAHAONE's login page is a design reference, not a standard the product complies
with.

**Recommendation:** rename the section to **"References and design
benchmarks"** so the heading matches what sits under it. Claiming compliance
above a list that does not describe compliance is the kind of small overstatement
this project has avoided everywhere else.

If the team prefers to keep the heading, keep it — but make that a decision
rather than an oversight.

**Also note:** slide 6 of the SIH deck cites NIST SP 800-92 and OWASP ASVS in
its reference list. After this change the site and the deck cite different
sources. That is not wrong — a deck's bibliography and a site's reference strip
serve different purposes — but the team should know, in case a judge compares
them.

---

# PART E — Build order

Six commits. Each ends with `npm run build` green.

| # | Commit | Done when |
|---|---|---|
| 1 | Remove the decorative motif | No pattern on any authenticated page; component deleted if orphaned |
| 2 | Password visibility toggle | Works with mouse and keyboard, resets on mount, `aria-pressed` correct |
| 3 | References strip | Four cards, correct links, full width, heading decided |
| 4 | Pseudo-locale harness + the extraction audit | A written list of every untranslated string found, page by page |
| 5 | Extract everything found, all four languages | Walking the product in `zz` shows no plain text anywhere |
| 6 | Number routing through `num()` + the lint check | No `toLocaleString()` outside `format.js`; the check runs and passes |

Commit 4 produces a list, not a fix. Review it before commit 5 starts — the
list is the deliverable that proves the sweep was systematic rather than
sampled.

---

# PART F — Do not

1. Do not machine-translate at runtime or call a translation API.
2. Do not translate work descriptions, district names, member names, agency
   names, vendor names, work IDs, case IDs or hashes.
3. Do not render Devanagari or Gujarati numerals unless the team explicitly
   flips `USE_NATIVE_DIGITS`.
4. Do not build a sentence by concatenating translated fragments.
5. Do not ship the `zz` pseudo-locale to production.
6. Do not use an emoji as a temporary icon for the password toggle.
7. Do not centre four cards in a five-column grid.
8. Do not suppress the focus ring on the password toggle.
9. Do not replace the removed motif with a different decorative layer.
10. Do not weaken the C5 lint check to make it pass — tune the allowlist.

---

# PART G — Acceptance

Verify by doing, not by reading code.

1. `npm run build` passes; the Vercel deploy succeeds; `pytest` is still 645.
2. Sign in as each role. No diamond pattern on any dashboard, flat grounds
   throughout, no layout shift where the layer used to be.
3. On `/sign-in`, the eye toggle reveals and hides the password, works by
   keyboard alone, and is hidden again after a reload.
4. Switch to `zz` in development and walk all eleven page types plus their
   error and empty states. **Nothing renders without `»…«`.**
5. Switch to हिन्दी, then मराठी, then ગુજરાતી. Every heading, label, button,
   placeholder, chart axis, empty state and error message changes.
6. In Gujarati, confirm `BIDAR`, `BABURAM NISHAD`, `DISTRICT MAGISTRATE
   JALAUN`, every work description, every work ID and every case ID are
   unchanged.
7. In all four languages, every numeral is Latin, grouping is Indian, and the
   unit words are translated.
8. The references strip shows four cards filling the width; each opens the
   correct site in a new tab; each has an accessible name that says it opens in
   a new tab.
9. Zoom to 200% in Hindi on the case sheet and the district queue. No clipped
   matras, no overlap.
10. Tab through the sign-in page: language switcher → email → password → eye
    toggle → Sign in.

---

# PART H — Report

At the end, print:

1. Every file changed or deleted, and why.
2. The full list of untranslated strings the pseudo-locale audit found, grouped
   by page — this is the evidence the sweep was systematic.
3. Which §C3 digit option was implemented and the value of `USE_NATIVE_DIGITS`.
4. Which §D3 heading was chosen.
5. The §G results, item by item, including anything that failed.
6. Any decision this document did not settle.
