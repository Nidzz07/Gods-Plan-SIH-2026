import { Link, useParams } from 'react-router-dom'
import PageHero from '../components/PageHero.jsx'

const DOCS_CONTENT = {
  'data-profile': {
    title: 'Data profile & 12 portal datasets',
    lede: 'Complete schema, volume and nullity measurements across the twelve published MPLADS portal exports in the committed corpus.',
    sections: [
      {
        heading: 'Committed exports',
        body: 'The corpus contains 118,704 raw records covering works, recommended projects, sanctions, expenditure installments, completions and member accounts from mplads.mospi.gov.in as of August 2026.',
      },
      {
        heading: 'Ingest and canonicalisation',
        body: 'Every row is canonicalised and validated during ingest. Rows failing referential integrity or schema constraints are preserved in ingest_rejects with reasons, ensuring zero silent drops.',
      },
    ],
  },
  'api-reference': {
    title: 'API reference & role scoping',
    lede: 'Every endpoint under /api requires bearer authentication and enforces server-side role scoping at the SQL query level.',
    sections: [
      {
        heading: 'Scoping predicates',
        body: 'Role predicates are compiled into database WHERE clauses (invariant 10). District Authority tokens can only query works within their bound state and district. Unscoped access yields 404 / 403 refusals.',
      },
      {
        heading: 'Endpoints overview',
        body: 'Endpoints provide national analytics (/api/analytics/national), state comparisons (/api/analytics/state/:state), district queues (/api/analytics/district/:district), case details (/api/cases/:id), rulebook management (/api/rulebook), and alert triage (/api/alerts).',
      },
    ],
  },
  'audit-trail': {
    title: 'Append-only audit trail model',
    lede: '84,666 hash-chained events enforcing NIST SP 800-92 integrity without update or delete operations.',
    sections: [
      {
        heading: 'Hash-chain structure',
        body: 'Each audit entry incorporates the SHA-256 digest of its predecessor, creating a tamper-evident sequence. Any recalculation of historical cases re-evaluates against the snapshot stored on that day.',
      },
      {
        heading: 'Reproducibility',
        body: 'Scores recomputed months later against stored rulebook snapshots reproduce identical traces and values.',
      },
    ],
  },
}

export default function StaticDocPage() {
  const { docId } = useParams()
  const doc = DOCS_CONTENT[docId] || {
    title: 'System documentation',
    lede: 'Official specification and system architecture records for NIGRANI.',
    sections: [
      {
        heading: 'Architecture',
        body: 'Four-tier detection architecture enforcing a strict boundary between deterministic rule scoring and zero-weight machine learning badges.',
      },
    ],
  }

  return (
    <article className="relative isolate flex-1 bg-paper">
      <PageHero
        title={doc.title}
        lede={doc.lede}
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Documentation', href: '/#docs' },
          { label: doc.title },
        ]}
      />

      <div className="mx-auto max-w-[1240px] px-6 py-8">
        <div className="space-y-6">
          {doc.sections.map((sec, idx) => (
            <div key={idx} className="rounded border border-rule bg-paper p-6 shadow-card">
              <h3 className="font-display text-[20px] font-semibold text-navy mb-2">
                {sec.heading}
              </h3>
              <p className="text-body text-ink-secondary leading-relaxed">{sec.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-8 pt-4 border-t border-rule flex items-center gap-4">
          <Link
            to="/rulebook"
            className="rounded bg-portal px-4 py-2 text-[14px] font-medium text-white hover:bg-portal-deep"
          >
            Open Rulebook
          </Link>
          <Link
            to="/reports/data-gap"
            className="rounded border border-rule bg-paper px-4 py-2 text-[14px] font-medium text-ink hover:bg-paper-sunk"
          >
            View Data-gap Report
          </Link>
        </div>
      </div>
    </article>
  )
}
