import { useMemo } from 'react'
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

import PageHero from '../components/PageHero.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import Figure from '../components/Figure.jsx'
import { AXIS_LINE, AXIS_TICK, GRID, INK, INK_SECONDARY, PORTAL, GREEN } from '../chart.js'
import { CORPUS } from '../data/corpus-facts.js'
import { useLanguage } from '../i18n/useLanguage.js'
import { num } from '../i18n/format.js'
import { formatCount } from '../severity.js'

const COMPARISON_DATA = [
  { name: 'Current coverage', value: CORPUS.meanCoverage, fill: PORTAL },
  { name: 'Potential with linkage', value: CORPUS.ablation.expenditureLinkage.coverageTo, fill: GREEN },
]

const ABLATION_FIELDS = [
  {
    field: 'expenditure_installments.linked_work_id',
    impact: '+30.44 pp',
    skips: '70,647 skips (23,549 works)',
    recommendation:
      'Mandate explicit work_id foreign key in the public expenditure CSV export to connect disbursement hop.',
  },
  {
    field: 'physical_progress.completion_certificate',
    impact: '+3.65 pp',
    skips: '14,104 skips (14,104 works)',
    recommendation:
      'Require upload and recording of physical handover certificates before marking status completed.',
  },
  {
    field: 'beneficiary_details.ward_code',
    impact: '+1.20 pp',
    skips: '8,410 skips',
    recommendation:
      'Include urban local body / panchayat ward identifiers to enable geocoded uniqueness verification.',
  },
]

