import { Link, useOutletContext, useParams } from 'react-router-dom'

import CaseActions from '../components/CaseActions.jsx'
import { ErrorState } from '../components/EmptyState.jsx'
import { FundLadder, LifecycleLadder } from '../components/Ladder.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import Tag, { SeverityTag, StatusTag } from '../components/Tag.jsx'
import TraceTable from '../components/TraceTable.jsx'
import ZeroPointBadges from '../components/ZeroPointBadges.jsx'
import { useApi } from '../hooks/useApi.js'
import {
  HOP_LABEL,
  LAG_LABEL,
  LAG_MEANING,
  SKIP_REASON,
  formatRupees,
} from '../severity.js'
import { CAPTION, CARD, LABEL } from '../ui.js'

// The case sheet. ONE SCREEN FOR EVERY ROLE.
//
// What differs between a Ministry analyst and a District Magistrate opening a
// case is which cases they can reach, and that is decided in the server's
// query. It is emphatically NOT decided here: nothing on this page branches on
// role except which ACTIONS are offered, and that branch reads `can_write` from
// the server rather than inferring it from the role name. A page that hid a key
// from one role would be a second place scoping lives, and the second place is
// always the one that is wrong.
//
// **The layout is an argument, and it goes in this order deliberately.**
//
//   the score, and what it is out of
//   the two ladders            — the readings the rules were evaluated over
//   the trace                  — every rule, with its evidence ON the row
//   the corroboration bonus    — the only source of score that is not a rule
//   the badges                 — set apart, each printing +0
//   what could not be read     — the coverage, itemised
//   the memo                   — the whole thing as a paragraph
//
// A reader who stops at any point has a true, if shorter, account. The badges
// come AFTER the trace and the bonus because by then the score has already been
// fully accounted for, and their zero is a confirmation of an arithmetic the
// reader has just watched close rather than an assertion made in advance.

