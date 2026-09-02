// Chart palette and geometry, in one place.
//
// WHY THESE ARE HEX LITERALS AND NOT TAILWIND CLASSES. Recharts draws SVG and
// takes its colours as `fill`/`stroke` attribute values, not as class names, so
// a utility class on a wrapper cannot reach a bar or an axis tick. These five
// values are therefore a SECOND copy of the brand palette, and the duplication
// is deliberate rather than accidental — but it is still a duplication, so it
// is confined to this file and nowhere else in the app spells a colour.
//
// They mirror `tailwind.config.js` exactly and must be changed with it. The
// palette has been locked since Stage 0, which is what makes a mirror safe
// enough to prefer over the alternatives (a CSS-variable indirection Tailwind
// is not emitting here, or a runtime getComputedStyle read on a probe element).
//
// RECHARTS' OWN PALETTE IS NEVER USED. Every Bar, Cell, axis and grid line in
// this app is passed an explicit colour from this file. CLAUDE.md names default
// chart palettes among the banned items, and the way that ban gets broken is
// not by choosing them — it is by omitting a `fill` and letting the library
// choose.
export const INK = '#14171A'
export const INK_SECONDARY = '#5B6169'
export const INK_MUTED = '#94989E'
export const BORDER = '#DDD9D0'
export const BORDER_STRONG = '#C7C2B6'
export const SURFACE = '#FFFFFF'
export const SURFACE_SUNK = '#F3F0EA'
export const NAVY = '#132A47'
export const GREEN = '#2E7D5B'
export const GOLD = '#C8952B'
export const CORAL = '#D4573D'

// Severity keeps the colours it carries everywhere else in the app: a HIGH bar
// and a HIGH row border are the same coral, so a reader who has learnt the
// scale on the case queue does not have to learn it again on a chart.
//
// Each series carries a LABEL, and the label is what the legend and the tooltip
// print. Colour is never the only signal on a chart here either.
export const SEVERITY_SERIES = [
  { key: 'high_cases', label: 'High', color: CORAL },
  { key: 'medium_cases', label: 'Medium', color: GOLD },
  { key: 'low_cases', label: 'Low', color: GREEN },
]

// Axis and grid styling, applied identically by every chart so two charts on
// one screen do not read as two design systems.
//
// 12px matches the meta-label and table-header token, which is the size every
// other piece of chart-adjacent structural text on the page uses. The tick
// colour is ink-secondary, never ink: an axis is structure, not data.
export const AXIS_TICK = { fill: INK_SECONDARY, fontSize: 12 }
export const AXIS_LINE = { stroke: BORDER_STRONG }

// One grid direction, not two. A horizontal ranked bar is read along its value
// axis, so only that axis gets grid lines; the crossing set would be chart junk
// separating category labels that are already separated by being on their own
// rows.
export const GRID = { stroke: BORDER, strokeDasharray: '2 4' }

// Row geometry for a horizontal ranked bar. 28px a row plus the axis band is
// what keeps a 10-row chart and a 3-row chart looking like the same object
// rather than one stretched and one squashed — the chart grows with its data
// instead of the bars growing to fill a fixed box.
export const ROW_HEIGHT = 28
export const AXIS_BAND = 48

export function chartHeight(rowCount) {
  return Math.max(rowCount, 1) * ROW_HEIGHT + AXIS_BAND
}
