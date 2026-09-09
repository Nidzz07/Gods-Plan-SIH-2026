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
    titleKey: 'footer.theSystem',
    defaultTitle: 'The system',
    links: [
      { labelKey: 'landing.howItWorks', defaultLabel: 'How it works', href: '#how-it-works' },
      { labelKey: 'landing.theFinding', defaultLabel: 'The finding', href: '#the-finding' },
      { labelKey: 'footer.detectionTiers', defaultLabel: 'Detection tiers', href: '#the-wall' },
      { labelKey: 'footer.liveSignalSample', defaultLabel: 'Live signal sample', href: '#live-signal' },
    ],
  },
  {
    titleKey: 'footer.forAuthorities',
    defaultTitle: 'For authorities',
    links: [
      { labelKey: 'footer.ministryDashboard', defaultLabel: 'Ministry dashboard', href: '/ministry' },
      { labelKey: 'common.stateOverview', defaultLabel: 'State overview', href: '/state' },
      { labelKey: 'common.districtQueue', defaultLabel: 'District queue', href: '/district' },
      { labelKey: 'footer.memberAccount', defaultLabel: 'Member account', href: '/member' },
    ],
  },
  {
    titleKey: 'footer.documentation',
    defaultTitle: 'Documentation',
    links: [
      { labelKey: 'footer.rulebookVer', defaultLabel: 'Rulebook v1.0.0', href: '/rulebook' },
      { labelKey: 'common.dataGapReport', defaultLabel: 'Data-gap report', href: '/reports/data-gap' },
      { labelKey: 'common.alerts', defaultLabel: 'Alert queue', href: '/alerts' },
      { labelKey: 'landing.docDataProfile', defaultLabel: 'Data profile', href: '/docs/data-profile' },
    ],
  },
  {
    titleKey: 'footer.dataIntegrity',
    defaultTitle: 'Data & Integrity',
    links: [
      { labelKey: 'footer.corpusFacts', defaultLabel: 'Corpus facts', href: '/#corpus-facts' },
      { labelKey: 'footer.rawDatasets', defaultLabel: '12 Raw datasets', href: 'https://mplads.mospi.gov.in', external: true },
      { labelKey: 'footer.scoringSpec', defaultLabel: 'Scoring engine spec', href: '/rulebook' },
      { labelKey: 'footer.auditModel', defaultLabel: 'Audit trail model', href: '/docs/audit-trail' },
    ],
  },
  {
    titleKey: 'landing.about',
    defaultTitle: 'About',
    links: [
      { labelKey: 'footer.sihProblem', defaultLabel: 'SIH 2026 PS 26102', href: '#about' },
      { labelKey: 'footer.mospiDiid', defaultLabel: 'MoSPI / DIID', href: 'https://mospi.gov.in', external: true },
      { labelKey: 'footer.teamGodsPlan', defaultLabel: "Team GOD's Plan", href: '#about' },
      { labelKey: 'footer.signInPortal', defaultLabel: 'Sign in to portal', href: '/sign-in' },
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
              <div key={col.defaultTitle}>
                <h2 className="text-[15px] font-semibold text-white mb-4">
                  {t(col.titleKey, col.defaultTitle)}
                </h2>
                <ul className="space-y-2">
                  {col.links.map((link) => (
                    <li key={link.defaultLabel}>
                      {link.external ? (
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[14px] text-[#C9D8E4] transition-colors hover:text-white hover:underline"
                        >
                          {t(link.labelKey, link.defaultLabel)} ↗
                        </a>
                      ) : link.href.startsWith('#') ? (
                        <a
                          href={link.href}
                          className="text-[14px] text-[#C9D8E4] transition-colors hover:text-white hover:underline"
                        >
                          {t(link.labelKey, link.defaultLabel)}
                        </a>
                      ) : (
                        <Link
                          to={link.href}
                          className="text-[14px] text-[#C9D8E4] transition-colors hover:text-white hover:underline"
                        >
                          {t(link.labelKey, link.defaultLabel)}
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
              {t('footer.colophonP1', 'Built for Smart India Hackathon 2026, Problem Statement 26102 (MoSPI, Data Informatics and Innovation Division) by team GOD’s Plan. Detection figures are measured on twelve published MPLADS portal exports — a large sample, not the complete national record.')}
            </p>
            <p className="font-medium text-white/80">
              {t('footer.colophonP2', 'Last reviewed and updated on 06 September 2026 at 15:30 IST.')}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <span className="font-display font-semibold text-white/90">NIGRANI</span>
            <span className="block text-[11px] text-white/50">
              {t('footer.buildVersion', 'v1.0.0 · Production build')}
            </span>
          </div>
        </div>
      </section>
    </footer>
  )
}
