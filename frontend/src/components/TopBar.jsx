import { useNavigate } from 'react-router-dom'

import { useAuth } from '../auth.jsx'
import { ROLE_LABEL } from '../roles.js'
import { BUTTON } from '../ui.js'

// THE ROLE SWITCHER IS GONE, and its absence is the point of this file.
//
// What stood here was a <select> labelled "Viewing as", holding three roles,
// changeable by anyone looking at it. It was honest about itself — the comment
// said "this is a dropdown, not authentication" — and it was the right control
// for a build where the API answered the same rows whichever value it held.
//
// It would be a lie now. The role in this bar came back from the server for a
// token this browser holds, and it cannot be changed from here because
// changing it would mean nothing: every predicate that decides which rows
// exist is a WHERE clause the server applies before the response is built. A
// dropdown that appeared to switch role would be a control that either does
// nothing or, worse, looks like it did something.
//
// So the bar states rather than offers: who is signed in, what their role is,
// what that role reaches, and the one action that does change the session.
export default function TopBar({ user }) {
  const navigate = useNavigate()
  const { signOut } = useAuth()

  function logout() {
    signOut()
    navigate('/sign-in', { replace: true })
  }

  return (
    <header className="flex h-topbar shrink-0 items-center justify-between gap-4 border-b border-border bg-surface px-8">
      {/* The scope sentence is the SERVER's, from /api/auth/me. It is not
          assembled here from a state name and a district: `scope.describes` is
          written next to the predicate that enforces it, so the line on screen
          and the WHERE clause in the query cannot drift into describing two
          different things. */}
      <nav aria-label="Scope" className="min-w-0 truncate text-meta-label uppercase text-ink-secondary">
        Reaching {user.scope?.describes ?? 'an unknown scope'}
      </nav>

      <div className="flex shrink-0 items-center gap-4">
        <span className="text-right">
          <span className="block text-body-secondary font-medium text-ink">
            {user.display_name}
          </span>
          <span className="block text-meta-label uppercase text-ink-secondary">
            {ROLE_LABEL[user.role] ?? user.role}
            {/* The member of parliament is read-only everywhere — they can see
                a case and cannot annotate, escalate, resolve or recompute one.
                Saying so in the bar means the person knows before they click,
                rather than after a 403. */}
            {user.can_write ? null : ' · read-only'}
          </span>
        </span>

        <button type="button" onClick={logout} className={BUTTON}>
          Sign out
        </button>
      </div>
    </header>
  )
}
