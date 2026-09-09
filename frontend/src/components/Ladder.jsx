import { useTranslation } from 'react-i18next'
import Tag from './Tag.jsx'
import { GOLD, GREEN, INK_MUTED, NAVY } from '../chart.js'
import { SKIP_REASON, formatDays, formatPct, formatRupees } from '../severity.js'
import { CAPTION, CARD, LABEL } from '../ui.js'
import SectionHeading from './SectionHeading.jsx'

const STEP_TONE = { open: 'medium', closed: 'low', computed: 'low', unavailable: 'neutral' }

function StepTag({ state }) {
  const { t } = useTranslation()
  const STEP_LABEL = {
    open: t('common.open', 'Open'),
    closed: t('common.closed', 'Closed'),
    computed: t('common.computed', 'Computed'),
    unavailable: t('common.unavailable', 'Unavailable'),
  }
  return <Tag tone={STEP_TONE[state] ?? 'neutral'}>{STEP_LABEL[state] ?? state}</Tag>
}

function published(availability) {
  return availability === 'published' || availability === 'published_zero'
}

// One reading as a bar, or as the reason there is not one.
//
// `published_zero` prints the zero AND says the portal published it. Dropping
// to the dashed track would turn a fact about the work into a reporting failure
// by MoSPI; printing a bare 0 would lose that the portal actually said so. Both
// halves are needed and neither is optional.
function Bar({ label, text, availability, width, color }) {
  const isPublished = published(availability)
  return (
    <div className="grid grid-cols-[130px_1fr_170px] items-center gap-4">
      <span className="text-meta-label uppercase text-ink-secondary">{label}</span>

      {isPublished ? (
        <span className="block h-4 w-full rounded bg-surface-sunk">
          <span
            className="block h-4 rounded"
            style={{ width: `${width}%`, backgroundColor: color }}
            // The bar restates a number already printed beside it, so it is
            // hidden rather than announced twice.
            aria-hidden="true"
          />
        </span>
      ) : (
        <span className="flex h-4 w-full items-center rounded border border-dashed border-border-strong px-2">
          <span className="text-meta-label text-ink-muted">
            {SKIP_REASON[availability] ?? availability}
          </span>
        </span>
      )}

      <span className="num text-right text-table-cell text-ink">
        {isPublished ? (
          <>
            {text ?? '—'}
            {availability === 'published_zero' ? (
              <span className="block text-meta-label text-ink-muted">
                {SKIP_REASON.published_zero}
              </span>
            ) : null}
          </>
        ) : (
          <span className="italic text-ink-muted">
            {SKIP_REASON[availability] ?? availability}
          </span>
        )}
      </span>
    </div>
  )
}

// The step between two readings: what it measured, what that was compared
// against, and what the officer does about it when it is open.
function Step({ label, measured, compared, state, reason, action, highlighted }) {
  return (
    <div
      className={`ml-6 rounded border-y border-r border-border border-l-4 px-4 py-4 ${
        highlighted ? 'border-l-gold bg-surface' : 'border-l-border-strong bg-surface'
      }`}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <span className="text-table-cell text-ink">{label}</span>
        <span className="flex items-center gap-4">
          {compared ? (
            <span className="num text-body-secondary text-ink-secondary">{compared}</span>
          ) : null}
          <span className="num text-table-cell text-ink">{measured ?? '—'}</span>
          <StepTag state={state} />
        </span>
      </div>

      {state === 'unavailable' && reason ? (
        <p className="mt-2 text-body-secondary text-ink-secondary">
          {SKIP_REASON[reason] ?? reason}
        </p>
      ) : null}

      {/* What to go and check. Only on an open step: an instruction printed
          under a closed hop is an instruction an officer learns to skip. */}
      {state === 'open' && action ? (
        <p className="mt-2 max-w-3xl text-body-secondary text-ink-secondary">{action}</p>
      ) : null}
    </div>
  )
}

