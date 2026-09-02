import { CAPTION, CARD, LABEL } from '../ui.js'

// Tiers 3 and 4 — the statistical and graph findings — drawn so that a
// SCREENSHOT of this page makes it obvious they never touch the score.
//
// This is invariant 1 rendered rather than asserted. The invariant says the
// composite score is the sum of fired rulebook weights plus the corroboration
// bonus and nothing else, and that anomaly scores, delay forecasts and graph
// centrality are badges worth ZERO. A test asserts it per model. But a judge
// reading this screen over somebody's shoulder cannot run the test suite, so
// the claim has to survive being looked at.
//
// THREE THINGS MAKE THE BADGES READ AS A DIFFERENT KIND OF OBJECT from the
// trace rows above them, and all three are deliberate:
//
//   1. They sit on the SUNK ground, not on white. Every scoring row in this
//      product - the trace, the ladders, the corroboration - is a white
//      surface. The badges are the only panel that is not, so they are visibly
//      not part of that set before a word is read.
//   2. They carry NO severity colour and no coloured left border. The trace
//      rows carry coral, green and grey edges encoding fired, passed and
//      skipped. A badge has no such state because it has no bearing on the
//      outcome, and giving it one would be borrowing the vocabulary of the
//      tier that does.
//   3. Each one prints its contribution as an explicit `+0`, in the same
//      column position and the same tabular figures the trace uses for `+22`.
//      Not a missing value, not a dash: a zero, in the place where a number
//      that mattered would be, so the comparison is made for the reader
//      instead of being left to them.
//
// The banner above them says the same thing in a sentence, because the visual
// argument and the written one should agree.

function Badge({ label, value, model, children }) {
  return (
    <div className="rounded border border-border bg-surface-sunk p-4">
      <div className="flex items-baseline justify-between gap-4">
        <p className={LABEL}>{label}</p>
        {/* The zero, in the column a contribution would occupy on a trace row,
            in the same tabular figures. */}
        <span className="num text-table-cell text-ink-muted">+0</span>
      </div>
      <p className="num font-display text-section-heading text-ink-secondary">{value ?? '—'}</p>
      {children ? <p className={CAPTION}>{children}</p> : null}
      {model ? (
        <p className="num mt-2 text-meta-label text-ink-muted">{model}</p>
      ) : null}
    </div>
  )
}

export default function ZeroPointBadges({ statistical, forecast, concentration }) {
  return (
    <div className={`${CARD} p-6`}>
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <h3 className="font-display text-section-heading text-navy">Badges — tiers 3 and 4</h3>
        <span className="num text-body-secondary text-ink-secondary">
          0 of this case&rsquo;s points
        </span>
      </div>
      <p className={`${CAPTION} max-w-3xl`}>
        Statistical and graph findings. They confirm, or fail to confirm, what the rulebook
        already found, and they never move the number — every one of them contributes exactly
        zero, and the score above is the sum of the fired rulebook weights and the corroboration
        bonus alone. Nothing on this panel is an input to it.
      </p>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Badge
          label="Anomaly"
          value={statistical.anomaly_score}
          model={statistical.anomaly_model_version}
        >
          {statistical.z_peer_group ? `Peer group: ${statistical.z_peer_group}.` : null}{' '}
          {statistical.confirms === null || statistical.confirms === undefined
            ? null
            : statistical.confirms
              ? 'Confirms the rulebook finding.'
              : 'Does not confirm the rulebook finding.'}
        </Badge>

        <Badge
          label="Delay risk"
          value={forecast.delay_risk}
          model={forecast.model_version}
        >
          {forecast.horizon_meaning
            ? `${forecast.horizon_meaning}. Illustrative: trained on a truncated sample, and the horizon is a demonstration rather than a commitment. Read it as a ranking, not a probability.`
            : 'Illustrative, on a truncated sample.'}
        </Badge>

        <Badge
          label="Vendor concentration"
          value={concentration.hhi}
          model={concentration.model_version}
        >
          {concentration.top_vendor
            ? `Largest share: ${concentration.top_vendor} at ${concentration.top_vendor_share_pct}% of this agency's disbursement.`
            : 'No vendor share published for this agency.'}
        </Badge>
      </div>
    </div>
  )
}
