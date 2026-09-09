import { useTranslation } from 'react-i18next'
import { CARD } from '../ui.js'

export default function EmptyState({ title, children }) {
  return (
    <div className={`${CARD} p-6`}>
      <p className="text-body font-medium text-ink">{title}</p>
      {children ? <p className="mt-1 text-body-secondary text-ink-secondary">{children}</p> : null}
    </div>
  )
}

export function ErrorState({ error, children }) {
  const { t } = useTranslation()
  const status = typeof error === 'object' && error !== null ? error.status : undefined
  const message = typeof error === 'object' && error !== null ? error.message : error

  const headlineMap = {
    0: t('errors.network', 'Could not reach the API'),
    403: t('errors.forbidden', 'Your role cannot open this view'),
    404: t('errors.notFoundScope', 'Not found, or not within your scope'),
  }

  return (
    <div className={`${CARD} p-6`} role="alert">
      <p className="font-medium text-coral">
        {headlineMap[status] ?? t('errors.fallback', 'Could not load this from the API')}
      </p>
      <p className="mt-1 text-body-secondary text-ink-secondary">{message}</p>
      {status === 404 ? (
        <p className="mt-2 text-body-secondary text-ink-secondary">
          {t('errors.scopeExplanation', 'The API answers a case id outside your scope exactly as it answers one that was never issued. That is deliberate: telling the two apart would confirm that another district’s case exists.')}
        </p>
      ) : null}
      {children ? <p className="mt-2 text-body-secondary text-ink-secondary">{children}</p> : null}
    </div>
  )
}
