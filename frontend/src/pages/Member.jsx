import { useMemo } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHero from '../components/PageHero.jsx'
import PageMotif from '../components/PageMotif.jsx'
import ScopedTable from '../components/ScopedTable.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { GREEN, GOLD, NAVY } from '../chart.js'
import { useApi } from '../hooks/useApi.js'
import { useLanguage } from '../i18n/useLanguage.js'
import { num, formatRupees, formatRulebookVersion } from '../i18n/format.js'
import {
  HOP_LABEL,
  LAG_LABEL,
  SEVERITY_BORDER,
  SKIP_REASON,
} from '../severity.js'
import { CAPTION } from '../ui.js'

const TERM = 'term_to_date'

const RUNG_COLOR = {
  allocated_amt: NAVY,
  sanctioned_amt: GOLD,
  disbursed_amt: GREEN,
}

function Rung({ rung, scale, lang, t }) {
  const published = rung.availability === 'published' || rung.availability === 'published_zero'
  const width = published && scale > 0 ? Math.max((rung.amount ?? 0) / scale, 0) * 100 : 0

  return (
    <div className="grid grid-cols-[150px_1fr_180px] items-center gap-4 py-1.5">
      <span className="text-[13px] font-semibold uppercase tracking-wider text-ink-secondary whitespace-nowrap">
        {rung.label}
      </span>

      {published ? (
        <span className="block h-[22px] w-full rounded bg-paper-sunk overflow-hidden border border-rule/40">
          <span
            className="block h-[22px] rounded"
            style={{ width: `${width}%`, backgroundColor: RUNG_COLOR[rung.key] }}
            aria-hidden="true"
          />
        </span>
      ) : (
        <span className="flex h-[22px] w-full items-center rounded border border-dashed border-rule-strong bg-paper-sunk/50 px-2.5">
          <span className="text-[12px] font-medium text-ink-muted uppercase tracking-wider">
            {SKIP_REASON[rung.availability] ?? t('common.notPublishedByMospi', 'not published by MoSPI')}
          </span>
        </span>
      )}

      <span className="num text-right text-[15px] text-ink font-medium">
        {published ? (
          formatRupees(rung.amount ?? 0, lang)
        ) : (
          <span className="italic text-ink-muted text-[13px]">
            {SKIP_REASON[rung.availability] ?? t('common.notPublishedByMospi', 'not published by MoSPI')}
          </span>
        )}
      </span>
    </div>
  )
}

function AccountLadderCard({ ladder, scale, title, caption, lang, t }) {
  return (
    <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card w-full">
      <div className="flex flex-wrap items-baseline justify-between gap-4 border-b border-rule pb-2.5">
        <p className="font-display font-semibold text-navy text-[17px]">{title}</p>
        <p className="num text-[14px] font-medium text-ink-secondary">
          {ladder.mp_utilisation_pct === null || ladder.mp_utilisation_pct === undefined
            ? t('common.notPublished', 'utilisation not published')
            : `${ladder.mp_utilisation_pct.toFixed(2)}% utilised`}
        </p>
      </div>

      <div className="mt-3 space-y-2">
        {ladder.rungs.map((rung) => (
          <Rung key={rung.key} rung={rung} scale={scale} lang={lang} t={t} />
        ))}
      </div>

      {caption && <p className="mt-3 text-[13px] text-ink-secondary">{caption}</p>}
    </div>
  )
}

