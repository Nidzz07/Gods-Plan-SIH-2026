import { useOutletContext } from 'react-router-dom'

import CaseRows from '../components/CaseRows.jsx'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { useApi } from '../hooks/useApi.js'
import { formatCount, formatCrore, formatRupees } from '../severity.js'
import { CAPTION, CARD, COLUMN_HEAD, LABEL } from '../ui.js'

// The Member of Parliament landing screen — the account ladder, deliberately
// minimal.
//
// WHY THIS ROLE EXISTS AT ALL, since it is the one persona that is read-only
// and could have been left out: MPLADS criticism routinely lands on the member
// for a delay that occurred entirely inside the district administration. The
// account ladder shows where their allocation stands and the lifecycle ladder
// on each case shows where the time went. Giving the scheme's subject a view
// and withholding the ability to adjudicate their own findings is the whole
// design of the role.
//
// THE ALLOCATION IS PUBLISHED ONCE, CUMULATIVELY, AND NOT PER YEAR. The portal
// carries one term-to-date allocation per member and no per-year breakdown, so
// the utilisation ratio is computable only on the term_to_date row and every
// per-FY row carries a null allocation with reason `not_published`. Those
// nulls are rendered as "not published", never as zero — a year with no
// published allocation is not a year with no money.

function Rung({ rung }) {
  return (
    <div>
      <p className={LABEL}>{rung.label}</p>
      <p className="num font-display text-section-heading text-ink">
        {rung.amount === null || rung.amount === undefined ? (
          <span className="text-body italic text-ink-muted">
            {rung.availability === 'not_published' ? 'not published' : 'not applicable'}
          </span>
        ) : (
          formatRupees(rung.amount)
        )}
      </p>
    </div>
  )
}

export default function Member() {
  const { user } = useOutletContext()
  const mpId = user.scope?.mp_id

  const { data, error, loading } = useApi(mpId ? `/api/analytics/mp/${mpId}` : null)

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="mp" />

      <PageHeader
        title="My account"
        note="Where this allocation stands, financial year by financial year, and which of these recommendations stalled. This view is read-only: the scheme's subject does not adjudicate the scheme's findings."
      />

      <div className="px-8 py-8">
        {!mpId ? (
          <EmptyState title="This account is not bound to a member">
            A Member of Parliament account is scoped to one member id. Re-run{' '}
            <code>python -m app.seed_users</code> to provision it.
          </EmptyState>
        ) : null}

        {loading ? (
          <LoadingRegion label="Loading the account ladder">
            <SkeletonPanel lines={4} />
            <SkeletonRows rows={4} />
          </LoadingRegion>
        ) : null}

        {error ? <ErrorState error={error} /> : null}

        {data ? (
          <>
            <section>
              <SectionHeading title={data.mp.name}>
                {data.mp.house === 'rajya_sabha' ? 'Rajya Sabha' : 'Lok Sabha'} ·{' '}
                {data.mp.constituency ?? data.mp.state} · term {data.mp.term ?? 'not published'}
              </SectionHeading>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Cases" value={formatCount(data.portfolio?.cases)} />
                <Figure label="High" value={formatCount(data.portfolio?.high_cases)} />
                <Figure label="Sanctioned" value={formatCrore(data.portfolio?.sanctioned_amt)} />
                <Figure
                  label="Utilisation percentile"
                  value={
                    data.utilisation_percentile === null ? null : `${data.utilisation_percentile}`
                  }
                  note={`Against ${formatCount(data.utilisation_peers)} ${data.utilisation_peer_group}.`}
                />
              </div>

              <p className={`${CAPTION} mt-4 max-w-3xl`}>{data.caption}</p>
            </section>

            <section className="mt-8">
              <SectionHeading title="Account ladder">
                Allocated, sanctioned and disbursed, per financial year. MoSPI publishes one
                cumulative allocation per member and no per-year breakdown, so the per-year
                allocation rows read &ldquo;not published&rdquo; and only the term-to-date row
                carries a utilisation ratio. That is a reporting gap, not a zero.
              </SectionHeading>

              <div className="mt-4 space-y-2">
                {data.account.map((ladder) => (
                  <div key={ladder.fy} className={`${CARD} p-4`}>
                    <div className="flex items-baseline justify-between gap-4">
                      <p className={COLUMN_HEAD}>
                        {ladder.fy === 'term_to_date' ? 'Term to date' : ladder.fy}
                      </p>
                      <p className="num text-body-secondary text-ink-secondary">
                        {ladder.mp_utilisation_pct === null ||
                        ladder.mp_utilisation_pct === undefined
                          ? 'utilisation not computable'
                          : `${ladder.mp_utilisation_pct.toFixed(2)}% utilised`}
                      </p>
                    </div>
                    <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-3">
                      {ladder.rungs.map((rung) => (
                        <Rung key={rung.key} rung={rung} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="mt-8">
              <SectionHeading title="Recommendations that scored worst">
                The {data.worst_cases.length} highest-scoring of this member&rsquo;s cases, across
                every district and every year. Opening one shows the lifecycle ladder, which is
                where a delay is attributed to the stage it actually occurred in.
              </SectionHeading>

              {data.worst_cases.length === 0 ? (
                <EmptyState title="No cases for this member">
                  No sanctioned work recommended by this member produced a case in the committed
                  sample.
                </EmptyState>
              ) : (
                <CaseRows cases={data.worst_cases} />
              )}
            </section>
          </>
        ) : null}
      </div>
    </article>
  )
}
