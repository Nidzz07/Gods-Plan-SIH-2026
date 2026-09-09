# NIGRANI — Spacing corrections, supplied icon assets, and the sign-in rebuild

**Implementation brief for Antigravity — round three.**
Repository: `Gods-Plan-SIH-2026` · Frontend only: `frontend/` · Backend: do not touch.

Assumes rounds one and two are built: the landing page, four authenticated
dashboards, the alert inbox, and four-language support are all live.

---

## 0. Rules of engagement

1. **Never modify `backend/`.** `pytest` stays at 645.
2. **Never invent a number.** Figures come from the API or from
   `frontend/src/data/corpus-facts.js`.
3. **`npm run build` must pass after every commit.**
4. Commit messages must not name any assistant and must not contain the string
   `CLAUDE` — the repository has a literal grep check that this trips.
5. Severity colours stay semantic: coral = HIGH, gold = MEDIUM, green = LOW.
6. One border radius (4px), one shadow depth, no gradients, no `rounded-full`.
7. **Every string added or changed in this round must be added to all four
   locale files** (`en`, `hi`, `mr`, `gu`). A new English string with no
   translation is a regression.
8. Do not break authentication. The sign-in form still posts to
   `POST /api/auth/login` and still stores the JWT in `sessionStorage`.

---

## 1. Assets the team will supply — exact paths

Create these directories and drop the supplied files in at these **exact
names**. Antigravity should reference these paths and must not rename them or
substitute placeholders.

### 1.1 Documentation tile icons — five files

Replace the five emoji currently rendered in the *Documentation & reference*
section of the landing page.

| Tile on screen | File path | What the icon should depict |
|---|---|---|
| Rulebook | `frontend/src/assets/icons/doc-rulebook.png` | a rule book / list of rules |
| Data profile | `frontend/src/assets/icons/doc-data-profile.png` | a chart or data sheet |
| Data-gap report | `frontend/src/assets/icons/doc-data-gap.png` | a report or clipboard |
| API reference | `frontend/src/assets/icons/doc-api.png` | code, a plug, or an endpoint |
| Audit trail | `frontend/src/assets/icons/doc-audit.png` | a lock, seal, or chain |

Spec: square PNG with a transparent background, at least **256×256**, single
consistent visual weight across all five. If the supplied set is inconsistent in
style, say so rather than shipping a mismatched row.

### 1.2 Filter-menu icon — one file

Replaces the emoji inside the sidebar's `Filter menu…` field on every
authenticated page.

```
frontend/src/assets/icons/ui-filter.png
```

Square PNG, transparent, at least **128×128**. It renders at 16px, so it must
be legible when very small — a simple magnifier or funnel silhouette, not a
detailed illustration.

### 1.3 Sign-in background video — one file, plus a poster

```
frontend/src/assets/video/signin-loop.mp4      ← the video
frontend/src/assets/video/signin-poster.jpg    ← first frame, for instant paint
```

Spec to give the team:

| Property | Requirement |
|---|---|
| Container / codec | MP4, H.264 |
| Resolution | 1920×1080 or higher, landscape |
| Duration | 12–25 seconds — long enough not to feel repetitive, short enough to load |
| Audio | **Remove the audio track entirely.** Not muted — removed. Smaller file, and no autoplay blocking. |
| File size | Under **10 MB** after compression. Above that, the first paint suffers on venue wifi. |
| Loop point | The last frame should be close to the first so the wrap is not a visible jump |
| Subject | MPLADS-relevant public works — construction, civic infrastructure, a district office. Slow camera movement only; fast cuts fight the form beside it. |
| Poster | A JPEG of frame 1, same dimensions, under 250 KB |

Optionally also supply `signin-loop.webm` (VP9) for a smaller transfer; if
present, list it first in the `<source>` order with the MP4 as fallback.

### 1.4 Credits

Add every file above to `frontend/src/assets/IMAGE-CREDITS.md` with its source,
licence and date. If a licence cannot be confirmed for the video, ship the
poster image as a static background instead — an unlicensed video on a
government-facing submission is not worth the risk.

---

## PART A — Landing hero: lookup bar and jump chips

**Problem.** The search field, the record-type dropdown and the `Look up`
button are welded together with no separation; the placeholder text touches the
field edge; and the three `Jump to` links sit inside one bordered strip with no
gaps, reading as a single object rather than three choices.

### A1. The lookup bar

Rebuild it as three separated controls on one row, sized for the landscape hero.

