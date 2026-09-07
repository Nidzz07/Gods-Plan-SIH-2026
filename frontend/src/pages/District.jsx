import { useMemo, useState } from 'react'
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHero from '../components/PageHero.jsx'
import PageMotif from '../components/PageMotif.jsx'
import RankedBar from '../components/RankedBar.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { NAVY } from '../chart.js'
import { useApi } from '../hooks/useApi.js'
import { useLanguage } from '../i18n/useLanguage.js'
import { num, formatRupees, formatRulebookVersion } from '../i18n/format.js'
import {
  HOP_LABEL,
  LAG_LABEL,
  SEVERITY_BORDER,
} from '../severity.js'
import { CAPTION, CARD, CELL, CELL_NUM, COLUMN_HEAD, SORT_HEAD } from '../ui.js'

const QUEUE_LIMIT = 100

export default function District() {
  const { t } = useTranslation()
  const { lang } = useLanguage()
  const { user } = useOutletContext()
  const { state: routeState, district: routeDistrict } = useParams()
  const navigate = useNavigate()

  const targetDistrict = routeDistrict ? decodeURIComponent(routeDistrict) : user.scope?.district
  const targetState = routeState ? decodeURIComponent(routeState) : user.scope?.state

  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [textFilter, setTextFilter] = useState('')
  const [selectedAgency, setSelectedAgency] = useState(null)

  const { data, error, loading } = useApi(
    targetDistrict
      ? `/api/analytics/district/${encodeURIComponent(targetDistrict)}?limit=${QUEUE_LIMIT}`
      : null,
  )

  // Agencies by case load, reversed for Recharts vertical layout
  const agencies = useMemo(
    () => (data ? [...data.agencies].sort((a, b) => a.cases - b.cases) : []),
    [data],
  )

  const topAgency = useMemo(() => {
    if (!data || data.agencies.length === 0) return null
    const ranked = [...data.agencies].sort((a, b) => b.cases - a.cases)
    const total = ranked.reduce((sum, row) => sum + row.cases, 0)
    return {
      row: ranked[0],
      sharePct: total > 0 ? (ranked[0].cases / total) * 100 : null,
      count: ranked.length,
    }
  }, [data])

  // Client-side filter over cases by severity, agency, and text
  const filteredCases = useMemo(() => {
    if (!data?.cases) return []
    return data.cases.filter((item) => {
      if (severityFilter !== 'ALL' && item.severity !== severityFilter) return false
      if (selectedAgency && item.agency !== selectedAgency) return false
      if (textFilter.trim()) {
        const term = textFilter.toLowerCase()
        const matchId = item.work_id?.toLowerCase().includes(term)
        const matchCase = item.case_id?.toLowerCase().includes(term)
        const matchDesc = item.description?.toLowerCase().includes(term)
        const matchMp = item.mp_name?.toLowerCase().includes(term)
        if (!matchId && !matchCase && !matchDesc && !matchMp) return false
      }
      return true
    })
  }, [data?.cases, severityFilter, selectedAgency, textFilter])

  const columns = useMemo(
    () => [
      {
        accessorKey: 'description',
        header: t('common.works', 'Work & Identification'),
        enableSorting: false,
        cell: (cell) => {
          const row = cell.row.original
          return (
            <div className="py-1 min-w-0">
              <Link
                to={`/cases/${row.case_id}`}
                title={row.description ?? row.work_id}
                className="block truncate text-[16px] font-medium text-navy hover:underline"
              >
                {row.description ?? row.work_id}
              </Link>
              <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[13px] text-ink-secondary">
                <span className="font-mono text-ink-muted">{row.work_id}</span>
                <span>·</span>
                <span>{row.gap_hop ? (HOP_LABEL[row.gap_hop] ?? row.gap_hop) : 'no open hop'}</span>
                <span>·</span>
                <span>{row.slowest_lag ? (LAG_LABEL[row.slowest_lag] ?? row.slowest_lag) : 'no lag'}</span>
              </div>
            </div>
          )
        },
      },
      {
        accessorKey: 'mp_name',
        header: t('district.recommendedBy', 'Recommended by'),
        cell: (c) => (
          <span className="block w-40 truncate text-[15px] text-ink-secondary" title={c.getValue() || ''}>
            {c.getValue() || '—'}
          </span>
        ),
      },
      {
        accessorKey: 'score',
        header: t('common.score', 'Score'),
        meta: { numeric: true },
        cell: (c) => (
          <span className="num text-[17px] font-bold text-navy">{num(c.getValue(), lang)}</span>
        ),
      },
      {
        accessorKey: 'coverage_pct',
        header: t('common.coverage', 'Coverage'),
        meta: { numeric: true },
        cell: (c) => `${c.getValue()}%`,
      },
      {
        accessorKey: 'severity',
        header: t('common.severity', 'Severity'),
        cell: (c) => {
          const val = c.getValue()
          const colorClass =
            val === 'HIGH' ? 'text-coral font-bold' : val === 'MEDIUM' ? 'text-gold font-medium' : 'text-green font-medium'
          const label = val === 'HIGH' ? t('common.high', 'HIGH') : val === 'MEDIUM' ? t('common.medium', 'MEDIUM') : t('common.low', 'LOW')
          return <span className={`text-[14px] uppercase ${colorClass}`}>{label}</span>
        },
      },
      {
        accessorKey: 'sanctioned_amt',
        header: t('common.sanctioned', 'Sanctioned'),
        meta: { numeric: true },
        cell: (c) => (
          <span className="whitespace-nowrap text-[15px]">
            {formatRupees(c.getValue(), lang) ?? t('common.notPublished', 'not published')}
          </span>
        ),
      },
    ],
    [lang, t],
  )

  const [sorting, setSorting] = useState([{ id: 'score', desc: true }])

  const table = useReactTable({
    data: filteredCases,
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
      <PageMotif variant="district" />

      {/* Page Hero with proper pluralisation fix (§1 Defect 2) */}
      <PageHero
        title={targetDistrict ? `${targetDistrict} case queue` : t('district.defaultTitle', 'District queue')}
        lede={
          data
            ? t('district.lede', {
                caseCount: num(data.summary.cases, lang),
                highCount: num(data.summary.high_cases, lang),
                agencyCount: t('district.agencyCount', { count: data.agencies.length }),
                state: data.state,
                rulebookVersion: cleanRulebookVersion,
                meanCoverage: data.summary.mean_coverage_pct,
                defaultValue: `${num(data.summary.cases, lang)} cases (${num(data.summary.high_cases, lang)} HIGH) under ${t('district.agencyCount', { count: data.agencies.length })} in ${data.state}, scored against rulebook ${cleanRulebookVersion}. Mean signal coverage ${data.summary.mean_coverage_pct}%.`,
              })
            : 'Ranked highest score first — this queue is the primary working screen for district inspection.'
        }
        breadcrumbs={[
          { label: t('common.home', 'Home'), href: '/' },
          ...(user?.role === 'ministry'
            ? [{ label: t('ministry.title', 'National overview'), href: '/ministry' }]
            : []),
          ...(targetState
            ? [{ label: `${targetState} overview`, href: `/state/${encodeURIComponent(targetState)}` }]
            : []),
          { label: targetDistrict ? `${targetDistrict} queue` : 'District queue' },
        ]}
      />

      {/* Main Container: Full main column width (§C3) */}
      <div className="w-full px-4 sm:px-6 py-8 space-y-10">
        {!targetDistrict && (
          <EmptyState title={t('district.noDistrictBound', 'This account has no district bound to it')}>
            A District Authority account is scoped to one district. Re-run{' '}
            <code>python -m app.seed_users</code> to provision it against a district with cases.
          </EmptyState>
        )}

        {loading && (
          <LoadingRegion label={`Loading queue for ${targetDistrict}…`}>
            <SkeletonPanel lines={3} />
            <SkeletonRows rows={6} />
          </LoadingRegion>
        )}

        {error && <ErrorState error={error} />}

        {data && (
          <>
            {/* Stat summary */}
            <section aria-labelledby="district-stats-heading">
              <h2 id="district-stats-heading" className="sr-only">
                District metrics
              </h2>
              <div className="grid grid-cols-2 gap-grid-gap lg:grid-cols-4">
                <Figure label={t('common.cases', 'District cases')} value={num(data.summary.cases, lang)} />
                <Figure
                  label={t('common.highRisk', 'HIGH cases')}
                  value={num(data.summary.high_cases, lang)}
                  note="Triage inspection candidates"
                />
                <Figure
                  label={t('common.worstScore', 'Worst score')}
                  value={num(data.summary.worst_score, lang)}
                  note="Maximum case score in district"
                />
                <Figure
                  label={t('common.sanctioned', 'Sanctioned volume')}
                  value={formatRupees(data.summary.sanctioned_amt, lang)}
                  note="Total sanctioned funds"
                />
              </div>
            </section>

            {/* Layout: Rebalanced 34% Agency Concentration / 66% Working Queue (§C3) */}
            <div className="flex flex-col lg:flex-row gap-8 items-start w-full">
              {/* Left: Agency Concentration Panel (34% width, 360px tall chart, §C3) */}
              <section className="w-full lg:w-[34%] shrink-0 rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <h3 className="font-display text-section-heading text-navy">
                  {t('district.agencyConcentration', 'Agency concentration')}
                </h3>
                <p className={CAPTION}>
                  {t('district.agencyCount', { count: data.agencies.length })} in this district. Click
                  an agency to filter the queue.
                </p>

                {topAgency && (
                  <div className="mt-4 rounded bg-portal-tint p-3 text-[14px] text-ink">
                    <p className="font-semibold text-portal">Primary agency: {topAgency.row.agency}</p>
                    <p className="mt-0.5 text-ink-secondary">
                      {num(topAgency.row.cases, lang)} of {num(data.summary.cases, lang)} cases
                      {topAgency.sharePct !== null ? ` (${topAgency.sharePct.toFixed(1)}% share)` : ''}
                    </p>
                  </div>
                )}

                {/* Enlarged 360px tall chart (§C3) */}
                <div className="mt-4 h-[360px] w-full">
                  <RankedBar
                    title=""
                    caption=""
                    data={agencies}
                    categoryKey="agency"
                    series={[{ key: 'cases', label: 'Cases', color: NAVY }]}
                    valueFormat={(value) => num(value, lang)}
                    axisLabel="cases"
                    categoryWidth={140}
                    onBarClick={(entry) =>
                      setSelectedAgency((curr) => (curr === entry.agency ? null : entry.agency))
                    }
                  />
                </div>

                {selectedAgency && (
                  <div className="mt-3 flex items-center justify-between text-[13px] bg-paper-sunk p-2.5 rounded border border-rule">
                    <span>
                      Filtered to: <strong>{selectedAgency}</strong>
                    </span>
                    <button
                      type="button"
                      onClick={() => setSelectedAgency(null)}
                      className="text-portal font-semibold hover:underline"
                    >
                      Clear agency filter
                    </button>
                  </div>
                )}
              </section>

              {/* Right: The Working Queue (66% width, §C3) */}
              <section className="w-full lg:w-[66%] flex-1 space-y-4 min-w-0">
                <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-rule pb-4">
                    <div>
                      <h3 className="font-display text-section-heading text-navy">
                        {t('district.workingQueue', 'Working queue')}
                      </h3>
                      <p className={CAPTION}>
                        {num(filteredCases.length, lang)} cases displayed (minimum 64px row
                        height, 90ms hover). Click any row to open the full case sheet.
                      </p>
                    </div>

                    {/* Severity filter chips: 16px font, 10px×16px padding, 12px gap, 44px min-height (§C4, F2) */}
                    <div className="flex items-center gap-btn-gap shrink-0">
                      {[
                        { key: 'ALL', label: t('district.filterAll', 'ALL') },
                        { key: 'HIGH', label: t('district.filterHigh', 'HIGH') },
                        { key: 'MEDIUM', label: t('district.filterMedium', 'MEDIUM') },
                        { key: 'LOW', label: t('district.filterLow', 'LOW') },
                      ].map((item) => (
                        <button
                          key={item.key}
                          type="button"
                          onClick={() => setSeverityFilter(item.key)}
                          className={`rounded px-4 py-2.5 min-h-[44px] text-[16px] font-semibold transition-colors ${
                            severityFilter === item.key
                              ? 'bg-portal text-white shadow-xs'
                              : 'bg-paper-sunk text-ink-secondary hover:bg-portal-tint hover:text-navy border border-rule'
                          }`}
                        >
                          {item.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Text search filter input */}
                  <div className="mt-4">
                    <input
                      type="text"
                      value={textFilter}
                      onChange={(e) => setTextFilter(e.target.value)}
                      placeholder="Filter queue by work ID, description, MP…"
                      aria-label="Filter queue cases"
                      className="w-full rounded border border-rule bg-paper py-2.5 px-3.5 text-[15px] text-ink placeholder-ink-muted focus:border-portal focus:outline-none"
                    />
                  </div>
                </div>

                {/* Queue Table with full width description column and 64px min-h rows (§C3) */}
                <div className="overflow-x-auto rounded border border-rule bg-paper shadow-card">
                  <table className="w-full border-collapse">
                    <caption className="sr-only">
                      District case queue sorted by risk score
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
                                  header.column.columnDef.meta?.numeric
                                    ? 'text-right'
                                    : 'text-left'
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
                      {table.getRowModel().rows.map((row) => {
                        const original = row.original
                        const borderClass = SEVERITY_BORDER[original.severity] ?? 'border-l-border-strong'
                        return (
                          <tr
                            key={row.id}
                            onClick={() => navigate(`/cases/${original.case_id}`)}
                            className={`min-h-[64px] cursor-pointer border-b border-rule last:border-b-0 border-l-[3px] ${borderClass} hover:bg-portal-tint/70 transition-colors duration-[90ms]`}
                          >
                            {row.getVisibleCells().map((cell) => (
                              <td
                                key={cell.id}
                                className={`${
                                  cell.column.columnDef.meta?.numeric ? CELL_NUM : CELL
                                } px-4 py-4`}
                              >
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                              </td>
                            ))}
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          </>
        )}
      </div>
    </article>
  )
}
