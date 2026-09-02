import { CARD } from '../ui.js'

// An empty state is a sentence, not a shrug. Each one says what is not here,
// why, and what to do next — "No results" tells a judge nothing and looks like
// a bug.
//
// Deliberately a plain hairline card with no coloured left-border: that accent
// encodes a severity value, and an empty state has no severity. Spending the
// idiom here would blunt it on the rows that carry one.
export default function EmptyState({ title, children }) {
  return (
    <div className={`${CARD} p-6`}>
      <p className="text-body font-medium text-ink">{title}</p>
      {children ? <p className="mt-1 text-body-secondary text-ink-secondary">{children}</p> : null}
    </div>
  )
}

// The headline per status. The three the API uses mean genuinely different
// things and the same sentence for all of them would flatten the one
// distinction the scoping design turns on.
//
// 404 is the delicate one. It means "this row is not in your scope, OR it does
// not exist" and the API refuses to say which — a 403 there would confirm that
// another district's case id is real, which is a scoping leak spelled with a
// status code. So this screen must not resolve the ambiguity either. It says
// both, in that order, rather than guessing at the likelier one.
const HEADLINE = {
  0: 'Could not reach the API',
  403: 'Your role cannot open this view',
  404: 'Not found, or not within your scope',
}

// The same shape as EmptyState for a failed fetch. Kept next to it because the
// two are read in the same slot and should not drift apart visually.
//
// Coral on the heading, not on a left-border: the border accent belongs to
// severity values on data rows, and a failed request has no severity.
export function ErrorState({ error, children }) {
  // Tolerates either an ApiError or a bare string, so a caller that only has a
  // message is not forced to construct an error object to render one.
  const status = typeof error === 'object' && error !== null ? error.status : undefined
  const message = typeof error === 'object' && error !== null ? error.message : error

  return (
    <div className={`${CARD} p-6`} role="alert">
      <p className="font-medium text-coral">
        {HEADLINE[status] ?? 'Could not load this from the API'}
      </p>
      <p className="mt-1 text-body-secondary text-ink-secondary">{message}</p>
      {status === 404 ? (
        <p className="mt-2 text-body-secondary text-ink-secondary">
          The API answers a case id outside your scope exactly as it answers one that was never
          issued. That is deliberate: telling the two apart would confirm that another
          district&rsquo;s case exists.
        </p>
      ) : null}
      {children ? <p className="mt-2 text-body-secondary text-ink-secondary">{children}</p> : null}
    </div>
  )
}
