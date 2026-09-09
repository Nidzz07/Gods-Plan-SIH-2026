# NIGRANI — Multilingual support, landing-page hero, and layout corrections

**Implementation brief for Antigravity — round two.**
Repository: `Gods-Plan-SIH-2026` · Frontend only: `frontend/` · Backend: do not touch.

This document assumes the previous brief (`NIGRANI-FRONTEND-PLAN.md`) has been
implemented and the app currently runs with a landing page at `/` and four
authenticated dashboards at `/ministry`, `/state`, `/district` and `/member`.

---

## 0. Rules of engagement

Unchanged from the previous brief, restated because they still bind:

1. **Never modify `backend/`.** `pytest` must stay at 645.
2. **Never invent a number.** Every figure on screen is fetched at runtime or
   read from `frontend/src/data/corpus-facts.js`.
3. **`npm run build` must pass after every commit.**
4. Commit messages must not name any assistant and must not contain the string
   `CLAUDE` — the repository has a literal grep check that this trips.
5. Severity colours stay semantic: coral = HIGH, gold = MEDIUM, green = LOW.
   Never decorative, anywhere, in any language.
6. One border radius (4px), one shadow depth, no gradients, no `rounded-full`,
   no emoji.

---

## 1. Three defects visible in the current build — fix these first

Found by reading the screenshots. Each is small and each is embarrassing on a
projector.

| # | Where | Symptom | Cause and fix |
|---|---|---|---|
| 1 | `/ministry` hero lede | Reads **"scored against rulebook vv1.0.0"** | The version string from the API already carries its `v` prefix and the template adds another. Print the value as returned; do not prepend. |
| 2 | `/district` hero lede | Reads **"under 1 implementing agencies"** | Hard-coded plural. Route every count-plus-noun through the i18n pluralisation rules built in Part A, never through string concatenation. |
| 3 | All four dashboards | The rail's `Sign out` button and the scope sentence are clipped at the left viewport edge | The rail has no horizontal gutter and its footer block is unconstrained. Fixed in Part C1. |

Do these as the first commit, before anything else, so the rest of the work is
built on a clean page.

---

# PART A — Multilingual support

## A1. Scope of the requirement

Four languages, selectable on the landing page and from every page afterwards.
The choice persists through sign-in and across every authenticated screen.

| Code | Language | Script | Font |
|---|---|---|---|
| `en` | English *(default)* | Latin | Inter |
| `hi` | हिन्दी (Hindi) | Devanagari | Noto Sans Devanagari |
| `mr` | मराठी (Marathi) | Devanagari | Noto Sans Devanagari |
| `gu` | ગુજરાતી (Gujarati) | Gujarati | Noto Sans Gujarati |

All four are left-to-right. No `dir="rtl"` handling is needed.

## A2. Stack

```bash
npm install i18next react-i18next
npm install @fontsource/noto-sans-devanagari @fontsource/noto-sans-gujarati
```

Do **not** add `i18next-browser-languagedetector`. Detection from the browser
would silently override a choice the user made deliberately on the landing
page, which is exactly the behaviour this feature must not have. Language comes
from one place only: the stored preference, defaulting to `en`.

Do **not** add a machine-translation service, a translation API, or any runtime
network call for text. Every string ships in the bundle.

## A3. File structure

```
frontend/src/i18n/
├── index.js                 i18next init, exported `i18n` instance
├── useLanguage.js           hook: { lang, setLang, languages }
├── LanguageSwitcher.jsx     the control, used in two places
└── locales/
    ├── en.json              the source of truth — write this first, in full
    ├── hi.json
    ├── mr.json
    └── gu.json
```

Each locale file uses the same nested key structure. Namespaces as top-level
keys, not separate files:

```json
{
  "common":   { "signIn": "Sign in", "signOut": "Sign out", ... },
  "utility":  { "skipToContent": "Skip to main content", ... },
  "landing":  { "title": "NIGRANI", "slogan": "National Project Monitoring System", ... },
  "roles":    { "ministry": "Ministry", "stateNodal": "State Nodal Authority", ... },
  "ministry": { ... },
  "state":    { ... },
  "district": { ... },
  "member":   { ... },
  "case":     { ... },
  "rulebook": { ... },
  "alerts":   { ... },
  "errors":   { ... }
}
```

