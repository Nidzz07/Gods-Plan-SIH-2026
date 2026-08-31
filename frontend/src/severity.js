// Severity and trace-state styling, in one place so a row on the case list and
// a row in the trace table can never disagree about what coral means.
//
// Tailwind classes are written out in full rather than composed at runtime:
// the JIT scans source text, so a class built as `border-${colour}` would be
// absent from the stylesheet and the row would silently lose its border.
//
// TWO severity patterns exist and they never mix on one element:
//   (1) coloured left-border on a full data row — SEVERITY_BORDER below,
//       used by the case list and the case header
//   (2) the rectangular Tag component — components/Tag.jsx, used for compact
//       inline status (rulebook severities, case status, audit event types)
// Where a row carries the left-border, its severity TEXT is plain ink: the
// border is already the colour signal, and colouring the word as well would
// be encoding the same fact twice. There is deliberately no severity-to-text-
// colour map here — a bare coloured word is never the right answer, because
// colour alone is not a label.

export const SEVERITY_BORDER = {
  HIGH: 'border-l-coral',
  MEDIUM: 'border-l-gold',
  LOW: 'border-l-green',
}

// Rulebook comparisons, written the way an officer reads them rather than the
// way YAML stores them. All six operators the rulebook admits, `ne` included:
// no v1.0.0 rule uses it, and a rulebook edited in the UI could introduce one,
// at which point a missing key here would print `undefined` into the middle of
// a trace row.
export const OPERATOR_SYMBOL = {
  lt: '<',
  lte: '≤',
  gt: '>',
  gte: '≥',
  eq: '=',
  ne: '≠',
}

// ---------------------------------------------------------------------------
// The fund ladder — two hops, where the money is
// ---------------------------------------------------------------------------

// The case detail response labels its own hops and the case sheet reads them
// from there. This map is for the places that receive a bare `gap_hop` string
// with no ladder attached — a case list row, a dashboard column — and it
// carries the same wording the backend sends, so the two cannot describe one
// hop in two ways.
export const HOP_LABEL = {
  sanction_to_disbursement: 'Sanction to disbursement',
  disbursement_to_certification: 'Disbursement to certification',
}

// What a located gap tells an officer to go and do. Taken verbatim from
// docs/domain/DOMAIN-MODEL.md (b), which is the authority for both hops — not
// paraphrased, because a paraphrase would put two versions of one instruction
// in front of an officer and neither would be the one the domain model is
// held to.
export const HOP_ACTION = {
  sanction_to_disbursement:
    "Pull the agency's payment register for this work. Confirm whether the balance is " +
    'committed against an unpaid bill, unspent, or was returned. If unspent for more than ' +
    'one financial year, the sanction should be revalidated or surrendered rather than left ' +
    'standing.',
  disbursement_to_certification:
    'Obtain the utilisation certificate from the implementing agency and match the certified ' +
    'amount and asset description against the sanction. If no UC exists for a disbursement ' +
    'older than 12 months, that is a recovery proceeding, not a query.',
}

// ---------------------------------------------------------------------------
// The lifecycle ladder — three lags, where the time went
// ---------------------------------------------------------------------------

export const LAG_LABEL = {
  recommend_to_sanction: 'Recommendation to sanction',
  sanction_to_first_payment: 'Sanction to first payment',
  first_payment_to_completion: 'First payment to completion',
}

// What it means when this lag is the slowest one. DOMAIN-MODEL.md (c), and the
// reason the lifecycle ladder exists at all: MPLADS criticism lands on the
// member for delays that occurred entirely inside the district administration,
// and the slowest lag is what says which of the two it was.
export const LAG_MEANING = {
  recommend_to_sanction:
    'The delay is administrative and sits before implementation — with the district ' +
    'sanctioning office, not the agency or the member.',
  sanction_to_first_payment:
    'The sanction issued but nothing moved. Vendor identification, tender, or agency capacity.',
  first_payment_to_completion:
    'Execution itself is slow. This is the one an inspector can go and look at.',
}

// ---------------------------------------------------------------------------
// Graceful degradation — invariant 2, on screen
// ---------------------------------------------------------------------------

// "Not published by MoSPI" and "published as zero" are different findings and
// must stay distinguishable end to end: in the derived features, in
// rule_hits.skip_reason, in the contract, AND HERE. A skipped row that did not
// say which of the three it was would collapse a reporting gap into a fact
// about the work, which is the exact confusion the invariant forbids.
export const SKIP_REASON = {
  not_published: 'not published by MoSPI',
  published_zero: 'published as zero',
  not_applicable: 'the work has not reached this stage',
}

// The three trace-row states. A skipped rule is greyed and italic — it must
// never be mistaken for a rule that passed, so it is the one state that
// changes the type style and not just the colour.
export const TRACE_ROW = {
  fired: {
    border: 'border-l-coral',
    row: 'bg-surface text-ink',
    label: 'Fired',
    labelClass: 'text-coral font-medium',
  },
  passed: {
    border: 'border-l-green',
    row: 'bg-surface text-ink',
    label: 'Passed',
    labelClass: 'text-green',
  },
  skipped: {
    border: 'border-l-border-strong',
    row: 'bg-surface-sunk text-ink-muted italic',
    label: 'Skipped',
    labelClass: 'text-ink-muted',
  },
}

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------

// en-IN, so grouping is lakh-and-crore (1,99,539) rather than thousands
// (199,539). Every rupee figure in the corpus is a whole rupee — the exports
// carry no paise — so no fraction digits are ever shown.
const INDIAN = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })

export function formatCount(value) {
  return value === null || value === undefined ? null : INDIAN.format(value)
}

// An exact rupee figure, for a case sheet where an officer reconciles against
// a sanction order. Charts do NOT use this — see formatCrore.
export function formatRupees(value) {
  return value === null || value === undefined ? null : `₹${INDIAN.format(value)}`
}

// Aggregate money, in crore. The UI conventions are explicit that an axis
// carries rupees in crore or lakh and never a raw integer, and a national
// total written out in rupees is fourteen digits nobody reads. One decimal: at
// crore scale the second one is noise.
export function formatCrore(value) {
  if (value === null || value === undefined) return null
  return `₹${(value / 10000000).toFixed(1)} cr`
}

export function formatPct(value) {
  // Two decimals, matching the precision the fund ladder is reconciled at.
  // Nulls stay null: an unmeasured hop is not a 0.00% hop.
  return value === null || value === undefined ? null : `${value.toFixed(2)}%`
}

export function formatDays(value) {
  if (value === null || value === undefined) return null
  return `${INDIAN.format(value)} ${value === 1 ? 'day' : 'days'}`
}
