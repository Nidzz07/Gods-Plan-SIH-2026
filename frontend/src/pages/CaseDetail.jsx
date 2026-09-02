import { Link, useParams } from 'react-router-dom'

import { ErrorState } from '../components/EmptyState.jsx'
import { FundLadder, LifecycleLadder } from '../components/Ladder.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import Tag, { SeverityTag, StatusTag } from '../components/Tag.jsx'
import TraceTable from '../components/TraceTable.jsx'
import { useApi } from '../hooks/useApi.js'
import { HOP_LABEL, LAG_LABEL, LAG_MEANING, SKIP_REASON, formatRupees } from '../severity.js'
import { CAPTION, CARD, LABEL } from '../ui.js'

// The case sheet. ONE SCREEN FOR EVERY ROLE.
//
// What differs between a Ministry analyst and a District Magistrate opening a
// case is which cases they can reach, and that is decided in the server's
// query (invariant 10). It is emphatically NOT decided here: nothing on this
// page branches on role, because a page that hid a key from one role would be
// a second place scoping lives, and the second place is always the one that is
// wrong. A case id outside a caller's scope answers 404 — indistinguishable
// from an id that was never issued — and this screen renders that refusal.
//
// PHASE SCOPE. Simply formatted on purpose: the trace, both ladders, the
// coverage, the badges and the memo, each in a plain section. The polished
// sheet — the score display, the audit trail, notes, recompute — is Phase 10.
// What this proves is that the frozen contract renders end to end and that a
// case reached by clicking a queue row is the same object the contract froze.

// The three zero-point badges, stated as figures with the invariant on the
// same block. Tiers 3 and 4 confirm or fail to confirm what the rulebook
// already found; they never move the number, and a screen that showed them
// without saying so would be the overclaim CLAUDE.md's honesty rules name.
function Badge({ label, value, children }) {
  return (
    <div className={`${CARD} p-4`}>
      <div className="flex items-baseline justify-between gap-4">
        <p className={LABEL}>{label}</p>
        <Tag tone="neutral">0 points</Tag>
      </div>
      <p className="num font-display text-section-heading text-ink">{value ?? '—'}</p>
      {children ? <p className={CAPTION}>{children}</p> : null}
    </div>
  )
}

// A skip reason as a tag label, capitalised WITHOUT being lowercased first.
//
// Tag sentence-cases a string child by lowercasing it whole and raising the
// first letter, which is right for `HIGH` and `under_review` and wrong for
// these: "not published by MoSPI" comes back "Not published by mospi", and the
// department's own name is not a thing to get wrong on a case sheet. The
// strings in SKIP_REASON are prose written to sit mid-sentence in the trace
// table, so they are already cased correctly apart from the first letter.
// Wrapping the text in an element means Tag leaves it alone.
function ReasonTag({ reason }) {
  const text = SKIP_REASON[reason] ?? reason
  return (
    <Tag tone="neutral">
      <span>{text.charAt(0).toUpperCase() + text.slice(1)}</span>
    </Tag>
  )
}