**Write `en.json` completely first.** Extract every hard-coded string in
`frontend/src/` into it before translating anything. A missing key must fall
back to English, never to a blank or to the raw key — configure
`fallbackLng: 'en'` and `returnEmptyString: false`.

## A4. Persistence and the store

```js
// frontend/src/i18n/index.js
const STORAGE_KEY = 'nigrani.lang';
const SUPPORTED = ['en', 'hi', 'mr', 'gu'];

const stored = localStorage.getItem(STORAGE_KEY);
const initial = SUPPORTED.includes(stored) ? stored : 'en';
```

- Store in **`localStorage`**, not `sessionStorage`. A language preference is
  not a credential; it should survive a tab close. The JWT stays in
  `sessionStorage` exactly as it is — do not move it.
- On every language change: write to `localStorage`, call
  `i18n.changeLanguage(code)`, and set `document.documentElement.lang = code`.
- Setting `<html lang>` is not optional. Screen readers use it to choose a
  voice, and an English voice reading Devanagari is unusable.

Because the language lives outside React state, a full page reload preserves
it, and so does the redirect through `/sign-in`. Verify this explicitly: choose
Marathi on the landing page, sign in as District Authority, confirm the
dashboard renders in Marathi without a second selection.

## A5. What is translated, and what must never be

This is the most important section in Part A. Get it wrong and the product
stops matching the government record it is auditing.

**Translate — interface chrome, written by us:**
page titles, section headings, table column headers, button labels, form
labels, helper text, empty states, error messages, the utility strip, the
sidebar navigation, the scope sentence, tooltips, the memo template's
connective phrasing, rule labels and rule rationale text.

**Never translate — data, supplied by MoSPI:**

| Never translate | Why |
|---|---|
| State, district and constituency names | `JALAUN` is how the record is keyed; a translated name cannot be cross-checked against the portal |
| Member of Parliament names | Proper nouns |
| Implementing agency names | Proper nouns, and the canonicalisation ledger keys on the exact string |
| Vendor names | Proper nouns |
| Work descriptions | Verbatim text from the portal; the duplicate-detection similarity was computed on these exact strings |
| Work IDs (`WS/MP847/2025-2026/160261`) | Identifiers |
| Case IDs (`NG-094E347D96`) | Identifiers |
| Rulebook version strings, SHA-256 digests, audit hashes | Identifiers |
| Rule IDs (`utilisation_shortfall`) | Keys, not prose — but their **labels** are translated |

Put a comment at the top of each locale file stating this rule, so the next
person to add a string knows which side of the line it sits on.

**Severity words are translated, but the colour never changes.** `HIGH` renders
as `उच्च` in Hindi on the same coral ground. Colour is the constant across
languages; the word is the variable.

## A6. Numbers, currency and dates

```js
// frontend/src/i18n/format.js
const LOCALE = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN', gu: 'gu-IN' };

export const num = (v, lang) =>
  new Intl.NumberFormat(LOCALE[lang], { numberingSystem: 'latn' }).format(v);
```

**`numberingSystem: 'latn'` is mandatory.** Without it, `hi-IN` can render
Devanagari digits (२७,०७८) and `gu-IN` Gujarati digits. For an audit tool whose
entire purpose is letting an officer match a figure against a portal record
printed in Latin digits, that is a defect, not a feature. All four languages
show `27,078`.

All four locales use Indian digit grouping (lakh/crore), which is already
correct.

- Currency: keep the existing `₹ … cr` / `₹ … lakh` formatter. Translate only
  the unit words: `cr` → `करोड़` (hi) / `कोटी` (mr) / `કરોડ` (gu).
- Dates: `Intl.DateTimeFormat(LOCALE[lang], { dateStyle: 'medium' })`.
- Percentages: `Intl.NumberFormat` with `style: 'percent'`, `latn` digits.

## A7. Fonts

Load Devanagari and Gujarati faces alongside the existing ones in `main.jsx`:

```js
import '@fontsource/noto-sans-devanagari/400.css';
import '@fontsource/noto-sans-devanagari/600.css';
import '@fontsource/noto-sans-gujarati/400.css';
import '@fontsource/noto-sans-gujarati/600.css';
```

Extend the Tailwind font stack so the right face is picked automatically:

