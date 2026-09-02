import { useOutletContext } from 'react-router-dom'

import CaseRows from '../components/CaseRows.jsx'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Figure from '../components/Figure.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import { useApi } from '../hooks/useApi.js'
import { formatCount, formatMoney } from '../severity.js'
import { CAPTION } from '../ui.js'

// The District Authority landing screen — the case queue, deliberately minimal.
//
// This is the one landing screen that arrives with real case rows on it,
// because /api/analytics/district returns the queue alongside the summary. It
// is therefore also the screen that makes a case sheet reachable by clicking
// rather than by typing an id, which is how the shell becomes walkable end to
// end.
//
// THE DISTRICT COMES FROM THE SESSION. A district name is not unique in this
// corpus — AGRA, KAITHAL, PILIBHIT and SHAHJAHANPUR each name a district in
// five different states — so the server's predicate is `state_id == S AND
// district == D`, both terms, and its grain check compares the district's own
// state against the caller's rather than trusting the name. Nothing on this
// page has to know that; it asks about the one district it was bound to.

export default function District() {
  const { user } = useOutletContext()
  const district = user.scope?.district

  const { data, error, loading } = useApi(
    district ? `/api/analytics/district/${encodeURIComponent(district)}` : null,
  )

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="district" />

      <PageHeader
        title={district ? `${district} case queue` : 'Case queue'}
        note="Ranked highest score first — that ordering IS the triage order. The score and the coverage are shown together on every row, because a case at 50 with full coverage and a case at 50 with two thirds of it are different objects."
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
            <SkeletonRows rows={5} />
          </LoadingRegion>
        ) : null}

        {error ? <ErrorState error={error} /> : null}

        {data ? (
          <>
            <section>
              <SectionHeading title="This district">
                {formatCount(data.summary.cases)} cases under{' '}
                {formatCount(data.agencies.length)}{' '}
                {data.agencies.length === 1 ? 'implementing agency' : 'implementing agencies'} in{' '}
                {data.state}.
              </SectionHeading>

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <Figure label="Cases" value={formatCount(data.summary.cases)} />
                <Figure label="High" value={formatCount(data.summary.high_cases)} />
                <Figure label="Sanctioned" value={formatMoney(data.summary.sanctioned_amt)} />
                <Figure
                  label="Mean coverage"
                  value={`${data.summary.mean_coverage_pct}%`}
                  note="Skipped rulebook weight is never redistributed."
                />
              </div>

              <p className={`${CAPTION} mt-4 max-w-3xl`}>{data.caption}</p>
            </section>

            <section className="mt-8">
              <SectionHeading title="Queue">
                The {data.cases.length} highest-scoring cases in {data.district}, ranked by score
                then by coverage. Every row opens the same case sheet — what a role changes is
                which cases it can reach, never which keys a case carries.
              </SectionHeading>

              {data.cases.length === 0 ? (
                <EmptyState title="No cases in this district">
                  The rollup counts {formatCount(data.summary.cases)} cases here, so an empty queue
                  means the case query and the rollup disagree — that is worth reporting rather
                  than reloading.
                </EmptyState>
              ) : (
                <CaseRows cases={data.cases} />
              )}
            </section>
          </>
        ) : null}
      </div>
    </article>
  )
}
