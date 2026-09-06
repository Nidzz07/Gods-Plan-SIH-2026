import { useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { AUTH_LOADING, AUTH_SIGNED_IN, useAuth } from '../auth.jsx'
import { redirectFor } from '../roles.js'
import Sidebar from './Sidebar.jsx'
import TopBar from './TopBar.jsx'
import UtilityStrip from './UtilityStrip.jsx'
import Footer from './Footer.jsx'

export default function Layout() {
  const location = useLocation()
  const { status, user } = useAuth()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  if (status === AUTH_LOADING) return null

  if (status !== AUTH_SIGNED_IN || !user) return <Navigate to="/sign-in" replace />

  const elsewhere = redirectFor(user.role, location.pathname)
  if (elsewhere) return <Navigate to={elsewhere} replace />

  return (
    <div className="flex min-h-screen flex-col bg-paper">
      {/* 1. Global utility strip (top 36px, portal-deep) */}
      <UtilityStrip />

      {/* 2. Top Bar (60px sticky portal header) */}
      <TopBar user={user} onOpenMobileNav={() => setMobileNavOpen(true)} />

      {/* 3. Main structural body: app-shell with 28px gutter, max-width 1920px */}
      <div className="app-shell flex-1 w-full my-6">
        <Sidebar
          user={user}
          isOpen={mobileNavOpen}
          onClose={() => setMobileNavOpen(false)}
        />

        <div className="app-main flex flex-col justify-between">
          <main id="main" tabIndex={-1} className="flex flex-1 flex-col focus:outline-none">
            <Outlet context={{ user }} />
          </main>
        </div>
      </div>

      <Footer />
    </div>
  )
}
