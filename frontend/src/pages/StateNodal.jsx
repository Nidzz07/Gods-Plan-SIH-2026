import { useMemo } from 'react'
import { useOutletContext } from 'react-router-dom'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import RankedBar from '../components/RankedBar.jsx'
import ScopedTable from '../components/ScopedTable.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import StatPair from '../components/StatPair.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { SEVERITY_SERIES } from '../chart.js'
import { useApi } from '../hooks/useApi.js'
import { countNoun, formatCount, formatMoney } from '../severity.js'
import { CAPTION } from '../ui.js'

// The State Nodal dashboard — the Ministry's view one level down, over the
// districts of one state.
//
// THE STATE COMES FROM THE SESSION, not from a picker and not from a route
// parameter. `user.scope.state` is what the server bound to this account and
// what its predicate uses; asking for any other state's rollup answers 403 from
// the grain check, whichever spelling is tried.
//
// THERE IS NO TREND ON THIS SCREEN, and it is worth being exact about why,
// because a state overview is where a time series is most expected.
//
// A trend needs a time axis and nothing reachable from this role has one. The
// rollup tables aggregate over the whole corpus with no financial-year
// dimension; the case list carries no `fy` at all; and every case in the corpus
// shares one `opened_at`, because they were all opened by a single derivation
// run. A chart drawn from that would be a line through points that are all the
// same date — noise given the shape of a finding, which is worse than an
// absence. The distribution below is what the data genuinely supports: the
// severity MIX across districts, which answers "is this state's problem
// concentrated or spread" without pretending to answer "is it getting worse".
//
// Adding a per-FY aggregate would be a backend change, and this phase does not
// touch the backend. It is written down here as the thing that would have to
// exist first.

// How many districts the distribution chart shows. Uttar Pradesh has 74 and a
// stacked bar of 74 rows is a wall, not a chart — the tail is districts with one
// or two LOW cases each, which the table below carries in full. Twelve is about
// what fits on a projected screen without the category labels colliding.
const CHART_DISTRICTS = 12

