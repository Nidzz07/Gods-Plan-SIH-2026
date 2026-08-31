import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { apiFetch, apiPost, clearToken, getToken, setToken, subscribeSessionEnded } from './api.js'

// The session, owned in one place.
//
// This replaces the inherited project's `const [role, setRole] = useState(null)`
// in App.jsx, and the difference is the whole of Phase 6 arriving on the
// client. That role was a string the user picked from a list; nothing verified
// it, nothing stored it, and the API answered the same rows whichever value it
// held. What lives here instead is a signed token plus the identity block the
// SERVER returns for it.
//
// TWO RULES THIS PROVIDER KEEPS.
//
// The role is never chosen on the client. It arrives in `user.role` from
// POST /api/auth/login and is re-read from GET /api/auth/me on every reload.
// Nothing in the app writes it. That matters beyond tidiness: the backend
// reads the role from the users row rather than from the token's claims
// precisely so that a corrected scope takes effect on the next request, and a
// client that cached a role from twelve hours ago would undo that.
//
// The role is not a permission either, on this side. Every predicate that
// decides which rows exist is a WHERE clause in the server's query
// (invariant 10). What the client does with `user.role` is wayfinding — which
// links to draw, which screen to land on — and a person who edits it in the
// devtools gets a differently-shaped menu over exactly the same data.

const AuthContext = createContext(null)

// Three states, not a boolean. `loading` is the one an `isSignedIn` flag
// cannot express: on a reload there IS a token in sessionStorage but the
// identity behind it has not come back yet, and treating that moment as signed
// out bounces an officer to the door on every refresh.
export const AUTH_LOADING = 'loading'
export const AUTH_ANONYMOUS = 'anonymous'
export const AUTH_SIGNED_IN = 'signed-in'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(getToken() ? AUTH_LOADING : AUTH_ANONYMOUS)
  // Why the session ended, when it ended by itself rather than by a click. The
  // login screen prints it, because "you were signed out" with no reason
  // reads as a bug and "Token is invalid or has expired" reads as a system
  // working correctly.
  const [endedReason, setEndedReason] = useState(null)

  const signOut = useCallback((reason = null) => {
    clearToken()
    setUser(null)
    setEndedReason(reason)
    setStatus(AUTH_ANONYMOUS)
  }, [])

  // A 401 from ANY request in the app lands here. api.js has already cleared
  // the token by the time this runs, so there is no window in which a dead
  // token could be re-sent.
  useEffect(() => subscribeSessionEnded((detail) => signOut(detail)), [signOut])

  // On mount with a token in hand, ask the server who it belongs to. This is
  // what makes a reload keep the session: the token survives in sessionStorage
  // and the identity is fetched back rather than stored beside it. Storing the
  // identity too would let a stale role and a live token disagree.
  useEffect(() => {
    if (!getToken()) return undefined

    let live = true
    apiFetch('/api/auth/me')
      .then((me) => {
        if (!live) return
        setUser(me)
        setStatus(AUTH_SIGNED_IN)
      })
      .catch(() => {
        // A 401 has already been handled by the subscription above. Anything
        // else — the API being down, say — still leaves us without an
        // identity, and an app that cannot say who you are cannot scope a
        // screen, so it goes back to the door either way.
        if (live) signOut(null)
      })

    return () => {
      live = false
    }
  }, [signOut])

  // Returns nothing and throws nothing on a bad password: the login screen
  // needs to render the failure, not catch it. It resolves to the identity on
  // success and to an ApiError on failure, and the caller branches.
  const signIn = useCallback(async (email, password) => {
    const token = await apiPost('/api/auth/login', { email, password })
    setToken(token.access_token)
    // The login response carries the identity block with it, so the screen
    // that follows a login has the role and the scope in hand without a second
    // request. That is the server's design, not an optimisation invented here.
    setUser(token.user)
    setEndedReason(null)
    setStatus(AUTH_SIGNED_IN)
    return token.user
  }, [])

  const value = useMemo(
    () => ({ user, status, endedReason, signIn, signOut }),
    [user, status, endedReason, signIn, signOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside an AuthProvider')
  return context
}
