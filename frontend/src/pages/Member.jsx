import { useMemo } from 'react'
import { Link, useOutletContext } from 'react-router-dom'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import ScopedTable from '../components/ScopedTable.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { GREEN, GOLD, NAVY } from '../chart.js'
import { useApi } from '../hooks/useApi.js'
import {
  HOP_LABEL,
  LAG_LABEL,
  SEVERITY_BORDER,
  SKIP_REASON,
  formatCount,
  formatMoney,
  formatRupees,
} from '../severity.js'
import { CAPTION, CARD, LABEL } from '../ui.js'

// The Member of Parliament dashboard — the account ladder and the portfolio.
//
// WHY THIS ROLE EXISTS AT ALL, since it is the one persona that is read-only:
// MPLADS criticism routinely lands on the member for a delay that occurred
// entirely inside the district administration. The account ladder shows where
// their allocation stands; the lifecycle ladder on each case shows where the
// time went. Giving the scheme's subject a view and withholding the ability to
// adjudicate their own findings is the whole design of the role.

const TERM = 'term_to_date'

// Each rung's colour, held next to the ladder rather than in the shared chart
// module because these three are a sequence and not a category set: money
// steps down from allocated to sanctioned to disbursed, and the colours read
// as that descent.
const RUNG_COLOR = {
  allocated_amt: NAVY,
  sanctioned_amt: GOLD,
  disbursed_amt: GREEN,
}

// One rung of the ladder, as a bar.
//
// THE WHOLE POINT OF THIS COMPONENT IS THE UNPUBLISHED CASE. A rung MoSPI never
// published must not render as a zero-width bar: a zero-width bar is visually
// identical to an amount of nothing, and "the portal published no allocation
// for this year" and "this member was allocated nothing this year" are
// different claims — the first is a reporting gap and the second would be a
// finding about a person. So an unavailable rung draws a DASHED EMPTY TRACK
// with the reason written in it, which is a shape a filled bar can never be
// mistaken for, and its amount column says the reason rather than a number.
//
// Every per-FY allocation row in this corpus takes that path: the portal
// publishes one cumulative allocation per member and no per-year breakdown.
function Rung({ rung, scale }) {
  const published = rung.availability === 'published' || rung.availability === 'published_zero'
  const width = published && scale > 0 ? Math.max((rung.amount ?? 0) / scale, 0) * 100 : 0

  return (
    <div className="grid grid-cols-[120px_1fr_160px] items-center gap-4">
      <span className="text-meta-label uppercase text-ink-secondary">{rung.label}</span>

      {published ? (
        <span className="block h-4 w-full rounded bg-surface-sunk">
          <span
            className="block h-4 rounded"
            style={{ width: `${width}%`, backgroundColor: RUNG_COLOR[rung.key] }}
            // The bar is decoration over a number that is already printed
            // beside it, so it is hidden from assistive technology rather than
            // announced twice.
            aria-hidden="true"
          />
        </span>
      ) : (
        <span className="flex h-4 w-full items-center rounded border border-dashed border-border-strong px-2">
          <span className="text-meta-label text-ink-muted">
            {SKIP_REASON[rung.availability] ?? rung.availability}
          </span>
        </span>
      )}

      <span className="num text-right text-table-cell text-ink">
        {published ? (
          formatRupees(rung.amount ?? 0)
        ) : (
          <span className="italic text-ink-muted">
            {SKIP_REASON[rung.availability] ?? rung.availability}
          </span>
        )}
      </span>
    </div>
  )
}

function Ladder({ ladder, scale, title, caption }) {
  return (
    <div className={`${CARD} p-4`}>
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <p className={LABEL}>{title}</p>
        <p className="num text-body-secondary text-ink-secondary">
          {ladder.mp_utilisation_pct === null || ladder.mp_utilisation_pct === undefined
            ? 'utilisation not computable'
            : `${ladder.mp_utilisation_pct.toFixed(2)}% utilised`}
        </p>
      </div>

      <div className="mt-4 space-y-2">
        {ladder.rungs.map((rung) => (
          <Rung key={rung.key} rung={rung} scale={scale} />
        ))}
      </div>

      {caption ? <p className={CAPTION}>{caption}</p> : null}
    </div>
  )
}

