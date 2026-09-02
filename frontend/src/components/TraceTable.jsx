import { OPERATOR_SYMBOL, SKIP_REASON, TRACE_ROW } from '../severity.js'
import { COLUMN_HEAD } from '../ui.js'
import SectionHeading from './SectionHeading.jsx'

// The reasoning trace. Every rule the rulebook holds gets a row, including the
// ones that passed and the ones we could not evaluate — the trace is a record
// of what was examined, not a list of accusations.
//
// Three visually distinct states, because conflating two of them is how an
// audit system loses credibility:
//   fired   coral edge, full-strength ink, its weight in the score
//   passed  green edge, full-strength ink, a dash where the weight would be
//   skipped grey edge, SUNK GROUND, MUTED AND ITALIC — we could not check
//           this, and it must never read as "we checked and it was fine"
//
// Reading, Threshold and Weight are right-aligned with tabular figures: they
// are three columns of measurements, and a reader compares them down the
// column, not across the row.
//
// TWO ADDITIONS OVER THE INHERITED TABLE, both required rather than decorative.
//
// The threshold cell prints the OPERATOR with the number — `< -15`, not `-15`.
// The whole claim of this product is that an officer can re-derive the score
// on paper, and a threshold with no comparison in front of it is half of the
// arithmetic. The inherited table could omit it because its rulebook was all
// one direction; NIGRANI's ten rules run in four (lt, gt, gte, eq).
//
// A skipped row NAMES ITS SKIP REASON. Invariant 2 requires that "not
// published by MoSPI" and "published as zero" stay distinguishable end to end
// — in the derived features, in rule_hits.skip_reason, in the contract, and on
// screen. This is the "on screen". A grey italic row saying only "no reading"
// would collapse a reporting failure by MoSPI into a fact about the work, and
// those are different findings that belong to different people.

const GRID = 'grid grid-cols-[1fr_140px_120px_88px_96px] items-center gap-4'

// A trace value is a float, an integer, a boolean or null. It is printed as
// the rulebook stores it rather than prettified: `true`, not `Yes`, because
// the row beside it says `= true` and the reader is checking one against the
// other. Floats keep two decimals, which is the precision the fund ladder
// reconciles at.
function traceValue(value) {
  if (value === null || value === undefined) return null
  if (typeof value === 'boolean') return String(value)
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2)
  return String(value)
}

// The evidence a fired `duplicate_work` row owes the officer, drawn inside the
// row itself.
//
// Sunk ground and an indent rather than a card, deliberately: this is part of
// the row it sits in, not a second object beside it, and giving it its own
// surface would make it read as a finding of its own. It carries no severity
// colour for the same reason — the row's left border already said how serious
// this is.
//
// The reading — "a cluster for review, not an accusation" — is the SERVER's
// sentence, printed as it arrives. It is written next to the model that
// produced the number, and paraphrasing it here would put two versions of the
// same warning in front of an officer.
function Citation({ citation }) {
  return (
    <div className="mt-2 rounded border-l-4 border-l-border-strong bg-surface-sunk px-4 py-4">
      <p className="text-meta-label uppercase not-italic text-ink-secondary">Cited evidence</p>
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
          Open and compare:{' '}
          <span className="num">{citation.matched_work_ids.join(', ')}</span>
        </p>
      ) : null}
      <p className="mt-2 max-w-3xl text-body-secondary not-italic text-ink-secondary">
        {citation.reading}
      </p>
    </div>
  )
}

export default function TraceTable({ hits }) {
  return (
    <section>
      <SectionHeading title="Reasoning trace">
        Every rule in the rulebook, what it read, what it compared that against, and what it did
        about it — including the rules that passed and the ones there was no reading for.
      </SectionHeading>

      {/* bg-bg on the header row for the same reason the heading is plated: the
          column labels sit on bare ground, and a ruled motif behind them reads
          as a line struck through the table's top edge. */}
      <div className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}>
        <span className={COLUMN_HEAD}>Rule</span>
        <span className={`${COLUMN_HEAD} text-right`}>Reading</span>
        <span className={`${COLUMN_HEAD} text-right`}>Threshold</span>
        <span className={`${COLUMN_HEAD} text-right`}>Weight</span>
        <span className={COLUMN_HEAD}>Status</span>
      </div>

      <ul>
        {hits.map((hit) => {
          const state = TRACE_ROW[hit.status] ?? TRACE_ROW.passed
          const reading = traceValue(hit.raw_value)
          const operator = OPERATOR_SYMBOL[hit.operator] ?? hit.operator

          return (
            <li
              key={hit.rule_id}
              // Not the shared CARD class: CARD sets bg-surface, and the
              // skipped row needs bg-surface-sunk. Two background utilities of
              // equal specificity are resolved by stylesheet order, not by the
              // order written here, so the greyed row would win or lose at
              // random. Same radius and shadow tokens, background left to the
              // state.
              className={`${state.row} mt-2 rounded border-y border-r border-border border-l-4 ${state.border} px-4 py-4 shadow-card`}
            >
              <div className={GRID}>
                <span>
                  <span className="block text-table-cell">{hit.label}</span>
                  <span className="block text-meta-label text-ink-muted">{hit.rule_id}</span>
                </span>

                <span className="num text-right text-table-cell">
                  {/* A null reading is the whole point of a skipped row: there
                      was nothing to quote. The reason it was missing goes
                      underneath, because "no reading" alone does not say
                      whether MoSPI never published the field or the work has
                      simply not reached the stage that produces it. */}
                  {reading ?? 'no reading'}
                  {hit.status === 'skipped' && hit.skip_reason ? (
                    <span className="block text-meta-label normal-case not-italic text-ink-muted">
                      {SKIP_REASON[hit.skip_reason] ?? hit.skip_reason}
                    </span>
                  ) : null}
                </span>

                {/* The comparison, not just the number. `< -15` is what an
                    officer re-derives against; `-15` on its own is not. */}
                <span className="num text-right text-table-cell">
                  {operator} {traceValue(hit.threshold)}
                </span>

                <span className="num text-right text-table-cell">
                  {hit.status === 'fired' ? `+${hit.contribution}` : '—'}
                </span>

                <span className={`text-table-cell ${state.labelClass}`}>{state.label}</span>
              </div>

              {/* The caveat travels with the flag, on the same row, not in a
                  footnote — declared limitation 6 is explicit that the
                  completed-without-payment signal is partly a truncation
                  artefact and that the caveat has to travel with it. */}
              {hit.caveat ? (
                <p className="mt-2 max-w-3xl text-body-secondary not-italic text-ink-secondary">
                  {hit.caveat}
                </p>
              ) : null}

              {/* THE CITATION IS ON THE ROW, and this is where it belongs.
                  `duplicate_work` is the one rule fed by a model output, and it
                  is admissible as a scoring rule ONLY because the row hands
                  over the records the number came from — the matched works, the
                  shared text, the method. It sat in a section of its own for
                  one phase, which put the evidence a screen away from the claim
                  it supports; the same principle that keeps a caveat on its own
                  row keeps this here. */}
              {hit.citation ? <Citation citation={hit.citation} /> : null}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
