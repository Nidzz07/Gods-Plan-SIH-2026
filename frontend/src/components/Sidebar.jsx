import { useMemo, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ROLE_LABEL, ROLE_NAV_CONFIG } from '../roles.js'
import { useAuth } from '../auth.jsx'
import { useApi } from '../hooks/useApi.js'

export default function Sidebar({ user, isOpen, onClose }) {
  const { t } = useTranslation()
  const [filterQuery, setFilterQuery] = useState('')
  const { signOut } = useAuth()
  const navigate = useNavigate()

  // Fetch alerts count for badge if available
  const alertsApi = useApi(user ? '/api/alerts?status=open&limit=1' : null)
  const openAlertsCount = alertsApi.data?.total ?? null

  const config = ROLE_NAV_CONFIG[user?.role] ?? { primary: [], secondary: [] }

  const filteredPrimary = useMemo(() => {
    if (!filterQuery.trim()) return config.primary
    const q = filterQuery.toLowerCase()
    return config.primary.filter((item) => item.label.toLowerCase().includes(q))
  }, [config.primary, filterQuery])

  const filteredSecondary = useMemo(() => {
    if (!filterQuery.trim()) return config.secondary
    const q = filterQuery.toLowerCase()
    return config.secondary.filter((item) => item.label.toLowerCase().includes(q))
  }, [config.secondary, filterQuery])

  function handleSignOut() {
    signOut()
    navigate('/sign-in', { replace: true })
  }

  function navClass({ isActive }) {
    const base =
      'flex items-center justify-between px-3.5 py-2.5 text-[15px] transition-colors duration-100 rounded border-l-[3px]'
    return isActive
      ? `${base} border-portal bg-portal-tint text-navy font-semibold`
      : `${base} border-transparent text-ink-secondary hover:bg-portal-tint/50 hover:text-ink`
  }

  const headerContent = (
    <div className="rail__head">
      {/* Explore Heading with Saffron rule */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-[24px] font-semibold text-navy">
            {t('common.explore', 'Explore')}
          </h2>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="lg:hidden rounded p-1 text-ink-secondary hover:bg-portal-tint"
              aria-label="Close sidebar"
            >
              ✕
            </button>
          )}
        </div>
        <div className="mt-1 h-[3px] w-12 bg-saffron" aria-hidden="true" />
      </div>

      {/* Client-side filter */}
      <div className="mb-4">
        <div className="relative">
          <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-ink-secondary text-xs">
            🔍
          </span>
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder={t('common.filterMenu', 'Filter menu…')}
            aria-label="Filter navigation items"
            className="w-full rounded border border-rule bg-paper py-2 pl-8 pr-3 text-[14px] text-ink placeholder-ink-muted focus:border-portal focus:outline-none"
          />
        </div>
      </div>
    </div>
  )

  const navContent = (
    <div className="rail__nav">
      {/* Primary nav items */}
      <nav aria-label="Primary navigation" className="space-y-1">
        {filteredPrimary.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onClose}
            className={navClass}
          >
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Divider */}
      {filteredSecondary.length > 0 && (
        <div className="my-3 border-t border-rule" aria-hidden="true" />
      )}

      {/* Secondary nav items */}
      <nav aria-label="System navigation" className="space-y-1">
        {filteredSecondary.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onClose}
            className={navClass}
          >
            <span>{item.label}</span>
            {item.showBadge && openAlertsCount !== null && openAlertsCount > 0 && (
              <span className="num ml-2 rounded bg-gold px-1.5 py-0.5 text-[12px] font-semibold text-white">
                {openAlertsCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  )

  const footerContent = (
    <div className="rail__footer">
      <p className="text-[12px] font-medium uppercase tracking-wider text-ink-muted">
        {t('common.signedInAs', 'Signed in as')}
      </p>
      <p className="mt-1 font-semibold text-navy text-[15px] truncate">
        {user?.display_name ?? 'Officer'}
      </p>
      <p className="text-[13px] text-ink-secondary truncate">
        {ROLE_LABEL[user?.role] ?? user?.role}
      </p>
      {user?.scope?.describes && (
        <p className="scope mt-1 text-[12px] text-ink-muted leading-tight">
          {user.scope.describes}
        </p>
      )}
      <button
        type="button"
        onClick={handleSignOut}
        className="mt-3 w-full rounded border border-rule bg-paper py-2 text-center text-[14px] font-medium text-ink transition-colors hover:border-ink-secondary hover:bg-paper-sunk"
      >
        {t('common.signOut', 'Sign out')}
      </button>
    </div>
  )

  return (
    <>
      {/* Desktop fixed/sticky rail per §C1 */}
      <aside className="hidden lg:flex rail bg-paper shadow-card">
        {headerContent}
        {navContent}
        {footerContent}
      </aside>

      {/* Mobile drawer overlay (<1024px) */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-portal-deep/60 backdrop-blur-xs transition-opacity"
            onClick={onClose}
            aria-hidden="true"
          />
          <div className="relative flex w-[288px] max-w-[85vw] flex-1 flex-col bg-paper p-5 border-r border-rule shadow-card justify-between overflow-y-auto">
            <div>
              {headerContent}
              {navContent}
            </div>
            {footerContent}
          </div>
        </div>
      )}
    </>
  )
}