```js
fontFamily: {
  sans: ['Inter', 'Noto Sans Devanagari', 'Noto Sans Gujarati', 'system-ui', 'sans-serif'],
  display: ['Source Serif 4', 'Noto Sans Devanagari', 'Noto Sans Gujarati', 'Georgia', 'serif'],
}
```

**Devanagari and Gujarati need more line-height than Latin** — the matras sit
above and below the baseline and will collide at the current values. Add a
root-level rule:

```css
html[lang="hi"], html[lang="mr"], html[lang="gu"] {
  line-height: 1.65;
}
html[lang="hi"] .type-hero, html[lang="mr"] .type-hero, html[lang="gu"] .type-hero {
  line-height: 1.25;   /* the hero at 1.04 clips matras */
}
```

Check every heading after switching language. Clipped matras are the single
most common Indic-typography bug.

## A8. The switcher control

One component, `LanguageSwitcher.jsx`, rendered in two places with two
variants.

**Variant `compact`** — in the utility strip, on every page. An `अ / A` glyph
button that opens a dropdown listing the four languages, each written **in its
own script**, matching the india.gov.in pattern in the reference screenshots:

```
English
हिन्दी
मराठी
ગુજરાતી
```

Never list them in English (`Hindi`, `Marathi`) — a user who cannot read
English cannot find their language in an English list.

**Variant `prominent`** — on the landing page hero only. Four pill buttons in a
row, the active one filled, sitting directly above or beside the lookup bar so
it is impossible to miss on first load.

Both variants:
- Real `<button>` elements inside a listbox pattern, `aria-label` from the
  `utility.language` key.
- Current language marked `aria-current="true"`.
- Keyboard operable: arrows move, `Enter` selects, `Escape` closes.

## A9. Starter glossary

Use these as the seed for `hi.json`, `mr.json` and `gu.json`. They cover the
terms that repeat across every screen.

> **These translations must be reviewed by a native speaker before submission.**
> They are a working draft. Add a `"_reviewStatus": "draft — pending native
> review"` key at the top of each non-English locale file and remove it only
> once a person who speaks the language has read it. Do not present the deck or
> the demo claiming professionally translated content until that is done.

| English | हिन्दी (hi) | मराठी (mr) | ગુજરાતી (gu) |
|---|---|---|---|
| National Project Monitoring System | राष्ट्रीय परियोजना निगरानी प्रणाली | राष्ट्रीय प्रकल्प देखरेख प्रणाली | રાષ્ટ્રીય પરિયોજના દેખરેખ પ્રણાલી |
| Ministry of Statistics and Programme Implementation | सांख्यिकी और कार्यक्रम कार्यान्वयन मंत्रालय | सांख्यिकी आणि कार्यक्रम अंमलबजावणी मंत्रालय | આંકડા અને કાર્યક્રમ અમલીકરણ મંત્રાલય |
| Sign in | साइन इन करें | साइन इन करा | સાઇન ઇન કરો |
| Sign out | साइन आउट करें | साइन आउट करा | સાઇન આઉટ કરો |
| Search | खोजें | शोधा | શોધો |
| Home | मुख्य पृष्ठ | मुख्यपृष्ठ | મુખ્ય પૃષ્ઠ |
| Skip to main content | मुख्य सामग्री पर जाएँ | मुख्य मजकुराकडे जा | મુખ્ય સામગ્રી પર જાઓ |
| Contrast | कंट्रास्ट | कॉन्ट्रास्ट | કોન્ટ્રાસ્ટ |
| Language | भाषा | भाषा | ભાષા |
| Ministry | मंत्रालय | मंत्रालय | મંત્રાલય |
| State Nodal Authority | राज्य नोडल प्राधिकरण | राज्य नोडल प्राधिकरण | રાજ્ય નોડલ સત્તામંડળ |
| District Authority | जिला प्राधिकरण | जिल्हा प्राधिकरण | જિલ્લા સત્તામંડળ |
| Member of Parliament | संसद सदस्य | संसद सदस्य | સંસદ સભ્ય |
| Overview | अवलोकन | आढावा | ઝાંખી |
| National overview | राष्ट्रीय अवलोकन | राष्ट्रीय आढावा | રાષ્ટ્રીય ઝાંખી |
| District queue | जिला कार्य-सूची | जिल्हा कार्यसूची | જિલ્લા કાર્યસૂચિ |
| Works | कार्य | कामे | કામો |
| Cases | मामले | प्रकरणे | કેસ |
| Total cases | कुल मामले | एकूण प्रकरणे | કુલ કેસ |
| High risk | उच्च जोखिम | उच्च धोका | ઊંચું જોખમ |
| Medium risk | मध्यम जोखिम | मध्यम धोका | મધ્યમ જોખમ |
| Low risk | निम्न जोखिम | कमी धोका | નીચું જોખમ |
| Worst score | उच्चतम स्कोर | सर्वाधिक गुण | સૌથી ખરાબ સ્કોર |
| Sanctioned | स्वीकृत | मंजूर | મંજૂર |
| Disbursed | वितरित | वितरित | વિતરિત |
| Recommended | अनुशंसित | शिफारस केलेले | ભલામણ કરેલ |
| Signal coverage | संकेत आवरण | संकेत व्याप्ती | સિગ્નલ કવરેજ |
| Not published | प्रकाशित नहीं | प्रकाशित नाही | પ્રકાશિત નથી |
| Not applicable | लागू नहीं | लागू नाही | લાગુ નથી |
| Rulebook | नियम-पुस्तिका | नियमपुस्तिका | નિયમપુસ્તિકા |
| Alerts | चेतावनियाँ | सूचना | ચેતવણીઓ |
| Audit trail | लेखा-परीक्षा शृंखला | लेखापरीक्षण नोंद | ઓડિટ ટ્રેલ |
| Data-gap report | डेटा-अंतराल रिपोर्ट | डेटा-तफावत अहवाल | ડેટા-ગેપ અહેવાલ |
| Open record | रिकॉर्ड खोलें | नोंद उघडा | રેકોર્ડ ખોલો |
| Implementing agency | कार्यान्वयन एजेंसी | अंमलबजावणी संस्था | અમલીકરણ એજન્સી |
| Look up | खोजें | शोधा | શોધો |
| Crore | करोड़ | कोटी | કરોડ |
| Lakh | लाख | लाख | લાખ |

