import { useMemo, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHero from '../components/PageHero.jsx'
import PageMotif from '../components/PageMotif.jsx'
import PreviewList from '../components/PreviewList.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import {
  AXIS_LINE,
  AXIS_TICK,
  GRID,
  INK,
  INK_SECONDARY,
  SEVERITY_SERIES,
} from '../chart.js'
import { useApi } from '../hooks/useApi.js'
import { useLanguage } from '../i18n/useLanguage.js'
import { num, formatRupees, formatRulebookVersion } from '../i18n/format.js'
import { CAPTION, CARD, CELL, CELL_NUM, COLUMN_HEAD, SORT_HEAD } from '../ui.js'

const CHART_DISTRICTS = 12

function ChartTooltip({ active, payload, label, valueFormat }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded border border-rule bg-paper p-3 shadow-card text-[14px]">
      <p className="font-semibold text-navy uppercase text-[12px]">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="num text-ink mt-1">
          {entry.name}: <span className="font-bold">{valueFormat ? valueFormat(entry.value) : entry.value}</span>
        </p>
      ))}
    </div>
  )
}

export default function StateNodal() {
  const { t } = useTranslation()
  const { lang } = useLanguage()
  const { user } = useOutletContext()
  const { state: routeState } = useParams()

  // Use URL parameter state if provided (for Ministry drilldown), else user's scoped state
  const targetState = routeState ? decodeURIComponent(routeState) : user.scope?.state

  const { data, error, loading } = useApi(
    targetState ? `/api/analytics/state/${encodeURIComponent(targetState)}` : null,
  )

  // Top 6 districts for PreviewList (§8.2, 38%/62% split in §C4)
  const previewItems = useMemo(() => {
    if (!data?.districts) return []
    return [...data.districts]
      .sort((a, b) => b.high_cases - a.high_cases || b.cases - a.cases)
      .slice(0, 6)
      .map((dst) => ({
        id: dst.district,
        label: dst.district,
        title: `${dst.district} District`,
        badge: `${num(dst.high_cases, lang)} HIGH`,
        meta: `${num(dst.cases, lang)} cases · worst score ${num(dst.worst_score, lang) ?? '—'} · ${dst.mean_coverage_pct ?? '—'}% cov`,
        body: `${num(dst.high_cases, lang)} HIGH, ${num(dst.medium_cases, lang)} MEDIUM, ${num(dst.cases - dst.high_cases - dst.medium_cases, lang)} LOW cases. Sanctioned volume: ${formatRupees(dst.sanctioned_amt, lang) ?? '—'}.`,
        href: `/district/${encodeURIComponent(targetState)}/${encodeURIComponent(dst.district)}`,
      }))
  }, [data, targetState, lang])

  // Distribution chart data: 420px tall stacked bar (§C3)
  const distribution = useMemo(() => {
    if (!data) return []
    return [...data.districts]
      .sort((a, b) => b.high_cases - a.high_cases || b.cases - a.cases)
      .slice(0, CHART_DISTRICTS)
      .reverse()
  }, [data])

  const columns = useMemo(
    () => [
      {
        accessorKey: 'district',
        header: t('common.district', 'District'),
        cell: (c) => (
          <Link
            to={`/district/${encodeURIComponent(targetState)}/${encodeURIComponent(c.getValue())}`}
            className="font-medium text-navy hover:underline"
          >
            {c.getValue()}
          </Link>
        ),
      },
      {
        accessorKey: 'cases',
        header: t('common.cases', 'Cases'),
        meta: { numeric: true },
        cell: (c) => num(c.getValue(), lang),
      },
      {
        accessorKey: 'high_cases',
        header: t('common.highRisk', 'High'),
        meta: { numeric: true },
        cell: (c) => (
          <span className="num font-semibold text-coral">{num(c.getValue(), lang)}</span>
        ),
      },
      {
        accessorKey: 'medium_cases',
        header: t('common.mediumRisk', 'Medium'),
        meta: { numeric: true },
        cell: (c) => num(c.getValue(), lang),
      },
      {
        accessorKey: 'worst_score',
        header: t('common.worstScore', 'Worst score'),
        meta: { numeric: true },
        cell: (c) => (c.getValue() === null ? '—' : num(c.getValue(), lang)),
      },
      {
        accessorKey: 'mean_coverage_pct',
        header: t('common.meanCoverage', 'Mean coverage'),
        meta: { numeric: true },
        cell: (c) => (c.getValue() === null ? '—' : `${c.getValue()}%`),
      },
      {
        accessorKey: 'corroborated_cases',
        header: t('ministry.corroborated', 'Corroborated'),
        meta: { numeric: true },
        cell: (c) => num(c.getValue(), lang),
      },
      {
        accessorKey: 'sanctioned_amt',
        header: t('common.sanctioned', 'Sanctioned'),
        meta: { numeric: true },
        cell: (c) => formatRupees(c.getValue(), lang) ?? '—',
      },
    ],
    [targetState, lang, t],
  )

  const [sorting, setSorting] = useState([{ id: 'high_cases', desc: true }])
  const tableData = useMemo(() => data?.districts ?? [], [data])

  const table = useReactTable({
    data: tableData,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    sortDescFirst: true,
  })

  const cleanRulebookVersion = formatRulebookVersion(data?.rulebook_version || '1.0.0')

  return (
    <article className="relative isolate flex-1 bg-paper w-full">
      <PageMotif variant="state" />

      {/* Page Hero */}
      <PageHero
        title={targetState ? t('state.title', { state: targetState, defaultValue: `${targetState} overview` }) : t('common.overview', 'State overview')}
        lede={
          data
            ? t('state.lede', {
                cases: num(data.summary.cases, lang),
                districts: num(data.districts.length, lang),
                state: data.state,
                rulebookVersion: cleanRulebookVersion,
                meanCoverage: data.summary.mean_coverage_pct,
                defaultValue: `${num(data.summary.cases, lang)} works across ${num(data.districts.length, lang)} districts in ${data.state}, scored against rulebook ${cleanRulebookVersion}. Mean signal coverage ${data.summary.mean_coverage_pct}%.`,
              })
            : 'Every district in this state carrying at least one case, ranked by HIGH case count.'
        }
        breadcrumbs={[
          { label: t('common.home', 'Home'), href: '/' },
          ...(user?.role === 'ministry'
            ? [{ label: t('ministry.title', 'National overview'), href: '/ministry' }]
            : []),
          { label: targetState ? `${targetState} overview` : 'State' },
        ]}
      />

      {/* Main Container: Full main column width (§C3) */}
      <div className="w-full px-4 sm:px-6 py-8 space-y-10">
        {!targetState && (
          <EmptyState title="This account has no state bound to it">
            A State Nodal account is scoped to one state. Re-run{' '}
            <code>python -m app.seed_users</code> to provision it against a state with cases.
          </EmptyState>
        )}

        {loading && (
          <LoadingRegion label={`Loading state data for ${targetState}…`}>
            <SkeletonPanel lines={4} />
            <SkeletonRows rows={5} />
          </LoadingRegion>
        )}

        {error && <ErrorState error={error} />}

        {data && (
          <>
            {/* Stat Strip */}
            <section aria-labelledby="state-stats-heading">
              <h2 id="state-stats-heading" className="sr-only">
                State statistics
              </h2>
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label={t('common.totalCases', 'Total cases')} value={num(data.summary.cases, lang)} />
                <Figure
                  label={t('common.highRisk', 'HIGH cases')}
                  value={num(data.summary.high_cases, lang)}
                  note="Cases requiring urgent inspection"
                />
                <Figure
                  label={t('common.worstScore', 'Worst score')}
                  value={num(data.summary.worst_score, lang) ?? '—'}
                  note="Maximum case score in state"
                />
                <Figure
                  label={t('common.sanctioned', 'Sanctioned')}
                  value={formatRupees(data.summary.sanctioned_amt, lang)}
                  note="Total sanctioned funds"
                />
              </div>
            </section>

            {/* PreviewList of top 6 districts (Expanded to full main-column width per §C4) */}
            <section className="rounded border border-rule bg-portal-tint/50 p-6 shadow-card w-full">
              <div className="mb-4">
                <h2 className="font-display text-section-heading text-navy">
                  {t('state.districtTriage', 'District triage register')} ({data.state})
                </h2>
                <div className="mt-1 h-[3px] w-14 bg-saffron" aria-hidden="true" />
                <p className="mt-1 text-body-secondary text-ink-secondary">
                  {t('state.districtTriageSubtitle', 'All districts within the state ranked by anomaly concentration and severity. Hover or focus to inspect details.')}
                </p>
              </div>

              <PreviewList
                items={previewItems}
                title="District triage queue"
                caption="Select a district to inspect its working case queue"
              />
            </section>

            {/* Severity distribution chart enlarged to 420px tall (§C3) */}
            <section className={`${CARD} p-6 w-full`}>
              <div className="mb-4">
                <h3 className="font-display text-section-heading text-navy">
                  {t('state.highDistricts', 'Severity mix across districts')}
                </h3>
                <p className={CAPTION}>
                  {distribution.length === 1
                    ? `The one district in ${data.state}`
                    : `The ${distribution.length} busiest districts in ${data.state}, worst first`}
                  , each bar split by severity band.
                </p>
              </div>

              <div className="h-[420px] w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={distribution}
                    layout="vertical"
                    margin={{ top: 10, right: 30, left: 40, bottom: 20 }}
                  >
                    <CartesianGrid {...GRID} horizontal={false} />
                    <XAxis
                      type="number"
                      tick={AXIS_TICK}
                      axisLine={AXIS_LINE}
                      tickLine={false}
                      tickFormatter={(v) => num(v, lang)}
                    />
                    <YAxis
                      type="category"
                      dataKey="district"
                      width={140}
                      tick={{ ...AXIS_TICK, fill: INK }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      content={<ChartTooltip valueFormat={(v) => num(v, lang)} />}
                      cursor={{ fill: '#E8EFF5' }}
                    />
                    {SEVERITY_SERIES.map((entry) => (
                      <Bar
                        key={entry.key}
                        dataKey={entry.key}
                        name={entry.label}
                        fill={entry.color}
                        stackId="severity"
                        isAnimationActive={false}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <ul className="mt-4 flex flex-wrap gap-4 border-t border-rule pt-3">
                {SEVERITY_SERIES.map((entry) => (
                  <li key={entry.key} className="flex items-center gap-1.5 text-[13px]">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded"
                      style={{ backgroundColor: entry.color }}
                      aria-hidden="true"
                    />
                    <span className="uppercase text-ink-secondary">{entry.label}</span>
                  </li>
                ))}
              </ul>
            </section>

            {/* All districts sortable table — spans full main-column width */}
            <section className="w-full">
              <div className="mb-4">
                <h3 className="font-display text-section-heading text-navy">
                  Every district in {data.state}
                </h3>
                <p className={CAPTION}>
                  All {num(data.districts.length, lang)} districts in the sample. Click any district row to open its working case queue.
                </p>
              </div>

              <div className="overflow-x-auto rounded border border-rule bg-paper shadow-card">
                <table className="w-full border-collapse">
                  <caption className="sr-only">
                    All districts in {data.state} sortable by severity
                  </caption>
                  <thead>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <tr key={headerGroup.id} className="border-b border-rule bg-paper-sunk">
                        {headerGroup.headers.map((header) => {
                          const sortable = header.column.getCanSort()
                          const direction = header.column.getIsSorted()
                          return (
                            <th
                              key={header.id}
                              scope="col"
                              className={`${COLUMN_HEAD} ${
                                header.column.columnDef.meta?.numeric ? 'text-right' : 'text-left'
                              } px-4 py-3.5`}
                            >
                              {sortable ? (
                                <button
                                  type="button"
                                  onClick={header.column.getToggleSortingHandler()}
                                  className={`${SORT_HEAD} ${
                                    direction ? 'text-ink' : 'text-ink-secondary'
                                  }`}
                                >
                                  {flexRender(
                                    header.column.columnDef.header,
                                    header.getContext(),
                                  )}
                                  {direction === 'asc' ? ' ↑' : direction === 'desc' ? ' ↓' : ''}
                                </button>
                              ) : (
                                flexRender(header.column.columnDef.header, header.getContext())
                              )}
                            </th>
                          )
                        })}
                      </tr>
                    ))}
                  </thead>
                  <tbody>
                    {table.getRowModel().rows.map((row) => (
                      <tr
                        key={row.id}
                        className="border-b border-rule last:border-b-0 hover:bg-portal-tint/40 transition-colors"
                      >
                        {row.getVisibleCells().map((cell) => (
                          <td
                            key={cell.id}
                            className={`${
                              cell.column.columnDef.meta?.numeric ? CELL_NUM : CELL
                            } px-4 py-3.5`}
                          >
                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </div>
    </article>
  )
}