export default function StateNodal() {
  const { user } = useOutletContext()
  const state = user.scope?.state

  const { data, error, loading } = useApi(
    state ? `/api/analytics/state/${encodeURIComponent(state)}` : null,
  )

  // The busiest districts, reversed so the worst sits at the top of the axis —
  // a Recharts vertical layout draws its first category at the bottom.
  //
  // Ranked on HIGH count then on total cases, matching the table's opening
  // sort, so the chart and the table under it tell the same story in the same
  // order rather than two orders a reader has to reconcile.
  const distribution = useMemo(() => {
    if (!data) return []
    return [...data.districts]
      .sort((a, b) => b.high_cases - a.high_cases || b.cases - a.cases)
      .slice(0, CHART_DISTRICTS)
      .reverse()
  }, [data])

  const columns = useMemo(
    () => [
      { accessorKey: 'district', header: 'District', cell: (c) => c.getValue() },
      {
        accessorKey: 'cases',
        header: 'Cases',
        meta: { numeric: true },
        cell: (c) => formatCount(c.getValue()),
      },
      {
        accessorKey: 'high_cases',
        header: 'High',
        meta: { numeric: true },
        cell: (c) => formatCount(c.getValue()),
      },
      {
        accessorKey: 'medium_cases',
        header: 'Medium',
        meta: { numeric: true },
        cell: (c) => formatCount(c.getValue()),
      },
      {
        accessorKey: 'worst_score',
        header: 'Worst score',
        meta: { numeric: true },
        cell: (c) => (c.getValue() === null ? '—' : c.getValue()),
      },
      {
        accessorKey: 'mean_coverage_pct',
        header: 'Mean coverage',
        meta: { numeric: true },
        cell: (c) => (c.getValue() === null ? '—' : `${c.getValue()}%`),
      },
      {
        accessorKey: 'corroborated_cases',
        header: 'Corroborated',
        meta: { numeric: true },
        cell: (c) => formatCount(c.getValue()),
      },
      {
        accessorKey: 'sanctioned_amt',
        header: 'Sanctioned',
        meta: { numeric: true },
        cell: (c) => formatMoney(c.getValue()) ?? '—',
      },
    ],
    [],
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
            <SkeletonRows rows={5} />
          </LoadingRegion>
        ) : null}

        {error ? <ErrorState error={error} /> : null}

        {data ? (
          <>
            <section>
              <SectionHeading title="Case load">
                {countNoun(data.summary.cases, 'case', 'cases')} across{' '}
                {countNoun(data.districts.length, 'district', 'districts')}, as of{' '}
                {data.data_as_of}.
              </SectionHeading>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Cases" value={formatCount(data.summary.cases)} />
                <Figure label="High" value={formatCount(data.summary.high_cases)} />
                <Figure label="Medium" value={formatCount(data.summary.medium_cases)} />
                <Figure label="Low" value={formatCount(data.summary.low_cases)} />
              </div>

              <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <StatPair
                    label="Fund flow"
                    totalLabel="Sanctioned"
                    totalValue={formatMoney(data.summary.sanctioned_amt)}
                    totalAmount={data.summary.sanctioned_amt}
                    partLabel="Behind an open hop"
                    partValue={formatMoney(data.summary.undisbursed_amt)}
                    partAmount={data.summary.undisbursed_amt}
                    caption="Sanctioned minus disbursed, counted only on cases whose first fund hop is open. The remainder is not money confirmed delivered — most of it belongs to works MoSPI's expenditure export never reached."
                    note={`${formatCount(data.summary.cases_without_expenditure_row)} of ${formatCount(data.summary.cases)} cases in this state have no expenditure row at all.`}
                  />
                </div>

                <div className="grid grid-cols-1 gap-4">
                  <Figure
                    label="Worst score"
                    value={data.summary.worst_score}
                    note="The highest score any single case in this state carries, capped at 100."
                  />
                  <Figure
                    label="Mean coverage"
                    value={`${data.summary.mean_coverage_pct}%`}
                    note="Weighted by case count. Skipped rulebook weight is never redistributed."
                  />
                </div>
              </div>

              <p className={`${CAPTION} mt-4 max-w-3xl`}>{data.caption}</p>
            </section>

            <div className="mt-8">
              <RankedBar
                title="Severity mix across districts"
                caption={`${distribution.length === 1 ? `The one district in ${data.state}` : `The ${distribution.length} districts in ${data.state} carrying the most HIGH cases, worst first`}, each bar split by severity band. This says whether the state's problem is concentrated in a few districts or spread across many — it is a distribution, not a trend.`}
                data={distribution}
                categoryKey="district"
                series={SEVERITY_SERIES}
                valueFormat={(value) => formatCount(value)}
                axisLabel="cases"
                emptyTitle="No districts to rank"
                emptyBody="No district in this state carries a case."
              />

              {/* The absence is stated on screen rather than left as a gap a
                  reader fills in with an assumption. Same discipline as a
                  skipped rule naming its reason: a thing not shown says why. */}
              <p className={`${CAPTION} max-w-3xl`}>
                No trend is shown because none is computable from what this role can reach: the
                rollups carry no financial-year dimension, the case list carries no year, and
                every case in the corpus shares one opening timestamp from a single derivation
                run. A line through points that are all the same date would be noise in the shape
                of a finding.
                {data.districts.length > CHART_DISTRICTS
                  ? ` The remaining ${data.districts.length - CHART_DISTRICTS} districts are in the table below.`
                  : ''}
              </p>
            </div>

            <div className="mt-8">
              <ScopedTable
                title={`Every district in ${data.state}`}
                caption={`${data.districts.length === 1 ? 'The one district' : `All ${countNoun(data.districts.length, 'district', 'districts')}`} carrying at least one case. Sortable on any column — click a heading. Corroborated counts the cases where the agency pattern-of-conduct bonus applied.`}
                columns={columns}
                data={data.districts}
                initialSort={[{ id: 'high_cases', desc: true }]}
                footnote="District names are not unique across India — AGRA, KAITHAL, PILIBHIT and SHAHJAHANPUR each name a district in five different states — so every row here is this state's district of that name and no other. The state travels with the district in the query, not just in the label."
              />
            </div>
          </>
        ) : null}
      </div>
    </article>
  )
}
