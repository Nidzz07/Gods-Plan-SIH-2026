import { useMemo } from 'react'
import { Link, useOutletContext } from 'react-router-dom'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import RankedBar from '../components/RankedBar.jsx'
import ScopedTable from '../components/ScopedTable.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { NAVY } from '../chart.js'
import { useApi } from '../hooks/useApi.js'
import {
  HOP_LABEL,
  LAG_LABEL,
  SEVERITY_BORDER,
  countNoun,
  formatCount,
  formatMoney,
  formatRupees,
} from '../severity.js'
import { CAPTION, CARD, LABEL } from '../ui.js'

// The District Authority dashboard — the case queue, and the one screen in this
// product an officer actually works from.
//
// THE QUEUE IS A TABLE HERE AND A LIST ELSEWHERE, deliberately. The Ministry's
// feed is eight rows read once, so it stays the list-of-cards pattern. This is a
// working queue of a hundred rows that an officer re-sorts — by score to triage,
// by coverage to find the cases the rulebook could barely evaluate, by
// sanctioned amount to find where the money is — and that is a table. The
// severity accent, the tabular figures and the right-aligned numerics are the
// same tokens either way, so the two read as one design.
//
// SEVERITY IS THE ROW'S LEFT-BORDER AND THE WORD IN ITS OWN COLUMN, and never a
// tag on top of that. `severity.js` is explicit: where a row carries the
// border, its severity text is plain ink, because colouring the word as well
// encodes one fact twice. The word is still printed — colour alone is not a
// label, and a photocopy of this screen has to survive.
//
// THE DISTRICT COMES FROM THE SESSION. A district name is not unique in this
// corpus, so the server's predicate is `state_id == S AND district == D`, both
// terms. Nothing on this page has to know that; it asks about the one district
// it was bound to.

// A working queue rather than a preview. The endpoint caps at 500; a hundred is
// what an officer scrolls before they would rather filter, and the caption says
// what it is a hundred OF.
const QUEUE_LIMIT = 100

