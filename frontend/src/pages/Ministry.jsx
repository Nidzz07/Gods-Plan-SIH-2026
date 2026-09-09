import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import CaseRows from '../components/CaseRows.jsx'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHero from '../components/PageHero.jsx'
import PreviewList from '../components/PreviewList.jsx'
import ScopedTable from '../components/ScopedTable.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import StatPair from '../components/StatPair.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { AXIS_LINE, AXIS_TICK, CORAL, GRID, INK, INK_SECONDARY, PORTAL } from '../chart.js'
import { useApi } from '../hooks/useApi.js'
import { useLanguage } from '../i18n/useLanguage.js'
import { num, formatRupees, formatRulebookVersion } from '../i18n/format.js'
import { CAPTION, CARD } from '../ui.js'

const FEED_LIMIT = 8

function CustomTooltip({ active, payload, label, lang }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded border border-rule bg-paper p-3 shadow-card text-[14px]">
      <p className="font-semibold text-navy">{label}</p>
      <p className="num mt-1 text-ink">
        {payload[0].name}: <span className="font-bold">{num(payload[0].value, lang)}</span>
      </p>
    </div>
  )
}

export default function Ministry() {
  const { t } = useTranslation()
  const { lang } = useLanguage()

  const national = useApi('/api/analytics/national')
  const feed = useApi(`/api/cases?severity=HIGH&limit=${FEED_LIMIT}`)

  const data = national.data

  // Chart data: states with HIGH cases, 420px tall chart (§C3)
  const rankedStates = useMemo(() => {
    if (!data) return []
    return [...data.top_states_by_high]
      .filter((row) => row.high_cases > 0)
      .slice(0, 10)
      .reverse()
  }, [data])

  // Top 6 states for PreviewList
  const previewItems = useMemo(() => {
    if (!data?.states) return []
    return [...data.states]
      .sort((a, b) => b.high_cases - a.high_cases || b.cases - a.cases)
      .slice(0, 6)
      .map((st) => ({
        id: st.state,
        label: st.state,
        title: `${st.state} Overview`,
        badge: `${num(st.high_cases, lang)} HIGH`,
        meta: `${num(st.cases, lang)} cases · ${num(st.districts, lang)} districts · ${st.mean_coverage_pct ?? '—'}% cov`,
        body: `${num(st.high_cases, lang)} HIGH risk cases identified. Sanctioned volume: ${formatRupees(st.sanctioned_amt, lang) ?? '—'}. Undisbursed across open hops: ${formatRupees(st.undisbursed_amt, lang) ?? '—'}.`,
        href: `/state/${encodeURIComponent(st.state)}`,
      }))
  }, [data, lang])

  const columns = useMemo(
    () => [
      {
        accessorKey: 'state',
        header: t('common.state', 'State'),
        cell: (c) => (
          <Link
            to={`/state/${encodeURIComponent(c.getValue())}`}
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
        header: t('common.highRisk', 'HIGH'),
        meta: { numeric: true },
        cell: (c) => (
          <span className="num font-semibold text-coral">{num(c.getValue(), lang)}</span>
        ),
      },
      {
        accessorKey: 'districts',
        header: t('common.districts', 'Districts'),
        meta: { numeric: true },
        cell: (c) => num(c.getValue(), lang),
      },
      {
        accessorKey: 'mean_coverage_pct',
        header: t('common.meanCoverage', 'Mean coverage'),
        meta: { numeric: true },
        cell: (c) => (c.getValue() === null ? '—' : `${c.getValue()}%`),
      },
      {
        accessorKey: 'sanctioned_amt',
        header: t('common.sanctioned', 'Sanctioned'),
        meta: { numeric: true },
        cell: (c) => formatRupees(c.getValue(), lang) ?? '—',
      },
      {
        accessorKey: 'undisbursed_amt',
        header: t('common.undisbursed', 'Undisbursed'),
        meta: { numeric: true },
        cell: (c) => formatRupees(c.getValue(), lang) ?? '—',
      },
    ],
    [lang, t],
  )

  const cleanRulebookVersion = formatRulebookVersion(data?.rulebook_version || '1.0.0')

  return (
    <article className="relative isolate flex-1 bg-paper w-full">
      {/* Page Hero with single 'v' prefix fix (§1 Defect 1) */}
      <PageHero
        title={t('ministry.title', 'National overview')}
        lede={
          data
            ? t('ministry.lede', {
                totalCases: num(data.total_cases, lang),
                stateCount: num(data.states?.length, lang),
                rulebookVersion: cleanRulebookVersion,
                meanCoverage: data.mean_coverage_pct,
                defaultValue: `${num(data.total_cases, lang)} works across ${num(data.states?.length, lang)} states and union territories, scored against rulebook ${cleanRulebookVersion}. Mean signal coverage ${data.mean_coverage_pct}%.`,
              })
            : '27,078 works across 31 states and union territories, scored against rulebook v1.0.0. Mean signal coverage 58.47%.'
        }
        breadcrumbs={[
          { label: t('common.home', 'Home'), href: '/' },
          { label: t('roles.ministry', 'Ministry'), href: '/ministry' },
          { label: t('ministry.title', 'National overview') },
        ]}
      />

      {/* Main Container: Full main column width without narrow max-w-1240px (§C3) */}
      <div className="w-full px-4 sm:px-6 py-8 space-y-10">
        {national.loading && (
          <LoadingRegion label="Loading national rollup…">
            <SkeletonPanel lines={4} />
            <SkeletonRows rows={6} />
          </LoadingRegion>
        )}

        {national.error && <ErrorState error={national.error} />}

        {data && (
          <>
            {/* Stat strip (§8.1 & §C2) */}
            <section aria-labelledby="stat-strip-heading">
              <h2 id="stat-strip-heading" className="sr-only">
                National case load summary
              </h2>
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure
                  label={t('ministry.highRiskCases', 'HIGH Risk')}
                  value={num(data.high_cases, lang)}
                  note={t('ministry.highRiskNote', { version: cleanRulebookVersion, defaultValue: `Cases scoring ≥ 75 on rulebook ${cleanRulebookVersion}` })}
                />
                <Figure
                  label={t('ministry.mediumRiskCases', 'MEDIUM Risk')}
                  value={num(data.medium_cases, lang)}
                  note={t('ministry.mediumRiskNote', 'Cases scoring between 50 and 74')}
                />
                <Figure
                  label={t('ministry.lowRiskCases', 'LOW Risk')}
                  value={num(data.low_cases, lang)}
                  note={t('ministry.lowRiskNote', 'Cases scoring below 50')}
                />
                <Figure
                  label={t('ministry.corroborated', 'Corroborated')}
                  value={num(data.corroborated_cases, lang)}
                  note={t('ministry.corroboratedNote', 'Agency repetition pattern bonus applied')}
                />
              </div>
            </section>

            {/* Portal Band containing PreviewList (§7 & §8.1) */}
            <section className="rounded border border-rule bg-portal-tint/50 py-card-y px-card-x shadow-card">
              <div className="mb-4">
                <h2 className="font-display text-section-heading text-navy">
                  {t('ministry.highestRiskStates', 'Highest-risk state environments')}
                </h2>
                <div className="mt-1 h-[3px] w-14 bg-saffron" aria-hidden="true" />
                <p className="mt-1 text-body-secondary text-ink-secondary">
                  {t('ministry.highestRiskSubtitle', 'Top states ordered by HIGH case count. Hover or focus to inspect the state\'s risk split and open its comparative view.')}
                </p>
              </div>

              <PreviewList
                items={previewItems}
                title="State priority triage"
                caption="Select a state to inspect aggregated findings"
              />
            </section>

            {/* Charts section enlarged to 420px tall (§C3) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Chart 1: States by HIGH count (420px tall) */}
              <section className={`${CARD} py-card-y px-card-x`}>
                <div className="mb-4">
                  <h3 className="font-display text-section-heading text-navy">
                    {t('ministry.topStatesByHigh', 'States by HIGH case count')}
                  </h3>
                  <p className={CAPTION}>
                    States carrying the highest concentration of high-severity cases. The top bar is
                    highlighted in coral.
                  </p>
                </div>

                <div className="h-[420px] w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={rankedStates}
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
                        dataKey="state"
                        width={140}
                        tick={{ ...AXIS_TICK, fill: INK }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip content={<CustomTooltip lang={lang} />} cursor={{ fill: '#E8EFF5' }} />
                      <Bar dataKey="high_cases" name="HIGH cases" isAnimationActive={false}>
                        {rankedStates.map((entry, idx) => (
                          <Cell
                            key={`cell-${idx}`}
                            fill={idx === rankedStates.length - 1 ? CORAL : PORTAL}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>

              {/* Chart 2: Fund flow proportion (420px tall) */}
              <section className={`${CARD} py-card-y px-card-x flex flex-col justify-between`}>
                <div>
                  <h3 className="font-display text-section-heading text-navy">
                    Fund-flow proportion
                  </h3>
                  <p className={CAPTION}>
                    Sanctioned volume vs. funds sitting behind an open or unverified hop.
                  </p>
                </div>

                <div className="my-6">
                  <StatPair
                    label="National fund flow"
                    totalLabel="Sanctioned in sample"
                    totalValue={formatRupees(data.sanctioned_amt, lang)}
                    totalAmount={data.sanctioned_amt}
                    partLabel="Behind an open hop"
                    partValue={formatRupees(data.undisbursed_amt, lang)}
                    partAmount={data.undisbursed_amt}
                    caption="Sanctioned minus disbursed on open hops. Most unverified amounts reflect MoSPI published export gaps."
                    note={`${num(data.cases_without_expenditure_row, lang)} of ${num(data.total_cases, lang)} cases have no expenditure row in published exports.`}
                  />
                </div>

                <div className="rounded border border-rule bg-paper-sunk py-card-y px-card-x text-[14px] text-ink-secondary">
                  <p>
                    Mean signal coverage stands at{' '}
                    <span className="font-semibold text-ink">{data.mean_coverage_pct}%</span>.
                    Skipped rule weight is never redistributed.
                  </p>
                </div>
              </section>
            </div>

            {/* Full state league table — spans full width of main column (§C3) */}
            <section className="w-full">
              <ScopedTable
                title={t('ministry.stateLeagueTable', 'State league table')}
                caption={t('ministry.stateLeagueSubtitle', 'All 31 states and union territories in the sample. Click any state row to navigate to its district comparison.')}
                columns={columns}
                data={data.states}
                initialSort={[{ id: 'high_cases', desc: true }]}
                footnote="Undisbursed represents sanctioned minus disbursed on works with open first hops."
              />
            </section>

            {/* Highest-scoring HIGH cases feed */}
            <section className="pt-4 w-full">
              <SectionHeading title={t('ministry.recentHighRiskFeed', 'Priority HIGH case triage feed')}>
                {t('ministry.recentHighRiskFeedSubtitle', 'Ranked by composite score, the product\'s triage order. Every row opens the universal case sheet.')}
              </SectionHeading>

              {feed.loading && (
                <LoadingRegion label="Loading case feed…">
                  <SkeletonRows rows={4} />
                </LoadingRegion>
              )}

              {feed.data && (
                <div className="mt-4">
                  {feed.data.items.length === 0 ? (
                    <EmptyState title="No HIGH cases">
                      No case scores 75 or above in the current sample.
                    </EmptyState>
                  ) : (
                    <CaseRows cases={feed.data.items} />
                  )}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </article>
  )
}
