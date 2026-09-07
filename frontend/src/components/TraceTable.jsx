import { useState } from 'react'
import { OPERATOR_SYMBOL, SKIP_REASON, TRACE_ROW } from '../severity.js'
import { COLUMN_HEAD } from '../ui.js'
import SectionHeading from './SectionHeading.jsx'
import DuplicateCompareModal from './DuplicateCompareModal.jsx'

const GRID = 'grid grid-cols-[1fr_140px_120px_88px_96px] items-center gap-4'

function traceValue(value) {
  if (value === null || value === undefined) return null
  if (typeof value === 'boolean') return String(value)
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2)
  return String(value)
}

function Citation({ citation, onOpenCompare }) {
  return (
    <div className="mt-3 rounded border-l-4 border-l-border-strong bg-surface-sunk py-card-y px-card-x">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-meta-label uppercase not-italic text-ink-secondary">Cited evidence</p>
        <button
          type="button"
          onClick={onOpenCompare}
          className="rounded border border-rule-strong bg-paper px-3 py-1 text-[12px] font-semibold text-portal hover:bg-portal-tint"
        >
          Compare side-by-side
        </button>
      </div>

      <p className="mt-1 text-table-cell not-italic text-ink">
        &ldquo;{citation.shared_description}&rdquo;
      </p>

      <p className="num mt-1 text-body-secondary not-italic text-ink-secondary">
        Similarity {citation.similarity} by {citation.method}
        {citation.cluster_size ? `, in a cluster of ${citation.cluster_size}` : ''}
        {citation.agency ? `, under ${citation.agency}` : ''}.
      </p>

      {citation.matched_work_ids?.length ? (
        <p className="mt-2 text-body-secondary not-italic text-ink">
          Candidate works:{' '}
          <span className="num font-mono text-[13px]">{citation.matched_work_ids.join(', ')}</span>
        </p>
      ) : null}

      <p className="mt-2 max-w-3xl text-body-secondary not-italic text-ink-secondary">
        {citation.reading}
      </p>
    </div>
  )
}

export default function TraceTable({ hits, primaryWork }) {
  const [activeModalCitation, setActiveModalCitation] = useState(null)

  return (
    <section>
      <SectionHeading title="Reasoning trace">
        Every rule in the rulebook, what it read, what it compared that against, and what it did
        about it — including the rules that passed and the ones there was no reading for.
      </SectionHeading>

      <div className={`${GRID} mt-4 border-b border-border-strong bg-paper-sunk px-4 pb-2 pt-2`}>
        <span className={COLUMN_HEAD}>Rule</span>
        <span className={`${COLUMN_HEAD} text-right`}>Reading</span>
        <span className={`${COLUMN_HEAD} text-right`}>Threshold</span>
        <span className={`${COLUMN_HEAD} text-right`}>Weight</span>
        <span className={COLUMN_HEAD}>Status</span>
      </div>

      <ul className="space-y-card-gap mt-4">
        {hits.map((hit) => {
          const state = TRACE_ROW[hit.status] ?? TRACE_ROW.passed
          const reading = traceValue(hit.raw_value)
          const operator = OPERATOR_SYMBOL[hit.operator] ?? hit.operator

          return (
            <li
              key={hit.rule_id}
              className={`${state.row} rounded border-y border-r border-border border-l-4 ${state.border} py-card-y px-card-x shadow-card`}
            >
              <div className={GRID}>
                <span>
                  <span className="block text-table-cell font-medium">{hit.label}</span>
                  <span className="block text-meta-label text-ink-muted">{hit.rule_id}</span>
                </span>

                <span className="num text-right text-table-cell">
                  {reading ?? 'no reading'}
                  {hit.status === 'skipped' && hit.skip_reason ? (
                    <span className="block text-meta-label normal-case not-italic text-ink-muted">
                      {SKIP_REASON[hit.skip_reason] ?? hit.skip_reason}
                    </span>
                  ) : null}
                </span>

                <span className="num text-right text-table-cell">
                  {operator} {traceValue(hit.threshold)}
                </span>

                <span className="num text-right text-table-cell font-semibold">
                  {hit.status === 'fired' ? `+${hit.contribution}` : '—'}
                </span>

                <span className={`text-table-cell font-medium ${state.labelClass}`}>
                  {state.label}
                </span>
              </div>

              {hit.caveat && (
                <p className="mt-2 max-w-3xl text-body-secondary not-italic text-ink-secondary">
                  {hit.caveat}
                </p>
              )}

              {hit.citation && (
                <Citation
                  citation={hit.citation}
                  onOpenCompare={() => setActiveModalCitation(hit.citation)}
                />
              )}
            </li>
          )
        })}
      </ul>

      <DuplicateCompareModal
        isOpen={Boolean(activeModalCitation)}
        onClose={() => setActiveModalCitation(null)}
        primaryWork={primaryWork}
        citation={activeModalCitation}
      />
    </section>
  )
}
