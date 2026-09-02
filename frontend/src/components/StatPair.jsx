import { CAPTION, CARD, LABEL } from '../ui.js'

// Two rupee aggregates and the proportion between them, as one bar.
//
// WHY THIS AND NOT A SANKEY. A Sankey is the obvious picture for a fund ladder
// and it is the wrong one on this corpus. It draws flows between nodes, and
// NIGRANI's ladder has three: sanctioned, disbursed, certified. The certified
// rung is never published by MoSPI for any work, and the disbursed rung joins
// for only 3,529 of the 27,078 works in the sample. A Sankey over that would
// spend most of its width on a band that means "MoSPI's expenditure export did
// not reach these works", drawn in the same visual language as the bands that
// mean "this money did not move" — and a reader would take the truncation of an
// export for a finding about money. One bar, one caption naming exactly what
// the filled portion counts, is the honest version of the same fact.
//
// The proportion is a SUBSET, not a part-whole split of everything: the filled
// amount is drawn from the total, but the unfilled remainder is not "money that
// arrived" — most of it is money whose fate the corpus cannot see. The caption
// is not decoration here; it is what stops the bar being read as a completion
// meter, so it is a required prop rather than an optional one.

export default function StatPair({
  label,
  totalLabel,
  totalValue,
  totalAmount,
  partLabel,
  partValue,
  partAmount,
  caption,
  note,
}) {
  // Guarded: a zero or absent total is a division, and a bar of NaN width
  // renders as an invisible element rather than as an error anyone would catch.
  const share =
    totalAmount && partAmount !== null && partAmount !== undefined && totalAmount > 0
      ? Math.min(100, (partAmount / totalAmount) * 100)
      : null

  return (
    <div className={`${CARD} p-6`}>
      <p className={LABEL}>{label}</p>

      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-4">
        <span>
          <span className="num block font-display text-section-heading text-ink">
            {totalValue ?? '—'}
          </span>
          <span className="block text-meta-label uppercase text-ink-secondary">{totalLabel}</span>
        </span>
        <span className="text-right">
          <span className="num block font-display text-section-heading text-ink">
            {partValue ?? '—'}
          </span>
          <span className="block text-meta-label uppercase text-ink-secondary">{partLabel}</span>
        </span>
      </div>

      {/* The track is the sunk ground, the fill is gold. Gold rather than coral:
          money sitting behind an open hop wants attention, and it is not by
          itself a HIGH finding — coral is the severity band, and spending it
          here would leave nothing to say when a case is actually severe.

          One radius token on both, and no gradient in the fill. */}
      {share === null ? null : (
        <div
          className="mt-4 h-2 w-full overflow-hidden rounded bg-surface-sunk"
          role="img"
          aria-label={`${partLabel}: ${share.toFixed(1)} per cent of ${totalLabel}`}
        >
          <div className="h-2 rounded bg-gold" style={{ width: `${share}%` }} />
        </div>
      )}

      {share === null ? null : (
        <p className="num mt-2 text-body-secondary text-ink-secondary">
          {share.toFixed(1)}% of {totalLabel.toLowerCase()}
        </p>
      )}

      <p className={`${CAPTION} max-w-3xl`}>{caption}</p>
      {note ? <p className={`${CAPTION} max-w-3xl`}>{note}</p> : null}
    </div>
  )
}
