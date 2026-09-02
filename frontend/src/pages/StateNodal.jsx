import { useOutletContext } from 'react-router-dom'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel } from '../components/Skeleton.jsx'
import { useApi } from '../hooks/useApi.js'
import { formatCount, formatMoney } from '../severity.js'
import { CAPTION, CARD, COLUMN_HEAD } from '../ui.js'

// The State Nodal landing screen, deliberately minimal — see Ministry.jsx for
// what this phase is and is not doing.
//
// THE STATE NAME COMES FROM THE SESSION, not from a picker and not from a
// route parameter. `user.scope.state` is what the server bound to this account
// and what its predicate uses; asking for any other state's rollup answers 403
// from the grain check, whichever spelling is tried. So the page has exactly
// one state it can ask about, and it asks about that one.

const GRID = 'grid grid-cols-[1fr_88px_88px_88px_120px_100px] items-center gap-4'

export default function StateNodal() {
  const { user } = useOutletContext()
  const state = user.scope?.state

  const { data, error, loading } = useApi(
    state ? `/api/analytics/state/${encodeURIComponent(state)}` : null,
  )

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="state" />

      <PageHeader
        title={state ? `${state} overview` : 'State overview'}
        note="Every district in this state that carries at least one case, ranked by HIGH count. A truncated download of the MPLADS portal, not the state's full record."
      />

      <div className="px-8 py-8">
        {/* An account with the state_nodal role and no state bound to it is a
            provisioning error, not a data problem, and it has to say so — an
            empty screen would look identical to a state with no cases. */}
        {!state ? (
          <EmptyState title="This account has no state bound to it">
            A State Nodal account is scoped to one state. Re-run{' '}
            <code>python -m app.seed_users</code> to provision it against a state that has cases.
          </EmptyState>
        ) : null}

        {loading ? (
          <LoadingRegion label={`Loading the rollup for ${state}`}>
            <SkeletonPanel lines={4} />
          </LoadingRegion>
        ) : null}

        {error ? <ErrorState error={error} /> : null}

        {data ? (
          <>
            <section>
              <SectionHeading title="Case load">
                {formatCount(data.summary.cases)} cases across {data.districts.length} districts,
                as of {data.data_as_of}.
              </SectionHeading>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Cases" value={formatCount(data.summary.cases)} />
                <Figure label="High" value={formatCount(data.summary.high_cases)} />
                <Figure label="Medium" value={formatCount(data.summary.medium_cases)} />
                <Figure label="Low" value={formatCount(data.summary.low_cases)} />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Sanctioned" value={formatMoney(data.summary.sanctioned_amt)} />
                <Figure
                  label="Undisbursed"
                  value={formatMoney(data.summary.undisbursed_amt)}
                  note="Only on cases whose first fund hop is open."
                />
                <Figure label="Worst score" value={data.summary.worst_score} />
                <Figure
                  label="Mean coverage"
                  value={`${data.summary.mean_coverage_pct}%`}
                  note="Skipped rulebook weight is never redistributed."
                />
              </div>

              <p className={`${CAPTION} mt-4 max-w-3xl`}>{data.caption}</p>
            </section>

            <section className="mt-8">
              <SectionHeading title="Districts by HIGH case count">
                The {data.districts.length} districts in {data.state} carrying at least one case.
                Corroborated cases are those where the agency pattern-of-conduct bonus applied.
              </SectionHeading>

              <div className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}>
                <span className={COLUMN_HEAD}>District</span>
                <span className={`${COLUMN_HEAD} text-right`}>Cases</span>
                <span className={`${COLUMN_HEAD} text-right`}>High</span>
                <span className={`${COLUMN_HEAD} text-right`}>Medium</span>
                <span className={`${COLUMN_HEAD} text-right`}>Sanctioned</span>
                <span className={`${COLUMN_HEAD} text-right`}>Corrob.</span>
              </div>

              <ul>
                {data.districts.map((row) => (
                  <li key={row.district} className={`${GRID} ${CARD} mt-2 px-4 py-4`}>
                    <span className="truncate text-table-cell text-ink">{row.district}</span>
                    <span className="num text-right text-table-cell text-ink">
                      {formatCount(row.cases)}
                    </span>
                    <span className="num text-right text-table-cell text-ink">
                      {formatCount(row.high_cases)}
                    </span>
                    <span className="num text-right text-table-cell text-ink">
                      {formatCount(row.medium_cases)}
                    </span>
                    <span className="num text-right text-table-cell text-ink">
                      {formatMoney(row.sanctioned_amt)}
                    </span>
                    <span className="num text-right text-table-cell text-ink">
                      {formatCount(row.corroborated_cases)}
                    </span>
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
