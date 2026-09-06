import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import PageMotif from '../components/PageMotif.jsx'
import PageHero from '../components/PageHero.jsx'
import { useApi } from '../hooks/useApi.js'
import { formatCount, formatRupees, SEVERITY_BORDER } from '../severity.js'
import { LoadingRegion, SkeletonRows } from '../components/Skeleton.jsx'
import { ErrorState } from '../components/EmptyState.jsx'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('q') || ''
  const cat = searchParams.get('cat') || 'all'

  const [inputVal, setInputVal] = useState(q)
  const [selectedCat, setSelectedCat] = useState(cat)

  // Search against cases endpoint with text filtering
  const { data, loading, error } = useApi(
    q ? `/api/cases?limit=100` : null,
  )

  const filteredItems = useMemo(() => {
    if (!data?.items) return []
    if (!q.trim()) return data.items
    const term = q.toLowerCase()
    return data.items.filter((item) => {
      const matchWork = item.work_id?.toLowerCase().includes(term)
      const matchCase = item.case_id?.toLowerCase().includes(term)
      const matchDesc = item.description?.toLowerCase().includes(term)
      const matchDist = item.district?.toLowerCase().includes(term)
      const matchAgency = item.agency?.toLowerCase().includes(term)
      const matchMp = item.mp_name?.toLowerCase().includes(term)
      return matchWork || matchCase || matchDesc || matchDist || matchAgency || matchMp
    })
  }, [data, q])

  function handleSearch(e) {
    e.preventDefault()
    setSearchParams({ q: inputVal.trim(), cat: selectedCat })
  }

  return (
    <article className="relative isolate flex-1 bg-paper">
      <PageMotif variant="district" />

      <PageHero
        title="Record search"
        lede={`Search across works, case IDs, districts, agencies and members in your authenticated scope.`}
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Search' },
        ]}
      />

      <div className="mx-auto max-w-[1240px] px-6 py-8">
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex flex-col sm:flex-row shadow-card rounded border border-rule-strong bg-paper overflow-hidden">
            <input
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              placeholder="Search work ID, district, agency, member…"
              aria-label="Search query"
              className="flex-1 px-4 py-3 text-[15px] text-ink placeholder-ink-muted focus:outline-none"
            />
            <select
              value={selectedCat}
              onChange={(e) => setSelectedCat(e.target.value)}
              aria-label="Category"
              className="border-t sm:border-t-0 sm:border-l border-rule bg-paper-sunk px-3 py-3 text-[14px] text-ink focus:outline-none"
            >
              <option value="all">All categories</option>
              <option value="works">Works</option>
              <option value="districts">Districts</option>
              <option value="agencies">Agencies</option>
              <option value="members">Members</option>
            </select>
            <button
              type="submit"
              className="bg-portal px-6 py-3 text-[14px] font-semibold text-white hover:bg-portal-deep"
            >
              Search
            </button>
          </div>
        </form>

        {loading && (
          <LoadingRegion label="Searching records…">
            <SkeletonRows rows={5} />
          </LoadingRegion>
        )}

        {error && <ErrorState error={error} />}

        {!loading && q && (
          <div>
            <p className="text-[14px] text-ink-secondary mb-4">
              Showing {formatCount(filteredItems.length)} matching record
              {filteredItems.length === 1 ? '' : 's'} for &ldquo;{q}&rdquo;
            </p>

            {filteredItems.length === 0 ? (
              <div className="rounded border border-rule bg-paper p-8 text-center text-ink-secondary">
                No records matched your search in this scope.
              </div>
            ) : (
              <ul className="space-y-3">
                {filteredItems.map((item) => (
                  <li
                    key={item.case_id}
                    className={`rounded border border-rule border-l-4 ${
                      SEVERITY_BORDER[item.severity] ?? 'border-l-border-strong'
                    } bg-paper p-4 shadow-card hover:bg-portal-tint/40 transition-colors`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <Link
                          to={`/cases/${item.case_id}`}
                          className="font-medium text-navy text-[16px] hover:underline"
                        >
                          {item.description || item.work_id}
                        </Link>
                        <p className="num text-[12px] text-ink-muted mt-1">
                          Case {item.case_id} · Work {item.work_id} · {item.district || item.state}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="num font-bold text-navy text-[18px]">{item.score}</span>
                        <span className="block text-[11px] uppercase text-ink-muted">
                          {item.severity} · {item.coverage_pct}% cov
                        </span>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </article>
  )
}
