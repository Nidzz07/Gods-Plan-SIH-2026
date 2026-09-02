import { useState } from 'react'

import { ApiError, apiPost } from '../api.js'
import { BUTTON, BUTTON_PRIMARY, CAPTION, CARD, FIELD, LABEL } from '../ui.js'

// The two things an officer can DO to a case, on the case itself.
//
// Both endpoints have existed since Phase 5 and neither was reachable from the
// screen, which made them features only a curl user had. They are here now, and
// the copy around them is doing as much work as the buttons.
//
// **A note is an audit event and nothing else.** There is no notes table: the
// text lands in the append-only, hash-chained trail beside the score it
// comments on, which means it cannot be edited or removed afterwards any more
// than a score can. The form says so before it is submitted, because "add a
// note" in most software means something a person can take back.
//
// **A recompute is an OBSERVATION, not a correction.** It re-derives the case
// against the rulebook snapshot the case was scored under - not against the
// file as it reads today - and records what it found next to what was stored,
// leaving the stored case exactly as it was. If the two disagree, the
// disagreement is the finding, and overwriting the old score would destroy the
// evidence that anything moved. The result panel is therefore worded as a
// comparison and never as an update.
//
// Neither is offered to the member of parliament: `can_write` comes from the
// server on `/api/auth/me`, the server refuses the write regardless, and this
// component simply does not draw a button that would be refused.

function RecomputeResult({ outcome }) {
  const moved = outcome.trace_diff ?? []
  return (
    <div className="mt-4 rounded border border-border bg-surface-sunk p-4" role="status">
      <p className="text-table-cell text-ink">
        {outcome.identical
          ? 'Re-derived against this case’s own rulebook snapshot. Every rule, reading, threshold and contribution matches what was stored.'
          : `Re-derived against this case’s own rulebook snapshot. ${moved.length} trace row${
              moved.length === 1 ? '' : 's'
            } differ from what was stored.`}
      </p>
      <p className={CAPTION}>
        Compared under rulebook {outcome.rulebook_version}. The stored case has not been changed
        by this: a recompute records what it found beside what was there.
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
                stored {JSON.stringify(row.stored ?? null)} · recomputed{' '}
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
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [noted, setNoted] = useState(null)
  const [outcome, setOutcome] = useState(null)

  if (!canWrite) {
    return (
      <div className={`${CARD} p-6`}>
        <p className={LABEL}>Actions</p>
        <p className="text-body-secondary text-ink-secondary">
          This account is read-only. A member of parliament can open a case and cannot annotate,
          recompute, resolve or escalate one — the scheme&rsquo;s subject does not adjudicate the
          scheme&rsquo;s findings. The server refuses these writes whatever a screen offers, so
          they are not offered.
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
      <p className={LABEL}>Actions</p>

      {error ? (
        <div className="mt-2 rounded border border-border bg-surface-sunk p-4" role="alert">
          <p className="text-body-secondary font-medium text-coral">That did not go through</p>
          <p className="mt-1 text-body-secondary text-ink-secondary">{error}</p>
        </div>
      ) : null}

      <form onSubmit={submitNote} className="mt-2">
        <label htmlFor="note" className={LABEL}>
          Field note
        </label>
        <textarea
          id="note"
          rows={3}
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={4000}
          className={`${FIELD} w-full`}
          placeholder="What was checked, and what was found."
        />
        <p className={CAPTION}>
          A note is written into the append-only audit trail, hash-chained beside this
          case&rsquo;s score. It cannot be edited or removed afterwards — by anyone, including
          whoever wrote it.
        </p>
        <button
          type="submit"
          disabled={busy !== null || !text.trim()}
          className={`${BUTTON} mt-4`}
        >
          {busy === 'note' ? 'Recording…' : 'Record note'}
        </button>
      </form>

      {noted ? (
        <p className="num mt-4 text-body-secondary text-ink-secondary" role="status">
          Recorded as audit event {noted.id} at {String(noted.at).slice(0, 19).replace('T', ' ')},
          by the {String(noted.actor_role).replace('_', ' ')}.
        </p>
      ) : null}

      <div className="mt-6 border-t border-border pt-6">
        <p className={LABEL}>Recompute</p>
        <p className={CAPTION}>
          Re-derives this case against the rulebook snapshot it was scored under — not against
          the rulebook as it reads today — and reports what moved. The stored case is left
          exactly as it was; if the two disagree, the disagreement is the finding.
        </p>
        <button
          type="button"
          onClick={runRecompute}
          disabled={busy !== null}
          className={`${BUTTON_PRIMARY} mt-4`}
        >
          {busy === 'recompute' ? 'Re-deriving…' : 'Recompute against the stored snapshot'}
        </button>
      </div>

      {outcome ? <RecomputeResult outcome={outcome} /> : null}
    </div>
  )
}