export default function Member() {
  const { t } = useTranslation()
  const { lang } = useLanguage()
  const { user } = useOutletContext()
  const mpId = user.scope?.mp_id
  const navigate = useNavigate()

  const { data, error, loading } = useApi(mpId ? `/api/analytics/mp/${mpId}` : null)

  const term = useMemo(
    () => data?.account.find((row) => row.fy === TERM) ?? null,
    [data],
  )
  const years = useMemo(
    () => data?.account.filter((row) => row.fy !== TERM) ?? [],
    [data],
  )

  const scale = useMemo(() => {
    if (!data) return 0
    const amounts = data.account.flatMap((row) =>
      row.rungs
        .filter((rung) => rung.availability === 'published' || rung.availability === 'published_zero')
        .map((rung) => rung.amount ?? 0),
    )
    return amounts.length ? Math.max(...amounts) : 0
  }, [data])

  const columns = useMemo(
    () => [
      {
        accessorKey: 'description',
        header: t('common.works', 'Work & Details'),
        enableSorting: false,
        cell: (cell) => {
          const row = cell.row.original
          return (
            <div className="py-1 min-w-0">
              <Link
                to={`/cases/${row.case_id}`}
                className="block truncate text-[16px] font-medium text-navy hover:underline"
                title={row.description ?? row.work_id}
              >
                {row.description ?? row.work_id}
              </Link>
              <span className="block text-[13px] text-ink-muted mt-0.5">
                {row.work_id} · {row.gap_hop ? HOP_LABEL[row.gap_hop] : 'no open hop'} ·{' '}
                {row.slowest_lag ? LAG_LABEL[row.slowest_lag] : 'no lag computable'}
              </span>
            </div>
          )
        },
      },
      {
        accessorKey: 'district',
        header: t('common.district', 'District'),
        cell: (c) => c.getValue() ?? '—',
      },
      {
        accessorKey: 'score',
        header: t('common.score', 'Score'),
        meta: { numeric: true },
        cell: (c) => (
          <span className="num font-bold text-navy text-[17px]">{num(c.getValue(), lang)}</span>
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
        cell: (c) => formatRupees(c.getValue(), lang) ?? t('common.notPublished', 'not published'),
      },
    ],
    [lang, t],
  )

  const cleanRulebookVersion = formatRulebookVersion(data?.rulebook_version || '1.0.0')

  return (
    <article className="relative isolate flex-1 bg-paper w-full">
      <PageMotif variant="mp" />

      {/* Page Hero */}
      <PageHero
        title={data ? `${data.mp.name} account` : t('member.defaultTitle', 'Constituency overview')}
        lede={
          data
            ? `${data.mp.house === 'rajya_sabha' ? 'Rajya Sabha' : 'Lok Sabha'} · ${data.mp.constituency ?? data.mp.state} · term ${data.mp.term ?? 'current'}. Read-only audit view: scheme subjects do not adjudicate scheme findings.`
            : 'Member of Parliament account overview and recommended works portfolio.'
        }
        breadcrumbs={[
          { label: t('common.home', 'Home'), href: '/' },
          { label: t('roles.member', 'Member account') },
        ]}
      />

      {/* Main Container: Full main column width (§C3) */}
      <div className="w-full px-4 sm:px-6 py-8 space-y-10">
        {!mpId && (
          <EmptyState title={t('member.noMemberBound', 'This account is not bound to a member')}>
            A Member of Parliament account is scoped to one member id. Re-run{' '}
            <code>python -m app.seed_users</code> to provision it.
          </EmptyState>
        )}

        {loading && (
          <LoadingRegion label="Loading account ladder…">
            <SkeletonPanel lines={4} />
            <SkeletonRows rows={4} />
          </LoadingRegion>
        )}

        {error && <ErrorState error={error} />}

        {data && (
          <>
            {/* Stat Strip */}
            <section aria-labelledby="member-stats-heading">
              <h2 id="member-stats-heading" className="sr-only">
                Member account metrics
              </h2>
              <div className="grid grid-cols-2 gap-grid-gap lg:grid-cols-4">
                <Figure label={t('common.works', 'Recommended works')} value={num(data.portfolio?.cases, lang)} />
                <Figure
                  label={t('common.highRisk', 'HIGH cases')}
                  value={num(data.portfolio?.high_cases, lang)}
                  note="Cases with severe delay or gap"
                />
                <Figure
                  label={t('common.sanctioned', 'Total Sanctioned')}
                  value={formatRupees(data.portfolio?.sanctioned_amt, lang)}
                />
                <Figure
                  label="Utilisation percentile"
                  value={
                    data.utilisation_percentile === null
                      ? '—'
                      : `${num(data.utilisation_percentile, lang)}th`
                  }
                  note={`Against ${num(data.utilisation_peers, lang)} peer members`}
                />
              </div>
            </section>

            {/* Account Ladder Section with 22px bar height (§C4) */}
            <section className="w-full">
              <div className="mb-4">
                <h3 className="font-display text-section-heading text-navy">
                  {t('member.accountLadder', 'Account allocation ladder')}
                </h3>
                <p className={CAPTION}>
                  Allocated, sanctioned and disbursed funds. Unpublished years render as a dashed
                  outline carrying &ldquo;not published by MoSPI&rdquo; — never as a zero bar.
                </p>
              </div>

              {term && (
                <div className="mb-6 w-full">
                  <AccountLadderCard
                    ladder={term}
                    scale={scale}
                    lang={lang}
                    t={t}
                    title="Term to date cumulative allocation"
                    caption="Cumulative allocation published on the portal. MoSPI publishes one cumulative figure per member and no per-financial-year breakdown."
                  />
                </div>
              )}

              {years.length > 0 && (
                <div className="grid grid-cols-1 gap-grid-gap lg:grid-cols-2 w-full">
                  {years.map((ladder) => (
                    <AccountLadderCard
                      key={ladder.fy}
                      ladder={ladder}
                      scale={scale}
                      lang={lang}
                      t={t}
                      title={ladder.fy}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* Portfolio Table */}
            <section className="w-full">
              <div className="mb-4">
                <h3 className="font-display text-section-heading text-navy">
                  {t('member.recommendedWorks', 'Recommended works portfolio')}
                </h3>
                <p className={CAPTION}>
                  All {num(data.worst_cases.length, lang)} works recommended across districts. Read-only view.
                </p>
              </div>

              <ScopedTable
                title=""
                caption=""
                columns={columns}
                data={data.worst_cases}
                initialSort={[{ id: 'score', desc: true }]}
                rowAccent={(row) => SEVERITY_BORDER[row.severity]}
                emptyTitle="No cases for this member"
                emptyBody="No sanctioned work recommended by this member produced a case in the committed sample."
                footnote="This table is read-only. An MP can inspect any case sheet to review the lifecycle ladder and attribution of administrative delays."
              />
            </section>
          </>
        )}
      </div>
    </article>
  )
}
