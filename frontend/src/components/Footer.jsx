import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const REFERENCES = [
  {
    title: 'MPLADS Portal, MoSPI',
    descriptorKey: 'footer.refMplads',
    defaultDescriptor: 'All twelve datasets used in this project',
    href: 'https://mplads.mospi.gov.in/digigov/dashboard.html',
  },
  {
    title: 'National Portal of India',
    descriptorKey: 'footer.refIndiaGov',
    defaultDescriptor: 'Design and status-guidance benchmark',
    href: 'https://www.india.gov.in/',
  },
  {
    title: 'MAHAONE Portal',
    descriptorKey: 'footer.refMahaone',
    defaultDescriptor: 'Maharashtra SSO — sign-in page reference',
    href: 'https://mahaone.maharashtra.gov.in/',
  },
  {
    title: 'W3C WCAG 2.1 AA',
    descriptorKey: 'footer.refWcag',
    defaultDescriptor: 'Accessibility conformance reference',
    href: 'https://www.w3.org/TR/WCAG21/',
  },
]

const SITEMAP_COLUMNS = [
  {
    title: 'The system',
    links: [
      { label: 'How it works', href: '#how-it-works' },
      { label: 'The finding', href: '#the-finding' },
      { label: 'Detection tiers', href: '#the-wall' },
      { label: 'Live signal sample', href: '#live-signal' },
    ],
  },
  {
    title: 'For authorities',
    links: [
      { label: 'Ministry dashboard', href: '/ministry' },
      { label: 'State overview', href: '/state' },
      { label: 'District queue', href: '/district' },
      { label: 'Member account', href: '/member' },
    ],
  },
  {
    title: 'Documentation',
    links: [
      { label: 'Rulebook v1.0.0', href: '/rulebook' },
      { label: 'Data-gap report', href: '/reports/data-gap' },
      { label: 'Alert queue', href: '/alerts' },
      { label: 'Data profile', href: '/docs/data-profile' },
    ],
  },
  {
    title: 'Data & Integrity',
    links: [
      { label: 'Corpus facts', href: '/#corpus-facts' },
      { label: '12 Raw datasets', href: 'https://mplads.mospi.gov.in', external: true },
      { label: 'Scoring engine spec', href: '/rulebook' },
      { label: 'Audit trail model', href: '/docs/audit-trail' },
    ],
  },
  {
    title: 'About',
    links: [
      { label: 'SIH 2026 PS 26102', href: '#about' },
      { label: 'MoSPI / DIID', href: 'https://mospi.gov.in', external: true },
      { label: "Team GOD's Plan", href: '#about' },
      { label: 'Sign in to portal', href: '/sign-in' },
    ],
  },
]

export default function Footer() {
  const { t } = useTranslation()

  return (
    <footer className="w-full text-ink">
      {/* 1. References strip (paper-sunk) */}
      <section className="border-t border-rule bg-paper-sunk py-6">
        <div className="mx-auto max-w-[1240px] px-6">
          <p className="text-[12px] font-medium uppercase tracking-wider text-ink-secondary mb-3">
            {t('footer.referencesHeading', 'References and design benchmarks')}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 items-stretch">
            {REFERENCES.map((item) => (
              <a
                key={item.title}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex flex-col justify-between rounded border border-rule/60 bg-paper transition-colors hover:border-rule-strong hover:bg-portal-tint"
                style={{ padding: '22px 24px' }}
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[15px] font-semibold text-ink/80 transition-colors group-hover:text-navy">
                      {item.title}
                    </span>
                    <span className="text-[13px] text-ink-secondary opacity-70 group-hover:opacity-100 transition-opacity" aria-hidden="true">
                      ↗
                    </span>
                  </div>
                  <p className="mt-2 text-[12px] text-ink-secondary leading-relaxed">
                    {t(item.descriptorKey, item.defaultDescriptor)}
                  </p>
                </div>
                <span className="sr-only"> ({t('common.opensInNewTab', 'opens in a new tab')})</span>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* 2. Sitemap (portal-deep, 5 columns) */}
      <section className="bg-portal-deep py-12 text-white border-t border-portal">
        <div className="mx-auto max-w-[1240px] px-6">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-5">
            {SITEMAP_COLUMNS.map((col) => (
              <div key={col.title}>
                <h2 className="text-[15px] font-semibold text-white mb-4">{col.title}</h2>
                <ul className="space-y-2">
                  {col.links.map((link) => (
                    <li key={link.label}>
                      {link.external ? (
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[14px] text-[#C9D8E4] transition-colors hover:text-white hover:underline"
                        >
                          {link.label} ↗
                        </a>
                      ) : link.href.startsWith('#') ? (
                        <a
                          href={link.href}
                          className="text-[14px] text-[#C9D8E4] transition-colors hover:text-white hover:underline"
                        >
                          {link.label}
                        </a>
                      ) : (
                        <Link
                          to={link.href}
                          className="text-[14px] text-[#C9D8E4] transition-colors hover:text-white hover:underline"
                        >
                          {link.label}
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. Colophon */}
      <section className="bg-portal-deep border-t border-white/10 py-6 text-[13px] text-[#8FA6B8]">
        <div className="mx-auto max-w-[1240px] px-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="max-w-3xl space-y-1">
            <p>
              Built for Smart India Hackathon 2026, Problem Statement 26102 (MoSPI, Data Informatics
              and Innovation Division) by team GOD&rsquo;s Plan. Detection figures are measured on
              twelve published MPLADS portal exports — a large sample, not the complete national record.
            </p>
            <p className="font-medium text-white/80">
              Last reviewed and updated on 06 September 2026 at 15:30 IST.
            </p>
          </div>
          <div className="shrink-0 text-right">
            <span className="font-display font-semibold text-white/90">NIGRANI</span>
            <span className="block text-[11px] text-white/50">v1.0.0 · Production build</span>
          </div>
        </div>
      </section>
    </footer>
  )
}
