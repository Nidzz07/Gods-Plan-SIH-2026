import { Link, useOutletContext, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import CaseActions from '../components/CaseActions.jsx'
import { ErrorState } from '../components/EmptyState.jsx'
import { FundLadder, LifecycleLadder } from '../components/Ladder.jsx'
import PageHero from '../components/PageHero.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import Tag, { SeverityTag, StatusTag } from '../components/Tag.jsx'
import TraceTable from '../components/TraceTable.jsx'
import ZeroPointBadges from '../components/ZeroPointBadges.jsx'
import { useApi } from '../hooks/useApi.js'
import { useLanguage } from '../i18n/useLanguage.js'
import { num } from '../i18n/format.js'
import {
  HOP_LABEL,
  LAG_LABEL,
  LAG_MEANING,
  SKIP_REASON,
  formatRupees,
} from '../severity.js'
import { CAPTION, CARD, LABEL } from '../ui.js'

export default function CaseDetail() {
  const { t } = useTranslation()
  const { lang } = useLanguage()
  const { caseId } = useParams()
  const { user } = useOutletContext()
  const { data, error, loading, reload } = useApi(`/api/cases/${encodeURIComponent(caseId)}`)

  return (
    <article className="relative isolate flex-1 bg-paper">
      {/* §7.2 Page Hero */}
      <PageHero
        title={
          loading || error
            ? t('case.sheetTitle', 'Case sheet')
            : (data?.work?.description ?? data?.work?.work_id ?? t('case.sheetTitle', 'Case sheet'))
        }
        lede={t('case.sheetLede', 'Every rule evaluated against this work, with its readings, tolerances, contributions and corroboration bonus. Reconstructible on paper and auditable months later.')}
        breadcrumbs={[
          { label: t('common.home', 'Home'), href: '/' },
          {
            label: user?.role === 'ministry' ? t('roles.ministry', 'Ministry') : user?.role === 'state_nodal' ? t('common.state', 'State') : t('common.queue', 'Queue'),
            href: user?.role === 'ministry' ? '/ministry' : user?.role === 'state_nodal' ? '/state' : '/district',
          },
          { label: caseId },
        ]}
      />

      <div className="w-full px-4 sm:px-6 py-8 space-y-10">
        {loading && (
          <LoadingRegion label={t('case.loadingSheet', { caseId, defaultValue: `Loading case sheet for ${caseId}…` })}>
            <SkeletonPanel lines={4} />
            <SkeletonRows rows={6} />
          </LoadingRegion>
        )}

        {error && (
          <ErrorState error={error}>
            <p className="mt-2 text-ink-secondary">
              {error.status === 404
                ? t('case.scopeErrorTitle', 'No case with that identifier exists in your scope.')
                : t('case.scopeErrorBody', 'This case is outside your permitted scope.')}
            </p>
            <Link to="/" className="mt-3 inline-block font-semibold text-portal hover:underline">
              {t('common.returnHome', 'Return to your home screen')}
            </Link>
          </ErrorState>
        )}

        {data && (
          <>
            {/* Header info bar */}
            <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
                <div className="space-y-1 max-w-2xl">
                  <span className="font-mono text-[14px] font-bold text-portal">
                    {t('common.caseId', 'Case')} {data.case_id}
                  </span>
                  <h2 className="font-display text-[22px] font-semibold text-navy">
                    {data.work?.description || data.work?.work_id}
                  </h2>
                  <p className="text-[14px] text-ink-secondary">
                    {t('common.workId', 'Work ID')}: <span className="font-mono text-ink">{data.work?.work_id}</span> ·{' '}
                    {t('common.agency', 'Agency')}:{' '}
                    <span className="font-medium text-ink">
                      {data.work?.agency || t('common.notRecorded', 'Not recorded')}
                    </span>{' '}
                    · {t('common.district', 'District')}:{' '}
                    <span className="font-medium text-ink">
                      {data.work?.district || data.work?.state}
                    </span>{' '}
                    · {t('common.fy', 'FY')}: <span className="font-mono text-ink">{data.work?.fy}</span> · {t('case.metaRecommendedBy', 'Recommended by')}{' '}
                    <span className="font-medium text-ink">{data.mp?.name}</span>
                  </p>
                </div>

                {/* Prominent Score Box (§8.5: 64px Source Serif, severity tag, coverage %) */}
                <div className="flex flex-col items-center justify-center rounded border border-rule-strong bg-portal-tint/70 px-8 py-5 text-center min-w-[200px] shadow-card">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-portal">
                    {t('case.compositeScore', 'Composite score')}
                  </span>
                  <p className="num font-display text-[64px] font-semibold text-navy leading-none my-1">
                    {num(data.score, lang)}
                  </p>
                  <div className="mt-1 flex items-center gap-2">
                    <SeverityTag severity={data.severity} />
                    <StatusTag status={data.status} />
                  </div>
                  <span className="num mt-2 text-[13px] font-medium text-ink-secondary">
                    {num(data.coverage_pct, lang)}% {t('common.coverage', 'coverage')}
                  </span>
                  {data.work?.is_synthetic && (
                    <span className="mt-1 text-[11px] font-bold text-coral">{t('case.syntheticControl', 'Synthetic Control')}</span>
                  )}
                </div>
              </div>
            </section>

            {/* Fund & Lifecycle Ladders (≥120px tall) */}
            <div className="grid grid-cols-1 gap-8 xl:grid-cols-2">
              <FundLadder ladder={data.fund_ladder} gapHop={data.gap_hop} />
              <LifecycleLadder ladder={data.lifecycle_ladder} slowestLag={data.slowest_lag} />
            </div>

            {/* Reasoning Trace Table with inline duplicate compare */}
            <TraceTable hits={data.rule_hits} primaryWork={data.work} />

            {/* Pattern of conduct corroboration */}
            <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
              <SectionHeading title={t('case.patternCorroborationTitle', 'Pattern-of-conduct corroboration')}>
                {t('case.patternCorroborationCaption', 'The only score source that is not a rule. Agency-level repetition within the same financial year.')}
              </SectionHeading>

              <div
                className={`mt-4 rounded border-y border-r border-rule border-l-4 py-card-y px-card-x ${
                  data.corroboration.applied
                    ? 'border-l-gold bg-portal-tint/40'
                    : 'border-l-border-strong bg-paper-sunk/50'
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-4">
                  <span className="text-[15px] font-medium text-navy">
                    {t('common.agency', 'Agency')}: {data.corroboration.agency || t('common.notRecorded', 'Not recorded')} · {t('case.window', 'Window')}:{' '}
                    {data.corroboration.window}
                  </span>
                  <div className="flex items-center gap-4 text-[14px]">
                    <span className="num text-ink-secondary">
                      {t('case.otherHighCases', {
                        count: num(data.corroboration.high_case_count, lang),
                        threshold: num(data.corroboration.min_high_cases, lang),
                        defaultValue: `${num(data.corroboration.high_case_count, lang)} other HIGH cases (threshold ≥ ${num(data.corroboration.min_high_cases, lang)})`,
                      })}
                    </span>
                    <span className="num font-bold text-navy">
                      {data.corroboration.applied ? `+${num(data.corroboration.contribution, lang)}` : '0'}
                    </span>
                    <span
                      className={`font-semibold ${
                        data.corroboration.applied ? 'text-gold' : 'text-ink-muted'
                      }`}
                    >
                      {data.corroboration.applied ? t('case.applied', 'Applied') : t('case.notApplied', 'Not applied')}
                    </span>
                  </div>
                </div>
              </div>
            </section>

            {/* Zero Point Badges section (§8.5) */}
            <ZeroPointBadges
              statistical={data.statistical}
              forecast={data.forecast}
              concentration={data.concentration}
            />

            {/* What could not be read */}
            {data.unavailable_fields?.length > 0 && (
              <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <SectionHeading title={t('case.unreadableTitle', 'What could not be read')}>
                  {t('case.unreadableCaption', 'Reporting gaps from published exports. Skipped weight is never redistributed.')}
                </SectionHeading>

                <ul className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                  {data.unavailable_fields.map((field) => (
                    <li
                      key={field.field}
                      className="rounded border border-rule bg-paper-sunk p-3 text-[13px]"
                    >
                      <div className="flex justify-between items-baseline">
                        <span className="font-mono font-semibold text-navy">{field.field}</span>
                        <span className="text-ink-muted italic">
                          {SKIP_REASON[field.reason] ?? field.reason}
                        </span>
                      </div>
                      {field.detail && (
                        <p className="mt-1 text-ink-secondary text-[12px]">{field.detail}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Plain Memo & Actions */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <SectionHeading title={t('case.caseMemoTitle', 'Case Memo')}>
                  {t('case.caseMemoCaption', 'Template-derived plain-language summary (not generated by a language model).')}
                </SectionHeading>
                <div className="mt-4 rounded bg-paper-sunk py-card-y px-card-x text-[15px] leading-relaxed text-ink whitespace-pre-line">
                  {data.memo}
                </div>
              </section>

              <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <SectionHeading title={t('case.officerActionsTitle', 'Officer Actions')}>
                  {t('case.officerActionsCaption', 'Record note or trigger deterministic recompute against stored snapshot.')}
                </SectionHeading>
                <div className="mt-4">
                  <CaseActions
                    caseId={data.case_id}
                    canWrite={Boolean(user?.can_write)}
                    onChanged={reload}
                  />
                </div>
              </section>
            </div>
          </>
        )}
      </div>
    </article>
  )
}
