// The tag component, after GOV.UK's.
//
// A small RECTANGLE at the app's single 4px radius — not a pill. Tinted
// background at 15% of the signal colour, solid full-strength colour for the
// text, and ALWAYS a text label inside it. Colour is never the only signal:
// the label is what a colour-blind reader, a greyscale print of the case
// sheet, and a magistrate's photocopy all still have.
//
// Sentence case ("High", not "HIGH") — the tag is a label, not an alarm.
//
// This is the pattern for COMPACT INLINE status: a rule's severity in the
// rulebook table, a case's open/resolved state, an audit event's type. It is
// NOT for full data rows — those keep the coloured left-border (case list,
// trace table), and the two patterns never appear on the same element.

const TONES = {
  // Severity, as the rulebook and the case both spell it.
  high: 'bg-coral/15 text-coral',
  medium: 'bg-gold/15 text-gold',
  low: 'bg-green/15 text-green',

  // Case status, the four the backend admits. Gold for the two states that
  // still want somebody's attention, green for the one that no longer does.
  // `escalated` takes coral because it is the only status that has moved a
  // case onto another officer's desk — that is a state worth spotting from
  // across a queue.
  open: 'bg-gold/15 text-gold',
  under_review: 'bg-gold/15 text-gold',
  escalated: 'bg-coral/15 text-coral',
  resolved: 'bg-green/15 text-green',

  // For labels that classify without ranking — audit event types, a role
  // name, a skip reason. Reaching for a severity colour there would spend
  // signal on something that carries none.
  neutral: 'bg-surface-sunk text-ink-secondary',
}

// Sentence case, applied here rather than trusted to the caller so a raw
// "HIGH" from the API cannot leak onto the page shouting.
function sentenceCase(text) {
  const words = String(text).replace(/_/g, ' ').toLowerCase()
  return words.charAt(0).toUpperCase() + words.slice(1)
}

export default function Tag({ tone = 'neutral', children, className = '' }) {
  return (
    <span
      // transition-colors so a tag that swaps tone — a case going from Open to
      // Escalated, say — crossfades rather than snapping. Same 150ms as every
      // other state change in the app.
      className={`inline-block rounded px-2 py-1 text-meta-label transition-colors duration-150 ease-out ${
        TONES[tone] ?? TONES.neutral
      } ${className}`}
    >
      {typeof children === 'string' ? sentenceCase(children) : children}
    </span>
  )
}

// Severity arrives as "HIGH" from a case and "high" from a rule; both map to
// the same tone without the caller having to know which it is holding.
export function SeverityTag({ severity, className = '' }) {
  return (
    <Tag tone={String(severity).toLowerCase()} className={className}>
      {severity}
    </Tag>
  )
}

export function StatusTag({ status, className = '' }) {
  return (
    <Tag tone={String(status).toLowerCase()} className={className}>
      {status}
    </Tag>
  )
}