export default function CaseDetail() {
  const { caseId } = useParams()
  const { user } = useOutletContext()
  const { data, error, loading, reload } = useApi(`/api/cases/${encodeURIComponent(caseId)}`)

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="district" />

      <PageHeader
        title={loading || error ? 'Case' : (data?.work?.description ?? data?.work?.work_id ?? 'Case')}
        note="Every rule the rulebook holds, what it read, what it compared that against and what it contributed — plus the two ladders those readings were derived from. The arithmetic is on this page in full, so an officer can re-derive the score on paper and an auditor can re-derive it months later."
      />

      <div className="px-8 py-8">
        {loading ? (
          <LoadingRegion label={`Loading case ${caseId}`}>
            <SkeletonPanel lines={4} />
            <SkeletonRows rows={6} />
          </LoadingRegion>
        ) : null}

        {error ? (
          <ErrorState error={error}>
            <Link to="/" className="underline underline-offset-2">
              Back to your own screen
            </Link>
          </ErrorState>
        ) : null}

        {data ? (
          <>
            <section>
              <SectionHeading title={data.case_id}>
                {data.work.work_id} · {data.work.agency ?? 'agency not recorded'} ·{' '}
                {data.work.district ?? data.work.state} · {data.work.fy} · recommended by{' '}
                {data.mp.name}
              </SectionHeading>

              <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
                {/* The score, given the whole width of a column and the app's
                    one display size. The raw total sits under it because the
                    display score is CAPPED at 100 and not renormalised —
                    dividing the weights would change the arithmetic the officer
                    is re-deriving on paper. */}
                <div className={`${CARD} p-6`}>
                  <p className={LABEL}>Score</p>
                  <p className="num font-display text-score-display text-navy">{data.score}</p>
                  <p className="num mt-2 text-body-secondary text-ink-secondary">
                    {data.raw_score} raw of 154 possible · displayed capped at {data.score_cap}
                  </p>
                  <p className={CAPTION}>
                    The sum of the fired rulebook weights below plus the corroboration bonus, and
                    nothing else. Weights are never rescaled.
                  </p>
                  <p className="mt-4 flex flex-wrap items-center gap-2">
                    <SeverityTag severity={data.severity} />
                    <StatusTag status={data.status} />
                    {data.work.is_synthetic ? (
                      <Tag tone="neutral">Synthetic control — excluded from every aggregate</Tag>
                    ) : null}
                  </p>
                  <p className={CAPTION}>
                    HIGH ≥ 75 · MEDIUM ≥ 50 · LOW below 50, on the capped score.
                  </p>
                </div>

                <div className={`${CARD} p-6`}>
                  <p className={LABEL}>Coverage</p>
                  <p className="num font-display text-score-display text-ink">
                    {data.coverage_pct}%
                  </p>
                  <p className={CAPTION}>{data.coverage_basis}</p>
                  <p className={`${CAPTION} mt-2`}>
                    A case at this score with full coverage and a case at this score with two
                    thirds of it are different objects. Skipped weight is never redistributed to
                    the rules that did run.
                  </p>
                </div>

                <div className={`${CARD} p-6`}>
                  <p className={LABEL}>What was found</p>
                  <p className="mt-1 text-table-cell text-ink">
                    {data.gap_hop
                      ? (HOP_LABEL[data.gap_hop] ?? data.gap_hop)
                      : 'No open fund hop'}
                  </p>
                  <p className={CAPTION}>The first open hop walking down the fund ladder.</p>
                  <p className="mt-4 text-table-cell text-ink">
                    {data.slowest_lag
                      ? (LAG_LABEL[data.slowest_lag] ?? data.slowest_lag)
                      : 'No lag computable'}
                  </p>
                  <p className={CAPTION}>
                    {data.slowest_lag
                      ? LAG_MEANING[data.slowest_lag]
                      : 'Neither end of any lag on this work is published.'}
                  </p>
                  <p className="num mt-4 text-meta-label text-ink-muted">
                    Opened {String(data.opened_at).slice(0, 10)} · rulebook{' '}
                    {data.rulebook_version} ({data.rulebook_version_sha256.slice(0, 12)}) · as of{' '}
                    {data.data_as_of}
                  </p>
                </div>
              </div>
            </section>

            <div className="mt-8 grid grid-cols-1 gap-8 xl:grid-cols-2">
              <FundLadder ladder={data.fund_ladder} gapHop={data.gap_hop} />
              <LifecycleLadder ladder={data.lifecycle_ladder} slowestLag={data.slowest_lag} />
            </div>

            {/* Every rule, with each fired duplicate row's cited evidence drawn
                INSIDE it rather than in a section of its own. */}
            <div className="mt-8">
              <TraceTable hits={data.rule_hits} />
            </div>

            <section className="mt-8">
              <SectionHeading title="Pattern-of-conduct corroboration">
                The only source of score that is not a rule. Rendered whether or not it applied —
                an officer has to be able to see the bonus NOT fire, and why.
              </SectionHeading>

              <div
                className={`mt-4 rounded border-y border-r border-border border-l-4 bg-surface px-4 py-4 shadow-card ${
                  data.corroboration.applied ? 'border-l-gold' : 'border-l-border-strong'
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-4">
                  <span className="text-table-cell text-ink">
                    {data.corroboration.agency ?? 'agency not recorded'} ·{' '}
                    {data.corroboration.window}
                  </span>
                  <span className="flex items-center gap-4">
                    <span className="num text-body-secondary text-ink-secondary">
                      {data.corroboration.high_case_count} other HIGH cases, minimum{' '}
                      {data.corroboration.min_high_cases}
                    </span>
                    <span className="num text-table-cell text-ink">
                      {data.corroboration.applied ? `+${data.corroboration.contribution}` : '—'}
                    </span>
                    <span className="text-table-cell text-ink">
                      {data.corroboration.applied ? 'Applied' : 'Not applied'}
                    </span>
                  </span>
                </div>
                <p className={CAPTION}>
                  One bad work is an incident; a pattern under one agency in one financial year is
                  a posture. The bonus is all-or-nothing and is never scaled by the count.
                </p>
              </div>
            </section>

            <div className="mt-8">
              <ZeroPointBadges
                statistical={data.statistical}
                forecast={data.forecast}
                concentration={data.concentration}
              />
            </div>

            {data.unavailable_fields.length > 0 ? (
              <section className="mt-8">
                <SectionHeading title="What could not be read">
                  Graceful degradation, itemised. This list is the difference between a case
                  scored on full coverage and one scored on {data.coverage_pct}%.
                </SectionHeading>

                <ul className="mt-4 grid grid-cols-1 gap-2 lg:grid-cols-2">
                  {data.unavailable_fields.map((field) => (
                    <li key={field.field} className={`${CARD} p-4`}>
                      <div className="flex flex-wrap items-baseline justify-between gap-4">
                        <span className="num text-table-cell text-ink">{field.field}</span>
                        <span className="text-body-secondary text-ink-secondary">
                          {SKIP_REASON[field.reason] ?? field.reason}
                        </span>
                      </div>
                      {field.detail ? <p className={CAPTION}>{field.detail}</p> : null}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            <div className="mt-8 grid grid-cols-1 gap-8 xl:grid-cols-2">
              <section>
                <SectionHeading title="Memo">
                  A TEMPLATE, filled from the values above. Not generated language, not a model,
                  and nothing on this page is described as either. Template now, model later.
                </SectionHeading>
                <div className={`${CARD} mt-4 p-6`}>
                  <p className="whitespace-pre-line text-body text-ink">{data.memo}</p>
                </div>
              </section>

              <section>
                <SectionHeading title="Act on this case">
                  A note and a recompute, both of which write to the append-only trail. Neither
                  changes the stored score.
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

            <p className={`${CAPTION} mt-8 max-w-3xl`}>
              Sanctioned {formatRupees(data.fund_ladder.rungs[0]?.amount) ?? 'not published'} ·
              scored under rulebook {data.rulebook_version} · a recompute re-derives against that
              stored snapshot, not against the rulebook file as it reads today.
            </p>
          </>
        ) : null}
      </div>
    </article>
  )
}
