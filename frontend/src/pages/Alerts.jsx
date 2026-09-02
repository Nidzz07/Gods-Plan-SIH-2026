import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'

import { ApiError, apiPost } from '../api.js'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonRows } from '../components/Skeleton.jsx'
import Tag from '../components/Tag.jsx'
import { useApi } from '../hooks/useApi.js'
import { ROLE_LABEL } from '../roles.js'
import { SEVERITY_BORDER, formatCount } from '../severity.js'
import { BUTTON, BUTTON_PRIMARY, CAPTION, CARD, LABEL, ROW } from '../ui.js'

// The alert inbox, scoped like everything else.
//
// **The escalation notice is the part of this screen that must not drift.** An
// escalation moves the alert to another desk's queue and writes a row to the
// append-only trail. In the shipped configuration it sends no email, and the
// response says so — `delivered: false`, transport `dry-run`, and the message
// that would have gone out returned verbatim. This page prints that answer as
// it arrives instead of rewording it, and shows the composed message, because
// "escalated" in most software means somebody was emailed and here it does not.
//
// PROJECT-BRIEF.md's declared limitation 8 is the rule: the word is "queued",
// never "notified". If a deployment ever configures a mail host the response
// comes back `delivered: true` and this screen will say so on its own — it
// reads the answer rather than assuming one.

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

function Escalation({ result }) {
  return (
    <div className="mt-2 rounded border-l-4 border-l-gold bg-surface-sunk p-4" role="status">
      <p className="text-table-cell text-ink">
        {result.delivered ? 'Escalated and emailed.' : 'Escalated. No email was sent.'}
      </p>
      <p className={CAPTION}>{result.detail}</p>

      {/* The message it would have sent, shown rather than summarised. An
          officer can see exactly what a configured deployment would put in
          somebody's inbox, which is the only way "dry run" means anything. */}
      <details className="mt-4">
        <summary className="cursor-pointer text-body-secondary text-ink-secondary underline-offset-2 hover:underline">
          {result.dry_run ? 'The message that would have been sent' : 'The message that was sent'}
        </summary>
        <p className="num mt-2 text-meta-label uppercase text-ink-muted">
          to {result.recipient} · transport {result.transport}
        </p>
        <p className="mt-2 text-body-secondary text-ink">{result.subject}</p>
        <pre className="mt-2 max-w-3xl overflow-x-auto whitespace-pre-wrap rounded bg-surface p-4 text-body-secondary text-ink-secondary">
          {result.body}
        </pre>
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
    <article className="relative isolate flex-1">
      <PageMotif variant="district" />

      <PageHeader
        title="Alerts"
        note="One alert per HIGH case within this account's scope, worked down by status and then by score. Escalation moves an alert to the next desk and writes an audit event; it sends no email unless a mail server is configured, and none is."
      />

      <div className="px-8 py-8">
        {loading ? (
          <LoadingRegion label="Loading the alert queue">
            <SkeletonRows rows={5} />
          </LoadingRegion>
        ) : null}

        {error ? <ErrorState error={error} /> : null}

        {failure ? (
          <div className={`${CARD} mb-4 p-4`} role="alert">
            <p className="text-body-secondary font-medium text-coral">That did not go through</p>
            <p className="mt-1 text-body-secondary text-ink-secondary">{failure}</p>
          </div>
        ) : null}

        {data ? (
          <>
            <section>
              <SectionHeading title="This queue">
                {formatCount(data.total)} alert{data.total === 1 ? '' : 's'} reaching the{' '}
                {ROLE_LABEL[user.role] ?? user.role}
                {user.scope?.describes ? `, over ${user.scope.describes}` : ''}.
              </SectionHeading>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="In this view" value={formatCount(data.items.length)} />
                <Figure label="Open" value={formatCount(counts.open ?? 0)} />
                <Figure label="Acknowledged" value={formatCount(counts.acknowledged ?? 0)} />
                <Figure label="Escalated" value={formatCount(counts.escalated ?? 0)} />
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {FILTERS.map((filter) => (
                  <button
                    key={filter.key || 'all'}
                    type="button"
                    onClick={() => setStatus(filter.key)}
                    className={`${BUTTON} ${
                      status === filter.key ? 'border-ink-secondary bg-surface-sunk' : ''
                    }`}
                    aria-pressed={status === filter.key}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </section>

            <section className="mt-8">
              <SectionHeading title="Queue">
                Severity is the coloured edge on each row. Every row opens the same case sheet
                every other role opens — what a role changes is which alerts it can reach.
              </SectionHeading>

              {data.items.length === 0 ? (
                <div className="mt-4">
                  <EmptyState title="Nothing in this queue">
                    {status
                      ? `No alert in this account's scope is ${status}.`
                      : "No HIGH case falls within this account's scope, so nothing has been routed here."}
                  </EmptyState>
                </div>
              ) : (
                <ul>
                  {data.items.map((item) => (
                    <li
                      key={item.id}
                      className={`${CARD} ${ROW} mt-2 border-l-4 ${
                        SEVERITY_BORDER[item.severity] ?? 'border-l-border-strong'
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <Link
                            to={`/cases/${item.case_id}`}
                            className="block truncate text-body text-ink underline-offset-2 hover:underline"
                          >
                            {item.description ?? item.work_id ?? item.case_id}
                          </Link>
                          <p className="num mt-1 truncate text-meta-label text-ink-muted">
                            {item.case_id} · {item.district ?? item.state} ·{' '}
                            {item.rule_id ?? 'no single rule'}
                          </p>
                          <p className="mt-2 max-w-3xl text-body-secondary text-ink-secondary">
                            {item.message}
                          </p>
                        </div>

                        <div className="shrink-0 text-right">
                          {/* Severity is the row's edge; the word prints in
                              plain ink beside the score. The STATUS is a tag,
                              which is a different fact and the one that
                              changes as the queue is worked. */}
                          <span className="num block text-body font-medium text-ink">
                            {item.score}
                          </span>
                          <span className="block text-meta-label text-ink-secondary">
                            {item.severity}
                          </span>
                          <span className="mt-2 block">
                            <Tag tone={STATUS_TONE[item.status] ?? 'neutral'}>{item.status}</Tag>
                          </span>
                        </div>
                      </div>

                      {item.escalated_to ? (
                        <p className={CAPTION}>
                          Queued for the {ROLE_LABEL[item.escalated_to] ?? item.escalated_to} on{' '}
                          {String(item.escalated_at).slice(0, 10)}.
                        </p>
                      ) : null}

                      {user.can_write ? (
                        <div className="mt-4 flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => act(item.id, 'acknowledge')}
                            disabled={busy === item.id || item.status !== 'open'}
                            className={BUTTON}
                          >
                            {item.status === 'open' ? 'Acknowledge' : 'Acknowledged'}
                          </button>
                          <button
                            type="button"
                            onClick={() => act(item.id, 'escalate')}
                            disabled={busy === item.id || item.status === 'closed'}
                            className={BUTTON_PRIMARY}
                          >
                            {busy === item.id ? 'Working…' : 'Escalate'}
                          </button>
                        </div>
                      ) : (
                        <p className={CAPTION}>
                          This account is read-only: a member of parliament sees the alerts raised
                          on their own works and does not act on them.
                        </p>
                      )}

                      {escalations[item.id] ? (
                        <Escalation result={escalations[item.id]} />
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}

              <p className={`${CAPTION} mt-4 max-w-3xl`}>
                Alerts are raised by a build step over stored cases, not computed per request, so
                an acknowledgement survives a refresh and a re-run of the step never resets one.
              </p>
            </section>
          </>
        ) : null}
      </div>
    </article>
  )
}
