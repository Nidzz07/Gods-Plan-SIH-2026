import Tag from './Tag.jsx'
import { GOLD, GREEN, INK_MUTED, NAVY } from '../chart.js'
import { SKIP_REASON, formatDays, formatPct, formatRupees } from '../severity.js'
import { CAPTION, CARD, LABEL } from '../ui.js'
import SectionHeading from './SectionHeading.jsx'

// The two ladders, drawn to scale.
//
// They answer the same shape of question about two different quantities: fund
// reconciles AMOUNT, lifecycle reconciles TIME. Rungs and dates are the
// readings; hops and lags are the steps between them, and a step is where a
// finding lives.
//
// **Everything is a bar against one scale**, the same treatment the member's
// account ladder uses, so an officer moving between the two screens is reading
// one idiom. Within a ladder every bar is measured against that ladder's own
// largest published value, so the reader can see that disbursement was two
// fifths of sanction without doing the arithmetic. Scaling each bar to itself
// would make every rung look equally full, which is the opposite of what a
// ladder is for.
//
// **AN UNMEASURED STEP IS NEVER A CLEAN STEP.** This is the rule the whole
// component is built around. A rung MoSPI never published draws a DASHED EMPTY
// TRACK with the reason written inside it - never a bar of zero length, because
// a zero-length bar is visually identical to an amount of nothing, and "the
// portal published no certified amount" and "nothing was certified" are
// different claims. Only the first is true, and it is true of every work in the
// corpus. A hop that could not be computed reads `Unavailable`, never `Closed`.
//
// Severity is carried as a rectangular tag with a text label - pattern (2) -
// and never as a coloured left-border here, because these are not full data
// rows. The trace table is where pattern (1) belongs on this screen, and the
// two never meet on one element.

// State to tag tone. The LABEL carries the meaning, so a reader in greyscale
// loses nothing.
//
// An open step takes gold, not coral. Coral is the case's own HIGH severity and
// an open hop is not by itself a HIGH case - the score decides that, from the
// rulebook. Spending the alarm colour on every open hop would leave nothing to
// say when a case actually is severe.
const STEP_TONE = { open: 'medium', closed: 'low', computed: 'low', unavailable: 'neutral' }
const STEP_LABEL = {
  open: 'Open',
  closed: 'Closed',
  computed: 'Computed',
  unavailable: 'Unavailable',
}

// Rung colours descend the way the money does: sanctioned, disbursed, certified.
const RUNG_COLOR = { sanctioned_amt: NAVY, disbursed_amt: GOLD, certified_amt: GREEN }

function StepTag({ state }) {
  return <Tag tone={STEP_TONE[state] ?? 'neutral'}>{STEP_LABEL[state] ?? state}</Tag>
}

function published(availability) {
  return availability === 'published' || availability === 'published_zero'
}

// One reading as a bar, or as the reason there is not one.
//
// `published_zero` prints the zero AND says the portal published it. Dropping
// to the dashed track would turn a fact about the work into a reporting failure
// by MoSPI; printing a bare 0 would lose that the portal actually said so. Both
// halves are needed and neither is optional.
function Bar({ label, text, availability, width, color }) {
  const isPublished = published(availability)
  return (
    <div className="grid grid-cols-[130px_1fr_170px] items-center gap-4">
      <span className="text-meta-label uppercase text-ink-secondary">{label}</span>

      {isPublished ? (
        <span className="block h-4 w-full rounded bg-surface-sunk">
          <span
            className="block h-4 rounded"
            style={{ width: `${width}%`, backgroundColor: color }}
            // The bar restates a number already printed beside it, so it is
            // hidden rather than announced twice.
            aria-hidden="true"
          />
        </span>
      ) : (
        <span className="flex h-4 w-full items-center rounded border border-dashed border-border-strong px-2">
          <span className="text-meta-label text-ink-muted">
            {SKIP_REASON[availability] ?? availability}
          </span>
        </span>
      )}

      <span className="num text-right text-table-cell text-ink">
        {isPublished ? (
          <>
            {text ?? '—'}
            {availability === 'published_zero' ? (
              <span className="block text-meta-label text-ink-muted">
                {SKIP_REASON.published_zero}
              </span>
            ) : null}
          </>
        ) : (
          <span className="italic text-ink-muted">
            {SKIP_REASON[availability] ?? availability}
          </span>
        )}
      </span>
    </div>
  )
}

// The step between two readings: what it measured, what that was compared
// against, and what the officer does about it when it is open.
function Step({ label, measured, compared, state, reason, action, highlighted }) {
  return (
    <div
      className={`ml-6 rounded border-y border-r border-border border-l-4 px-4 py-4 ${
        highlighted ? 'border-l-gold bg-surface' : 'border-l-border-strong bg-surface'
      }`}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <span className="text-table-cell text-ink">{label}</span>
        <span className="flex items-center gap-4">
          {compared ? (
            <span className="num text-body-secondary text-ink-secondary">{compared}</span>
          ) : null}
          <span className="num text-table-cell text-ink">{measured ?? '—'}</span>
          <StepTag state={state} />
        </span>
      </div>

      {state === 'unavailable' && reason ? (
        <p className="mt-2 text-body-secondary text-ink-secondary">
          {SKIP_REASON[reason] ?? reason}
        </p>
      ) : null}

      {/* What to go and check. Only on an open step: an instruction printed
          under a closed hop is an instruction an officer learns to skip. */}
      {state === 'open' && action ? (
        <p className="mt-2 max-w-3xl text-body-secondary text-ink-secondary">{action}</p>
      ) : null}
    </div>
  )
}