**Pluralisation.** i18next handles this per language; use it rather than
concatenating a count and a noun. This is what fixes defect #2:

```json
"district": {
  "agencyCount_one":   "{{count}} implementing agency",
  "agencyCount_other": "{{count}} implementing agencies"
}
```

Hindi, Marathi and Gujarati each need `_one` and `_other` forms. Do not assume
the English plural rule applies.

## A10. Acceptance for Part A

1. Landing page loads in English with no stored preference.
2. Choosing मराठी re-renders the landing page immediately, with no reload.
3. Sign in as District Authority; the dashboard is in Marathi without a second
   selection.
4. `document.documentElement.lang` is `mr`.
5. `JALAUN`, `BABURAM NISHAD`, `DISTRICT MAGISTRATE JALAUN`, work IDs and case
   IDs are unchanged in all four languages.
6. All numerals are Latin digits in all four languages.
7. No heading has clipped matras at any of the four languages.
8. Switching to a language, closing the tab and reopening restores it.
9. Removing a key from `hi.json` falls back to the English string, not to a
   blank and not to `landing.slogan`.

---

# PART B — Landing page

## B1. Hero background carousel

The hero band becomes a full-bleed photographic carousel behind white text,
matching the india.gov.in reference.

**Assets.** Five images supplied by the team at
`frontend/src/assets/hero/hero-1.jpg` … `hero-5.jpg`. Requirements to give the
team are in Part D. Record source and licence for each in
`frontend/src/assets/IMAGE-CREDITS.md`.

**Behaviour.**

| Property | Value |
|---|---|
| Transition | Horizontal slide, images move as one filmstrip on `translateX` |
| Interval | 3000 ms |
| Duration | 900 ms, `cubic-bezier(.4, 0, .2, 1)` |
| Loop | Infinite, wrapping 5 → 1 without a visible jump |
| Pause | On pointer hover **and** on keyboard focus anywhere in the hero |
| Controls | Five dot indicators, bottom-right of the hero, each a real `<button>` with `aria-label` naming the slide number |
| Reduced motion | `prefers-reduced-motion: reduce` → no auto-advance, show slide 1, dots still work |
| Preload | First image eager, the rest `loading="lazy"` |

Implement the filmstrip as a single flex row of five `<div>`s each 100% wide,
inside `overflow: hidden`, translated by `-index * 100%`. Do not cross-fade
stacked absolutely-positioned images — the requirement is a sideways slide.

