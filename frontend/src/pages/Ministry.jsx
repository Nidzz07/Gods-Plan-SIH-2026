import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel } from '../components/Skeleton.jsx'
import { useApi } from '../hooks/useApi.js'
import { formatCount, formatCrore } from '../severity.js'
import { CAPTION, CARD, COLUMN_HEAD } from '../ui.js'

// The Ministry landing screen, deliberately minimal.
//
// PHASE SCOPE: this is not the national dashboard. There is no map, no chart
// and no ranking beyond one sorted table, and that is on purpose — the job of
// this phase is to prove that correctly scoped data reaches the screen for
// each of the four personas, and a styled dashboard built before the shell is
// walked is a styled dashboard built on a guess. The charts, the choropleth
// and the rulebook governance panel are the next phase's work.
//
// /api/analytics/national is behind require_role(ministry) and answers 403 to
// every other role, whatever rows it would have returned. Nothing on this page
// filters anything: the numbers below are the rollup tables as the server
// aggregated them.

const GRID = 'grid grid-cols-[1fr_88px_88px_88px_120px_120px] items-center gap-4'

export default function Ministry() {
  const { data, error, loading } = useApi('/api/analytics/national')

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="ministry" />

      <PageHeader
        title="National overview"
        note="Every case in the committed sample, aggregated by state. This is a truncated download of the MPLADS portal, not the national record — no figure on this screen is a national total."
      />

      <div className="px-8 py-8">
        {loading ? (
          <LoadingRegion label="Loading the national rollup">
            <SkeletonPanel lines={4} />
          </LoadingRegion>
        ) : null}

        {error ? <ErrorState error={error} /> : null}

        {data ? (
          <>
            <section>
              <SectionHeading title="Case load">
                Counts over {formatCount(data.total_cases)} real sanctioned works. The labelled
                synthetic control is excluded from every figure here.
              </SectionHeading>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Cases" value={formatCount(data.total_cases)} />
                <Figure label="High" value={formatCount(data.high_cases)} />
                <Figure label="Medium" value={formatCount(data.medium_cases)} />
                <Figure label="Low" value={formatCount(data.low_cases)} />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Sanctioned" value={formatCrore(data.sanctioned_amt)} />
                <Figure
                  label="Undisbursed"
                  value={formatCrore(data.undisbursed_amt)}
                  note="Sanctioned minus disbursed, and only on cases whose first fund hop is open. A work with no expenditure row contributes nothing."
                />
                <Figure
                  label="Mean coverage"
                  value={`${data.mean_coverage_pct}%`}
                  note="The share of rulebook weight that could actually be evaluated. Skipped weight is never redistributed."
                />
                <Figure
                  label="No expenditure row"
                  value={formatCount(data.cases_without_expenditure_row)}
                  note="Works the truncated expenditure export never reached. A reporting gap, not a finding."
                />
              </div>

              <p className={`${CAPTION} mt-4 max-w-3xl`}>{data.caption}</p>
            </section>

            <section className="mt-8">
              <SectionHeading title="States by HIGH case count">
                All {data.states.length} states carrying at least one case, ranked by HIGH count
                and then by the value sitting behind an open fund hop. Scored under rulebook{' '}
                {data.rulebook_version}.
              </SectionHeading>

              {data.states.length === 0 ? (
                <EmptyState title="No states in the rollup">
                  The rollup tables are empty. Run <code>python -m app.derive_all</code> and reload.
                </EmptyState>
              ) : (
                <>
                  <div
                    className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}
                  >
                    <span className={COLUMN_HEAD}>State</span>
                    <span className={`${COLUMN_HEAD} text-right`}>Cases</span>
                    <span className={`${COLUMN_HEAD} text-right`}>High</span>
                    <span className={`${COLUMN_HEAD} text-right`}>Medium</span>
                    <span className={`${COLUMN_HEAD} text-right`}>Sanctioned</span>
                    <span className={`${COLUMN_HEAD} text-right`}>Undisbursed</span>
                  </div>

                  <ul>
                    {[...data.states]
                      .sort(
                        (a, b) =>
                          b.high_cases - a.high_cases ||
                          (b.undisbursed_amt ?? 0) - (a.undisbursed_amt ?? 0) ||
                          a.state.localeCompare(b.state),
                      )
                      .map((row) => (
                        <li
                          key={row.state}
                          className={`${GRID} ${CARD} mt-2 px-4 py-4`}
                        >
                          <span className="truncate text-table-cell text-ink">{row.state}</span>
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
                            {formatCrore(row.sanctioned_amt)}
                          </span>
                          <span className="num text-right text-table-cell text-ink">
                            {formatCrore(row.undisbursed_amt)}
                          </span>
                        </li>
                      ))}
                  </ul>
                </>
              )}
            </section>
          </>
        ) : null}
      </div>
    </article>
  )
}
