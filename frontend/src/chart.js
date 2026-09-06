// Chart palette and geometry, in one place.
//
// WHY THESE ARE HEX LITERALS AND NOT TAILWIND CLASSES. Recharts draws SVG and
// takes its colours as `fill`/`stroke` attribute values, not as class names, so
// a utility class on a wrapper cannot reach a bar or an axis tick. These
// values are therefore a SECOND copy of the brand palette, and the duplication
// is deliberate rather than accidental — but it is still a duplication, so it
// is confined to this file and nowhere else in the app spells a colour.

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

// Institutional portal colors (§4.1)
export const PORTAL = '#0B2E4F'
export const PORTAL_DEEP = '#071F36'
export const PORTAL_TINT = '#E8EFF5'
export const SAFFRON = '#E07A2F'
export const PAPER = '#FFFFFF'
export const PAPER_SUNK = '#F4F6F8'

// Severity keeps the colours it carries everywhere else in the app: a HIGH bar
// and a HIGH row border are the same coral.
export const SEVERITY_SERIES = [
  { key: 'high_cases', label: 'High', color: CORAL },
  { key: 'medium_cases', label: 'Medium', color: GOLD },
  { key: 'low_cases', label: 'Low', color: GREEN },
]

export const AXIS_TICK = { fill: INK_SECONDARY, fontSize: 12 }
export const AXIS_LINE = { stroke: BORDER_STRONG }
export const GRID = { stroke: BORDER, strokeDasharray: '2 4' }

export const ROW_HEIGHT = 28
export const AXIS_BAND = 48

export function chartHeight(rowCount) {
  return Math.max(rowCount, 1) * ROW_HEIGHT + AXIS_BAND
}
