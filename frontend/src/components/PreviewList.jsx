import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function PreviewList({ items = [], title, caption, className = '' }) {
  const { t } = useTranslation()
  const [activeIndex, setActiveIndex] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    if (activeIndex >= items.length && items.length > 0) {
      setActiveIndex(0)
    }
  }, [items.length, activeIndex])

  if (!items || items.length === 0) return null

  const activeItem = items[activeIndex] || items[0]

  function handleKeyDown(e, index) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      const next = (index + 1) % items.length
      setActiveIndex(next)
      document.getElementById(`preview-item-${items[next]?.id || next}`)?.focus()
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      const prev = (index - 1 + items.length) % items.length
      setActiveIndex(prev)
      document.getElementById(`preview-item-${items[prev]?.id || prev}`)?.focus()
    } else if (e.key === 'Enter') {
      if (items[index]?.href) {
        navigate(items[index].href)
      }
    }
  }

  return (
    <div className={`rounded border border-rule bg-paper shadow-card ${className}`}>
      {title && (
        <div className="border-b border-rule px-card-x py-card-y">
          <h3 className="font-display text-[20px] font-semibold text-navy">{title}</h3>
          {caption && <p className="mt-1 text-[14px] text-ink-secondary">{caption}</p>}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 min-h-[320px]">
        {/* Left column: List of rows (5 cols) */}
        <div className="md:col-span-5 border-b md:border-b-0 md:border-r border-rule p-3 space-y-1 overflow-y-auto">
          {items.map((item, idx) => {
            const isActive = idx === activeIndex
            const itemId = `preview-item-${item.id || idx}`

            return (
              <Link
                key={item.id || idx}
                id={itemId}
                to={item.href || '#'}
                onMouseEnter={() => setActiveIndex(idx)}
                onFocus={() => setActiveIndex(idx)}
                onKeyDown={(e) => handleKeyDown(e, idx)}
                tabIndex={0}
                className={`group flex w-full cursor-pointer items-center justify-between rounded px-4 py-3 text-left transition-all duration-100 ${
                  isActive
                    ? 'bg-paper text-navy font-semibold shadow-card border border-rule-strong ring-1 ring-portal/10'
                    : 'text-ink-secondary hover:bg-portal-tint/60 hover:text-ink border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span
                    className={`text-sm transition-transform duration-100 ${
                      isActive ? 'text-saffron font-bold' : 'text-ink-muted'
                    }`}
                  >
                    →
                  </span>
                  <span className="text-[15px] truncate">{item.label}</span>
                </div>

                {item.badge && (
                  <span className="num ml-2 shrink-0 rounded bg-portal-tint px-2 py-0.5 text-[12px] font-medium text-portal">
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </div>

        {/* Right column: Swappable Preview panel with 160ms cross-fade (7 cols) */}
        <div className="md:col-span-7 flex flex-col justify-between py-card-y px-card-x bg-paper-sunk/40">
          <div
            key={activeItem.id || activeIndex}
            className="flex flex-col sm:flex-row gap-6 transition-opacity duration-[160ms] ease-out animate-fadeIn"
          >
            {/* Visual / image panel (42% width on desktop) */}
            {activeItem.image ? (
              <div className="w-full sm:w-[42%] shrink-0 h-44 rounded border border-rule overflow-hidden bg-portal-deep/5 flex items-center justify-center">
                <img
                  src={activeItem.image}
                  alt={activeItem.title || activeItem.label}
                  className="h-full w-full object-cover"
                />
              </div>
            ) : (
              <div className="w-full sm:w-[42%] shrink-0 h-44 rounded border border-rule bg-portal-tint/70 py-card-y px-card-x flex flex-col justify-between">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-portal">
                    {t('landing.previewRecord', 'Preview record')}
                  </span>
                  <p className="mt-1 font-display text-[18px] font-semibold text-navy line-clamp-2">
                    {activeItem.title || activeItem.label}
                  </p>
                </div>
                {activeItem.meta && (
                  <p className="num text-[12px] font-medium text-ink-secondary">
                    {activeItem.meta}
                  </p>
                )}
              </div>
            )}

            {/* Description details */}
            <div className="flex-1 flex flex-col justify-between min-h-[160px]">
              <div>
                <h4 className="font-display text-[20px] font-semibold text-navy leading-snug">
                  {activeItem.title || activeItem.label}
                </h4>
                {activeItem.meta && (
                  <p className="num mt-1 text-[12px] font-medium uppercase tracking-wider text-ink-secondary">
                    {activeItem.meta}
                  </p>
                )}
                <p className="mt-2 text-[14px] text-ink-secondary leading-relaxed line-clamp-4">
                  {activeItem.body || activeItem.description}
                </p>
              </div>

              {activeItem.href && (
                <div className="mt-4 pt-3 border-t border-rule/60">
                  <Link
                    to={activeItem.href}
                    className="inline-flex items-center justify-center rounded bg-portal px-4 py-2 text-[14px] font-medium text-white transition-colors hover:bg-portal-deep focus:outline-none"
                  >
                    {t('common.openRecord', 'Open record')}
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
