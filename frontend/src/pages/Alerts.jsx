import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'

import { ApiError, apiPost } from '../api.js'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHero from '../components/PageHero.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonRows } from '../components/Skeleton.jsx'
import Tag from '../components/Tag.jsx'
import { useApi } from '../hooks/useApi.js'
import { ROLE_LABEL } from '../roles.js'
import { SEVERITY_BORDER, formatCount } from '../severity.js'
import { BUTTON, BUTTON_PRIMARY, CAPTION, CARD } from '../ui.js'

const STATUS_TONE = {
  open: 'open',
  acknowledged: 'under_review',
  escalated: 'escalated',
  closed: 'resolved',
}

const FILTERS = [
  { key: '', label: 'All' },
  { key: 'open', label: 'Open' },
  { key: 'acknowledged', label: 'Acknowledged' },
  { key: 'escalated', label: 'Escalated' },
]

function EscalationPanel({ result }) {
  return (
    <div className="mt-3 rounded border-l-4 border-l-gold bg-portal-tint/50 p-4" role="status">
      <p className="font-semibold text-navy text-[14px]">
        {result.delivered ? 'Escalated and emailed.' : 'Escalated. Dry-run transport (no email sent).'}
      </p>
      <p className="mt-1 text-[13px] text-ink-secondary">{result.detail}</p>

      <details className="mt-3 text-[13px]">
        <summary className="cursor-pointer font-medium text-portal hover:underline">
          {result.dry_run
            ? 'View verbatim dry-run message'
            : 'View delivered notification message'}
        </summary>
        <div className="mt-2 rounded border border-rule bg-paper p-3 font-mono text-[12px] text-ink-secondary space-y-1">
          <p>Recipient: {result.recipient}</p>
          <p>Transport: {result.transport}</p>
          <p>Subject: {result.subject}</p>
          <pre className="mt-2 max-h-40 overflow-y-auto whitespace-pre-wrap font-sans text-ink">
            {result.body}
          </pre>
        </div>
      </details>
    </div>
  )
}

export default function Alerts() {
  const { user } = useOutletContext()
  const [status, setStatus] = useState('')
  const query = status ? `?status=${status}&limit=200` : '?limit=200'
  const { data, error, loading, reload } = useApi(`/api/alerts${query}`)

  const [busy, setBusy] = useState(null)
  const [failure, setFailure] = useState(null)
  const [escalations, setEscalations] = useState({})

  async function act(alertId, action) {
    setBusy(alertId)
    setFailure(null)
    try {
      const result = await apiPost(`/api/alerts/${alertId}/${action}`)
      if (action === 'escalate') {
        setEscalations((current) => ({ ...current, [alertId]: result }))
      }
      reload()
    } catch (thrown) {
      setFailure(thrown instanceof ApiError ? thrown.message : String(thrown))
    } finally {
      setBusy(null)
    }
  }

  const counts = data
    ? data.items.reduce((acc, item) => ({ ...acc, [item.status]: (acc[item.status] ?? 0) + 1 }), {})
    : {}

  return (
    <article className="relative isolate flex-1 bg-paper">
      <PageMotif variant="district" />

      {/* §7.2 Page Hero */}
      <PageHero
        title="Alert inbox"
        lede={`One alert per HIGH-risk work within this account's scope. Escalations record an audit log and queue the item for the next administrative level.`}
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Alerts' },
        ]}
      />

      <div className="w-full px-4 sm:px-6 py-8 space-y-8">
        {loading && (
          <LoadingRegion label="Loading alert queue…">
            <SkeletonRows rows={5} />
          </LoadingRegion>
        )}

        {error && <ErrorState error={error} />}

        {failure && (
          <div className="rounded border border-coral/40 bg-coral/10 p-4 text-coral text-[14px]">
            {failure}
          </div>
        )}

        {data && (
          <>
            {/* Counts & Filters */}
            <section className="rounded border border-rule bg-paper p-6 shadow-card">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <Figure label="Total alerts" value={formatCount(data.total)} />
                <Figure label="Open" value={formatCount(counts.open ?? 0)} />
                <Figure label="Acknowledged" value={formatCount(counts.acknowledged ?? 0)} />
                <Figure label="Escalated" value={formatCount(counts.escalated ?? 0)} />
              </div>

              <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-rule pt-4">
                <span className="text-[13px] font-medium text-ink-secondary mr-2">Filter status:</span>
                {FILTERS.map((f) => (
                  <button
                    key={f.key || 'all'}
                    type="button"
                    onClick={() => setStatus(f.key)}
                    className={`rounded px-3 py-1 text-[13px] font-semibold transition-colors ${
                      status === f.key
                        ? 'bg-portal text-white'
                        : 'bg-paper-sunk text-ink-secondary border border-rule hover:bg-portal-tint hover:text-navy'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </section>

            {/* Alert Items List */}
            <section className="space-y-4">
              {data.items.length === 0 ? (
                <EmptyState title="No alerts in queue">
                  {status
                    ? `No alert is currently in '${status}' status.`
                    : 'No high-severity alerts have been routed to this scope.'}
                </EmptyState>
              ) : (
                <ul className="space-y-3">
                  {data.items.map((item) => (
                    <li
                      key={item.id}
                      className={`rounded border border-rule border-l-4 ${
                        SEVERITY_BORDER[item.severity] ?? 'border-l-border-strong'
                      } bg-paper p-5 shadow-card`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                        <div className="space-y-1">
                          <Link
                            to={`/cases/${item.case_id}`}
                            className="font-medium text-navy text-[16px] hover:underline"
                          >
                            {item.description || item.work_id || item.case_id}
                          </Link>
                          <p className="num text-[12px] text-ink-muted">
                            Case {item.case_id} · {item.district || item.state} · Rule:{' '}
                            <span className="font-mono">{item.rule_id || 'Composite HIGH'}</span>
                          </p>
                          <p className="mt-2 text-[14px] text-ink-secondary leading-relaxed max-w-3xl">
                            {item.message}
                          </p>
                        </div>

                        <div className="text-right shrink-0">
                          <span className="num font-bold text-navy text-[18px]">{item.score}</span>
                          <span className="block text-[11px] uppercase font-semibold text-coral">
                            {item.severity}
                          </span>
                          <div className="mt-1">
                            <Tag tone={STATUS_TONE[item.status] ?? 'neutral'}>{item.status}</Tag>
                          </div>
                        </div>
                      </div>

                      {user.can_write ? (
                        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-rule/60 pt-3">
                          <button
                            type="button"
                            onClick={() => act(item.id, 'acknowledge')}
                            disabled={busy === item.id || item.status !== 'open'}
                            className={`${BUTTON} text-[13px] py-1.5`}
                          >
                            {item.status === 'open' ? 'Acknowledge' : 'Acknowledged'}
                          </button>
                          <button
                            type="button"
                            onClick={() => act(item.id, 'escalate')}
                            disabled={busy === item.id || item.status === 'closed'}
                            className={`${BUTTON_PRIMARY} text-[13px] py-1.5`}
                          >
                            {busy === item.id ? 'Working…' : 'Escalate'}
                          </button>
                        </div>
                      ) : (
                        <p className="mt-3 text-[12px] italic text-ink-muted border-t border-rule/40 pt-2">
                          Read-only account. Alert status modifications are restricted to
                          administrative authorities.
                        </p>
                      )}

                      {escalations[item.id] && <EscalationPanel result={escalations[item.id]} />}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </article>
  )
}