```
┌──────────────────────────────────────────────┐ ┌───────────────┐ ┌────────────┐
│  Search by Case ID, Work ID, District or MP  │ │ All records ▾ │ │  Look up   │
└──────────────────────────────────────────────┘ └───────────────┘ └────────────┘
        flex: 1, min-width 420px                     220px            160px
                          ← 12px gap →      ← 12px gap →
```

| Property | Value |
|---|---|
| Row width | `min(880px, 100%)` — currently far too narrow for the hero |
| Gap between the three controls | **12px** |
| Control height | **56px** (was ~34px) |
| Field padding | `0 20px` — the placeholder must never touch the border |
| Font size | `1.05rem` on all three, including the placeholder |
| Radius | 4px on all three (the single token) |
| Field fill | `#FFFFFF`, text `#14171A`, placeholder `#6B7280` |
| Dropdown | same white fill and height as the field, its own border, its own 4px radius — **not** fused to the field |
| `Look up` button | `portal` fill `#0B2E4F`, white text, 600 weight, `padding: 0 28px` |
| Button hover | fill lightens to `#134672`, 120ms |
| Focus-visible | 2px white outline, 2px offset, on each control independently |

Below the row, keep the italic line **"Every flag carries its evidence."** with
**20px** of clear space above it. In the current build it is crowded directly
under the bar.

### A2. The `Jump to` chips

Three independent buttons, not one bordered strip.

| Property | Value |
|---|---|
| Gap between chips | **16px** |
| Gap between the `Jump to:` label and the first chip | **20px** |
| Chip padding | `14px 26px` |
| Chip font | Inter 600, `1.05rem` |
| Chip fill | `#FFFFFF`, text `#0B2E4F`, 1px white border, 4px radius |
| Chip hover | fill inverts to `#0B2E4F`, text to `#FFFFFF`, border stays white, 120ms |
| Minimum target | 44px tall |

Remove the shared container border entirely. Each chip carries its own edge.

Space above the chip row: **32px** below the italic slogan line.

---

## PART B — Metrics strip

**Problem.** `₹2,107.5 cr` wraps, putting `cr` alone on a second line and
breaking the row's baseline. The block also sits high in the strip, and the
emblem has an unexplained gap before the first figure.

### B1. Stop the wrap

Three changes together — apply all three, not one:

```css
.metric__value {
  white-space: nowrap;                       /* the direct fix */
  font-size: clamp(2.0rem, 2.8vw, 3.0rem);   /* was capped too high */
}
.metric:last-child { flex-basis: 220px; }    /* the widest value needs the most room */
```

The last metric holds the longest string in every language — `₹2,107.5 cr`
becomes `₹2,107.5 करोड़` in Hindi and is longer still. Give it room now rather
than discovering it in Hindi on stage.

### B2. Vertical placement

The block currently hugs the top of the strip. Push it down.

```css
.metrics-strip { padding: 46px 0 30px; }   /* was roughly 28px / 28px */
```

Keep the horizontal distribution exactly as it is — the figures are correctly
spread and should not change. Only the vertical position moves.

The caveat line — *"Measured on twelve published exports…"* — keeps **20px**
of clear space above it and sits centred, full width, unchanged.

### B3. Emblem

- Height **88px**, `width: auto`, never distorted.
- Gap between the emblem and the divider rule: **28px**.
- Gap between the divider and the first metric: **28px**.
- If the supplied file renders muddy at 88px, it is too low-resolution — ask
  for a larger source rather than upscaling it.

---

## PART C — Documentation & reference tiles

Replace the five emoji with the supplied images from §1.1.

```jsx
<img
  src={docRulebook}
  alt=""                       // decorative; the tile's own label names it
  aria-hidden="true"
  className="doc-tile__icon"
/>
```

| Property | Value |
|---|---|
| Icon size | **40×40** |
| Space below the icon | 14px |
| Tile padding | `28px 20px` |
| Gap between tiles | **20px** |
| Tile title | 1.05rem, Inter 600, `navy` |
| Tile sub-line | 0.9rem, `ink-secondary`, 6px below the title |

Icons are decorative — `alt=""` and `aria-hidden="true"` — because the visible
label already carries the meaning. Do not write alt text that repeats the label;
a screen reader would read it twice.

Tile hover stays as built: fill to `portal`, label inverts to white.

---

## PART D — Alert inbox and sidebar

### D1. Sidebar filter field

Replace the emoji with the supplied `ui-filter.png` at **16×16**, positioned
inside the field on the left with **12px** from the field edge and **10px**
before the placeholder text. `aria-hidden="true"`.

### D2. Remove the duplicated scope line

