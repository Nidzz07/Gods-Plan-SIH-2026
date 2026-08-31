import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { AUTH_LOADING, AUTH_SIGNED_IN, useAuth } from '../auth.jsx'
import { redirectFor } from '../roles.js'
import Sidebar from './Sidebar.jsx'
import TopBar from './TopBar.jsx'

// The shell, and the gate in front of it.
//
// Role used to be a prop threaded down from App, set by a picker at the door
// and by a dropdown in the top bar. It is read from the session now and
// nothing in the app writes it.
//
// THE FIRST REDIRECT IS NOT A PERMISSION CHECK EITHER, and it is worth being
// exact about why it is still here. Sending an unauthenticated visitor to the
// door protects nothing: every route below fetches from an API where each
// endpoint carries get_current_user, so a screen reached without a session
// renders errors rather than data. What this saves is the version of that
// where a person sees four failed panels instead of a login form.
export default function Layout() {
  const location = useLocation()
  const { status, user } = useAuth()

  // A reload arrives here with a token in sessionStorage and no identity yet.
  // Treating that as signed out would bounce an officer to the door on every
  // refresh, so it renders nothing for the one round trip /api/auth/me takes.
  // Nothing rather than a skeleton: the shell does not yet know which of four
  // dashboards it is about to draw, and a skeleton of the wrong screen is a
  // worse answer than a blank frame for 30ms.
  if (status === AUTH_LOADING) return null

  if (status !== AUTH_SIGNED_IN || !user) return <Navigate to="/sign-in" replace />

  // Second: a role standing on another role's landing screen goes to its own.
  // Reading it from the location on render rather than from an effect means
  // the wrong screen never paints for a frame first.
  const elsewhere = redirectFor(user.role, location.pathname)
  if (elsewhere) return <Navigate to={elsewhere} replace />

  return (
    <div className="flex min-h-screen">
      <Sidebar user={user} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar user={user} />

        {/* No padding here: the page's own header band needs to run edge to
            edge so its divider reads as a full-width rule. Each page pads its
            own header and content region instead.

            A column flex container so the page inside can take `flex-1` and
            fill the region even when its content is short. Without that, a
            page's motif layer — which is sized to the page element — would
            stop dead partway down the screen and leave a visible edge where
            the texture ends. */}
        <main className="flex flex-1 flex-col">
          <Outlet context={{ user }} />
        </main>
      </div>
    </div>
  )
}
