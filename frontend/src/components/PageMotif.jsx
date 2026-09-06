import { LogoMark } from './Logo.jsx'

// Background geometric motif layer (Layer A, §9).
// Renders at 4% opacity with a top fade mask.
const OPACITY = 0.04
const OPACITY_MARK = 0.035
const FADE = 'linear-gradient(to bottom, transparent 0px, #000 240px)'

function Tiled({ id, width, height, children }) {
  return (
    <svg className="h-full w-full" aria-hidden="true">
      <defs>
        <pattern id={id} width={width} height={height} patternUnits="userSpaceOnUse">
          {children}
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
    </svg>
  )
}

// 1. Ministry: a sparse district-boundary lattice
const LATTICE = (
  <Tiled id="motif-lattice" width={120} height={120}>
    <path
      d="M0 60L60 0L120 60L60 120Z M0 0L120 120 M120 0L0 120"
      stroke="currentColor"
      strokeWidth="1"
      strokeDasharray="2 4"
    />
    <circle cx="60" cy="60" r="3" fill="currentColor" />
  </Tiled>
)

// 2. State: stacked horizontal rules, like a register
const REGISTER = (
  <Tiled id="motif-register" width={160} height={32}>
    <path d="M0 31.5H160" stroke="currentColor" strokeWidth="1" />
    <path d="M0.5 0V32" stroke="currentColor" strokeWidth="1" />
  </Tiled>
)

// 3. District: the four-node ladder chain, repeated
const CHAIN = (
  <Tiled id="motif-chain" width={200} height={64}>
    <path d="M18.5 32H69.5M74.5 32H125.5M130.5 32H181.5" stroke="currentColor" strokeWidth="1" />
    <rect x="13.5" y="29.5" width="5" height="5" fill="currentColor" />
    <rect x="69.5" y="29.5" width="5" height="5" fill="currentColor" />
    <rect x="125.5" y="29.5" width="5" height="5" fill="currentColor" />
    <rect x="181.5" y="29.5" width="5" height="5" fill="currentColor" />
  </Tiled>
)

// 4. Member: a rupee-column grid
const RUPEE_GRID = (
  <Tiled id="motif-rupee" width={96} height={64}>
    <path d="M0 32H96 M48 0V64" stroke="currentColor" strokeWidth="1" strokeDasharray="1 3" />
    <text
      x="24"
      y="24"
      fontSize="12"
      fill="currentColor"
      fontFamily="sans-serif"
      textAnchor="middle"
    >
      ₹
    </text>
    <text
      x="72"
      y="56"
      fontSize="12"
      fill="currentColor"
      fontFamily="sans-serif"
      textAnchor="middle"
    >
      ₹
    </text>
  </Tiled>
)

// 5. Case sheet: the stepped ladder from the logo
const STEPPED_LADDER = (
  <Tiled id="motif-stepped" width={96} height={96}>
    <path d="M20 20H48V48H76V76" stroke="currentColor" strokeWidth="1.5" fill="none" />
    <rect x="20" y="80" width="56" height="2" fill="currentColor" />
  </Tiled>
)

// 6. Rulebook: ruled clause lines
const CLAUSES = (
  <Tiled id="motif-clauses" width={240} height={72}>
    <rect x="0" y="8" width="208" height="1" fill="currentColor" />
    <rect x="0" y="24" width="160" height="1" fill="currentColor" />
    <rect x="0" y="40" width="224" height="1" fill="currentColor" />
    <rect x="0" y="56" width="112" height="1" fill="currentColor" />
  </Tiled>
)

// 7. Alerts: a diagonal chevron field
const CHEVRON = (
  <Tiled id="motif-chevron" width={64} height={64}>
    <path d="M8 16L32 40L56 16" stroke="currentColor" strokeWidth="1.2" fill="none" />
    <path d="M8 40L32 64L56 40" stroke="currentColor" strokeWidth="1.2" fill="none" />
  </Tiled>
)

const VARIANTS = {
  ministry: LATTICE,
  state: REGISTER,
  district: CHAIN,
  mp: RUPEE_GRID,
  case: STEPPED_LADDER,
  rulebook: CLAUSES,
  alerts: CHEVRON,
  signin: (
    <div className="flex h-full w-full items-center justify-center">
      <LogoMark size={720} />
    </div>
  ),
}

export default function PageMotif({ variant }) {
  const motif = VARIANTS[variant] ?? VARIANTS.ministry
  const tiling = variant !== 'signin'

  return (
    <div
      aria-hidden="true"
      className="motif-layer pointer-events-none absolute inset-0 -z-10 overflow-hidden text-navy"
      style={{
        opacity: tiling ? OPACITY : OPACITY_MARK,
        maskImage: tiling ? FADE : undefined,
        WebkitMaskImage: tiling ? FADE : undefined,
      }}
    >
      {motif}
    </div>
  )
}