Delete the scope sentence from the sidebar footer — the line currently reading
*"every work in the committed sample, unrestricted"*. It is already shown in the
sticky header beside the wordmark, and repeating it in a cramped rail is what
pushes the `Sign out` button down.

The footer block becomes exactly three elements:

```
SIGNED IN AS
MoSPI DIID Analyst (demo)
Ministry
[      Sign out      ]
```

Do not remove it from the header — that is the copy that belongs there.

### D3. Filter status chips

```css
.filter-status { display: flex; gap: 12px; align-items: center; }
.filter-status__label { margin-right: 8px; }
.filter-status button { padding: 10px 20px; font-size: 0.95rem; border-radius: 4px; }
```

Active chip: `portal` fill, white text. Inactive: white fill, `ink` text, 1px
`rule` border. Minimum target 44px tall.

### D4. Alert card spacing — the main fix here

Currently the cards touch each other and the text runs to the card edge.

```css
.alert-list { display: flex; flex-direction: column; gap: 16px; }

.alert-card {
  border: 1px solid var(--rule);
  border-left: 4px solid var(--severity);    /* the accent stays */
  border-radius: 4px;
  padding: 22px 26px 20px 26px;              /* 26px clear of the accent bar */
  background: #FFFFFF;
}
```

Internal rhythm, top to bottom:

| Element | Spacing |
|---|---|
| Work title | 1.1rem, Inter 600, `navy` |
| ↓ | 6px |
| Meta line (case ID · district · rule) | 0.85rem, `ink-secondary`, monospace only for the ID itself |
| ↓ | 14px |
| Body sentence | 1rem, `ink`, `max-width: 78ch` |
| ↓ | 18px |
| Action row (`Acknowledge`, `Escalate`) | buttons `padding: 10px 20px`, **12px** gap between them |

The right-hand block — score, severity word, status tag — gets its own
**24px** of padding from the card's right edge, and **20px** of clear space
between it and the body text so the two columns never collide.

**Nothing inside a card may sit closer than 20px to any card edge.** That is the
rule; the values above are one way of satisfying it.

---

## PART E — Sign-in page rebuild

Reference: the Maharashtra SSO screenshot. Split screen, media on the left,
form on the right, government chrome across the top.

### E1. Layout

```
┌───────────────────────────────────────────────────────────────────────┐
│  [ utility strip — language switcher, right-aligned ]                 │  56px
├────────────────────────────────────┬──────────────────────────────────┤
│                                    │                                  │
│                                    │        ┌──────────────┐          │
│         VIDEO, LOOPING             │        │   [ mark ]   │          │
│         full clarity               │        │              │          │
│                                    │        │   NIGRANI    │          │
│                                    │        │  National    │          │
│                                    │        │  Project     │          │
│   ┌────────────────────────┐       │        │  Monitoring  │          │
│   │ NIGRANI  निगरानी       │       │        │  System      │          │
│   │ ───────────────        │       │        │              │          │
│   │ National Project       │       │        │  Email       │          │
│   │ Monitoring System      │       │        │  [        ]  │          │
│   │ Ministry of Statistics │       │        │  Password    │          │
│   │ … · Government of India│       │        │  [        ]  │          │
│   └────────────────────────┘       │        │  [ Sign in ] │          │
│    ↑ scrim behind THIS ONLY        │        │  MoSPI · GoI │          │
│                                    │        └──────────────┘          │
├────────────────────────────────────┴──────────────────────────────────┤
│  [ footer strip ]                                                     │
└───────────────────────────────────────────────────────────────────────┘
         58%                                        42%
```

```css
.signin { display: grid; grid-template-columns: 58% 42%; min-height: 100vh; }
```

Below **1024px** the grid collapses to one column: the video becomes a 240px
band across the top and the form sits beneath it, full width.

### E2. The video — clarity is preserved

Two of the requirements pull against each other: the video should be
*translucent*, and its *clarity must not be reduced anywhere*. A global opacity
or a full-panel dark overlay satisfies the first and breaks the second.

**Resolution: the video plays at full opacity and full clarity. A scrim is
applied only behind the wordmark block in the lower-left, sized to that block
and nothing more.** Everywhere else the footage is untouched. This is what
makes the white text legible without dulling the video.

```jsx
<video
  className="signin__video"
  src={signinLoop}
  poster={signinPoster}
  autoPlay
  muted
  loop
  playsInline
  preload="auto"
  aria-hidden="true"
  tabIndex={-1}
/>
```

