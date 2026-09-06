import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import { ROLE_LABEL } from '../roles.js'
import { LogoMark } from './Logo.jsx'

export default function TopBar({ user, onOpenMobileNav }) {
  const navigate = useNavigate()
  const { signOut } = useAuth()

  function logout() {
    signOut()
    navigate('/sign-in', { replace: true })
  }

  return (
    <header className="sticky top-0 z-30 flex h-[60px] shrink-0 items-center justify-between gap-4 bg-portal px-6 text-white shadow-card">
      <div className="flex items-center gap-4 min-w-0">
        {/* Mobile menu toggle */}
        <button
          type="button"
          onClick={onOpenMobileNav}
          className="lg:hidden rounded border border-white/20 p-1.5 text-white hover:bg-white/10 focus:outline-none"
          aria-label="Open navigation menu"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Brand mark in portal header */}
        <div className="flex items-center gap-2">
          <LogoMark size={24} className="text-white" />
          <span className="font-display font-semibold tracking-wide text-white text-lg hidden sm:inline">
            NIGRANI
          </span>
          <span className="font-devanagari font-semibold text-saffron text-sm hidden sm:inline">
            निगरानी
          </span>
        </div>

        {/* Server scope sentence */}
        <div className="hidden md:block truncate border-l border-white/20 pl-4 text-[13px] text-[#C9D8E4]">
          {user.scope?.describes ? `Scope: ${user.scope.describes}` : 'Authenticated session'}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-4">
        <div className="text-right hidden sm:block">
          <span className="block text-[14px] font-medium text-white truncate max-w-[180px]">
            {user.display_name}
          </span>
          <span className="block text-[11px] uppercase tracking-wider text-[#C9D8E4]">
            {ROLE_LABEL[user.role] ?? user.role}
            {!user.can_write && ' · read-only'}
          </span>
        </div>

        <button
          type="button"
          onClick={logout}
          className="rounded border border-white/30 bg-transparent px-3 py-1.5 text-[13px] font-medium text-white transition-colors hover:border-white hover:bg-white/10"
        >
          Sign out
        </button>
      </div>
    </header>
  )
}
