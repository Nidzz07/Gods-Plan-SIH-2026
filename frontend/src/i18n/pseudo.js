// frontend/src/i18n/pseudo.js — dev only, never shipped to production
/**
 * Generate a pseudo-locale by transforming every string value in en.json
 * into »väluë« with accented vowels so any untranslated string renders plainly in the UI,
 * while expanding string length and preserving placeholders like {{count}}.
 */
const VOWEL_MAP = {
  a: 'ä', e: 'ë', i: 'ï', o: 'ö', u: 'ü',
  A: 'Ä', E: 'Ë', I: 'Ï', O: 'Ö', U: 'Ü',
}

function pseudoTransform(str) {
  // Preserve {{placeholder}} or {placeholder}
  const parts = str.split(/(\{\{[^}]+\}\}|\{[^}]+\})/g)
  return parts.map((part) => {
    if (/^\{.*\}$/.test(part)) return part
    return part.replace(/[aeiouAEIOU]/g, (ch) => VOWEL_MAP[ch] || ch)
  }).join('')
}

export const makePseudo = (obj) =>
  Object.fromEntries(
    Object.entries(obj).map(([k, v]) => {
      if (typeof v === 'string') {
        return [k, `»${pseudoTransform(v)}«`]
      }
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        return [k, makePseudo(v)]
      }
      return [k, v]
    })
  )