export function FundLadder({ ladder, gapHop }) {
  const { t } = useTranslation()
  const amounts = ladder.rungs
    .filter((rung) => published(rung.availability))
    .map((rung) => rung.amount ?? 0)
  const scale = amounts.length ? Math.max(...amounts) : 0

  return (
    <section>
      <SectionHeading title={t('components.fundLadderTitle', 'Fund ladder')}>
        {t(
          'components.fundLadderDesc',
          'Where the money is. Three rungs to scale against the largest published amount, and two hops, each a signed variance against the rung above it compared with the tolerance the rulebook sets for that hop.'
        )}
        {gapHop
          ? ` ${t('components.fundLadderOpenHop', 'The first open hop walking down is what this case is scored on.')}`
          : ` ${t('components.fundLadderNoOpenHop', 'No hop on this work is open.')}`}
      </SectionHeading>

      <div className={`${CARD} mt-4 p-6`}>
        {ladder.rungs.map((rung, index) => (
          <div key={rung.key} className={index ? 'mt-4' : ''}>
            <Bar
              label={rung.label}
              text={formatRupees(rung.amount ?? (rung.availability === 'published_zero' ? 0 : null))}
              availability={rung.availability}
              width={scale > 0 ? ((rung.amount ?? 0) / scale) * 100 : 0}
              color={RUNG_COLOR[rung.key] ?? NAVY}
            />

            {rung.recommended_equals_sanctioned ? (
              <p className={`${CAPTION} ml-[146px]`}>
                {t('common.recommended', 'Recommended')} {formatRupees(rung.recommended_amt)} — {t('components.recEqualsSanc', 'equal to the sanctioned amount, as it is on every matched work in this corpus.')}
              </p>
            ) : null}
            {rung.note ? <p className={`${CAPTION} ml-[146px]`}>{rung.note}</p> : null}

            {ladder.hops[index] ? (
              <div className="mt-4">
                <Step
                  label={ladder.hops[index].label}
                  measured={formatPct(ladder.hops[index].variance_pct)}
                  compared={`${t('rulebook.colThreshold', 'tolerance')} ${formatPct(ladder.hops[index].tolerance_pct)}`}
                  state={ladder.hops[index].state}
                  reason={ladder.hops[index].unavailable_reason}
                  action={ladder.hops[index].hop_action}
                  highlighted={ladder.hops[index].key === gapHop}
                />
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  )
}

export function LifecycleLadder({ ladder, slowestLag }) {
  const { t } = useTranslation()
  const days = ladder.lags
    .filter((lag) => lag.days !== null && lag.days !== undefined)
    .map((lag) => lag.days)
  const scale = days.length ? Math.max(...days) : 0

  return (
    <section>
      <SectionHeading title={t('components.lifecycleLadderTitle', 'Lifecycle ladder')}>
        {t(
          'components.lifecycleLadderDesc',
          'Where the time went. Four dates and three lags, in whole days, computed date to date and never clamped — a negative lag is an ingest reject, not a zero. Each lag is drawn against the longest one on this work.'
        )}
        {slowestLag
          ? ` ${t('components.slowestLagDesc', 'The slowest lag is what says which stage the delay actually occurred in.')}`
          : ` ${t('common.noLagComputable', 'No lag on this work is computable.')}`}
      </SectionHeading>

      <div className={`${CARD} mt-4 p-6`}>
        {ladder.dates.map((entry, index) => (
          <div key={entry.key} className={index ? 'mt-4' : ''}>
            <div className="grid grid-cols-[130px_1fr_170px] items-center gap-4">
              <span className="text-meta-label uppercase text-ink-secondary">{entry.label}</span>
              <span className="h-px w-full bg-border" aria-hidden="true" />
              <span className="num text-right text-table-cell text-ink">
                {published(entry.availability) ? (
                  entry.date
                ) : (
                  <span className="italic text-ink-muted">
                    {SKIP_REASON[entry.availability] ?? entry.availability}
                  </span>
                )}
              </span>
            </div>

            {ladder.lags[index] ? (
              <div className="mt-4">
                <div className="ml-6 grid grid-cols-[124px_1fr_170px] items-center gap-4">
                  <span className="text-meta-label uppercase text-ink-secondary">{t('common.elapsed', 'Elapsed')}</span>
                  {ladder.lags[index].days === null ||
                  ladder.lags[index].days === undefined ? (
                    <span className="flex h-2 w-full items-center rounded border border-dashed border-border-strong" />
                  ) : (
                    <span className="block h-2 w-full rounded bg-surface-sunk">
                      <span
                        className="block h-2 rounded"
                        style={{
                          width: `${scale > 0 ? (ladder.lags[index].days / scale) * 100 : 0}%`,
                          backgroundColor:
                            ladder.lags[index].key === slowestLag ? GOLD : INK_MUTED,
                        }}
                        aria-hidden="true"
                      />
                    </span>
                  )}
                  <span className="num text-right text-table-cell text-ink">
                    {formatDays(ladder.lags[index].days) ?? '—'}
                  </span>
                </div>

                <div className="mt-2">
                  <Step
                    label={ladder.lags[index].label}
                    measured={formatDays(ladder.lags[index].days)}
                    state={ladder.lags[index].state}
                    reason={ladder.lags[index].unavailable_reason}
                    highlighted={ladder.lags[index].key === slowestLag}
                  />
                </div>
              </div>
            ) : null}
          </div>
        ))}
      </div>

      <p className={`${CAPTION} mt-4`}>
        {ladder.payment_count === 1
          ? t('components.paymentCount_one', '1 payment recorded')
          : t('components.paymentCount_other', '{{count}} payments recorded', { count: ladder.payment_count })}
        {ladder.last_payment_date ? `, ${t('components.lastOn', 'the last on')} ${ladder.last_payment_date}` : ''}.
      </p>
    </section>
  )
}
