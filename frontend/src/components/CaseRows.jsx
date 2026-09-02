import { Link } from 'react-router-dom'

import { HOP_LABEL, LAG_LABEL, SEVERITY_BORDER, formatRupees } from '../severity.js'
import Tag from './Tag.jsx'
import { CARD_INTERACTIVE, CELL_MUTED, ROW } from '../ui.js'

// A list of cases, ranked. The severity is a coloured LEFT-BORDER on the whole
// row — pattern (1) of the two the conventions allow — and the coverage sits
// beside the score as a rectangular tag with a text label, which is pattern
// (2). They are on the same row and not on the same element, which is the
// thing the rule actually forbids.
//
// The score and the coverage are shown TOGETHER and never apart. A case at 50
// with 100% coverage and a case at 50 with 65% coverage are different objects,
// and the UI is not allowed to let them look alike (invariant 2). Printing the
// score alone on a queue row is the easiest way to break that.
//
// The whole row is the link. A case id is reached from a queue, never typed.
export default function CaseRows({ cases }) {
  return (
    <ul>
      {cases.map((item) => (
        <li key={item.case_id}>
          <Link
            to={`/cases/${item.case_id}`}
            className={`${CARD_INTERACTIVE} ${ROW} mt-2 flex items-start gap-4 border-l-4 ${
              SEVERITY_BORDER[item.severity] ?? 'border-l-border-strong'
            }`}
          >
            <span className="min-w-0 flex-1">
              <span className="block truncate text-body text-ink">
                {item.description ?? item.work_id}
              </span>
              <span className={`mt-1 block truncate ${CELL_MUTED}`}>
                {item.work_id} · {item.agency ?? 'agency not recorded'} ·{' '}
                {item.district ?? item.state} · {item.mp_name}
              </span>
              <span className="mt-1 block text-meta-label text-ink-muted">
                {/* The two located findings, in words rather than as raw
                    enum values. A null gap_hop is a real answer — no hop is
                    open — and says so rather than printing nothing. */}
                {item.gap_hop ? HOP_LABEL[item.gap_hop] : 'No open fund hop'}
                {' · slowest lag: '}
                {item.slowest_lag ? LAG_LABEL[item.slowest_lag] : 'none computable'}
              </span>
            </span>

            <span className="shrink-0 text-right">
              <span className="num block text-body font-medium text-ink">{item.score}</span>
              <span className="num mt-1 block text-meta-label text-ink-secondary">
                {item.coverage_pct}% coverage
              </span>
            </span>

            <span className="shrink-0 text-right">
              <Tag tone={String(item.severity).toLowerCase()}>{item.severity}</Tag>
              <span className="num mt-1 block text-meta-label text-ink-secondary">
                {formatRupees(item.sanctioned_amt) ?? 'not published'}
              </span>
              {/* Invariant 12: an injected row is labelled wherever it is
                  shown, on the same screen and not in a footnote. */}
              {item.is_synthetic ? (
                <Tag tone="neutral" className="mt-1">
                  Synthetic control
                </Tag>
              ) : null}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  )
}
