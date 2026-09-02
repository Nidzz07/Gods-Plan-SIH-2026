import { useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'

import { ApiError, apiPost } from '../api.js'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel } from '../components/Skeleton.jsx'
import Tag from '../components/Tag.jsx'
import { useApi } from '../hooks/useApi.js'
import { MINISTRY } from '../roles.js'
import { OPERATOR_SYMBOL, formatCount } from '../severity.js'
import { BUTTON, BUTTON_PRIMARY, CAPTION, CARD, CELL_NUM, COLUMN_HEAD, FIELD, LABEL } from '../ui.js'

// The rulebook, readable by everyone and editable by the ministry.
//
// **The read half is not gated and that is deliberate.** Everyone judged by a
// rule is entitled to read the rule and check the arithmetic; a rulebook only
// its author may read is not an explainable system, it is an assertion. So this
// page renders for all four roles and only the WRITE controls are withheld.
//
// **The gate here is wayfinding, not security.** `user.role` decides whether
// the inputs are drawn. It decides nothing else: the endpoint is behind
// `require_role(ministry)` and answers 403 to anyone else whatever this page
// does, and a person who edits their role in the devtools gets a form whose
// submissions are refused. Client-side gating exists so that a state officer is
// not shown a control that would fail; it is not what stops them.
//
// **The notice above the submit button is the most important copy on the page.**
// An officer who changes a threshold will reasonably assume the corpus was
// rescored. It was not, it will not be, and the number of cases affected by an
// edit is zero until somebody recomputes them one at a time or rebuilds the
// corpus. Saying that once, plainly, before the button - and then again in the
// result - is what stops the assumption forming.

// Only these two move. `field` and `operator` are shown because an officer
// cannot judge a threshold without knowing what it is compared against, and
// they are NOT editable because changing what a rule measures is a modelling
// change with a data-profile pass attached, not a form submission.
const READ_ONLY_NOTE =
  'Field, operator, label and severity are shown because a threshold cannot be judged without ' +
  'them, and are not editable here. Changing what a rule measures needs a derived field, a ' +
  'threshold calibrated against a measured distribution and its own skip caveats — a modelling ' +
  'pass, not an edit.'

