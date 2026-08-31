import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { LogoMark } from '../components/Logo.jsx'
import PageMotif from '../components/PageMotif.jsx'
import { AUTH_LOADING, AUTH_SIGNED_IN, useAuth } from '../auth.jsx'
import { ROLE_HOME } from '../roles.js'
import { BUTTON_PRIMARY, CARD, FIELD, LABEL } from '../ui.js'

// The front door, and it is now a door.
//
// The inherited screen offered three cards — Officer, Inspector, Auditor —
// with a line under them reading "No password required — this demo uses role
// selection, not authentication." That sentence was true then and would be a
// lie now, so it is gone rather than reworded. Phase 6 closed it: passwords
// are bcrypt digests, the session is a signed token, and the rows a token
// reaches are decided by a WHERE clause in the server's query.
//
// WHAT IS STILL DECLARED, in body text on this screen rather than in a
// footnote or a slide. The accounts are seeded by `python -m app.seed_users`.
// There is no registration, no password reset and no recovery, because an
// officer's district is granted to them rather than chosen by them. That is
// the honest description of a login that stands in for an identity provider,
// and it belongs where the login is.
//
// Register, deliberately: this reads like the landing page of an internal
// departmental tool — an emblem, the service name, what the corpus covers, and
// one form. No welcome, no reassurance, no floating card on an empty ground.

export default function SignIn() {
  const navigate = useNavigate()
  const { status, user, signIn, endedReason } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Somebody already signed in who navigates back to the door goes to their
  // own landing screen instead of being asked to sign in twice.
  if (status === AUTH_SIGNED_IN && user) {
    return <Navigate to={ROLE_HOME[user.role] ?? '/'} replace />
  }

  async function submit(event) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const identity = await signIn(email.trim(), password)
      // The landing route comes from the role the SERVER returned, never from
      // anything typed into this form. This is the one line where the whole
      // four-persona routing turns, and it turns on the response.
      navigate(ROLE_HOME[identity.role] ?? '/', { replace: true })
    } catch (failure) {
      // The server answers one 401 with one sentence for a wrong password, an
      // unknown address and a deactivated account alike — three
      // distinguishable messages would turn this form into a way of asking
      // which officers hold accounts. That sentence is shown as it arrived; a
      // friendlier client-side rewrite would be guessing at which of the three
      // it was, which is the guess the server refused to make.
      setError(failure.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="relative isolate flex min-h-screen flex-col">
      <PageMotif variant="signin" />

      <div className="mx-auto flex w-full max-w-xl flex-1 flex-col justify-center px-8 py-12">
        <div className="flex flex-col items-center">
          <LogoMark size={64} className="text-navy" />
          <h1 className="mt-4 font-display text-page-title tracking-wide text-navy">NIGRANI</h1>
          <p className="mt-2 text-center text-meta-label uppercase text-ink-secondary">
            MPLADS oversight · MoSPI · committed sample to 24 August 2026
          </p>
        </div>

        {/* A hairline, not a card edge: the header block and the form are two
            parts of one sheet, not two floating panels. */}
        <form onSubmit={submit} className="mt-8 border-t border-border pt-8">
          <p className={LABEL}>Sign in</p>

          {/* The session ended by itself rather than by a click — an expired
              token, or an account deactivated mid-session. Saying which is
              what makes it read as a system working rather than as a bug. */}
          {endedReason && !error ? (
            <div className={`${CARD} mt-2 border-l-4 border-l-gold p-4`}>
              <p className="text-body-secondary text-ink">{endedReason}</p>
            </div>
          ) : null}

          {error ? (
            // Coral on the heading, not on a left-border: the border accent
            // encodes a severity value on a data row, and a refused login has
            // no severity. Same shape as ErrorState so the two do not drift.
            <div className={`${CARD} mt-2 p-4`} role="alert">
              <p className="text-body-secondary font-medium text-coral">Could not sign in</p>
              <p className="mt-1 text-body-secondary text-ink-secondary">{error}</p>
            </div>
          ) : null}

          <div className="mt-4">
            <label htmlFor="email" className={LABEL}>
              Email address
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className={`${FIELD} w-full`}
            />
          </div>

          <div className="mt-4">
            <label htmlFor="password" className={LABEL}>
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={`${FIELD} w-full`}
            />
          </div>

          <button
            type="submit"
            disabled={submitting || status === AUTH_LOADING}
            className={`${BUTTON_PRIMARY} mt-6 w-full`}
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>

          {/* On the screen, at body-secondary size, not in a tooltip and not in
              the deck only. Same discipline as the memo caption on a case
              sheet: the limitation is stated where the thing is used. */}
          <p className="mt-4 text-body-secondary text-ink-secondary">
            Accounts are provisioned by the operator running{' '}
            <span className="font-medium text-ink">python -m app.seed_users</span>. There is no
            registration and no password reset — in a real deployment an officer&rsquo;s district is
            granted to them, not chosen by them.
          </p>
        </form>

        <p className="mt-8 border-t border-border pt-4 text-meta-label text-ink-secondary">
          A truncated sample of the MPLADS portal, not the national record. Demo build — not a
          system of record.
        </p>
      </div>
    </main>
  )
}
