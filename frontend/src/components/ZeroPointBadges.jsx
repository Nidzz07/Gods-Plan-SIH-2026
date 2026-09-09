import { useTranslation } from 'react-i18next'
import { CAPTION, CARD, LABEL } from '../ui.js'

function Badge({ label, value, model, children }) {
  return (
    <div className="rounded border border-border bg-surface-sunk py-card-y px-card-x">
      <div className="flex items-baseline justify-between gap-4">
        <p className={LABEL}>{label}</p>
        <span className="num text-table-cell text-ink-muted">+0</span>
      </div>
      <p className="num font-display text-section-heading text-ink-secondary">{value ?? '—'}</p>
      {children ? <p className={CAPTION}>{children}</p> : null}
      {model ? (
        <p className="num mt-2 text-meta-label text-ink-muted">{model}</p>
      ) : null}
    </div>
  )
}

export default function ZeroPointBadges({ statistical, forecast, concentration }) {
  const { t } = useTranslation()

  return (
    <div className={`${CARD} py-card-y px-card-x`}>
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <h3 className="font-display text-section-heading text-navy">
          {t('components.zpTitle', 'Badges — tiers 3 and 4')}
        </h3>
        <span className="num text-body-secondary text-ink-secondary">
          {t('components.zpPointsNote', '0 of this case’s points')}
        </span>
      </div>
      <p className={`${CAPTION} max-w-3xl`}>
        {t(
          'components.zpCaption',
          'Statistical and graph findings. They confirm, or fail to confirm, what the rulebook already found, and they never move the number — every one of them contributes exactly zero, and the score above is the sum of the fired rulebook weights and the corroboration bonus alone. Nothing on this panel is an input to it.'
        )}
      </p>

      <div className="mt-4 grid grid-cols-1 gap-grid-gap lg:grid-cols-3">
        <Badge
          label={t('components.zpAnomaly', 'Anomaly')}
          value={statistical.anomaly_score}
          model={statistical.anomaly_model_version}
        >
          {statistical.z_peer_group ? `${t('common.peerGroup', 'Peer group')}: ${statistical.z_peer_group}.` : null}{' '}
          {statistical.confirms === null || statistical.confirms === undefined
            ? null
            : statistical.confirms
              ? t('components.confirmsFinding', 'Confirms the rulebook finding.')
              : t('components.doesNotConfirm', 'Does not confirm the rulebook finding.')}
        </Badge>

        <Badge
          label={t('components.zpDelayRisk', 'Delay risk')}
          value={forecast.delay_risk}
          model={forecast.model_version}
        >
          {forecast.horizon_meaning
            ? `${forecast.horizon_meaning}. ${t('components.illustrativeSampleDesc', 'Illustrative: trained on a truncated sample, and the horizon is a demonstration rather than a commitment. Read it as a ranking, not a probability.')}`
            : t('components.illustrativeSample', 'Illustrative, on a truncated sample.')}
        </Badge>

        <Badge
          label={t('components.zpHHI', 'Vendor concentration')}
          value={concentration.hhi}
          model={concentration.model_version}
        >
          {concentration.top_vendor
            ? `${t('components.largestShare', 'Largest share')}: ${concentration.top_vendor} (${concentration.top_vendor_share_pct}%).`
            : t('components.noVendorShare', 'No vendor share published for this agency.')}
        </Badge>
      </div>
    </div>
  )
}