export default function DataGapReport() {
  const { t } = useTranslation()
  const { lang } = useLanguage()

  function downloadReport() {
    const markdownContent = `# NIGRANI — Data-Gap & Reporting Recommendation Report
Prepared for: Ministry of Statistics and Programme Implementation (MoSPI) · DIID
Date: September 2026

## 1. Executive Summary
Evaluation of 118,704 raw records across twelve published MPLADS exports reveals a mean rule evaluation coverage of 58.47%.

Connecting missing relational keys and eliminating unpublished zero fields will elevate signal coverage from 58.47% to 88.91% (+30.44 percentage points) without changing scheme rules.

## 2. Key Ablation Findings
1. Expenditure Linkage: 70,647 skips across 23,549 works.
2. Asset Completion Evidence: 14,104 skips due to unrecorded handover certificates.
3. Published Zero Fields: 7 fields published as literal zeros rather than omitting unmeasured rungs.

## 3. Recommended Actions for MoSPI Portal Team
- Add canonical work_id key in monthly financial expenditure exports.
- Standardise null/empty representations to avoid false-zero readings.`

    const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'NIGRANI-DATA-GAP-REPORT.md')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <article className="relative isolate flex-1 bg-paper">
      {/* §7.2 Page Hero */}
      <PageHero
        title={t('datagap.title', 'Data-gap recommendation report')}
        lede={t('datagap.lede', 'Ablation analysis demonstrating that linking public expenditure exports raises mean signal coverage from 58.47% to 88.91%.')}
        breadcrumbs={[
          { label: t('common.home', 'Home'), href: '/' },
          { label: t('nav.docs', 'Documentation'), href: '/#docs' },
          { label: t('common.dataGapReport', 'Data-gap report') },
        ]}
        action={
          <button
            type="button"
            onClick={downloadReport}
            className="rounded bg-portal px-4 py-2 text-[14px] font-medium text-white hover:bg-portal-deep"
          >
            {t('common.downloadReport', 'Download report (.md)')}
          </button>
        }
      />

      <div className="mx-auto max-w-[1240px] px-6 py-8 space-y-10">
        {/* Metric summary */}
        <section aria-labelledby="ablation-metrics-heading">
          <h2 id="ablation-metrics-heading" className="sr-only">
            {t('datagap.metricsAria', 'Ablation Metrics')}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-grid-gap">
            <Figure
              label={t('datagap.currMeanCov', 'Current mean coverage')}
              value={`${num(CORPUS.meanCoverage, lang)}%`}
              note={t('datagap.acrossWorks', 'Across 27,078 evaluated works')}
            />
            <Figure
              label={t('datagap.potentialCov', 'Potential coverage')}
              value={`${num(CORPUS.ablation.expenditureLinkage.coverageTo, lang)}%`}
              note={t('datagap.withExpLink', 'With expenditure linkage')}
            />
            <Figure
              label={t('datagap.covGain', 'Coverage gain')}
              value={`+${num(CORPUS.ablation.expenditureLinkage.deltaPp, lang)} pp`}
              note={t('datagap.fromKeyLink', 'From single export key linkage')}
            />
            <Figure
              label={t('datagap.pubZeroFields', 'Published zero fields')}
              value={num(CORPUS.ablation.zeroFields, lang)}
              note={t('datagap.zeroFieldsDesc', 'Fields causing false-zero readings')}
            />
          </div>
        </section>

        {/* Coverage comparison chart */}
        <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
          <SectionHeading title={t('datagap.impactProjTitle', 'Signal coverage impact projection')}>
            {t('datagap.impactProjCaption', 'Comparing current evaluated rule weight against potential coverage when missing relational keys are linked in MoSPI portal exports.')}
          </SectionHeading>

          <div className="mt-6 h-[260px] w-full max-w-xl">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={COMPARISON_DATA}
                layout="vertical"
                margin={{ top: 10, right: 40, left: 60, bottom: 10 }}
              >
                <CartesianGrid {...GRID} horizontal={false} />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tick={AXIS_TICK}
                  axisLine={AXIS_LINE}
                  tickFormatter={(v) => `${v}%`}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={160}
                  tick={{ ...AXIS_TICK, fill: INK }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) => [`${value}%`, t('datagap.chartCoverage', 'Coverage')]}
                  cursor={{ fill: '#E8EFF5' }}
                />
                <Bar dataKey="value" name={t('datagap.chartCoverage', 'Coverage')} isAnimationActive={false}>
                  {COMPARISON_DATA.map((entry, idx) => (
                    <Cell key={`cell-${idx}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Ranked field table */}
        <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
          <SectionHeading title={t('datagap.rankedGapsTitle', 'Ranked data gap findings')}>
            {t('datagap.rankedGapsCaption', 'Specific reporting deficiencies identified in public MPLADS datasets, ordered by coverage loss magnitude.')}
          </SectionHeading>

          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[700px] border-collapse text-[14px]">
              <thead>
                <tr className="border-b border-rule bg-paper-sunk text-left text-[12px] font-semibold text-ink-secondary uppercase">
                  <th className="py-3 px-4">{t('datagap.colDeficient', 'Deficient Field / Export')}</th>
                  <th className="py-3 px-4">{t('datagap.colDelta', 'Coverage Delta')}</th>
                  <th className="py-3 px-4">{t('datagap.colSkipped', 'Evaluations Skipped')}</th>
                  <th className="py-3 px-4">{t('datagap.colRec', 'Actionable Recommendation')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rule">
                {ABLATION_FIELDS.map((item, idx) => (
                  <tr key={idx} className="hover:bg-paper-sunk/40">
                    <td className="py-3.5 px-4 font-mono font-semibold text-navy text-[13px]">
                      {item.field}
                    </td>
                    <td className="py-3.5 px-4 num font-bold text-coral">{item.impact}</td>
                    <td className="py-3.5 px-4 text-ink-secondary text-[13px]">{item.skips}</td>
                    <td className="py-3.5 px-4 text-ink leading-relaxed">{item.recommendation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Formal memo narrative */}
        <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
          <h3 className="font-display text-[20px] font-semibold text-navy mb-4">
            {t('datagap.formalStatementTitle', 'Formal recommendation statement to MoSPI')}
          </h3>
          <div className="space-y-4 text-body text-ink leading-relaxed max-w-4xl">
            <p>
              {t('datagap.formalStatementP1', '1. Retain Relational Integrity Across Exports: Currently, the public expenditure exports lack the uniform work identification keys present in work master datasets. Introducing a standardized composite key (Work ID + District ID) across financial ledgers will immediately recover up to 30.44 percentage points of audit signal without requiring modifications to state accounting systems.')}
            </p>
            <p>
              {t('datagap.formalStatementP2', '2. Distinguish Between Unrecorded and True Zero: Distinguishing between genuinely unspent balances and unrecorded milestone data is critical. Reporting nulls as explicit zero figures creates false-positive anomalies in deterministic rule matching. We recommend enforcing schema validation at portal ingestion to distinguish missing records from numeric zero balances.')}
            </p>
          </div>
        </section>
      </div>
    </article>
  )
}