export default function Member() {
  const { user } = useOutletContext()
  const mpId = user.scope?.mp_id

  const { data, error, loading } = useApi(mpId ? `/api/analytics/mp/${mpId}` : null)

  const term = useMemo(
    () => data?.account.find((row) => row.fy === TERM) ?? null,
    [data],
  )
  const years = useMemo(
    () => data?.account.filter((row) => row.fy !== TERM) ?? [],
    [data],
  )

  // Every bar on the screen is scaled against ONE maximum, so a year's
  // sanctioned bar can be compared against another year's by eye. Scaling each
  // row to its own maximum would make every year look equally full, which is
  // the opposite of what the picture is for.
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
        header: 'Work',
        enableSorting: false,
        cell: (cell) => {
          const row = cell.row.original
          return (
            <>
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
        accessorKey: 'district',
        header: 'District',
        cell: (c) => c.getValue() ?? '—',
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
        cell: (c) => `${c.getValue()}%`,
      },
      { accessorKey: 'severity', header: 'Severity', cell: (c) => c.getValue() },
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
                <Figure label="Sanctioned" value={formatMoney(data.portfolio?.sanctioned_amt)} />
                <Figure
                  label="Utilisation percentile"
                  value={
                    data.utilisation_percentile === null
                      ? null
                      : `${data.utilisation_percentile}`
                  }
                  note={`Against ${formatCount(data.utilisation_peers)} ${data.utilisation_peer_group}. A percentile, not a rank: it says what share of that peer group has utilised no more than this account has.`}
                />
              </div>

              <p className={`${CAPTION} mt-4 max-w-3xl`}>{data.caption}</p>
            </section>

            <section className="mt-8">
              <SectionHeading title="Account ladder">
                Allocated, sanctioned and disbursed. Every bar on this screen is drawn to one
                scale, so a year can be compared against another by eye. A rung the portal never
                published is a dashed empty track and never a bar of zero length — &ldquo;no
                allocation was published for this year&rdquo; and &ldquo;this member was allocated
                nothing&rdquo; are different claims, and only the first is true here.
              </SectionHeading>

              {term ? (
                <div className="mt-4">
                  <Ladder
                    ladder={term}
                    scale={scale}
                    title="Term to date"
                    caption="The only row carrying a published allocation, and therefore the only one with a utilisation ratio. MoSPI publishes one cumulative allocation per member and no per-year breakdown."
                  />
                </div>
              ) : null}

              {years.length > 0 ? (
                <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
                  {years.map((ladder) => (
                    <Ladder key={ladder.fy} ladder={ladder} scale={scale} title={ladder.fy} />
                  ))}
                </div>
              ) : null}

              <p className={`${CAPTION} max-w-3xl`}>
                The per-year allocation rows read &ldquo;not published&rdquo; because the portal
                publishes no per-year allocation, which is a reporting gap rather than a zero. It
                is why a per-year utilisation ratio cannot be computed for any member, and it is
                a finding in the data-gap report addressed back to MoSPI.
              </p>
            </section>

            <div className="mt-8">
              <ScopedTable
                title="Recommendations that scored worst"
                caption={`The ${formatCount(data.worst_cases.length)} highest-scoring of this member's cases, across every district and every year. Opening one shows the lifecycle ladder, which is where a delay is attributed to the stage it actually occurred in.`}
                columns={columns}
                data={data.worst_cases}
                initialSort={[{ id: 'score', desc: true }]}
                rowAccent={(row) => SEVERITY_BORDER[row.severity]}
                emptyTitle="No cases for this member"
                emptyBody="No sanctioned work recommended by this member produced a case in the committed sample."
                footnote="This table is read-only, as every screen this role reaches is. A case can be opened and cannot be annotated, escalated, resolved or recomputed from here — and the server refuses those writes regardless of what this screen offers."
              />
            </div>
          </>
        ) : null}
      </div>
    </article>
  )
}