export default function District() {
  const { user } = useOutletContext()
  const district = user.scope?.district

  const { data, error, loading } = useApi(
    district
      ? `/api/analytics/district/${encodeURIComponent(district)}?limit=${QUEUE_LIMIT}`
      : null,
  )

  // Agencies by case load, reversed so the largest sits at the top of the axis.
  const agencies = useMemo(
    () => (data ? [...data.agencies].sort((a, b) => a.cases - b.cases) : []),
    [data],
  )

  // The concentration finding, such as this district's data supports one: what
  // share of the district's cases sit under its single largest agency.
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

  const columns = useMemo(
    () => [
      {
        accessorKey: 'description',
        header: 'Work',
        enableSorting: false,
        cell: (cell) => {
          const row = cell.row.original
          return (
            <>
              {/* The whole row is not the link, because a table row that is a
                  link cannot hold a sortable column header's focus order
                  sensibly. The work description is, and it is the thing an
                  officer is reading anyway. */}
              <Link
                to={`/cases/${row.case_id}`}
                className="block max-w-md truncate text-table-cell text-ink underline-offset-2 hover:underline"
              >
                {row.description ?? row.work_id}
              </Link>
              <span className="block max-w-md truncate text-meta-label text-ink-muted">
                {row.work_id} · {row.gap_hop ? HOP_LABEL[row.gap_hop] : 'no open fund hop'} ·{' '}
                {row.slowest_lag ? LAG_LABEL[row.slowest_lag] : 'no lag computable'}
              </span>
            </>
          )
        },
      },
      {
        accessorKey: 'mp_name',
        header: 'Recommended by',
        cell: (c) => <span className="block max-w-[160px] truncate">{c.getValue()}</span>,
      },
      {
        accessorKey: 'score',
        header: 'Score',
        meta: { numeric: true },
        cell: (c) => c.getValue(),
      },
      {
        accessorKey: 'coverage_pct',
        header: 'Coverage',
        meta: { numeric: true },
        // Printed on every row beside the score and never without it. A case at
        // 50 with full coverage and a case at 50 with two thirds of it are
        // different objects, and a queue showing the score alone is the easiest
        // place in the product to lose that (invariant 2).
        cell: (c) => `${c.getValue()}%`,
      },
      {
        accessorKey: 'severity',
        header: 'Severity',
        // Plain ink, not a tag: the row's left-border already carries this
        // colour, and a tinted tag beside it would be the same fact twice.
        cell: (c) => c.getValue(),
      },
      {
        accessorKey: 'sanctioned_amt',
        header: 'Sanctioned',
        meta: { numeric: true },
        cell: (c) => formatRupees(c.getValue()) ?? 'not published',
      },
    ],
    [],
  )

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="district" />

      <PageHeader
        title={district ? `${district} case queue` : 'Case queue'}
        note="Ranked highest score first — that ordering IS the triage order. Re-sort on any column; the rows are the ones the server already decided this account may see, and sorting never widens that."
      />

      <div className="px-8 py-8">
        {!district ? (
          <EmptyState title="This account has no district bound to it">
            A District Authority account is scoped to one district within one state. Re-run{' '}
            <code>python -m app.seed_users</code> to provision it against a district that has
            cases.
          </EmptyState>
        ) : null}

        {loading ? (
          <LoadingRegion label={`Loading the queue for ${district}`}>
            <SkeletonPanel lines={3} />
            <SkeletonRows rows={6} />
          </LoadingRegion>
        ) : null}

        {error ? <ErrorState error={error} /> : null}

        {data ? (
          <>
            <section>
              <SectionHeading title="This district">
                {countNoun(data.summary.cases, 'case', 'cases')} under{' '}
                {countNoun(data.agencies.length, 'implementing agency', 'implementing agencies')}{' '}
                in {data.state}, as of {data.data_as_of}.
              </SectionHeading>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Cases" value={formatCount(data.summary.cases)} />
                <Figure label="High" value={formatCount(data.summary.high_cases)} />
                <Figure label="Worst score" value={data.summary.worst_score} />
                <Figure
                  label="Mean coverage"
                  value={`${data.summary.mean_coverage_pct}%`}
                  note="Skipped rulebook weight is never redistributed."
                />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Sanctioned" value={formatMoney(data.summary.sanctioned_amt)} />
                <Figure
                  label="Behind an open hop"
                  value={formatMoney(data.summary.undisbursed_amt)}
                  note="Sanctioned minus disbursed, and only on cases whose first fund hop is open."
                />
                <Figure
                  label="No expenditure row"
                  value={formatCount(data.summary.cases_without_expenditure_row)}
                  note="Works the truncated expenditure export never reached. A reporting gap, not a finding."
                />
                <Figure
                  label="Corroborated"
                  value={formatCount(data.summary.corroborated_cases)}
                  note="Cases where the agency pattern-of-conduct bonus applied."
                />
              </div>

              <p className={`${CAPTION} mt-4 max-w-3xl`}>{data.caption}</p>
            </section>

            <section className="mt-8">
              <SectionHeading title="Agency concentration">
                Which implementing agencies this district&rsquo;s cases sit under. This is the
                question the pattern-of-conduct bonus asks per case, asked over the district
                instead of over one work.
              </SectionHeading>

              {topAgency ? (
                <div className={`${CARD} mt-4 p-4`}>
                  <p className={LABEL}>Largest implementing agency</p>
                  <p className="text-table-cell text-ink">{topAgency.row.agency ?? 'not recorded'}</p>
                  <p className="num mt-1 text-body-secondary text-ink-secondary">
                    {formatCount(topAgency.row.cases)} of {formatCount(data.summary.cases)} cases
                    {topAgency.sharePct === null
                      ? ''
                      : ` — ${topAgency.sharePct.toFixed(1)}% of the district`}
                    , {formatCount(topAgency.row.high_cases)} of them HIGH.
                  </p>
                  <p className={CAPTION}>
                    {topAgency.count === 1
                      ? 'Every case in this district sits under one agency, so there is no concentration to compare against. That is a fact about how the district implements, not a finding about the agency — and it means the pattern-of-conduct bonus, which looks for repetition under one agency, has nothing here to distinguish.'
                      : `Concentration across ${formatCount(topAgency.count)} agencies. A large share is not by itself a finding: a district may genuinely run most of its works through one office.`}
                  </p>
                  {/* Said rather than left to be assumed, because the case sheet
                      DOES show a vendor concentration number and a reader moving
                      between the two screens would otherwise expect it here. */}
                  <p className={CAPTION}>
                    Vendor-level concentration — the Herfindahl index over an agency&rsquo;s
                    vendor shares — is computed per case and shown on the case sheet. It is not
                    aggregated to the district by any endpoint this screen can read, and nothing
                    is recomputed in the browser to fill the gap.
                  </p>
                </div>
              ) : null}

              <div className="mt-4">
                <RankedBar
                  title="Cases by implementing agency"
                  caption={
                    data.agencies.length === 1
                      ? `The one agency implementing every case in ${data.district}.`
                      : `All ${formatCount(data.agencies.length)} agencies implementing cases in ${data.district}, largest first.`
                  }
                  data={agencies}
                  categoryKey="agency"
                  series={[{ key: 'cases', label: 'Cases', color: NAVY }]}
                  valueFormat={(value) => formatCount(value)}
                  axisLabel="cases"
                  categoryWidth={240}
                  emptyTitle="No agency recorded"
                  emptyBody="No case in this district carries an implementing agency the portal published."
                />
              </div>
            </section>

            <div className="mt-8">
              <ScopedTable
                title="Queue"
                caption={`${
                  data.summary.cases === 1
                    ? `This district's only case`
                    : data.cases.length === data.summary.cases
                      ? `All ${countNoun(data.summary.cases, 'case', 'cases')} in this district`
                      : `The ${formatCount(data.cases.length)} highest-scoring of this district's ${formatCount(data.summary.cases)} cases`
                }. Severity is the coloured edge on each row and the word in its own column. Every row opens the same case sheet every other role opens.`}
                columns={columns}
                data={data.cases}
                initialSort={[{ id: 'score', desc: true }]}
                rowAccent={(row) => SEVERITY_BORDER[row.severity]}
                emptyTitle="No cases in this district"
                emptyBody={`The rollup counts ${formatCount(data.summary.cases)} cases here, so an empty queue means the case query and the rollup disagree — that is worth reporting rather than reloading.`}
                footnote="Sorting reorders the rows the server already scoped to this account. It never reaches a case outside the district: a case id from anywhere else answers 404, indistinguishable from one that was never issued."
              />
            </div>
          </>
        ) : null}
      </div>
    </article>
  )
}
