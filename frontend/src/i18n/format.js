// Formatting utilities for NIGRANI i18n
// Mandate: numberingSystem: 'latn' is mandatory across all locales to preserve Latin digits in audit views.

const LOCALE_MAP = {
  en: 'en-IN',
  hi: 'hi-IN',
  mr: 'mr-IN',
  gu: 'gu-IN',
}

const UNIT_MAP = {
  en: { cr: 'cr', lakh: 'lakh', k: 'k' },
  hi: { cr: 'करोड़', lakh: 'लाख', k: 'हज़ार' },
  mr: { cr: 'कोटी', lakh: 'लाख', k: 'हजार' },
  gu: { cr: 'કરોડ', lakh: 'લાખ', k: 'હજાર' },
}

export const USE_NATIVE_DIGITS = false

function getNumberOpts(extra = {}) {
  return USE_NATIVE_DIGITS ? extra : { numberingSystem: 'latn', ...extra }
}

export function getLocaleCode(lang = 'en') {
  return LOCALE_MAP[lang] || 'en-IN'
}

/**
 * Format integer or float count with Latin numerals and Indian grouping.
 */
export function num(v, lang = 'en') {
  if (v === null || v === undefined || isNaN(v)) return '—'
  return new Intl.NumberFormat(getLocaleCode(lang), getNumberOpts()).format(v)
}

/**
 * Format currency with Indian crore/lakh notation and translated units.
 */
export function formatRupees(v, lang = 'en') {
  if (v === null || v === undefined || isNaN(v)) return null
  const abs = Math.abs(v)
  const units = UNIT_MAP[lang] || UNIT_MAP.en
  const locale = getLocaleCode(lang)

  if (abs >= 1e7) {
    const val = (v / 1e7).toFixed(abs >= 1e9 ? 1 : 2)
    const formattedNum = new Intl.NumberFormat(
      locale,
      getNumberOpts({
        minimumFractionDigits: abs >= 1e9 ? 1 : 2,
        maximumFractionDigits: abs >= 1e9 ? 1 : 2,
      })
    ).format(Number(val))
    return `₹${formattedNum} ${units.cr}`
  }
  if (abs >= 1e5) {
    const val = (v / 1e5).toFixed(2)
    const formattedNum = new Intl.NumberFormat(
      locale,
      getNumberOpts({
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    ).format(Number(val))
    return `₹${formattedNum} ${units.lakh}`
  }
  return `₹${num(v, lang)}`
}

export const formatMoney = formatRupees

/**
 * Format date in locale style.
 */
export function formatDate(dateVal, lang = 'en', options = { dateStyle: 'medium' }) {
  if (!dateVal) return '—'
  const d = typeof dateVal === 'string' ? new Date(dateVal) : dateVal
  if (isNaN(d.getTime())) return String(dateVal)
  return new Intl.DateTimeFormat(getLocaleCode(lang), options).format(d)
}

/**
 * Format percentage.
 */
export function formatPercent(v, lang = 'en', decimals = 1) {
  if (v === null || v === undefined || isNaN(v)) return '—'
  const val = Number(v)
  return `${new Intl.NumberFormat(
    getLocaleCode(lang),
    getNumberOpts({
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  ).format(val)}%`
}

/**
 * Helper for version display (strips duplicated 'v').
 */
export function formatRulebookVersion(v) {
  if (!v) return 'v1.0.0'
  const clean = String(v).replace(/^v+/i, '')
  return `v${clean}`
}
