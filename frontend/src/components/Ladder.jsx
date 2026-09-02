import Tag from './Tag.jsx'
import { SKIP_REASON, formatDays, formatPct, formatRupees } from '../severity.js'
import { CAPTION, CARD, LABEL } from '../ui.js'
import SectionHeading from './SectionHeading.jsx'

// The two ladders, drawn the same way because they answer the same shape of
// question about two different quantities: fund reconciles AMOUNT, lifecycle
// reconciles TIME. Rungs and dates are the readings; hops and lags are the
// steps between them, and a step is where a finding lives.
//
// The inherited project's Ladder.jsx was deleted with the rest of the PDS
// domain layer rather than bent into shape — it drew one ladder over a
// three-rung shop-to-household chain, and NIGRANI has two ladders with
// different arities and different null semantics. This is the replacement.
//
// AN UNMEASURED STEP IS NOT A CLEAN STEP, and that is the whole reason the
// states are drawn distinctly. A fund hop that could not be computed is
// `unavailable`, never `closed`; a lag with no dates behind it is
// `unavailable`, not zero days. Both take the neutral tag and say which of the
// three reasons applied, because "MoSPI does not publish this" and "the portal
// published it as zero" are different findings (invariant 2).
//
// Severity is carried as a rectangular tag with a text label — pattern (2) of
// the two the conventions allow — and never as a coloured left-border here,
// because these are not full data rows. The trace table is where pattern (1)
// belongs on this screen, and the two never meet on one element.

// State to tag tone. The tones are the palette keys Tag already holds; the
// LABEL is what carries the meaning, so a reader in greyscale loses nothing.
//
// An open step takes gold, not coral. Coral is the case's own HIGH severity
// and an open hop is not by itself a HIGH case — the score decides that, from
// the rulebook. Spending the alarm colour on every open hop would leave
// nothing to say when a case actually is severe.
const STEP_TONE = { open: 'medium', closed: 'low', computed: 'low', unavailable: 'neutral' }
const STEP_LABEL = { open: 'Open', closed: 'Closed', computed: 'Computed', unavailable: 'Unavailable' }

function StepTag({ state }) {
  return <Tag tone={STEP_TONE[state] ?? 'neutral'}>{STEP_LABEL[state] ?? state}</Tag>
}

// A reading, or the reason there is not one. Availability carries four values
// and only the first of them is a number on screen.
//
// `published_zero` prints the zero AND says it was published as one. Dropping
// to the italic "not published" line would turn a fact about the work into a
// reporting failure by MoSPI, and printing a bare 0 would lose the fact that
// the portal actually said so. Both halves are needed.
function Reading({ text, availability }) {
  if (availability === 'published' || availability === 'published_zero') {
    return (
      <>
        {/* An em dash rather than a zero if the reading is somehow absent on a
            rung the response called published: a blank would read as a
            rendering fault, and a fabricated 0 would be worse than either. */}
        <span className="num block font-display text-section-heading text-ink">{text ?? '—'}</span>
        {availability === 'published_zero' ? (
          <span className="block text-meta-label text-ink-muted">
            {SKIP_REASON.published_zero}
          </span>
        ) : null}
      </>
    )
  }
  return (
    <span className="block text-body italic text-ink-muted">
      {SKIP_REASON[availability] ?? 'no reading'}
    </span>
  )
}

// The step between two readings: what it measured, what that was compared
// against, and what the officer does about it when it is open.
function Step({ label, measured, compared, state, reason, action }) {
  return (
    <div className={`${CARD} ml-6 border-l-4 border-l-border-strong px-4 py-4`}>
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

      {/* The reason a step could not be measured, on the step itself. */}
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
  return (
    <section>
      <SectionHeading title="Fund ladder">
        Where the money is. Two hops, each a signed variance against the rung above it, compared
        against the tolerance the rulebook sets for that hop.
        {gapHop
          ? ' The first open hop walking down is what this case is scored on.'
          : ' No hop on this work is open.'}
      </SectionHeading>

      <div className="mt-4 space-y-2">
        {ladder.rungs.map((rung, index) => (
          <div key={rung.key}>
            <div className={`${CARD} px-4 py-4`}>
              <p className={LABEL}>{rung.label}</p>
              <Reading
                text={rung.availability === 'published_zero' ? formatRupees(rung.amount ?? 0) : formatRupees(rung.amount)}
                availability={rung.availability}
              />
              {/* Declared limitation 3: recommended equals sanctioned in every
                  matched work in this corpus, which is why the cost-overrun
                  rule was designed and then removed. Where the response says
                  so, the case sheet says so. */}
              {rung.recommended_equals_sanctioned ? (
                <p className={CAPTION}>
                  Recommended {formatRupees(rung.recommended_amt)} — equal to the sanctioned
                  amount, as it is on every matched work in this corpus.
                </p>
              ) : null}
              {rung.note ? <p className={CAPTION}>{rung.note}</p> : null}
            </div>

            {/* The hop below this rung, if there is one. Rungs and hops
                interleave, so the step is drawn inside the rung's block rather
                than in a second list that could fall out of step with it. */}
            {ladder.hops[index] ? (
              <div className="mt-2">
                <Step
                  label={ladder.hops[index].label}
                  measured={formatPct(ladder.hops[index].variance_pct)}
                  compared={`tolerance ${formatPct(ladder.hops[index].tolerance_pct)}`}
                  state={ladder.hops[index].state}
                  reason={ladder.hops[index].unavailable_reason}
                  action={ladder.hops[index].hop_action}
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
  return (
    <section>
      <SectionHeading title="Lifecycle ladder">
        Where the time went. Four dates and three lags, in whole days, computed date to date and
        never clamped — a negative lag is an ingest reject, not a zero.
        {slowestLag
          ? ' The slowest lag is what says which stage the delay actually occurred in.'
          : ' No lag on this work is computable.'}
      </SectionHeading>

      <div className="mt-4 space-y-2">
        {ladder.dates.map((entry, index) => (
          <div key={entry.key}>
            <div className={`${CARD} px-4 py-4`}>
              <p className={LABEL}>{entry.label}</p>
              <Reading text={entry.date} availability={entry.availability} />
            </div>

            {ladder.lags[index] ? (
              <div className="mt-2">
                <Step
                  label={ladder.lags[index].label}
                  measured={formatDays(ladder.lags[index].days)}
                  state={ladder.lags[index].state}
                  reason={ladder.lags[index].unavailable_reason}
                />
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
