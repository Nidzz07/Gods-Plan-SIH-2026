import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import PageHeader from '../components/PageHeader.jsx'
import { BUTTON, CARD } from '../ui.js'

export default function NotFound() {
  const { t } = useTranslation()

  return (
    <article className="flex-1">
      <PageHeader
        title={t('notFound.title', 'No such screen')}
        note={t('notFound.note', 'That route is not part of this build.')}
      />

      <div className="px-8 py-8">
        <div className={`${CARD} min-h-region max-w-4xl p-8`}>
          <p className="text-body-secondary text-ink-secondary">
            {t('notFound.body', 'Check the address, or start again from your own screen. Note that a case id outside your role’s scope answers exactly like one that was never issued — the API will not confirm that another district’s case exists, so a mistyped id and a real one you cannot reach look the same from here, deliberately.')}
          </p>
          <Link to="/" className={`${BUTTON} mt-4 inline-block`}>
            {t('notFound.backBtn', 'Back to your own screen')}
          </Link>
        </div>
      </div>
    </article>
  )
}
