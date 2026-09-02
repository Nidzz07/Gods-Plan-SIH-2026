import { useMemo } from 'react'

import CaseRows from '../components/CaseRows.jsx'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import RankedBar from '../components/RankedBar.jsx'
import ScopedTable from '../components/ScopedTable.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import StatPair from '../components/StatPair.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { CORAL } from '../chart.js'
import { useApi } from '../hooks/useApi.js'
import { countNoun, formatCount, formatMoney } from '../severity.js'
import { CAPTION } from '../ui.js'

// The Ministry dashboard — the national view, over states.
//
// WHY THERE IS NO MAP ON THIS SCREEN, stated here because it is the first
// question anyone asks of a national oversight dashboard.
//
// A choropleth needs state boundary geometry. This repository has none: there
// is no GeoJSON or TopoJSON anywhere in it, MPLADS publishes no geometry, and
// nothing in `data/raw/` carries a coordinate. The three ways to get one all
// fail a rule this project holds:
//
//   * Fetch boundaries from a CDN at runtime. The demo then depends on
//     conference wifi reaching a third party, which is the same reason the
//     fonts in this app are self-hosted.
//   * Commit a boundary file. That is a new data dependency with its own
//     licence and its own vintage, and Indian state boundaries are a subject on
//     which a wrong file is a political statement rather than a rendering bug.
//   * Approximate the shapes, or place states at hand-picked latitudes and
//     longitudes. This is fabrication. `declared limitation 11` is explicit
//     that MPLADS publishes no coordinates and that NIGRANI never implies a
//     point-located asset.
//
// So the ranking is a ranked bar, which answers the question the map would have
// been asked — which states carry the most HIGH cases — without inventing
// anything. `react-leaflet` stays installed and unused; when a licensed
// boundary file is chosen it drops in behind this component's data.
//
// This screen reads two endpoints. The rollup is one query against
// pre-aggregated tables; the alert feed is the ranked case list filtered to
// HIGH. Both are Ministry-scoped by the server, and nothing here filters.

// Recency is not available, and the feed is ranked by score instead.
//
// Every case in this corpus carries the same `opened_at` — they were all opened
// by one `python -m app.derive_all` run, 27,079 of them, in one transaction. A
// "most recent HIGH cases" feed would therefore be ranking 37 rows by a column
// on which they are all tied, and whatever order fell out would look like
// recency without being it. Score IS the product's triage order (the case list
// endpoint calls itself `ranked_by` that), so the feed is ranked by it and
// titled for what it actually shows.
const FEED_LIMIT = 8

