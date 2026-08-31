// Single fetch wrapper. Every network call in the app goes through apiFetch(),
// so the bearer token is attached in exactly one place and there is no second
// place for a request to forget it.
//
// THE MOCK PATH IS GONE. The inherited version could serve
// docs/contract/case_detail.json from disk when the API was down, which made
// sense when there was one frozen fixture and no engine behind it. There is a
// backend now, with 27,079 derived cases, an authenticated session and
// server-side role scoping — and a fixture cannot have a role. A screen that
// silently fell back to the frozen case would show a District Authority a case
// from another district, which is precisely the failure invariant 10 exists to
// prevent. An outage should look like an outage.

// The base URL, overridable. The inherited version hardcoded
// http://localhost:8000 with no way to point it anywhere else, which was noted
// as a defect: the same build has to be able to reach a laptop during
// development and something else during a demo, and editing a source file to
// move it is not a configuration mechanism.
//
// Vite inlines import.meta.env at build time, so this is a build-time choice
// and not a runtime one. Set VITE_API_BASE in the environment or in a .env
// file; the fallback is the port `uvicorn app.main:app --port 8000` listens on,
// which is what the commands block in the project instructions tells you to run.
export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

// ---------------------------------------------------------------------------
// The token
// ---------------------------------------------------------------------------

// sessionStorage, and the choice is deliberate in both directions.
//
// NOT in-memory React state. A token that lives only in a component tree dies
// on reload, and reload is a thing this app has to survive for a reason beyond
// convenience: the scoping walkthrough works by TYPING A CASE ID INTO THE
// ADDRESS BAR to prove that another district's case comes back 404. If the
// address bar logs you out, the thing being demonstrated is unreachable, and
// every officer who refreshes a case sheet is thrown back to the door.
//
// NOT localStorage. localStorage outlives the tab, and this is a tool an
// officer opens on a shared district machine. The next person to open the
// browser would be signed in as the District Magistrate without ever seeing a
// password. sessionStorage is scoped to the tab and cleared when it closes,
// which is the session length this product actually wants.
//
// WHAT THIS IS NOT, stated rather than glossed: a bearer token in
// sessionStorage is readable by any script running on this origin, so it is
// not a defence against XSS the way an httpOnly cookie would be. The server
// issues a bearer token and this phase does not touch the backend, so that
// remains true and is declared. It sits alongside the limitations the login
// already carries — twelve-hour expiry, no refresh flow, no revocation list.
const TOKEN_KEY = 'nigrani.token'

// A private-mode browser can throw on sessionStorage access rather than merely
// returning null. A storage failure is not a reason for the whole app to fail
// to render, so every access is guarded and a failure reads as "no session".
export function getToken() {
  try {
    return window.sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    window.sessionStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Nothing to do: the session then lasts as long as the page does, which is
    // a worse experience and not a broken one.
  }
}

export function clearToken() {
  try {
    window.sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    // As above.
  }
}

// ---------------------------------------------------------------------------
// 401 handling
// ---------------------------------------------------------------------------

// api.js is not inside the React tree and cannot navigate. Rather than reach
// for the router from here, it publishes the event and lets the provider that
// owns the session decide — which keeps "the token stopped working" a single
// fact with a single reaction, instead of every page writing its own redirect.
let onSessionEnded = null

export function subscribeSessionEnded(handler) {
  onSessionEnded = handler
  return () => {
    onSessionEnded = null
  }
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

// The status travels with the error, because the three the API uses mean
// genuinely different things and a screen has to be able to tell them apart:
//
//   401  the session is over — token missing, expired, or the account is gone
//   403  this ROLE cannot ask this question at all (a wrong grain)
//   404  the row is not in this role's scope, OR it does not exist — and the
//        API refuses to say which, on purpose. A 403 here would confirm that
//        another district's case id is real, which is a scoping leak spelled
//        with a status code.
//
// The message is the server's own `detail` wherever there is one. Those
// sentences were written to be read by an officer ("This endpoint is
// restricted to ministry. Your role is district_authority."), and replacing
// them with a generic string here would throw away the better message.
export class ApiError extends Error {
  constructor(status, message, path) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.path = path
  }
}

async function detailOf(response) {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
    // 422 from Pydantic is a list of field errors rather than a sentence.
    if (Array.isArray(body?.detail)) {
      return body.detail.map((item) => item.msg ?? String(item)).join('; ')
    }
  } catch {
    // A non-JSON body — a proxy error page, or a connection cut mid-response.
  }
  return `${response.status} ${response.statusText}`.trim()
}

export async function apiFetch(path, options = {}) {
  const token = getToken()

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        // Attached to every request without exception. `/health` does not need
        // it and does not mind it; everything under /api requires it.
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })
  } catch (cause) {
    // fetch rejects only on a network-level failure, which here almost always
    // means uvicorn is not running. Say that, rather than "Failed to fetch" —
    // it is the single most likely thing to be wrong during a demo and the
    // browser's own wording does not point at it.
    throw new ApiError(
      0,
      `Could not reach the API at ${API_BASE}. Is the backend running?`,
      path,
    )
  }

  if (response.status === 401) {
    // The session is over however it got here. Clear it before notifying, so
    // whatever the handler does next cannot re-send the dead token.
    clearToken()
    const detail = await detailOf(response)
    if (onSessionEnded) onSessionEnded(detail)
    throw new ApiError(401, detail, path)
  }

  if (!response.ok) {
    throw new ApiError(response.status, await detailOf(response), path)
  }

  // 204 has no body. Nothing in the API returns one today, and a JSON parse of
  // an empty body throws a SyntaxError that would surface as a mysterious
  // failure rather than as a successful write.
  if (response.status === 204) return null

  return response.json()
}

// A POST with a JSON body. Written once here because every write in the app —
// login, a note, a recompute — needs the same three lines, and one of them
// (stringify) is easy to leave out in a way that fails as a 422 rather than as
// an obvious mistake.
export function apiPost(path, body) {
  return apiFetch(path, {
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}
