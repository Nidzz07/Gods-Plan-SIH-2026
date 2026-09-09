import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function PageHero({
  title,
  lede,
  breadcrumbs = [],
  action = null,
  className = '',
}) {
  const { t } = useTranslation()

  return (
    <header className={`border-b border-rule bg-paper px-6 py-6 lg:px-8 ${className}`}>
      <div className="mx-auto max-w-[1240px]">
        {/* Breadcrumb (§7.2: Home › <Role home> › <Page>) */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav aria-label={t('nav.breadcrumb', 'Breadcrumb')} className="mb-3">
            <ol className="flex flex-wrap items-center gap-1.5 text-[14px] text-ink-secondary">
              {breadcrumbs.map((crumb, idx) => {
                const isLast = idx === breadcrumbs.length - 1
                return (
                  <li key={idx} className="flex items-center gap-1.5">
                    {idx > 0 && <span className="text-ink-muted">›</span>}
                    {isLast || !crumb.href ? (
                      <span className="font-medium text-ink truncate max-w-[240px]">
                        {crumb.label}
                      </span>
                    ) : (
                      <Link
                        to={crumb.href}
                        className="transition-colors hover:text-navy hover:underline truncate max-w-[200px]"
                      >
                        {crumb.label}
                      </Link>
                    )}
                  </li>
                )
              })}
            </ol>
          </nav>
        )}

        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div className="max-w-[72ch]">
            <h1 className="font-display text-section-title text-navy font-semibold leading-tight">
              {title}
            </h1>
            {/* 3px saffron rule, 72px wide */}
            <div className="mt-1.5 h-[3px] w-[72px] bg-saffron" aria-hidden="true" />

            {lede && (
              <p className="mt-3 text-lede text-ink-secondary font-normal leading-relaxed">
                {lede}
              </p>
            )}
          </div>

          {action && <div className="shrink-0">{action}</div>}
        </div>
      </div>
    </header>
  )
}