export default function CaseDetail() {
  const { caseId } = useParams()
  const { data, error, loading } = useApi(`/api/cases/${encodeURIComponent(caseId)}`)

  // The one fired rule that is fed by a model output, and the block of
  // evidence that makes it admissible. See the section below.
  const cited = data ? data.rule_hits.filter((hit) => hit.citation) : []

  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="district" />

      <PageHeader
        title={loading || error ? 'Case' : data?.work?.description ?? data?.work?.work_id ?? 'Case'}
        note="Every rule the rulebook holds, what it read, what it compared that against and what it contributed — plus the two ladders those readings were derived from. The arithmetic is on this page in full, so an officer can re-derive the score on paper and an auditor can re-derive it months later."
      />

      <div className="px-8 py-8">
        {loading ? (
          <LoadingRegion label={`Loading case ${caseId}`}>
            <SkeletonPanel lines={4} />
            <SkeletonRows rows={6} />
          </LoadingRegion>
        ) : null}

        {/* Same component and the same three headlines the landing screens
            use. A 404 here is the interesting one: it is what a District
            Authority gets for another district's case id typed into the
            address bar, and it says both readings without resolving which. */}
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

              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <div className={`${CARD} p-4`}>
                  <p className={LABEL}>Score</p>
                  {/* The one navy number on the screen, and the only element
                      besides a heading allowed to be navy at all. The raw
                      total sits beside it because the display score is CAPPED
                      at 100 and not renormalised — weights are never divided,
                      because dividing them would change the arithmetic the
                      officer is re-deriving. */}
                  <p className="num font-display text-score-display text-navy">{data.score}</p>
                  <p className={CAPTION}>
                    {data.raw_score} raw of 154 possible, displayed capped at {data.score_cap}.
                    Weights are never rescaled.
                  </p>
                </div>

                <div className={`${CARD} p-4`}>
                  <p className={LABEL}>Severity</p>
                  <p className="mt-1">
                    <SeverityTag severity={data.severity} />
                  </p>
                  <p className={CAPTION}>HIGH ≥ 75 · MEDIUM ≥ 50 · LOW below 50, on the capped score.</p>
                </div>

                <div className={`${CARD} p-4`}>
                  <p className={LABEL}>Coverage</p>
                  <p className="num font-display text-section-heading text-ink">
                    {data.coverage_pct}%
                  </p>
                  <p className={CAPTION}>{data.coverage_basis}</p>
                </div>

                <div className={`${CARD} p-4`}>
                  <p className={LABEL}>Status</p>
                  <p className="mt-1">
                    <StatusTag status={data.status} />
                  </p>
                  <p className={CAPTION}>
                    Opened {String(data.opened_at).slice(0, 10)} · scored under rulebook{' '}
                    {data.rulebook_version}, as of {data.data_as_of}.
                  </p>
                  {/* Invariant 12: an injected row is labelled on the same
                      screen it appears on, never in a footnote. */}
                  {data.work.is_synthetic ? (
                    <p className="mt-2">
                      <Tag tone="neutral">Synthetic control — excluded from every aggregate</Tag>
                    </p>
                  ) : null}
                </div>
              </div>

              {/* The two located findings, in words. A null on either is a
                  real answer and says so rather than printing nothing. */}
              <p className={`${CAPTION} mt-4 max-w-3xl`}>
                Open fund hop:{' '}
                {data.gap_hop ? HOP_LABEL[data.gap_hop] ?? data.gap_hop : 'none — no hop is open'}.
                Slowest lifecycle lag:{' '}
                {data.slowest_lag ? LAG_LABEL[data.slowest_lag] ?? data.slowest_lag : 'none computable'}.
                {data.slowest_lag ? ` ${LAG_MEANING[data.slowest_lag] ?? ''}` : ''}
              </p>
            </section>

            <div className="mt-8">
              <FundLadder ladder={data.fund_ladder} gapHop={data.gap_hop} />
            </div>

            <div className="mt-8">
              <LifecycleLadder ladder={data.lifecycle_ladder} slowestLag={data.slowest_lag} />
            </div>

            {/* The orphaned trace table, wired up. It is unchanged: it already
                prints the operator with the threshold, names each skip reason,
                and carries a fired row's caveat on the row itself. */}
            <div className="mt-8">
              <TraceTable hits={data.rule_hits} />
            </div>

            <section className="mt-8">
              <SectionHeading title="Pattern-of-conduct corroboration">
                The one source of score that is not a rule. Rendered whether or not it applied —
                an officer has to be able to see the bonus NOT fire, and why.
              </SectionHeading>

              <div className={`${CARD} mt-4 p-4`}>
                <div className="flex flex-wrap items-baseline justify-between gap-4">
                  <span className="text-table-cell text-ink">
                    {data.corroboration.agency ?? 'agency not recorded'} · {data.corroboration.window}
                  </span>
                  <span className="flex items-center gap-4">
                    <span className="num text-body-secondary text-ink-secondary">
                      {data.corroboration.high_case_count} other HIGH cases, minimum{' '}
                      {data.corroboration.min_high_cases}
                    </span>
                    <span className="num text-table-cell text-ink">
                      {data.corroboration.applied ? `+${data.corroboration.contribution}` : '—'}
                    </span>
                    <Tag tone={data.corroboration.applied ? 'medium' : 'neutral'}>
                      {data.corroboration.applied ? 'Applied' : 'Not applied'}
                    </Tag>
                  </span>
                </div>
                <p className={CAPTION}>
                  One bad work is an incident; a pattern under one agency in one financial year is
                  a posture. The bonus is awarded only on corroborated repetition.
                </p>
              </div>
            </section>

            {cited.length > 0 ? (
              <section className="mt-8">
                <SectionHeading title="Cited evidence">
                  Explainability by citation, not by trust. The rules below read a number a
                  similarity model produced, and they are admissible only because the records that
                  number came from are handed over here for the officer to open and judge.
                </SectionHeading>

                {cited.map((hit) => (
                  <div key={hit.rule_id} className={`${CARD} mt-2 p-4`}>
                    <p className={LABEL}>{hit.rule_id}</p>
                    <p className="text-table-cell text-ink">
                      &ldquo;{hit.citation.shared_description}&rdquo;
                    </p>
                    <p className={CAPTION}>
                      Similarity {hit.citation.similarity} by {hit.citation.method}
                      {hit.citation.cluster_size
                        ? `, in a cluster of ${hit.citation.cluster_size}`
                        : ''}
                      {hit.citation.agency ? `, under ${hit.citation.agency}` : ''}.
                    </p>
                    <p className="mt-2 text-body-secondary text-ink">
                      Matched works: {hit.citation.matched_work_ids.join(', ')}
                    </p>
                    {/* The response's own wording, not a paraphrase: a cluster
                        is a candidate for review, never an accusation, and the
                        sentence saying so is written next to the model that
                        produced the number. */}
                    <p className={CAPTION}>{hit.citation.reading}</p>
                  </div>
                ))}
              </section>
            ) : null}

            <section className="mt-8">
              <SectionHeading title="Badges — tiers 3 and 4">
                Statistical and graph findings, each worth exactly zero points. They confirm, or
                fail to confirm, what the rulebook already found. They never move the number.
              </SectionHeading>

              <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
                <Badge label="Anomaly" value={data.statistical.anomaly_score}>
                  {data.statistical.z_peer_group
                    ? `Peer group: ${data.statistical.z_peer_group}.`
                    : null}{' '}
                  {data.statistical.confirms === null || data.statistical.confirms === undefined
                    ? null
                    : data.statistical.confirms
                      ? 'Confirms the rulebook finding.'
                      : 'Does not confirm the rulebook finding.'}
                </Badge>

                <Badge label="Delay risk" value={data.forecast.delay_risk}>
                  {data.forecast.horizon_meaning
                    ? `${data.forecast.horizon_meaning}. Illustrative: trained on a truncated sample, and the horizon is a demonstration rather than a commitment.`
                    : 'Illustrative, on a truncated sample.'}
                </Badge>

                <Badge label="Vendor concentration" value={data.concentration.hhi}>
                  {data.concentration.top_vendor
                    ? `Largest share: ${data.concentration.top_vendor} at ${data.concentration.top_vendor_share_pct}% of this agency's disbursement.`
                    : 'No vendor share published for this agency.'}
                </Badge>
              </div>
            </section>

            {data.unavailable_fields.length > 0 ? (
              <section className="mt-8">
                <SectionHeading title="What could not be read">
                  Graceful degradation, itemised. A skipped rule&rsquo;s weight is never
                  redistributed to the rules that did evaluate, so this list is the difference
                  between a case scored on full coverage and one scored on {data.coverage_pct}%.
                </SectionHeading>

                <ul className="mt-4 space-y-2">
                  {data.unavailable_fields.map((field) => (
                    <li key={field.field} className={`${CARD} p-4`}>
                      <div className="flex flex-wrap items-baseline justify-between gap-4">
                        <span className="text-table-cell text-ink">{field.field}</span>
                        <ReasonTag reason={field.reason} />
                      </div>
                      {field.detail ? <p className={CAPTION}>{field.detail}</p> : null}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            <section className="mt-8">
              <SectionHeading title="Memo">
                A TEMPLATE, filled from the values above. Not generated language, not an LLM, and
                nothing on this page is described as either. Template now, model later.
              </SectionHeading>

              <div className={`${CARD} mt-4 max-w-3xl p-6`}>
                <p className="whitespace-pre-line text-body text-ink">{data.memo}</p>
              </div>
            </section>

            <p className={`${CAPTION} mt-8 max-w-3xl`}>
              Sanctioned {formatRupees(data.fund_ladder.rungs[0]?.amount) ?? 'not published'} ·
              rulebook {data.rulebook_version} ({data.rulebook_version_sha256.slice(0, 12)}) · a
              recompute re-derives against this stored snapshot, not against the rulebook file as
              it reads today.
            </p>
          </>
        ) : null}
      </div>
    </article>
  )
}
