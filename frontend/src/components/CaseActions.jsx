import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError, apiPost } from '../api.js'
import { BUTTON, BUTTON_PRIMARY, CAPTION, CARD, FIELD, LABEL } from '../ui.js'

function RecomputeResult({ outcome }) {
  const { t } = useTranslation()
  const moved = outcome.trace_diff ?? []
  return (
    <div className="mt-4 rounded border border-border bg-surface-sunk p-4" role="status">
      <p className="text-table-cell text-ink">
        {outcome.identical
          ? t(
              'case.recomputeIdentical',
              'Re-derived against this case’s own rulebook snapshot. Every rule, reading, threshold and contribution matches what was stored.'
            )
          : t(
              'case.recomputeDiff',
              'Re-derived against this case’s own rulebook snapshot. {{count}} trace rows differ from what was stored.',
              { count: moved.length }
            )}
      </p>
      <p className={CAPTION}>
        {t(
          'case.recomputeStoredRulebook',
          'Compared under rulebook {{version}}. The stored case has not been changed by this: a recompute records what it found beside what was there.',
          { version: outcome.rulebook_version }
        )}
      </p>

      {moved.length ? (
        <ul className="mt-4">
          {moved.map((row) => (
            <li
              key={row.rule_id}
              className="mt-2 rounded border-y border-r border-border border-l-4 border-l-gold bg-surface px-4 py-2"
            >
              <span className="block text-table-cell text-ink">{row.rule_id}</span>
              <span className="num block text-body-secondary text-ink-secondary">
                {t('case.stored', 'stored')} {JSON.stringify(row.stored ?? null)} · {t('case.recomputed', 'recomputed')}{' '}
                {JSON.stringify(row.recomputed ?? null)}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}

export default function CaseActions({ caseId, canWrite, onChanged }) {
  const { t } = useTranslation()
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [noted, setNoted] = useState(null)
  const [outcome, setOutcome] = useState(null)

  if (!canWrite) {
    return (
      <div className={`${CARD} p-6`}>
        <p className={LABEL}>{t('common.actions', 'Actions')}</p>
        <p className="text-body-secondary text-ink-secondary">
          {t(
            'case.readOnlyAccountNote',
            'This account is read-only. A member of parliament can open a case and cannot annotate, recompute, resolve or escalate one — the scheme’s subject does not adjudicate the scheme’s findings. The server refuses these writes whatever a screen offers, so they are not offered.'
          )}
        </p>
      </div>
    )
  }

  async function submitNote(event) {
    event.preventDefault()
    const body = text.trim()
    if (!body) return
    setBusy('note')
    setError(null)
    try {
      const result = await apiPost(`/api/cases/${encodeURIComponent(caseId)}/notes`, {
        text: body,
      })
      setText('')
      setNoted(result.event)
      if (onChanged) onChanged()
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : String(failure))
    } finally {
      setBusy(null)
    }
  }

  async function runRecompute() {
    setBusy('recompute')
    setError(null)
    try {
      setOutcome(await apiPost(`/api/cases/${encodeURIComponent(caseId)}/recompute`))
      if (onChanged) onChanged()
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : String(failure))
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className={`${CARD} p-6`}>
      <p className={LABEL}>{t('common.actions', 'Actions')}</p>

      {error ? (
        <div className="mt-2 rounded border border-border bg-surface-sunk p-4" role="alert">
          <p className="text-body-secondary font-medium text-coral">{t('case.actionFailed', 'That did not go through')}</p>
          <p className="mt-1 text-body-secondary text-ink-secondary">{error}</p>
        </div>
      ) : null}

      <form onSubmit={submitNote} className="mt-2">
        <label htmlFor="note" className={LABEL}>
          {t('case.fieldNote', 'Field note')}
        </label>
        <textarea
          id="note"
          rows={3}
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={4000}
          className={`${FIELD} w-full`}
          placeholder={t('case.notePlaceholder', 'What was checked, and what was found.')}
        />
        <p className={CAPTION}>
          {t(
            'case.noteCaption',
            'A note is written into the append-only audit trail, hash-chained beside this case’s score. It cannot be edited or removed afterwards — by anyone, including whoever wrote it.'
          )}
        </p>
        <button
          type="submit"
          disabled={busy !== null || !text.trim()}
          className={`${BUTTON} mt-4`}
        >
          {busy === 'note' ? t('case.recording', 'Recording…') : t('case.recordNote', 'Record note')}
        </button>
      </form>

      {noted ? (
        <p className="num mt-4 text-body-secondary text-ink-secondary" role="status">
          {t('case.recordedAuditEvent', 'Recorded as audit event {{id}} by {{role}}.', {
            id: noted.id,
            role: String(noted.actor_role).replace('_', ' '),
          })}
        </p>
      ) : null}

      <div className="mt-6 border-t border-border pt-6">
        <p className={LABEL}>{t('case.recompute', 'Recompute')}</p>
        <p className={CAPTION}>
          {t(
            'case.recomputeCaption',
            'Re-derives this case against the rulebook snapshot it was scored under — not against the rulebook as it reads today — and reports what moved. The stored case is left exactly as it was; if the two disagree, the disagreement is the finding.'
          )}
        </p>
        <button
          type="button"
          onClick={runRecompute}
          disabled={busy !== null}
          className={`${BUTTON_PRIMARY} mt-4`}
        >
          {busy === 'recompute' ? t('case.rederiving', 'Re-deriving…') : t('case.recomputeBtn', 'Recompute against the stored snapshot')}
        </button>
      </div>

      {outcome ? <RecomputeResult outcome={outcome} /> : null}
    </div>
  )
}
