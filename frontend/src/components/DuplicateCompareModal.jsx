import { useEffect } from 'react'

export default function DuplicateCompareModal({
  isOpen,
  onClose,
  primaryWork,
  citation,
}) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen || !citation) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        className="fixed inset-0 bg-portal-deep/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-4xl rounded border border-rule bg-paper p-6 shadow-card transition-all transform duration-180 animate-fadeIn">
        <div className="flex items-start justify-between border-b border-rule pb-4">
          <div>
            <span className="text-[12px] font-bold uppercase tracking-wider text-portal">
              Duplicate work candidate comparison
            </span>
            <h3 id="modal-title" className="font-display text-[22px] font-semibold text-navy mt-1">
              Side-by-side candidate review
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded p-1 text-ink-secondary hover:bg-portal-tint"
          >
            ✕
          </button>
        </div>

        <div className="mt-4 rounded bg-portal-tint p-3 text-[13px] text-ink">
          <p>
            <strong className="text-navy">Model method:</strong> {citation.method} ·{' '}
            <strong className="text-navy">Syntactic similarity:</strong>{' '}
            <span className="num font-bold">{citation.similarity}</span>
            {citation.cluster_size ? ` (in cluster of ${citation.cluster_size})` : ''}
          </p>
          <p className="mt-1 text-ink-secondary">{citation.reading}</p>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Primary current work */}
          <div className="rounded border border-rule bg-paper p-4 shadow-card">
            <span className="text-[11px] font-bold uppercase tracking-wider text-ink-muted">
              Current work ID
            </span>
            <p className="font-mono text-[14px] font-semibold text-navy mt-1">
              {primaryWork?.work_id ?? 'Current Work'}
            </p>
            <div className="mt-3 border-t border-rule pt-2">
              <p className="text-[11px] font-medium uppercase text-ink-secondary">Description</p>
              <p className="mt-1 text-[14px] text-ink font-medium leading-relaxed">
                {primaryWork?.description ?? 'No description'}
              </p>
            </div>
            <div className="mt-3 text-[12px] text-ink-secondary space-y-1 border-t border-rule pt-2">
              <p>District: {primaryWork?.district ?? primaryWork?.state ?? '—'}</p>
              <p>Agency: {primaryWork?.agency ?? '—'}</p>
              <p>Financial Year: {primaryWork?.fy ?? '—'}</p>
            </div>
          </div>

          {/* Matched cited work */}
          <div className="rounded border border-rule-strong bg-portal-tint/40 p-4 shadow-card">
            <span className="text-[11px] font-bold uppercase tracking-wider text-portal">
              Cited candidate work ID
            </span>
            <p className="font-mono text-[14px] font-semibold text-portal mt-1">
              {citation.matched_work_ids?.join(', ') ?? 'Matched Works'}
            </p>
            <div className="mt-3 border-t border-rule pt-2">
              <p className="text-[11px] font-medium uppercase text-ink-secondary">
                Shared description / overlap
              </p>
              <p className="mt-1 text-[14px] text-navy font-semibold leading-relaxed">
                &ldquo;{citation.shared_description}&rdquo;
              </p>
            </div>
            <div className="mt-3 text-[12px] text-ink-secondary space-y-1 border-t border-rule pt-2">
              <p>Agency: {citation.agency ?? 'Same implementing agency'}</p>
              <p className="italic text-ink-muted">
                Candidate for administrative inspection — repetition across hand pumps or lighting
                may be legitimate.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end border-t border-rule pt-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded bg-portal px-5 py-2 text-[14px] font-medium text-white hover:bg-portal-deep"
          >
            Close comparison
          </button>
        </div>
      </div>
    </div>
  )
}