function asNumber(value) {
  if (value === '' || value === null || value === undefined) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export default function Rulebook() {
  const { user } = useOutletContext()
  const isMinistry = user?.role === MINISTRY

  const { data, error, loading, reload } = useApi('/api/rulebook')

  // Only what the officer actually typed. An untouched row contributes nothing
  // to the request, so a submit cannot silently re-assert nine values it was
  // never asked about.
  const [draft, setDraft] = useState({})
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState(null)
  const [result, setResult] = useState(null)

  const drifted = useMemo(
    () => new Set(data?.rules_edited_since_scoring ?? []),
    [data],
  )

  const changes = useMemo(() => {
    if (!data) return []
    const out = []
    for (const rule of data.rules) {
      const edit = draft[rule.id]
      if (!edit) continue
      const threshold = asNumber(edit.threshold)
      const weight = asNumber(edit.weight)
      if (threshold !== null && threshold !== rule.threshold) {
        out.push({ rule_id: rule.id, key: 'threshold', from: rule.threshold, to: threshold })
      }
      if (weight !== null && weight !== rule.weight) {
        out.push({ rule_id: rule.id, key: 'weight', from: rule.weight, to: weight })
      }
    }
    return out
  }, [draft, data])

  function set(ruleId, key, value) {
    setDraft((current) => ({ ...current, [ruleId]: { ...current[ruleId], [key]: value } }))
  }

  async function submit(event) {
    event.preventDefault()
    if (!changes.length || !note.trim()) return
    setBusy(true)
    setFailure(null)
    try {
      const byRule = new Map()
      for (const change of changes) {
        const entry = byRule.get(change.rule_id) ?? { rule_id: change.rule_id }
        entry[change.key] = change.to
        byRule.set(change.rule_id, entry)
      }
      setResult(
        await apiPost('/api/rulebook', { note: note.trim(), rules: [...byRule.values()] }),
      )
      setDraft({})
      setNote('')
      reload()
    } catch (thrown) {
      setFailure(thrown instanceof ApiError ? thrown.message : String(thrown))
    } finally {
      setBusy(false)
    }
  }

  const GRID = 'grid grid-cols-[1fr_150px_110px_110px_90px] items-start gap-4'

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="ministry" />

      <PageHeader
        title="Rulebook"
        note="Ten rules and one corroboration bonus, 154 points in total. This document is the only source of score in the product: every point on every case comes from a row below, and nothing else contributes one."
      />

      <div className="px-8 py-8">
        {loading ? (
          <LoadingRegion label="Loading the rulebook">
            <SkeletonPanel lines={5} />
          </LoadingRegion>
        ) : null}

        {error ? <ErrorState error={error} /> : null}

        {data ? (
          <>
            <section>
              <SectionHeading title={`Version ${data.version}`}>
                {data.updated_by} · {formatCount(data.rule_weight_total)} points across{' '}
                {data.rules.length} rules, plus a {data.corroboration.weight}-point corroboration
                bonus. HIGH ≥ {data.severity_bands_resolved.high} · MEDIUM ≥{' '}
                {data.severity_bands_resolved.medium}.
              </SectionHeading>

              {/* The state of the world, before anything is edited. */}
              <div className={`${CARD} mt-4 p-4`}>
                <div className="flex flex-wrap items-baseline justify-between gap-4">
                  <span className="text-table-cell text-ink">
                    Cases on screen were scored under{' '}
                    {data.cases_scored_under?.version ?? 'no stored version'}
                  </span>
                  <Tag tone={data.file_matches_stored_version ? 'low' : 'medium'}>
                    {data.file_matches_stored_version
                      ? 'File and cases agree'
                      : 'File edited since scoring'}
                  </Tag>
                </div>
                <p className={CAPTION}>
                  {data.file_matches_stored_version
                    ? 'The rulebook on disk hashes to the snapshot the current cases were scored under, so what you read here is what produced the scores you see.'
                    : `The rulebook on disk no longer matches the snapshot the current cases were scored under. Those cases still carry the scores the older rulebook gave them, and will until each is recomputed or the corpus is rebuilt. Rules affected: ${data.rules_edited_since_scoring.join(', ')}.`}
                </p>
              </div>
            </section>

            <form onSubmit={submit} className="mt-8">
              <SectionHeading title="Rules">
                {isMinistry
                  ? `Threshold and weight are editable; everything else is read-only. ${READ_ONLY_NOTE}`
                  : `The ten rules in force, with the value and weight each carries. ${READ_ONLY_NOTE}`}
              </SectionHeading>

              <div className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}>
                <span className={COLUMN_HEAD}>Rule</span>
                <span className={COLUMN_HEAD}>Reads</span>
                <span className={`${COLUMN_HEAD} text-right`}>Threshold</span>
                <span className={`${COLUMN_HEAD} text-right`}>Weight</span>
                <span className={COLUMN_HEAD}>Severity</span>
              </div>

              <ul>
                {data.rules.map((rule) => (
                  <li
                    key={rule.id}
                    className={`${GRID} ${CARD} mt-2 px-4 py-4 ${
                      drifted.has(rule.id) ? 'border-l-4 border-l-gold' : ''
                    }`}
                  >
                    <span>
                      <span className="block text-table-cell text-ink">{rule.label}</span>
                      <span className="num block text-meta-label text-ink-muted">{rule.id}</span>
                      {drifted.has(rule.id) ? (
                        <span className="mt-1 block text-meta-label text-ink-secondary">
                          Edited since the cases on screen were scored.
                        </span>
                      ) : null}
                    </span>

                    <span>
                      <span className="num block text-body-secondary text-ink-secondary">
                        {rule.field}
                      </span>
                      <span className="num block text-meta-label text-ink-muted">
                        {OPERATOR_SYMBOL[rule.operator] ?? rule.operator} threshold
                      </span>
                    </span>

                    {isMinistry ? (
                      <input
                        type="number"
                        step="any"
                        aria-label={`${rule.label} threshold`}
                        defaultValue={rule.threshold}
                        onChange={(event) => set(rule.id, 'threshold', event.target.value)}
                        className={`${FIELD} num w-full text-right`}
                      />
                    ) : (
                      <span className={CELL_NUM}>{String(rule.threshold)}</span>
                    )}

                    {isMinistry ? (
                      <input
                        type="number"
                        min="0"
                        max="100"
                        aria-label={`${rule.label} weight`}
                        defaultValue={rule.weight}
                        onChange={(event) => set(rule.id, 'weight', event.target.value)}
                        className={`${FIELD} num w-full text-right`}
                      />
                    ) : (
                      <span className={CELL_NUM}>{rule.weight}</span>
                    )}

                    <span className="text-body-secondary text-ink">{rule.severity}</span>
                  </li>
                ))}
              </ul>

              {!isMinistry ? (
                <div className="mt-4">
                  <EmptyState title="This account can read the rulebook and cannot change it">
                    Editing the rulebook is the ministry&rsquo;s. Everyone judged by a rule may
                    read it — that is why this page is not withheld from you — and the server
                    refuses an edit from any other role whatever this screen shows.
                  </EmptyState>
                </div>
              ) : (
                <div className={`${CARD} mt-8 p-6`}>
                  <p className={LABEL}>Propose this edit</p>

                  {/* THE NOTICE. Before the button, not after it. */}
                  <div className="mt-2 rounded border-l-4 border-l-gold bg-surface-sunk p-4">
                    <p className="text-table-cell text-ink">
                      This creates a NEW rulebook version. It rescores nothing.
                    </p>
                    <p className={CAPTION}>
                      Every case already in the database keeps the score it was given and goes on
                      pointing at the rulebook snapshot it was scored under. An edit changes what
                      the NEXT evaluation will use — it does not reach backwards and restate what
                      a case was found to say last month. Cases move only when each is recomputed
                      from its own case sheet, or when the corpus is rebuilt.
                    </p>
                  </div>

                  <div className="mt-4">
                    <label htmlFor="note" className={LABEL}>
                      Why (recorded on the version, and required)
                    </label>
                    <input
                      id="note"
                      value={note}
                      onChange={(event) => setNote(event.target.value)}
                      maxLength={2000}
                      className={`${FIELD} w-full`}
                      placeholder="e.g. raise the execution-delay threshold after the September re-measurement"
                    />
                    <p className={CAPTION}>
                      A version whose reason is blank is a version nobody can audit later. The
                      whole point of storing snapshots is that somebody months from now can ask
                      why a threshold moved.
                    </p>
                  </div>

                  {changes.length ? (
                    <ul className="mt-4">
                      {changes.map((change) => (
                        <li
                          key={`${change.rule_id}-${change.key}`}
                          className="num mt-1 text-body-secondary text-ink"
                        >
                          {change.rule_id} · {change.key}: {String(change.from)} →{' '}
                          {String(change.to)}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className={`${CAPTION} mt-4`}>
                      Nothing has been changed yet. Edit a threshold or a weight above.
                    </p>
                  )}

                  {failure ? (
                    <div
                      className="mt-4 rounded border border-border bg-surface-sunk p-4"
                      role="alert"
                    >
                      <p className="text-body-secondary font-medium text-coral">
                        The edit was refused
                      </p>
                      <p className="mt-1 text-body-secondary text-ink-secondary">{failure}</p>
                    </div>
                  ) : null}

                  <button
                    type="submit"
                    disabled={busy || !changes.length || !note.trim()}
                    className={`${BUTTON_PRIMARY} mt-4`}
                  >
                    {busy ? 'Creating version…' : `Create a new version (${changes.length})`}
                  </button>
                </div>
              )}
            </form>

            {result ? (
              <section className="mt-8" role="status">
                <SectionHeading title={`Version ${result.version} created`}>
                  From {result.previous_version}. {result.changes.length} value
                  {result.changes.length === 1 ? '' : 's'} moved.
                </SectionHeading>
                <div className={`${CARD} mt-4 p-6`}>
                  <p className="num text-table-cell text-ink">
                    {result.cases_rescored} cases rescored
                  </p>
                  <p className={CAPTION}>{result.recompute_hint}</p>
                  <ul className="mt-4">
                    {result.changes.map((change) => (
                      <li
                        key={`${change.rule_id}-${change.key}`}
                        className="num text-body-secondary text-ink"
                      >
                        {change.rule_id ?? 'rulebook'} · {change.key}: {String(change.from)} →{' '}
                        {String(change.to)}
                      </li>
                    ))}
                  </ul>
                  <p className="num mt-4 text-meta-label text-ink-muted">
                    snapshot {result.yaml_sha256.slice(0, 16)}
                  </p>
                  <p className={CAPTION}>
                    To see what this would do to a case, open one and use Recompute on its sheet:
                    it re-derives against that case&rsquo;s own snapshot and reports what moved,
                    without changing the stored score.
                  </p>
                </div>
              </section>
            ) : null}

            <section className="mt-8">
              <SectionHeading title="Version history">
                Every stored snapshot, newest first. A version is created and never mutated, which
                is what makes a score from months ago reproducible.
              </SectionHeading>
              <ul className="mt-4">
                {data.versions.map((version) => (
                  <li key={version.id} className={`${CARD} mt-2 p-4`}>
                    <div className="flex flex-wrap items-baseline justify-between gap-4">
                      <span className="num text-table-cell text-ink">{version.version}</span>
                      <span className="num text-meta-label text-ink-muted">
                        {version.yaml_sha256.slice(0, 16)} ·{' '}
                        {String(version.created_at).slice(0, 10)} · by the{' '}
                        {String(version.created_by_role).replace('_', ' ')}
                      </span>
                    </div>
                    {version.note ? <p className={CAPTION}>{version.note}</p> : null}
                  </li>
                ))}
              </ul>
            </section>
          </>
        ) : null}
      </div>
    </article>
  )
}