export default function Ministry() {
  const national = useApi('/api/analytics/national')
  const feed = useApi(`/api/cases?severity=HIGH&limit=${FEED_LIMIT}`)

  const data = national.data

  // Ranked highest-first for the chart. `top_states_by_high` arrives ranked by
  // the server on HIGH count then on the value behind an open hop, and it is
  // reversed here because a Recharts vertical layout draws its first category
  // at the BOTTOM of the axis — so the server's first row has to be last for
  // the worst state to sit at the top where a reader looks first.
  const ranked = useMemo(
    () =>
      data
        ? [...data.top_states_by_high]
            .filter((row) => row.high_cases > 0)
            .reverse()
        : [],
    [data],
  )

  const columns = useMemo(
    () => [
      { accessorKey: 'state', header: 'State', cell: (c) => c.getValue() },
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
        accessorKey: 'districts',
        header: 'Districts',
        meta: { numeric: true },
        cell: (c) => formatCount(c.getValue()),
      },
      {
        accessorKey: 'mean_coverage_pct',
        header: 'Mean coverage',
        meta: { numeric: true },
        // A null coverage is a state whose cases carried none, not a zero.
        cell: (c) => (c.getValue() === null ? '—' : `${c.getValue()}%`),
      },
      {
        accessorKey: 'sanctioned_amt',
        header: 'Sanctioned',
        meta: { numeric: true },
        cell: (c) => formatMoney(c.getValue()) ?? '—',
      },
      {
        accessorKey: 'undisbursed_amt',
        header: 'Undisbursed',
        meta: { numeric: true },
        cell: (c) => formatMoney(c.getValue()) ?? '—',
      },
    ],
    [],
  )

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="ministry" />

      <PageHeader
        title="National overview"
        note="Every case in the committed sample, aggregated by state. This is a truncated download of the MPLADS portal, not the national record — no figure on this screen is a national total."
      />

      <div className="px-8 py-8">
        {national.loading ? (
          <LoadingRegion label="Loading the national rollup">
            <SkeletonPanel lines={4} />
            <SkeletonRows rows={5} />
          </LoadingRegion>
        ) : null}

        {national.error ? <ErrorState error={national.error} /> : null}

        {data ? (
          <>
            <section>
              <SectionHeading title="Case load">
                Counts over {formatCount(data.total_cases)} real sanctioned works, scored under
                rulebook {data.rulebook_version} as of {data.data_as_of}. The labelled synthetic
                control is excluded from every figure here.
              </SectionHeading>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Cases" value={formatCount(data.total_cases)} />
                <Figure label="High" value={formatCount(data.high_cases)} />
                <Figure label="Medium" value={formatCount(data.medium_cases)} />
                <Figure label="Low" value={formatCount(data.low_cases)} />
              </div>

              <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <StatPair
                    label="Fund flow"
                    totalLabel="Sanctioned"
                    totalValue={formatMoney(data.sanctioned_amt)}
                    totalAmount={data.sanctioned_amt}
                    partLabel="Behind an open hop"
                    partValue={formatMoney(data.undisbursed_amt)}
                    partAmount={data.undisbursed_amt}
                    caption="The filled portion is sanctioned minus disbursed, counted only on cases whose first fund hop is open. The remainder is NOT money confirmed to have arrived: most of it belongs to works MoSPI's expenditure export never reached."
                    note={`${formatCount(data.cases_without_expenditure_row)} of ${formatCount(data.total_cases)} cases have no expenditure row at all. That is a truncation of the published export, not a finding about anyone, and it is why this is a bar and not a flow diagram.`}
                  />
                </div>

                <div className="grid grid-cols-1 gap-4">
                  <Figure
                    label="Mean coverage"
                    value={`${data.mean_coverage_pct}%`}
                    note="The share of rulebook weight that could actually be evaluated. Skipped weight is never redistributed."
                  />
                  <Figure
                    label="Corroborated"
                    value={formatCount(data.corroborated_cases)}
                    note="Cases where the agency pattern-of-conduct bonus applied — repetition under one agency in one financial year."
                  />
                </div>
              </div>

              <p className={`${CAPTION} mt-4 max-w-3xl`}>{data.caption}</p>
            </section>

            <div className="mt-8">
              <RankedBar
                title="States by HIGH case count"
                caption={`${countNoun(ranked.length, 'state', 'states')} carrying at least one HIGH case, worst first. Ranked on HIGH count, then on the value sitting behind an open fund hop — two states with one HIGH case each are not equally urgent if one has crore behind it. No map: MPLADS publishes no boundary geometry and none is invented here.`}
                data={ranked}
                categoryKey="state"
                series={[{ key: 'high_cases', label: 'High cases', color: CORAL }]}
                valueFormat={(value) => formatCount(value)}
                axisLabel="HIGH cases"
                emptyTitle="No HIGH cases in the sample"
                emptyBody="No state in the committed corpus carries a case scoring 75 or above."
              />
            </div>

            <div className="mt-8">
              <ScopedTable
                title="Every state in the sample"
                caption={`${data.states.length === 1 ? 'The one state' : `All ${countNoun(data.states.length, 'state', 'states')}`} carrying at least one case. Sortable on any column — click a heading. Coverage is weighted by case count, so a district of four does not count as much as one of seven thousand.`}
                columns={columns}
                data={data.states}
                initialSort={[{ id: 'high_cases', desc: true }]}
                footnote="Undisbursed is sanctioned minus disbursed and only on cases whose first fund hop is open, so it is not comparable to the sanctioned column as a percentage."
              />
            </div>

            <section className="mt-8">
              <SectionHeading title="Highest-scoring HIGH cases">
                The {countNoun(feed.data?.items.length ?? FEED_LIMIT, 'worst case', 'worst cases')} anywhere in the sample, across every state. Ranked by
                score, which is this product&rsquo;s triage order — not by recency, because every
                case in this corpus was opened by one derivation run and they all carry the same
                timestamp.
              </SectionHeading>

              {feed.loading ? (
                <LoadingRegion label="Loading the highest-scoring cases">
                  <SkeletonRows rows={4} />
                </LoadingRegion>
              ) : null}

              {feed.error ? <ErrorState error={feed.error} /> : null}

              {feed.data ? (
                feed.data.items.length === 0 ? (
                  <EmptyState title="No HIGH cases">
                    No case in the committed sample scores 75 or above.
                  </EmptyState>
                ) : (
                  <>
                    <CaseRows cases={feed.data.items} />
                    <p className={`${CAPTION} max-w-3xl`}>
                      {formatCount(feed.data.total)} HIGH cases in total. Every row opens the same
                      case sheet every other role opens — what a role changes is which cases it can
                      reach, never which keys a case carries.
                    </p>
                  </>
                )
              ) : null}
            </section>
          </>
        ) : null}
      </div>
    </article>
  )
}