export function FundLadder({ ladder, gapHop }) {
  const amounts = ladder.rungs
    .filter((rung) => published(rung.availability))
    .map((rung) => rung.amount ?? 0)
  const scale = amounts.length ? Math.max(...amounts) : 0

  return (
    <section>
      <SectionHeading title="Fund ladder">
        Where the money is. Three rungs to scale against the largest published
        amount, and two hops, each a signed variance against the rung above it compared with the
        tolerance the rulebook sets for that hop.
        {gapHop
          ? ' The first open hop walking down is what this case is scored on.'
          : ' No hop on this work is open.'}
      </SectionHeading>

      <div className={`${CARD} mt-4 p-6`}>
        {ladder.rungs.map((rung, index) => (
          <div key={rung.key} className={index ? 'mt-4' : ''}>
            <Bar
              label={rung.label}
              text={formatRupees(rung.amount ?? (rung.availability === 'published_zero' ? 0 : null))}
              availability={rung.availability}
              width={scale > 0 ? ((rung.amount ?? 0) / scale) * 100 : 0}
              color={RUNG_COLOR[rung.key] ?? NAVY}
            />

            {/* Declared limitation 3: recommended equals sanctioned on every
                matched work in this corpus, which is why the cost-overrun rule
                was designed and then removed. */}
            {rung.recommended_equals_sanctioned ? (
              <p className={`${CAPTION} ml-[146px]`}>
                Recommended {formatRupees(rung.recommended_amt)} — equal to the sanctioned amount,
                as it is on every matched work in this corpus.
              </p>
            ) : null}
            {rung.note ? <p className={`${CAPTION} ml-[146px]`}>{rung.note}</p> : null}

            {ladder.hops[index] ? (
              <div className="mt-4">
                <Step
                  label={ladder.hops[index].label}
                  measured={formatPct(ladder.hops[index].variance_pct)}
                  compared={`tolerance ${formatPct(ladder.hops[index].tolerance_pct)}`}
                  state={ladder.hops[index].state}
                  reason={ladder.hops[index].unavailable_reason}
                  action={ladder.hops[index].hop_action}
                  highlighted={ladder.hops[index].key === gapHop}
                />
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  )
}

export function LifecycleLadder({ ladder, slowestLag }) {
  const days = ladder.lags
    .filter((lag) => lag.days !== null && lag.days !== undefined)
    .map((lag) => lag.days)
  const scale = days.length ? Math.max(...days) : 0

  return (
    <section>
      <SectionHeading title="Lifecycle ladder">
        Where the time went. Four dates and three lags, in whole days, computed date to date and
        never clamped — a negative lag is an ingest reject, not a zero. Each lag is drawn against
        the longest one on this work.
        {slowestLag
          ? ' The slowest lag is what says which stage the delay actually occurred in.'
          : ' No lag on this work is computable.'}
      </SectionHeading>

      <div className={`${CARD} mt-4 p-6`}>
        {ladder.dates.map((entry, index) => (
          <div key={entry.key} className={index ? 'mt-4' : ''}>
            <div className="grid grid-cols-[130px_1fr_170px] items-center gap-4">
              <span className="text-meta-label uppercase text-ink-secondary">{entry.label}</span>
              <span className="h-px w-full bg-border" aria-hidden="true" />
              <span className="num text-right text-table-cell text-ink">
                {published(entry.availability) ? (
                  entry.date
                ) : (
                  <span className="italic text-ink-muted">
                    {SKIP_REASON[entry.availability] ?? entry.availability}
                  </span>
                )}
              </span>
            </div>

            {ladder.lags[index] ? (
              <div className="mt-4">
                {/* The lag as a bar as well as a number, so three lags on one
                    work can be compared by eye — which is the whole question
                    the lifecycle ladder exists to answer. */}
                <div className="ml-6 grid grid-cols-[124px_1fr_170px] items-center gap-4">
                  <span className="text-meta-label uppercase text-ink-secondary">Elapsed</span>
                  {ladder.lags[index].days === null ||
                  ladder.lags[index].days === undefined ? (
                    <span className="flex h-2 w-full items-center rounded border border-dashed border-border-strong" />
                  ) : (
                    <span className="block h-2 w-full rounded bg-surface-sunk">
                      <span
                        className="block h-2 rounded"
                        style={{
                          width: `${scale > 0 ? (ladder.lags[index].days / scale) * 100 : 0}%`,
                          backgroundColor:
                            ladder.lags[index].key === slowestLag ? GOLD : INK_MUTED,
                        }}
                        aria-hidden="true"
                      />
                    </span>
                  )}
                  <span className="num text-right text-table-cell text-ink">
                    {formatDays(ladder.lags[index].days) ?? '—'}
                  </span>
                </div>

                <div className="mt-2">
                  <Step
                    label={ladder.lags[index].label}
                    measured={formatDays(ladder.lags[index].days)}
                    state={ladder.lags[index].state}
                    reason={ladder.lags[index].unavailable_reason}
                    highlighted={ladder.lags[index].key === slowestLag}
                  />
                </div>
              </div>
            ) : null}
          </div>
        ))}
      </div>

      {/* Payment count is never null — zero payments is a fact about the work,
          not an unmeasured field — so it is stated flatly rather than guarded. */}
      <p className={`${CAPTION} mt-4`}>
        {ladder.payment_count === 1 ? '1 payment' : `${ladder.payment_count} payments`} recorded
        {ladder.last_payment_date ? `, the last on ${ladder.last_payment_date}` : ''}.
      </p>
    </section>
  )
}
