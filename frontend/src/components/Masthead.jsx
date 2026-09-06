import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LogoMark } from './Logo.jsx'
import { getToken } from '../api.js'
import { useAuth } from '../auth.jsx'
import { ROLE_HOME } from '../roles.js'

export default function Masthead() {
  const [scrolled, setScrolled] = useState(false)
  const { user } = useAuth()
  const token = getToken()

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > 200)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const dashboardTarget = user?.role ? (ROLE_HOME[user.role] ?? '/ministry') : '/ministry'

  return (
    <header
      className={`sticky top-0 z-40 w-full transition-colors duration-[180ms] ease-out ${
        scrolled
          ? 'h-[60px] bg-portal text-white shadow-card'
          : 'h-[88px] bg-paper text-ink border-b border-rule'
      }`}
    >
      <div className="mx-auto flex h-full max-w-[1240px] items-center justify-between px-6">
        {/* Brand identity */}
        <Link to="/" className="flex items-center gap-3 group focus:outline-none">
          <LogoMark
            size={scrolled ? 28 : 34}
            className={`transition-colors ${scrolled ? 'text-white' : 'text-navy'}`}
          />
          <div className="flex flex-col">
            <div className="flex items-baseline gap-2">
              <span
                className={`font-display font-semibold tracking-wide transition-all ${
                  scrolled ? 'text-lg text-white' : 'text-2xl text-navy'
                }`}
              >
                NIGRANI
              </span>
              <span
                className={`font-devanagari font-semibold text-saffron transition-all ${
                  scrolled ? 'text-sm' : 'text-base'
                }`}
              >
                निगरानी
              </span>
            </div>
            {!scrolled && (
              <span className="text-[12px] uppercase tracking-wider text-ink-secondary">
                MPLADS Oversight
              </span>
            )}
          </div>
        </Link>

        {/* Navigation links */}
        <nav aria-label="Main navigation" className="hidden md:flex items-center gap-6">
          <a
            href="#how-it-works"
            className={`text-body-secondary font-medium transition-colors hover:underline ${
              scrolled ? 'text-white/80 hover:text-white' : 'text-ink-secondary hover:text-ink'
            }`}
          >
            How it works
          </a>
          <a
            href="#the-finding"
            className={`text-body-secondary font-medium transition-colors hover:underline ${
              scrolled ? 'text-white/80 hover:text-white' : 'text-ink-secondary hover:text-ink'
            }`}
          >
            The finding
          </a>
          <Link
            to="/reports/data-gap"
            className={`text-body-secondary font-medium transition-colors hover:underline ${
              scrolled ? 'text-white/80 hover:text-white' : 'text-ink-secondary hover:text-ink'
            }`}
          >
            Data-gap report
          </Link>
          <a
            href="#about"
            className={`text-body-secondary font-medium transition-colors hover:underline ${
              scrolled ? 'text-white/80 hover:text-white' : 'text-ink-secondary hover:text-ink'
            }`}
          >
            About
          </a>
        </nav>

        {/* CTA Button */}
        <div className="flex items-center gap-3">
          {token ? (
            <Link
              to={dashboardTarget}
              className={`rounded px-4 py-2 text-body-secondary font-medium transition-all ${
                scrolled
                  ? 'bg-white text-portal hover:bg-portal-tint'
                  : 'bg-portal text-white hover:bg-portal-deep'
              }`}
            >
              Go to your dashboard
            </Link>
          ) : (
            <Link
              to="/sign-in"
              className={`rounded px-4 py-2 text-body-secondary font-medium transition-all ${
                scrolled
                  ? 'bg-white text-portal hover:bg-portal-tint'
                  : 'bg-portal text-white hover:bg-portal-deep'
              }`}
            >
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
