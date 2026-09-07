import { useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'

import { ApiError, apiPost } from '../api.js'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import PageHero from '../components/PageHero.jsx'
import PageMotif from '../components/PageMotif.jsx'
import PreviewList from '../components/PreviewList.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel } from '../components/Skeleton.jsx'
import Tag from '../components/Tag.jsx'
import { useApi } from '../hooks/useApi.js'
import { MINISTRY } from '../roles.js'
import { OPERATOR_SYMBOL, formatCount } from '../severity.js'
import { formatRulebookVersion } from '../i18n/format.js'
import { BUTTON, BUTTON_PRIMARY, CAPTION, CARD, CELL_NUM, COLUMN_HEAD, FIELD, LABEL } from '../ui.js'

const RULE_RATIONALE = {
  R01_SANCTION_DELAY:
    'Measures lag between MP recommendation date and district administrative sanction. Delays indicate administrative bottlenecks.',
  R02_FIRST_PAYMENT_DELAY:
    'Time elapsed from sanction to initial disbursement. Indicates tender or agency mobilisation stalls.',
  R03_COMPLETION_DELAY:
    'Time from first payment to asset completion. Captures physical execution issues in the field.',
  R04_UTILISATION_SHORTFALL:
    'Difference between sanctioned amount and actual certified expenditure. Identifies stalled balances.',
  R05_UNUTILIZED_SURRENDER:
    'Unspent funds left standing across financial years without formal revalidation.',
  R06_DUPLICATE_WORK:
    'Syntactic overlap in work descriptions within same district/agency. Indicates candidate works for review.',
  R07_COMMISSION_GAP:
    'Works marked completed without recording formal inspection / handover certificates.',
  R08_BENEFICIARY_DATA_GAP:
    'Works omitting community or ward beneficiary identifiers in the public portal.',
  R09_PHYSICAL_PROGRESS_STALL:
    'Works reporting zero incremental progress over consecutive reporting quarters.',
  R10_EXPENDITURE_MISMATCH:
    'Discrepancies between bank transaction logs and portal-declared disbursements.',
}

function asNumber(value) {
  if (value === '' || value === null || value === undefined) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export default function Rulebook() {
  const { user } = useOutletContext()
  const isMinistry = user?.role === MINISTRY

  const { data, error, loading, reload } = useApi('/api/rulebook')

  const [draft, setDraft] = useState({})
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState(null)
  const [result, setResult] = useState(null)

  const drifted = useMemo(
    () => new Set(data?.rules_edited_since_scoring ?? []),
    [data],
  )

  // PreviewList items for 10 rules (§8.6)
  const previewItems = useMemo(() => {
    if (!data?.rules) return []
    return data.rules.map((rule) => {
      const op = OPERATOR_SYMBOL[rule.operator] ?? rule.operator
      const rationale = RULE_RATIONALE[rule.id] ?? 'Evaluates domain indicators against measured thresholds.'
      return {
        id: rule.id,
        label: rule.label,
        title: `${rule.label} (${rule.id})`,
        badge: `${rule.weight} pts · ${rule.severity}`,
        meta: `Reads: ${rule.field} ${op} ${rule.threshold} · Firing weight: +${rule.weight}`,
        body: `${rationale} Severity band: ${rule.severity}. Contributes +${rule.weight} points to composite score when condition evaluates true.`,
        href: '#rules-table',
      }
    })
  }, [data])

  const changes = useMemo(() => {
    if (!data) return []
    const out = []
    for (const rule of data.rules) {
      const edit = draft[rule.id]
      if (!edit) continue
      const threshold = asNumber(edit.threshold)
      const weight = asNumber(edit.weight)
      if (threshold !== null && threshold !== rule.threshold) {
        out.push({ rule_id: rule.id, key: 'threshold', from: rule.threshold, to: threshold })
      }
      if (weight !== null && weight !== rule.weight) {
        out.push({ rule_id: rule.id, key: 'weight', from: rule.weight, to: weight })
      }
    }
    return out
  }, [draft, data])

  function set(ruleId, key, value) {
    setDraft((current) => ({ ...current, [ruleId]: { ...current[ruleId], [key]: value } }))
  }

  async function submit(event) {
    event.preventDefault()
    if (!changes.length || !note.trim()) return
    setBusy(true)
    setFailure(null)
    try {
      const byRule = new Map()
      for (const change of changes) {
        const entry = byRule.get(change.rule_id) ?? { rule_id: change.rule_id }
        entry[change.key] = change.to
        byRule.set(change.rule_id, entry)
      }
      setResult(
        await apiPost('/api/rulebook', { note: note.trim(), rules: [...byRule.values()] }),
      )
      setDraft({})
      setNote('')
      reload()
    } catch (thrown) {
      setFailure(thrown instanceof ApiError ? thrown.message : String(thrown))
    } finally {
      setBusy(false)
    }
  }

  const GRID = 'grid grid-cols-[1fr_150px_110px_110px_90px] items-start gap-4'

  return (
    <article className="relative isolate flex-1 bg-paper">
      <PageMotif variant="rulebook" />

      {/* §7.2 Page Hero */}
      <PageHero
        title="Rulebook specification"
        lede={
          data
            ? `Ten rules and one pattern bonus (${formatRulebookVersion(data.version)}), 154 total points. Every point on every case originates here — zero points come from black-box models.`
            : 'Ten rules and one corroboration bonus, 154 points in total.'
        }
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Rulebook' },
        ]}
      />

      <div className="w-full px-4 sm:px-6 py-8 space-y-10">
        {loading && (
          <LoadingRegion label="Loading the rulebook…">
            <SkeletonPanel lines={5} />
          </LoadingRegion>
        )}

        {error && <ErrorState error={error} />}

        {data && (
          <>
            {/* Version & Sync Status Box */}
            <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
              <div className="flex flex-wrap items-baseline justify-between gap-4 border-b border-rule pb-3">
                <span className="font-display text-[18px] font-semibold text-navy">
                  Version {data.version} · Updated by {data.updated_by}
                </span>
                <Tag tone={data.file_matches_stored_version ? 'low' : 'medium'}>
                  {data.file_matches_stored_version
                    ? 'Active snapshot matches cases'
                    : 'File edited since scoring'}
                </Tag>
              </div>

              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-grid-gap">
                <div>
                  <p className={LABEL}>Total rule weight</p>
                  <p className="num text-[18px] font-bold text-navy">
                    {data.rule_weight_total} points
                  </p>
                </div>
                <div>
                  <p className={LABEL}>Pattern bonus</p>
                  <p className="num text-[18px] font-bold text-gold">
                    +{data.corroboration.weight} points
                  </p>
                </div>
                <div>
                  <p className={LABEL}>HIGH Severity cut-off</p>
                  <p className="num text-[18px] font-bold text-coral">
                    ≥ {data.severity_bands_resolved.high}
                  </p>
                </div>
                <div>
                  <p className={LABEL}>MEDIUM Severity cut-off</p>
                  <p className="num text-[18px] font-bold text-gold">
                    ≥ {data.severity_bands_resolved.medium}
                  </p>
                </div>
              </div>
            </section>

            {/* PreviewList of the ten rules (§8.6) */}
            <section className="rounded border border-rule bg-portal-tint/50 py-card-y px-card-x shadow-card">
              <div className="mb-4">
                <h2 className="font-display text-[22px] font-semibold text-navy">
                  The ten scoring rules
                </h2>
                <div className="mt-1 h-[3px] w-14 bg-saffron" aria-hidden="true" />
                <p className="mt-1 text-[14px] text-ink-secondary">
                  Hover or focus on any rule to inspect its operational field, comparison threshold,
                  and rationale.
                </p>
              </div>

              <PreviewList
                items={previewItems}
                title="Rule directory & rationale"
                caption="Select a rule to view operator logic and weights"
              />
            </section>

            {/* Rule Table & Ministry Proposal Form */}
            <form id="rules-table" onSubmit={submit} className="space-y-6">
              <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <SectionHeading title="Rule threshold & weight matrix">
                  {isMinistry
                    ? 'Threshold and weight are live-editable for Ministry analysts. Other columns are governed by data-profile calibrations.'
                    : 'The ten rules in force. All parameters are verified against measured distributions.'}
                </SectionHeading>

                <div className={`${GRID} mt-6 border-b border-rule bg-paper-sunk px-4 py-3 text-[12px] font-semibold text-ink-secondary uppercase`}>
                  <span>Rule</span>
                  <span>Field read</span>
                  <span className="text-right">Threshold</span>
                  <span className="text-right">Weight</span>
                  <span>Severity</span>
                </div>

                <ul className="divide-y divide-rule text-[14px]">
                  {data.rules.map((rule) => (
                    <li
                      key={rule.id}
                      className={`${GRID} py-card-y px-card-x items-center ${
                        drifted.has(rule.id) ? 'bg-gold/10' : 'hover:bg-paper-sunk/50'
                      }`}
                    >
                      <div>
                        <span className="font-medium text-navy block">{rule.label}</span>
                        <span className="font-mono text-[12px] text-ink-muted">{rule.id}</span>
                      </div>

                      <div>
                        <span className="font-mono text-[13px] text-ink">{rule.field}</span>
                        <span className="block text-[11px] text-ink-secondary">
                          {OPERATOR_SYMBOL[rule.operator] ?? rule.operator} threshold
                        </span>
                      </div>

                      <div className="text-right">
                        {isMinistry ? (
                          <input
                            type="number"
                            step="any"
                            aria-label={`${rule.label} threshold`}
                            defaultValue={rule.threshold}
                            onChange={(e) => set(rule.id, 'threshold', e.target.value)}
                            className="num w-24 rounded border border-rule bg-paper py-1 px-2 text-right text-[14px] text-ink focus:border-portal focus:outline-none"
                          />
                        ) : (
                          <span className="num font-semibold text-ink">{rule.threshold}</span>
                        )}
                      </div>

                      <div className="text-right">
                        {isMinistry ? (
                          <input
                            type="number"
                            min="0"
                            max="100"
                            aria-label={`${rule.label} weight`}
                            defaultValue={rule.weight}
                            onChange={(e) => set(rule.id, 'weight', e.target.value)}
                            className="num w-20 rounded border border-rule bg-paper py-1 px-2 text-right text-[14px] text-ink focus:border-portal focus:outline-none"
                          />
                        ) : (
                          <span className="num font-bold text-navy">{rule.weight}</span>
                        )}
                      </div>

                      <div>
                        <span
                          className={`text-[12px] font-semibold uppercase ${
                            rule.severity === 'HIGH'
                              ? 'text-coral'
                              : rule.severity === 'MEDIUM'
                                ? 'text-gold'
                                : 'text-green'
                          }`}
                        >
                          {rule.severity}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>

                {/* Ministry Proposal Box with required plain-language disclaimer */}
                {isMinistry ? (
                  <div className="mt-8 rounded border border-rule bg-portal-tint/60 py-card-y px-card-x">
                    <h3 className="font-display text-[18px] font-semibold text-navy">
                      Propose rulebook modification
                    </h3>

                    {/* Disclaimer panel (§8.6) */}
                    <div className="mt-3 rounded border-l-4 border-l-gold bg-paper py-card-y px-card-x text-[13px] text-ink">
                      <p className="font-semibold text-navy">
                        This creates a new rulebook version. Existing cases keep the score they were
                        given and are not re-scored until each is recomputed individually.
                      </p>
                      <p className="mt-1 text-ink-secondary">
                        Snapshots ensure that historical scores remain reproducible and verifiable
                        under audit.
                      </p>
                    </div>

                    <div className="mt-4">
                      <label htmlFor="version-note" className={LABEL}>
                        Reason for modification (required for audit trail)
                      </label>
                      <input
                        id="version-note"
                        type="text"
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        placeholder="e.g. Adjusting delay tolerance after national distribution review"
                        className="w-full rounded border border-rule bg-paper py-2 px-3 text-[14px] text-ink focus:border-portal focus:outline-none"
                      />
                    </div>

                    {failure && (
                      <div className="mt-3 rounded bg-coral/10 p-3 text-[13px] text-coral font-medium">
                        {failure}
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={busy || !changes.length || !note.trim()}
                      className={`${BUTTON_PRIMARY} mt-4`}
                    >
                      {busy ? 'Creating version…' : `Create version (${changes.length} changes)`}
                    </button>
                  </div>
                ) : (
                  <div className="mt-6 rounded bg-paper-sunk py-card-y px-card-x text-[13px] text-ink-secondary">
                    Editing rulebook parameters is restricted to Ministry analysts. Other roles have
                    read-only access to verify scoring criteria.
                  </div>
                )}
              </div>
            </form>

            {/* Version History List */}
            <section className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
              <SectionHeading title="Immutable version log">
                Historical snapshots stored with cryptographic digests.
              </SectionHeading>

              <ul className="mt-4 space-y-2 text-[13px]">
                {data.versions.map((ver) => (
                  <li
                    key={ver.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded border border-rule bg-paper-sunk/60 p-3"
                  >
                    <div>
                      <span className="font-bold text-navy">v{ver.version}</span> ·{' '}
                      <span className="text-ink-secondary">{ver.note || 'Initial calibration'}</span>
                    </div>
                    <div className="font-mono text-[12px] text-ink-muted">
                      {ver.yaml_sha256?.slice(0, 16)} · {String(ver.created_at).slice(0, 10)}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}
      </div>
    </article>
  )
}