```css
.signin__media { position: relative; overflow: hidden; }
.signin__video {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  opacity: 1;                 /* full clarity — do not lower this */
  filter: none;               /* no blur, no brightness, no saturation change */
}
```

`muted` and `playsInline` are both mandatory — without them the browser blocks
autoplay and the panel shows a frozen poster.

**Reduced motion.** If `prefers-reduced-motion: reduce`, do not autoplay. Render
the poster image in the panel instead, and show a small play button so a user
who wants the video can start it.

> If the team decides they do want the whole video dimmed after all, the
> maximum is a flat `rgba(7,31,54,0.12)` overlay. Anything heavier and the
> footage stops being worth including.

### E3. The wordmark block over the video

Lower-left of the media panel, matching the landing page's treatment exactly.

```css
.signin__wordmark {
  position: absolute;
  left: 48px;
  bottom: 64px;
  max-width: 560px;
  padding: 28px 32px;
  background: rgba(7, 31, 54, 0.55);   /* the ONLY scrim on this panel */
  border-radius: 4px;
}
```

Contents, top to bottom — reuse the landing page components, do not rewrite them:

| Line | Treatment |
|---|---|
| `NIGRANI` + `निगरानी` | Source Serif 600, white / `#F4B860`, `clamp(2.4rem, 3.4vw, 3.4rem)` |
| Saffron rule beneath | `#F4B860`, 4px, 96px wide, 16px below |
| `National Project Monitoring System` | Source Serif 600, white, `clamp(1.3rem, 1.9vw, 1.8rem)`, 18px below the rule |
| `Ministry of Statistics and Programme Implementation · Government of India` | Inter 400, `#D6E2EC`, `1rem`, 8px below |

All four lines come from the existing i18n keys and translate with the rest of
the site. Verify the block does not overflow its panel in Hindi, Marathi or
Gujarati — the ministry name is longest in Gujarati.

### E4. The form card

**Remove entirely:**

- `MPLADS OVERSIGHT · MOSPI · COMMITTED SAMPLE TO 24 AUGUST 2026`
- The paragraph beginning *"Accounts are provisioned by the operator running
  `python -m app.seed_users`…"*
- The footer line *"A truncated sample of the MPLADS portal, not the national
  record. Demo build — not a system of record."*

Those belong in the README, not on a login screen a judge sees first.

**Add, and lay out in this order:**

| # | Element | Treatment | Space below |
|---|---|---|---|
| 1 | NIGRANI mark | 56px, centred | 20px |
| 2 | `NIGRANI` | Source Serif 600, 2.1rem, `navy`, centred | 8px |
| 3 | `National Project Monitoring System` | Inter 500, 1.05rem, `ink-secondary`, centred | 28px |
| 4 | Divider | 1px `rule`, full card width | 28px |
| 5 | `Email address` label + field | label 0.85rem `meta`; field 52px tall, `padding: 0 16px` | 20px |
| 6 | `Password` label + field | same | 28px |
| 7 | `Sign in` button | full width, 52px, `portal` fill, white, 1.05rem 600 | 24px |
| 8 | `Ministry of Statistics and Programme Implementation · Government of India` | Inter 400, 0.9rem, `ink-secondary`, centred, `line-height: 1.5` | — |

Card itself: white, 1px `rule` border, 4px radius, `padding: 44px 40px`,
`max-width: 440px`, centred in its column both horizontally and vertically.

Line 8 must wrap onto two lines cleanly, not three, and must not touch the card
edge — with a 440px card and 40px padding it has 360px, which is enough at
0.9rem. Check it in all four languages.

Error state on failed login: a coral-bordered strip above the email field, with
the message from the API and never the raw status code.

### E5. Utility strip on this page

The sign-in page currently has no top strip, so a user who wants to switch
language before logging in cannot. Add the standard utility strip, matching the
reference's `English / मराठी` control in the top-right. The skip link, text-size
and contrast controls come with it.

---

## PART F — Global card and control spacing

This applies to **every page in the app**, not only the screens above. It is the
"text should not touch the box" instruction, written as a system so it is
applied once rather than per component.

### F1. Tokens

Add to the Tailwind config and use these everywhere:

```js
spacing: {
  'card-x':   '26px',   // horizontal padding inside any card
  'card-y':   '22px',   // vertical padding inside any card
  'card-gap': '16px',   // between sibling cards in a list
  'grid-gap': '20px',   // between cards in a grid
  'stack-sm': '8px',    // title → meta
  'stack-md': '14px',   // meta → body
  'stack-lg': '20px',   // body → actions
  'btn-gap':  '12px',   // between adjacent buttons
}
```