**The scrim.** Over the filmstrip, a single solid overlay:

```css
background-color: rgba(7, 31, 54, 0.68);   /* portal-deep at 68% */
```

A solid `rgba` layer, **not** a gradient — gradients remain banned by the
project's own rules and a flat scrim gives more predictable contrast anyway.
Tune the alpha until white body text measures **at least 4.5:1** against the
lightest pixel of the lightest of the five images. If any image forces the
alpha above 0.75 to pass, that image is too bright — ask for a replacement
rather than darkening the whole hero.

`aria-hidden="true"` on the entire carousel. It is decoration; it must not
appear in the accessibility tree or the tab order except through the dots.

## B2. Text colour

Every text element inside the hero becomes white or near-white:

| Element | Colour |
|---|---|
| `NIGRANI` wordmark | `#FFFFFF` |
| `निगरानी` | `#F4B860` (a lighter saffron — the current `#E07A2F` fails on the scrim) |
| Saffron rule under the wordmark | `#F4B860`, 4px |
| Slogan / subheading | `#FFFFFF` |
| Attribution line | `#D6E2EC` |
| "Jump to:" label | `#D6E2EC` |
| Lookup bar | white fill, dark text inside — it is a control, not hero prose |

Check every one against the scrim. Nothing in the hero may sit below 4.5:1, and
the wordmark below 3:1.

## B3. Copy change

Replace the subheading. Current:

> AI-powered detection of anomalies, fraud and inefficiency in the MPLADS scheme.

New:

> **National Project Monitoring System**

Set it in Source Serif 4 600, white, at the `hero-sub` size stepped up per B4.
The i18n key is `landing.slogan` and it is translated in all four languages
using the glossary in A9.

Keep the existing italic line **"Every flag carries its evidence."** below the
lookup bar — it now does the job the old subheading was doing, and it is the
one piece of voice on the page.

Keep the attribution line unchanged.

## B4. Type scale for landscape

The screenshots show the page on a wide viewport with type sized for a much
narrower one. Move the landing page to fluid type so it fills the width
without breaking at 1280px.

```css
/* frontend/src/index.css */
.type-hero      { font-size: clamp(3.0rem, 5.2vw, 5.4rem); line-height: 1.04; }
.type-hero-sub  { font-size: clamp(1.5rem, 2.4vw, 2.4rem); line-height: 1.25; }
.type-attrib    { font-size: clamp(1.0rem, 1.2vw, 1.25rem); }
.type-stat      { font-size: clamp(2.2rem, 3.2vw, 3.4rem); line-height: 1.0; }
.type-stat-lbl  { font-size: clamp(0.9rem, 1.05vw, 1.1rem); }
.type-section   { font-size: clamp(1.9rem, 2.6vw, 2.6rem); }
.type-lede      { font-size: clamp(1.05rem, 1.35vw, 1.35rem); line-height: 1.6; }
.type-body-lg   { font-size: clamp(1.0rem, 1.15vw, 1.15rem); line-height: 1.6; }
```

Apply `.type-body-lg` to all landing-page body copy, card text and list items —
not just the headings. The instruction was that **all** text grows.

Increase the hero's vertical padding to match: `clamp(4rem, 7vw, 7.5rem)` top
and bottom. A taller hero is correct here; the carousel needs room to read as a
photograph rather than a stripe.

Body copy still caps at **72 characters** per line. On a wide viewport that
means the hero text column stays around 40% width — do not let the subheading
run the full 1240px, it becomes unreadable.

## B5. Buttons in the india.gov.in style

The reference's "Trending Searches" row is the model: solid white pills with a
thin border and dark text, clearly clickable against a photograph.

**Hero buttons — `Jump to:` chips and any hero CTA:**

```
background: #FFFFFF
color:      #0B2E4F          (portal)
border:     1px solid #FFFFFF
radius:     4px              (the one token — do NOT use a pill radius)
padding:    14px 22px
font:       Inter 600, 1.05rem
```

Hover: background `#0B2E4F`, text `#FFFFFF`, border stays white — a full fill
inversion, matching the pattern already used elsewhere in the app.
Focus-visible: 2px white outline, 2px offset.

The reference uses fully rounded pills. **We do not** — the project has a single
4px radius token and reintroducing a second radius for one row of buttons is
exactly the inconsistency the design system exists to prevent. Solid white with
a 4px radius reads as government and stays internally consistent.

