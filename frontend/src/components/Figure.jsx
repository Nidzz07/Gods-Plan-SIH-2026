import { CARD, LABEL } from '../ui.js'

// One labelled figure in a card. The four landing screens are, for now, rows
// of these — the point of Phase 8 is that correctly scoped numbers reach the
// screen, and a figure with its label above it is the smallest honest way to
// show one.
//
// The number is INK, not navy. Navy is for headings and the score-display
// number; a count of cases is data and takes body colour. This is the
// regression the design spec calls the most common one in the build, and a
// component that got it wrong would spread it across four screens at once.
//
// `note` is where a caveat lives when the figure has one — the count of cases
// with no expenditure row, say, which is a truncation artefact of MoSPI's
// export rather than a finding. A figure that needs a caveat and does not
// carry one is a figure that will be quoted without it.
export default function Figure({ label, value, note }) {
  return (
    <div className={`${CARD} p-4`}>
      <p className={LABEL}>{label}</p>
      {/* An absent figure prints an em dash, never a zero. "Not published" and
          "published as zero" are different findings (invariant 2) and this is
          the smallest place that distinction can be lost. */}
      <p className="num font-display text-section-heading text-ink">{value ?? '—'}</p>
      {note ? <p className="mt-2 text-body-secondary text-ink-secondary">{note}</p> : null}
    </div>
  )
}