### F2. Rules

1. **No text sits closer than 20px to any card, panel or field edge.**
2. **No two sibling cards touch.** Minimum 16px in a list, 20px in a grid.
3. **No two adjacent buttons touch.** Minimum 12px.
4. Every input has at least 16px of horizontal padding; a placeholder never
   sits against the border.
5. Every card follows the same internal rhythm: title → 8px → meta → 14px →
   body → 20px → actions.
6. Section heading to its first child: 24px. Section to section: 48px.
7. Minimum interactive target 44×44px, everywhere, including chips and icon
   buttons.
8. A card with a coloured left accent bar pads from the **inside edge of the
   bar**, not from the card border, so the text does not creep toward it.

### F3. Where to apply

Sweep these and correct each against F2: the four dashboards' stat cards, the
preview panels, the working queue rows, the case sheet's trace rows and badge
tiles, the rulebook table, the alert cards, the data-gap report table, the
landing page's authority cards and how-it-works grid, and every modal.

Report any component where satisfying F2 would break the layout, rather than
silently shrinking the text to make it fit.

---

## PART G — Build order

Eight commits. Each ends with `npm run build` green.

| # | Commit | Done when |
|---|---|---|
| 1 | Spacing tokens (F1) + the F2 rules applied to shared card components | The shared card, chip and field primitives all pass F2 |
| 2 | Landing lookup bar and jump chips (Part A) | Controls separated, 56px tall, chips independent |
| 3 | Metrics strip (Part B) | `₹2,107.5 cr` on one line in all four languages; block sits lower |
| 4 | Documentation tile icons (Part C) | Five supplied images render at 40px, consistent weight |
| 5 | Sidebar filter icon + scope line removal (D1, D2) | `Sign out` has clear space; no duplicated scope text |
| 6 | Alert inbox spacing (D3, D4) | Cards separated, nothing within 20px of an edge |
| 7 | Sign-in rebuild (Part E) | Split layout, video looping at full clarity, copy removed and added |
| 8 | F3 sweep across the remaining pages | Every listed component passes F2 |

If any supplied asset from §1 is missing when you reach its commit, **skip that
commit and continue** — do not commit a placeholder image or a stand-in emoji,
and report which asset is blocking.

---

## PART H — Do not

1. Do not lower the video's opacity or apply any `filter` to it.
2. Do not autoplay the video with an audio track, and do not rely on `muted`
   alone — the track should be absent from the file.
3. Do not put the video in the tab order or the accessibility tree.
4. Do not reintroduce the removed sign-in copy anywhere on that page.
5. Do not fuse the search field, dropdown and button back into one control.
6. Do not reduce a font size to solve an overflow — increase the container or
   allow the wrap, and report it.
7. Do not use `rounded-full` for the jump chips or the filter chips.
8. Do not add alt text to a decorative icon that repeats its visible label.
9. Do not add an English string without adding all four translations.
10. Do not change the horizontal distribution of the metrics strip — only its
    vertical position.
11. Do not solve card overflow with `overflow: hidden` on a parent; that hides
    the symptom and clips a dropdown later.

---

## PART I — Acceptance

Verify by doing, not by reading.

1. `npm run build` passes; `pytest` is still 645.
2. On the landing hero, the three lookup controls are visibly separate, 56px
   tall, and the placeholder is clear of the field border.
3. The three jump chips have 16px between them and each inverts independently
   on hover.
4. `₹2,107.5 cr` renders on one line — checked in English, Hindi, Marathi and
   Gujarati.
5. The metrics block sits visibly lower in the strip than before, with the
   emblem 88px tall and evenly gapped.
6. The five documentation tiles show the supplied images, all at the same
   visual weight.
7. The sidebar's `Filter menu…` field shows the supplied icon; the scope
   sentence is gone; `Sign out` has clear space beneath it.
8. Alert cards have 16px between them and no text within 20px of any edge.
9. `/sign-in` shows the video looping on the left at full clarity, with the
   wordmark block legible over it in the lower-left.
10. The sign-in card sits in the right column; the removed lines are gone; the
    ministry line beneath the button wraps to two lines without touching the
    card edge.
11. Switch to Gujarati on `/sign-in`. The wordmark block and the ministry line
    still fit.
12. With `prefers-reduced-motion: reduce`, the video does not autoplay and the
    poster is shown with a play control.
13. Sign in successfully as all four roles. Authentication still works.
14. Walk every page and look for any text touching a border or any two cards
    touching. There should be none.