**`Sign in` in the masthead** keeps its filled `portal` treatment. It is the
primary action and must not become another white chip.

## B6. Metrics strip — logo and reflow

Currently the six figures are centred with dead space at both ends. Add the
supplied Government of India / MoSPI emblem to the left and let the metrics
occupy the remaining width.

```
┌───────────────────────────────────────────────────────────────────────────┐
│  ┌──────────┐  │ 27,078 │ 1,18,704 │  12  │  638  │  31  │ ₹2,107.5 cr    │
│  │  emblem  │  │ works  │   rows   │portal│agenci-│states│ sanctioned in  │
│  │  + text  │  │ scored │ ingested │ sets │  es   │ & UTs│    sample      │
│  └──────────┘  │        │          │      │       │      │                │
└───────────────────────────────────────────────────────────────────────────┘
     ~18%                      metrics fill the remaining ~82%
```

- Strip height grows from 140px to **176px** to seat the emblem comfortably.
- Emblem at `frontend/src/assets/gov/mospi-emblem.png`, rendered at **96px**
  tall, `width: auto`, left-aligned inside the container's 24px padding.
- A 1px `rgba(255,255,255,.22)` vertical rule between the emblem and the first
  metric, matching the rules already between the figures.
- Metrics become a `flex: 1` row with `justify-content: space-between`; the
  first metric starts immediately after the divider. No centring.
- The caveat line — *"Measured on twelve published exports…"* — stays centred
  beneath the whole row, full width.
- Emblem needs `alt` text from the i18n key `landing.emblemAlt`, translated.

**One caution before you ship this.** The State Emblem of India is protected
under the State Emblem of India (Prohibition of Improper Use) Act, 2005, and
reproducing it can imply official endorsement the project does not have. This
is the team's call, not a build decision — but if there is any doubt, render
the MoSPI wordmark text alone without the lion capital, which carries the same
institutional weight and none of the risk. Flag this to the team rather than
deciding silently.

## B7. Acceptance for Part B

1. Five images cycle sideways every 3 seconds and loop cleanly 5 → 1.
2. Hovering the hero pauses the carousel; moving away resumes it.
3. `prefers-reduced-motion: reduce` stops the auto-advance entirely.
4. Every hero text element clears 4.5:1 against the brightest image.
5. The subheading reads *National Project Monitoring System* in all four
   languages.
6. At 1920px, 1440px and 1280px the hero fills the width without the
   subheading exceeding 72 characters per line.
7. The `Jump to:` chips are solid white with 4px corners and invert on hover.
8. The emblem sits left in the metrics strip; the six figures span the rest with
   no dead space at either end.
9. Tab order through the hero is: skip link → masthead nav → language →
   lookup → chips → carousel dots. The carousel images themselves are not
   focusable.

---

# PART C — The four authenticated pages

Applies identically to `/ministry`, `/state`, `/district` and `/member`.

## C1. The sidebar — the actual defect

In every screenshot the rail's content starts at `x ≈ 0`. `Explore`, the filter
field, the nav items, `SIGNED IN AS` and the `Sign out` button all sit flush
against the viewport edge, and `Sign out` is clipped.

Two causes, both fixed here.

**Cause 1 — no horizontal gutter.** The rail is positioned at the viewport edge
with no padding.

**Cause 2 — an unconstrained footer block.** The "signed in as" block is in
normal flow at the bottom of a `height: 100vh` container, so it overflows once
the nav list plus the footer exceed the viewport.

**The fix.** Make the rail a flex column with a fixed header, a scrolling
middle, and a pinned footer — and give the whole thing a real gutter.

```css
.app-shell {
  display: flex;
  gap: 32px;
  padding-inline: 28px;          /* the gutter that is currently missing */
  max-width: 1920px;
  margin-inline: auto;
}

.rail {
  flex: 0 0 288px;               /* was 264px */
  position: sticky;
  top: 96px;                     /* utility strip + sticky header */
  height: calc(100vh - 96px - 24px);
  display: flex;
  flex-direction: column;
  padding: 20px 18px 18px;       /* internal padding, on top of the gutter */
  border-right: 1px solid var(--rule);
  overscroll-behavior: contain;
}

.rail__head   { flex: 0 0 auto; }            /* "Explore" + filter field */
.rail__nav    { flex: 1 1 auto; overflow-y: auto; min-height: 0; }
.rail__footer { flex: 0 0 auto; padding-top: 16px; border-top: 1px solid var(--rule); }

.rail__footer .scope { overflow-wrap: anywhere; }   /* long scope sentences wrap */
.rail__footer button { width: 100%; }               /* Sign out fills the rail */

.app-main { flex: 1 1 auto; min-width: 0; }         /* min-width:0 lets tables shrink */
```

