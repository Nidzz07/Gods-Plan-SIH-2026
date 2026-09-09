import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const srcDir = path.resolve(__dirname, '../src')

const ALLOWLIST = new Set([
  'NIGRANI',
  'निगरानी',
  'MoSPI',
  'MPLADS',
  'GOI',
  'SIH 2026',
  'SIH 2026 PS 26102',
  'MAHAONE',
  'WCAG 2.1 AA',
  'W3C',
  'SHA-256',
  'IST',
  'USD',
  'INR',
  "Team GOD's Plan",
  'MoSPI / DIID',
  'MoSPI Analyst',
  'A',
  'A+',
  'A−',
  'अ / A',
  '▶',
  '▼',
  '→',
  '↗',
  '—',
  '·',
  '›',
  '…',
  '+',
  '-',
  '/',
  ':',
  'pp',
  '+3.65 pp',
  'Jalaun · Uttar Pradesh',
  'Kanpur Nagar · Uttar Pradesh',
  'Patna · Bihar',
  'Jaipur · Rajasthan',
  'Thane · Maharashtra',
])

function findJsxFiles(dir) {
  let results = []
  const list = fs.readdirSync(dir)
  for (const file of list) {
    const fullPath = path.join(dir, file)
    const stat = fs.statSync(fullPath)
    if (stat.isDirectory()) {
      results = results.concat(findJsxFiles(fullPath))
    } else if (file.endsWith('.jsx')) {
      results.push(fullPath)
    }
  }
  return results
}

const files = findJsxFiles(srcDir)
let errorCount = 0

console.log(`[i18n-lint] Checking ${files.length} JSX files for untranslated strings and toLocaleString...`)

for (const filePath of files) {
  const rel = path.relative(srcDir, filePath)
  const content = fs.readFileSync(filePath, 'utf8')
  const lines = content.split('\n')

  // Check 1: Banned toLocaleString()
  if (content.includes('.toLocaleString(')) {
    console.error(`[ERROR] ${rel}: Contains .toLocaleString() call. Route numbers through i18n/format.js num() instead.`)
    errorCount++
  }

  // Check 2: Props & JSX text
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()
    if (trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*')) {
      continue
    }

    // Check prop literals: placeholder, aria-label, title
    const propRegex = /(placeholder|aria-label|title)=["']([^"'{}>]+)["']/g
    let match
    while ((match = propRegex.exec(line)) !== null) {
      const prop = match[1]
      const val = match[2].trim()
      if (val && !ALLOWLIST.has(val) && /[a-zA-Z]{3,}/.test(val)) {
        if (!val.startsWith('#') && !val.startsWith('preview-') && !val.startsWith('http')) {
          console.error(`[ERROR] ${rel}:${i + 1} Untranslated prop [${prop}]: "${val}"`)
          errorCount++
        }
      }
    }

    // Check JSX text nodes: >Text<
    const textRegex = />([^<>{}$]+)</g
    while ((match = textRegex.exec(line)) !== null) {
      const val = match[1].trim()
      if (val && !ALLOWLIST.has(val) && /[a-zA-Z]{3,}/.test(val)) {
        if (!val.startsWith('/*') && !val.endsWith('*/') && !val.startsWith('&')) {
          console.error(`[ERROR] ${rel}:${i + 1} Untranslated JSX text: "${val}"`)
          errorCount++
        }
      }
    }
  }
}

if (errorCount > 0) {
  console.error(`\n❌ [i18n-lint] Failed with ${errorCount} untranslated or unrouted strings.`)
  process.exit(1)
} else {
  console.log(`\n✅ [i18n-lint] All ${files.length} JSX files passed i18n check successfully.`)
}
