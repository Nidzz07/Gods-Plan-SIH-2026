import { useState } from 'react'
import { Route, Routes } from 'react-router-dom'

import Layout from './components/Layout.jsx'
import NotFound from './pages/NotFound.jsx'
import SignIn from './pages/SignIn.jsx'

// The shell, mid-rebuild. The inherited project's five domain screens have
// been removed — they described shops, consignments and complaints, and none
// of that vocabulary survives the move to MPLADS — and NIGRANI's own screens
// arrive over the commits that follow this one. What is left standing is the
// part that DID port: the sign-in door, the layout chrome, and the design
// system underneath both.
//
// Everything under the layout therefore falls through to the 404 for now,
// which is a real screen with the app's own header band rather than a blank
// route, so the shell can still be walked end to end while it is empty.
export default function App() {
  const [role, setRole] = useState(null)

  return (
    <Routes>
      <Route path="/sign-in" element={<SignIn onSelect={setRole} />} />

      <Route element={<Layout role={role} onRoleChange={setRole} />}>
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