`min-height: 0` on `.rail__nav` and `min-width: 0` on `.app-main` are both
load-bearing — without them flex children refuse to shrink and the overflow
returns.

**Verify by doing:** scroll any dashboard to the bottom. The rail must not move
and `Sign out` must be fully visible with clear space to its left and below.

**Below 1024px** the rail becomes a slide-over drawer triggered by a hamburger
in the sticky header, with a focus trap and `Escape` to close. It must not
simply disappear.

## C2. Type scale for the dashboards

The instruction is that all text grows, including button text. Apply this as a
scale shift in the Tailwind config so every page inherits it — do not bump
individual components.

| Token | Was | Now |
|---|---|---|
| `page-title` | 30px | **38px** |
| `section-heading` | 22px | **26px** |
| `lede` | 19px | **21px** |
| `body` | 16px | **17px** |
| `body-secondary` | 14px | **15px** |
| `table-header` | 12px | **13px** |
| `table-cell` | 15px | **16px** |
| `meta-label` | 12px | **13px** |
| Stat card value | 34px | **42px** |
| Stat card label | 12px | **13px** |
| Button label | 14px | **16px** |

Button padding grows with the label: `12px 22px` for primary and secondary.
Minimum interactive target stays 44×44px.

Row heights follow: the working-queue row minimum goes from 56px to **64px**.

The heading-to-body ratio must stay at least 2.2:1 — at 38px title and 17px
body it is 2.24, which holds.

## C3. Wider tables

The screenshots show tables occupying roughly half the available width with
dead space to the right.

- Remove any `max-width` on the dashboard content column. With the rail at
  288px and a 28px gutter, the main column should occupy everything remaining
  up to the 1920px shell cap.
- Panels that currently sit side by side at 50/50 (for example *Agency
  concentration* beside *Working queue* on `/district`) become **34% / 66%**.
  The queue is the working surface and deserves the room.
- Inside the queue table, let the description column take the remaining width:
  give every other column an explicit width and set the description column to
  `width: auto`. Truncate at the cell with `text-overflow: ellipsis` and put
  the full string in a `title` attribute.
- The state and district league tables become full width of the main column.
- Numeric columns stay right-aligned with `tabular-nums`. Do not lose this when
  widening.
- Charts grow with the container: minimum height **420px** on the ministry and
  state charts, **360px** on the district agency chart.

## C4. Page-specific notes

