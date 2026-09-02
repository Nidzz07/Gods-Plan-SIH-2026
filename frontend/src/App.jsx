import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout.jsx'
import District from './pages/District.jsx'
import Member from './pages/Member.jsx'
import Ministry from './pages/Ministry.jsx'
import NotFound from './pages/NotFound.jsx'
import SignIn from './pages/SignIn.jsx'
import StateNodal from './pages/StateNodal.jsx'
import { AUTH_LOADING, AUTH_SIGNED_IN, useAuth } from './auth.jsx'
import { ROLE_HOME } from './roles.js'

// The router. Role no longer lives here — it lives in the session, and the
// session lives in AuthProvider — so App is back to being what its name says.
//
// `/` is a redirect rather than a screen. Four roles have four landing routes
// and none of them is the index; a shared index would be one component
// guessing which of four dashboards it was, and that guess belongs to the
// router.
function Index() {
  const { status, user } = useAuth()
  if (status === AUTH_LOADING) return null
  if (status !== AUTH_SIGNED_IN || !user) return <Navigate to="/sign-in" replace />
  return <Navigate to={ROLE_HOME[user.role] ?? '/sign-in'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/sign-in" element={<SignIn />} />

      <Route element={<Layout />}>
        <Route index element={<Index />} />

        {/* Four landing routes, one per role. They are ordinary routes and not
            guarded ones: Layout redirects a role standing on another role's
            landing screen, and the endpoint behind each one refuses anyway. */}
        <Route path="ministry" element={<Ministry />} />
        <Route path="state" element={<StateNodal />} />
        <Route path="district" element={<District />} />
        <Route path="member" element={<Member />} />

        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
