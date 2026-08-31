import { NavLink } from 'react-router-dom'

import { ROLE_NAV } from '../roles.js'
import { Logo } from './Logo.jsx'

// The nav is per role and lives in roles.js.
//
// Filtering here is wayfinding, not access control, and the reason that
// sentence survives the arrival of real auth is worth stating: a screen that
// is off this list is still reachable by typing its address. What has changed
// is what happens next — the API behind it applies the caller's predicate and
// answers 403 or 404, so an address typed into the bar now reaches a refusal
// rather than another district's rows. The sidebar is the menu; the query is
// the boundary.

function navClasses({ isActive }) {
  // Green edge bar plus a green-tinted ground. This is a navigation
  // active-state indicator, which is a different job from the severity
  // left-border on a data row: that one encodes a value, this one encodes
  // "you are here". Nothing else in the shell carries a left accent, so the
  // two never appear on the same screen competing for the same reading.
  const base = 'block border-l-4 py-2 pl-4 pr-4 text-body-secondary transition-colors'
  return isActive
    ? `${base} border-green bg-green/15 font-medium text-white`
    : `${base} border-transparent text-white/60 hover:border-white/20 hover:text-white`
}

export default function Sidebar({ user }) {
  return (
    <aside className="flex w-sidebar shrink-0 flex-col bg-navy">
      <div className="flex h-topbar items-center px-6">
        {/* Mark and wordmark together. The mark draws in currentColor, so on
            this navy ground it inherits the white the wordmark already used —
            the same drawing that renders navy on the sign-in screen's cream. */}
        <Logo className="text-white" />
      </div>

      <nav className="flex flex-col gap-1 py-4">
        {(ROLE_NAV[user.role] ?? []).map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={navClasses}>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* meta-label bakes its own 1.4 line-height, so leading-relaxed is gone
          rather than overriding half the token. The line names what the corpus
          actually is: a truncated download of the MPLADS portal, which is a
          declared limitation and therefore belongs on every screen rather than
          on one. */}
      <div className="mt-auto px-6 py-6 text-meta-label text-white/40">
        Truncated MPLADS portal sample.
        <br />
        Demo build — not a system of record.
      </div>
    </aside>
  )
}