**`/ministry`** — fix the doubled `v` (defect #1). The state league table goes
full width beneath the preview panel. The `Highest-risk state environments`
panel keeps its hover-preview behaviour.

**`/state`** — the district triage list and its preview card currently sit in a
narrow box inside a wider panel; let both expand to the full main-column width,
list at 38% and preview at 62%.

**`/district`** — fix the plural (defect #2). Rebalance to 34/66 as above. The
`ALL / HIGH / MEDIUM / LOW` filter chips are currently cramped and unreadable at
their size; give them the new 16px button label and 10px×16px padding, and
space them 8px apart.

**`/member`** — the account allocation ladder is the hero graphic and is
currently too small to read at a glance. Bar height goes from 14px to **22px**,
and the row label column widens so `ALLOCATED / SANCTIONED / DISBURSED` never
wrap. Keep the dashed "not published by MoSPI" treatment exactly as it is —
that is correct and it is the most important detail on the page.

## C5. Acceptance for Part C

1. On all four pages the rail has clear space at its left and the `Sign out`
   button is fully visible.
2. Scrolling the main column does not move the rail.
3. A rail with more nav items than fit scrolls internally without the footer
   leaving the viewport.
4. No dashboard shows more than 80px of unused horizontal space to the right of
   its widest table.
5. Body text is 17px and table cells 16px on every dashboard.
6. `/ministry` reads `rulebook v1.0.0`, once.
7. `/district` reads `1 implementing agency`, singular.
8. At 1024px the rail becomes a drawer; at 390px every page is usable and
   nothing overflows horizontally.

---

# PART D — Assets the team must supply

Blocked until these exist. Do not proceed with placeholder images committed to
the repository.

| Asset | Path | Spec |
|---|---|---|
| Hero images ×5 | `src/assets/hero/hero-1..5.jpg` | 2400×1200 minimum, landscape, JPEG q80, under 400 KB each after compression. Subject: MPLADS-funded public works — rural roads, community halls, school blocks, water tanks, street lighting. Not stock photos of people at laptops. Avoid images with a bright sky filling the upper half; they fight the white text. |
| GoI / MoSPI emblem | `src/assets/gov/mospi-emblem.png` | Transparent PNG, at least 300px tall, white or light artwork suitable for a navy ground. If the supplied file is dark-on-white, request a knockout version rather than inverting it in CSS. |
| Image credits | `src/assets/IMAGE-CREDITS.md` | Source URL, licence and date for every one of the six files. |

If a hero image's licence cannot be confirmed, drop to four images and adjust
the carousel length — an unlicensed photograph on a government-facing
submission is not worth the risk.

---

# PART E — Build order

Nine commits. Each ends with `npm run build` green.

| # | Commit | Done when |
|---|---|---|
| 1 | The three visible defects (§1) | Version prints once, plural is correct, rail is not clipped |
| 2 | i18n scaffolding + complete `en.json` | Every hard-coded string is extracted; app behaves identically in English |
| 3 | `hi` / `mr` / `gu` locale files + fonts + line-height rules | Switching language changes every chrome string; no clipped matras |
| 4 | `LanguageSwitcher`, both variants, persistence | Choice survives sign-in and a tab close |
| 5 | Number, currency and date formatting per locale | Latin digits everywhere; `cr` / `lakh` translated |
| 6 | Landing hero carousel + scrim + white text | Slides every 3s, pauses on hover, passes contrast |
| 7 | Landing type scale, button restyle, slogan change | Fills a 1920px viewport; chips are white with 4px corners |
| 8 | Metrics strip with emblem and reflow | Emblem left, metrics fill the rest, no dead space |
| 9 | Dashboard type scale, rail rebuild, wider tables | All of Part C's acceptance list passes |

---

# PART F — Do not

1. Do not machine-translate at runtime or call any translation API.
2. Do not translate district names, member names, agency names, vendor names,
   work descriptions, work IDs, case IDs or hashes.
3. Do not render Devanagari or Gujarati numerals.
4. Do not use a browser language detector to override a stored choice.
5. Do not introduce a second border radius for the hero buttons.
6. Do not use a gradient for the hero scrim — a flat `rgba` layer only.
7. Do not put the carousel images in the tab order.
8. Do not let the auto-advancing carousel run without a pause mechanism.
9. Do not fix the rail by adding `overflow: hidden` to a parent — that hides
   the symptom and will clip a dropdown later.
10. Do not lose `tabular-nums` or right-alignment on numeric columns when
    widening tables.
11. Do not commit placeholder or unlicensed images.
12. Do not claim in the deck or the demo that the translations are
    professionally reviewed until a native speaker has read them.

---

# PART G — Final acceptance

Verify each by doing it, not by reading the code.

1. `npm run build` passes; `pytest` is still 645.
2. Load `/` fresh with cleared storage. It is in English, the carousel is
   running, and the subheading reads *National Project Monitoring System*.
3. Switch to ગુજરાતી. The whole landing page changes. Sign in as Ministry. The
   dashboard is in Gujarati. Close the tab, reopen, it is still Gujarati.
4. In Gujarati, confirm `JALAUN`, `BABURAM NISHAD` and every work ID are
   unchanged, and every numeral is Latin.
5. Run the hero through a contrast checker on the brightest of the five images.
   No text fails.
6. Set `prefers-reduced-motion: reduce`. The carousel does not auto-advance.
7. On each of the four dashboards, scroll to the bottom. The rail has not
   moved and `Sign out` is fully visible.
8. Measure the widest table on each dashboard. Less than 80px of unused width
   to its right.
9. Tab through the landing page and one dashboard in each of the four
   languages. Focus is always visible and the order matches the visual order.
10. Zoom to 200% in Hindi. Nothing is clipped and no matra is cut.
