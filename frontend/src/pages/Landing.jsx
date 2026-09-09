import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import UtilityStrip from '../components/UtilityStrip.jsx'
import Masthead from '../components/Masthead.jsx'
import Footer from '../components/Footer.jsx'
import HeroCarousel from '../components/HeroCarousel.jsx'
import LanguageSwitcher from '../i18n/LanguageSwitcher.jsx'
import { useLanguage } from '../i18n/useLanguage.js'
import { num, formatRupees } from '../i18n/format.js'
import { CORPUS } from '../data/corpus-facts.js'
import mospiEmblem from '../assets/gov/mospi-emblem.jpeg'
import docRulebook from '../assets/icons/doc-rulebook.png'
import docDataProfile from '../assets/icons/doc-data-profile.png'
import docDataGap from '../assets/icons/doc-data-gap.png'
import docApi from '../assets/icons/doc-api.png'
import docAudit from '../assets/icons/doc-audit.png'

export default function Landing() {
  const { t } = useTranslation()
  const { lang } = useLanguage()
  const navigate = useNavigate()

  const [searchQuery, setSearchQuery] = useState('')
  const [searchCategory, setSearchCategory] = useState('all')
  const [statsVisible, setStatsVisible] = useState(false)
  const [findingVisible, setFindingVisible] = useState(false)
  const [animatedStats, setAnimatedStats] = useState({
    works: 0,
    rows: 0,
    datasets: 0,
    agencies: 0,
    states: 0,
  })

  const statsRef = useRef(null)
  const findingRef = useRef(null)

  // Intersection observer for stats count-up (once per session)
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !statsVisible) {
          setStatsVisible(true)
        }
      },
      { threshold: 0.2 },
    )
    if (statsRef.current) observer.observe(statsRef.current)
    return () => observer.disconnect()
  }, [statsVisible])

  // Count up animation
  useEffect(() => {
    if (!statsVisible) return
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (prefersReducedMotion) {
      setAnimatedStats({
        works: CORPUS.worksScored,
        rows: CORPUS.rowsIngested,
        datasets: CORPUS.datasets,
        agencies: CORPUS.agencies,
        states: CORPUS.states,
      })
      return
    }

    const duration = 900
    const start = performance.now()

    function step(timestamp) {
      const progress = Math.min((timestamp - start) / duration, 1)
      const easeOut = 1 - Math.pow(1 - progress, 3)

      setAnimatedStats({
        works: Math.floor(easeOut * CORPUS.worksScored),
        rows: Math.floor(easeOut * CORPUS.rowsIngested),
        datasets: Math.floor(easeOut * CORPUS.datasets),
        agencies: Math.floor(easeOut * CORPUS.agencies),
        states: Math.floor(easeOut * CORPUS.states),
      })

      if (progress < 1) {
        requestAnimationFrame(step)
      } else {
        setAnimatedStats({
          works: CORPUS.worksScored,
          rows: CORPUS.rowsIngested,
          datasets: CORPUS.datasets,
          agencies: CORPUS.agencies,
          states: CORPUS.states,
        })
      }
    }

    requestAnimationFrame(step)
  }, [statsVisible])

  // Intersection observer for finding bars
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setFindingVisible(true)
        }
      },
      { threshold: 0.3 },
    )
    if (findingRef.current) observer.observe(findingRef.current)
    return () => observer.disconnect()
  }, [])

  function handleSearch(e) {
    e.preventDefault()
    if (!searchQuery.trim()) return
    navigate(
      `/sign-in?next=/search&q=${encodeURIComponent(searchQuery)}&cat=${encodeURIComponent(searchCategory)}`,
    )
  }

  return (
    <div className="min-h-screen bg-paper text-ink flex flex-col selection:bg-portal selection:text-white">
      {/* Global Top Chrome */}
      <UtilityStrip />
      <Masthead />

      <main id="main" tabIndex={-1} className="focus:outline-none flex-1">
        {/* ========================================================================= */}
        {/* §1 Hero — Photographic Filmstrip Carousel with Solid 68% Scrim (Part B)   */}
        {/* ========================================================================= */}
        <section
          className="relative overflow-hidden border-b border-rule"
          style={{ paddingTop: 'clamp(4rem, 7vw, 7.5rem)', paddingBottom: 'clamp(4rem, 7vw, 7.5rem)' }}
        >
          {/* Background Hero Carousel */}
          <HeroCarousel />

          {/* Hero Foreground Content */}
          <div className="relative z-10 mx-auto max-w-[1920px] px-6 sm:px-10 lg:px-12">
            <div className="max-w-[760px] text-white">
              {/* Prominent Language Switcher */}
              <div className="mb-6">
                <LanguageSwitcher variant="prominent" />
              </div>

              {/* Wordmark with Devanagari */}
              <div className="flex items-baseline gap-4">
                <h1 className="font-display type-hero font-semibold text-white tracking-tight leading-none">
                  {t('landing.title', 'NIGRANI')}
                </h1>
                <span className="font-devanagari text-[36px] font-semibold text-[#F4B860]">
                  {t('common.appHindi', 'निगरानी')}
                </span>
              </div>

              {/* 4px Saffron Rule (lighter saffron #F4B860 on dark ground) */}
              <div className="mt-3 h-1 w-28 bg-[#F4B860]" aria-hidden="true" />

              {/* Slogan / Subheading */}
              <h2 className="mt-6 font-display type-hero-sub font-semibold text-white leading-snug">
                {t('landing.slogan', 'National Project Monitoring System')}
              </h2>

              {/* Attribution Line */}
              <p className="mt-3 type-attrib text-[#D6E2EC]">
                {t('landing.attribution', 'Ministry of Statistics and Programme Implementation · Government of India')}
              </p>

              {/* Real Lookup Bar — three separated controls (Part A1) */}
              <form onSubmit={handleSearch} className="mt-8" style={{ maxWidth: 'min(880px, 100%)' }}>
                <div className="flex flex-col sm:flex-row" style={{ gap: '12px' }}>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t('landing.searchPlaceholder', 'Search by Case ID, Work ID, District, or MP…')}
                    aria-label={t('common.search', 'Search')}
                    className="flex-1 rounded bg-white text-[#14171A] placeholder-[#6B7280] border border-white/30 focus:outline-none focus-visible:outline-2 focus-visible:outline-white focus-visible:outline-offset-2"
                    style={{ height: '56px', padding: '0 20px', fontSize: '1.05rem', minWidth: '280px', borderRadius: '4px' }}
                  />

                  <select
                    value={searchCategory}
                    onChange={(e) => setSearchCategory(e.target.value)}
                    aria-label={t('landing.searchCategory', 'Search filter category')}
                    className="rounded bg-white text-[#14171A] border border-white/30 font-medium focus:outline-none focus-visible:outline-2 focus-visible:outline-white focus-visible:outline-offset-2"
                    style={{ height: '56px', padding: '0 20px', fontSize: '1.05rem', width: '220px', borderRadius: '4px' }}
                  >
                    <option value="all">{t('landing.allRecords', 'All records')}</option>
                    <option value="works">{t('common.works', 'Works')}</option>
                    <option value="districts">{t('landing.districts', 'Districts')}</option>
                    <option value="agencies">{t('landing.agencies', 'Agencies')}</option>
                    <option value="members">{t('landing.members', 'Members')}</option>
                  </select>

                  <button
                    type="submit"
                    className="shrink-0 rounded text-white font-semibold focus:outline-none focus-visible:outline-2 focus-visible:outline-white focus-visible:outline-offset-2"
                    style={{
                      height: '56px',
                      padding: '0 28px',
                      fontSize: '1.05rem',
                      fontWeight: '600',
                      backgroundColor: '#0B2E4F',
                      borderRadius: '4px',
                      width: '160px',
                      transition: 'background-color 120ms ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#134672')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#0B2E4F')}
                  >
                    {t('landing.searchButton', 'Look up')}
                  </button>
                </div>
              </form>

              {/* Voice Quote — 20px clear above */}
              <p className="font-display text-[20px] italic text-white" style={{ marginTop: '20px' }}>
                &ldquo;{t('landing.evidenceVoice', 'Every flag carries its evidence.')}&rdquo;
              </p>

              {/* Jump to: Chips — independent buttons (Part A2) */}
              <div className="flex flex-wrap items-center" style={{ marginTop: '32px', gap: '16px' }}>
                <span className="font-semibold text-white text-[1.05rem]" style={{ marginRight: '4px' }}>
                  {t('landing.jumpTo', 'Jump to:')}
                </span>
                <Link
                  to="/ministry"
                  className="inline-block rounded text-center font-sans"
                  style={{
                    padding: '14px 26px',
                    fontWeight: '600',
                    fontSize: '1.05rem',
                    backgroundColor: '#FFFFFF',
                    color: '#0B2E4F',
                    border: '1px solid #FFFFFF',
                    borderRadius: '4px',
                    transition: 'background-color 120ms ease, color 120ms ease',
                    minHeight: '44px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#0B2E4F'
                    e.currentTarget.style.color = '#FFFFFF'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#FFFFFF'
                    e.currentTarget.style.color = '#0B2E4F'
                  }}
                >
                  {t('nav.nationalOverview', 'Ministry overview')}
                </Link>
                <Link
                  to="/district"
                  className="inline-block rounded text-center font-sans"
                  style={{
                    padding: '14px 26px',
                    fontWeight: '600',
                    fontSize: '1.05rem',
                    backgroundColor: '#FFFFFF',
                    color: '#0B2E4F',
                    border: '1px solid #FFFFFF',
                    borderRadius: '4px',
                    transition: 'background-color 120ms ease, color 120ms ease',
                    minHeight: '44px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#0B2E4F'
                    e.currentTarget.style.color = '#FFFFFF'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#FFFFFF'
                    e.currentTarget.style.color = '#0B2E4F'
                  }}
                >
                  {t('common.districtQueue', 'District queue')}
                </Link>
                <Link
                  to="/reports/data-gap"
                  className="inline-block rounded text-center font-sans"
                  style={{
                    padding: '14px 26px',
                    fontWeight: '600',
                    fontSize: '1.05rem',
                    backgroundColor: '#FFFFFF',
                    color: '#0B2E4F',
                    border: '1px solid #FFFFFF',
                    borderRadius: '4px',
                    transition: 'background-color 120ms ease, color 120ms ease',
                    minHeight: '44px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#0B2E4F'
                    e.currentTarget.style.color = '#FFFFFF'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#FFFFFF'
                    e.currentTarget.style.color = '#0B2E4F'
                  }}
                >
                  {t('common.dataGapReport', 'Data-gap report')}
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* §2 Metrics Strip with MoSPI Emblem (176px height, Part B6)               */}
        {/* ========================================================================= */}
        <section
          ref={statsRef}
          id="corpus-facts"
          className="bg-portal text-white border-b border-portal-deep"
          style={{ minHeight: '176px', padding: '46px 0 30px' }}
        >
          <div className="mx-auto max-w-[1920px] px-6 sm:px-10 lg:px-12 flex flex-col justify-center h-full">
            {/* Main Flex Row: Left Emblem + Divider + Full Width Metrics */}
            <div className="flex flex-col md:flex-row items-center" style={{ gap: '28px' }}>
              {/* Left: Emblem — 88px per Part B3 */}
              <div className="shrink-0 flex items-center justify-center">
                <img
                  src={mospiEmblem}
                  alt={t('landing.emblemAlt', 'Government of India / MoSPI Emblem')}
                  className="w-auto object-contain rounded"
                  style={{ height: '88px' }}
                />
              </div>

              {/* Vertical divider — 28px gap on each side already handled by parent gap */}
              <div
                className="hidden md:block h-20 w-px shrink-0"
                style={{ backgroundColor: 'rgba(255,255,255,0.22)' }}
                aria-hidden="true"
              />

              {/* Metrics: flex: 1 with space-between spanning remaining width */}
              <div className="flex-1 w-full grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
                <div className="px-2">
                  <p className="num font-display font-semibold text-white" style={{ fontSize: 'clamp(2.0rem, 2.8vw, 3.0rem)', lineHeight: '1.0', whiteSpace: 'nowrap' }}>
                    {num(animatedStats.works, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statWorks', 'works scored')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display font-semibold text-white" style={{ fontSize: 'clamp(2.0rem, 2.8vw, 3.0rem)', lineHeight: '1.0', whiteSpace: 'nowrap' }}>
                    {num(animatedStats.rows, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statRows', 'rows ingested')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display font-semibold text-white" style={{ fontSize: 'clamp(2.0rem, 2.8vw, 3.0rem)', lineHeight: '1.0', whiteSpace: 'nowrap' }}>
                    {num(animatedStats.datasets, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statSets', 'portal sets')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display font-semibold text-white" style={{ fontSize: 'clamp(2.0rem, 2.8vw, 3.0rem)', lineHeight: '1.0', whiteSpace: 'nowrap' }}>
                    {num(animatedStats.agencies, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statAgencies', 'agencies')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display font-semibold text-white" style={{ fontSize: 'clamp(2.0rem, 2.8vw, 3.0rem)', lineHeight: '1.0', whiteSpace: 'nowrap' }}>
                    {num(animatedStats.states, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statStates', 'states & UTs')}</p>
                </div>

                <div className="px-2" style={{ flexBasis: '220px' }}>
                  <p className="num font-display font-semibold text-white" style={{ fontSize: 'clamp(2.0rem, 2.8vw, 3.0rem)', lineHeight: '1.0', whiteSpace: 'nowrap' }}>
                    {formatRupees(CORPUS.sanctionedCrore * 1e7, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statSanctioned', 'sanctioned in sample')}</p>
                </div>
              </div>
            </div>

            {/* Caveat line centered beneath — 20px clear above */}
            <p className="text-center text-[13px] text-[#9FB6C8]" style={{ marginTop: '20px' }}>
              {t('landing.caveat', 'Measured on twelve published exports from the MPLADS national portal. All figures verified by reproducible SHA-256 audit runs.')}
            </p>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* §3 The finding — paper, asymmetric two-column                             */}
        {/* ========================================================================= */}
        <section ref={findingRef} id="the-finding" className="bg-paper py-18 border-b border-rule">
          <div className="mx-auto max-w-[1240px] px-6">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-12 items-center">
              {/* Graphic column (6 cols) */}
              <div className="md:col-span-6 space-y-6 rounded border border-rule bg-paper-sunk/60 p-8 shadow-card">
                <div>
                  <div className="flex justify-between type-body-lg font-medium text-ink mb-1.5">
                    <span>{t('landing.findingRecAmount', 'Recommended amount')}</span>
                    <span className="num font-semibold text-portal">100%</span>
                  </div>
                  <div className="h-6 w-full rounded bg-rule/50 overflow-hidden">
                    <div
                      className="h-full bg-portal transition-all duration-700 ease-out"
                      style={{ width: findingVisible ? '100%' : '0%' }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between type-body-lg font-medium text-ink mb-1.5">
                    <span>{t('landing.findingSancAmount', 'Sanctioned amount')}</span>
                    <span className="num font-semibold text-ink-secondary">100%</span>
                  </div>
                  <div className="h-6 w-full rounded bg-rule/50 overflow-hidden">
                    <div
                      className="h-full bg-rule-strong transition-all duration-700 ease-out delay-150"
                      style={{ width: findingVisible ? '100%' : '0%' }}
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-rule">
                  <p className="font-display text-[38px] text-coral leading-none font-bold">14,831</p>
                  <p className="mt-1 type-body-lg font-medium text-ink">
                    {t('landing.findingCount', 'of 14,831 matched works identical')}
                  </p>
                  <p className="mt-2 text-[14px] text-ink-secondary">
                    {t('landing.findingVariance', 'Every matched work where both numbers are published has zero variance.')}
                  </p>
                </div>
              </div>

              {/* Text column (6 cols) */}
              <div className="md:col-span-6 space-y-4">
                <div>
                  <h2 className="font-display type-section text-navy font-semibold">
                    {t('landing.findingHeading', 'What we found before we built')}
                  </h2>
                  <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
                </div>

                <p className="type-lede text-ink leading-relaxed">
                  {t('landing.findingP1', 'Across every work where both figures are published, the recommended amount and the sanctioned amount are the same number. Not close — identical.')}
                </p>

                <p className="type-body-lg text-ink-secondary leading-relaxed">
                  {t('landing.findingP2', 'The portal publishes no revised estimate, so cost overrun cannot be detected from public MPLADS data at all.')}
                </p>

                <p className="type-body-lg text-ink font-medium leading-relaxed">
                  {t('landing.findingP3', 'MPLADS data is financially flat and temporally rich. The signal is in time and repetition — and that is what NIGRANI reads.')}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* §4 The four authorities — paper-sunk                                      */}
        {/* ========================================================================= */}
        <section id="authorities" className="bg-paper-sunk py-18 border-b border-rule">
          <div className="mx-auto max-w-[1240px] px-6">
            <div>
              <h2 className="font-display type-section text-navy font-semibold">
                {t('landing.authoritiesHeading', 'Built for four authorities')}
              </h2>
              <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
              <p className="mt-3 type-lede text-ink-secondary max-w-[72ch]">
                {t('landing.authoritiesLede', 'Each sees only what their office is responsible for. Scoping is enforced in the database query, not in the interface.')}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4" style={{ marginTop: '24px', gap: '20px' }}>
              {/* Ministry */}
              <div className="group rounded border border-rule bg-paper shadow-card transition-colors duration-120 hover:border-rule-strong hover:bg-portal-tint flex flex-col justify-between" style={{ padding: '22px 26px' }}>
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-portal/10 px-2.5 py-1 text-[13px] font-semibold text-portal uppercase">
                      {t('roles.ministry', 'Ministry')}
                    </span>
                    <span className="text-xs text-ink-muted">{t('landing.scopeUnrestricted', 'Unrestricted')}</span>
                  </div>
                  <h3 className="mt-4 font-display text-[22px] font-semibold text-navy">
                    {t('roles.ministryAnalyst', 'MoSPI Analyst')}
                  </h3>
                  <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                    {t('landing.roleDescMinistry', 'National risk map, state league table, and a reporting-gap report on MoSPI’s own data format.')}
                  </p>
                </div>
                <Link
                  to="/sign-in?role=ministry"
                  className="mt-6 inline-block text-[15px] font-semibold text-portal hover:underline"
                >
                  {t('landing.signInAs', 'Sign in as {{role}}', { role: t('roles.ministry', 'Ministry') })}
                </Link>
              </div>

              {/* State Nodal */}
              <div className="group rounded border border-rule bg-paper shadow-card transition-colors duration-120 hover:border-rule-strong hover:bg-portal-tint flex flex-col justify-between" style={{ padding: '22px 26px' }}>
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-portal/10 px-2.5 py-1 text-[13px] font-semibold text-portal uppercase">
                      {t('roles.stateNodal', 'State Nodal')}
                    </span>
                    <span className="text-xs text-ink-muted">{t('landing.scopeOneState', 'One state')}</span>
                  </div>
                  <h3 className="mt-4 font-display text-[22px] font-semibold text-navy">
                    {t('roles.stateOfficer', 'State Officer')}
                  </h3>
                  <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                    {t('landing.roleDescState', 'District comparison and utilisation trend, so slow districts surface before financial year-end.')}
                  </p>
                </div>
                <Link
                  to="/sign-in?role=state_nodal"
                  className="mt-6 inline-block text-[15px] font-semibold text-portal hover:underline"
                >
                  {t('landing.signInAs', 'Sign in as {{role}}', { role: t('roles.stateNodal', 'State Nodal') })}
                </Link>
              </div>

              {/* District Authority */}
              <div className="group rounded border border-rule bg-paper shadow-card transition-colors duration-120 hover:border-rule-strong hover:bg-portal-tint flex flex-col justify-between" style={{ padding: '22px 26px' }}>
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-portal/10 px-2.5 py-1 text-[13px] font-semibold text-portal uppercase">
                      {t('roles.district', 'District')}
                    </span>
                    <span className="text-xs text-ink-muted">{t('landing.scopeOneDistrict', 'One district')}</span>
                  </div>
                  <h3 className="mt-4 font-display text-[22px] font-semibold text-navy">
                    {t('roles.districtMagistrate', 'District Magistrate')}
                  </h3>
                  <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                    {t('landing.roleDescDistrict', 'A ranked, evidence-ordered queue that replaces rotation-based inspection with evidence triage.')}
                  </p>
                </div>
                <Link
                  to="/sign-in?role=district_authority"
                  className="mt-6 inline-block text-[15px] font-semibold text-portal hover:underline"
                >
                  {t('landing.signInAs', 'Sign in as {{role}}', { role: t('roles.district', 'District') })}
                </Link>
              </div>

              {/* Member of Parliament */}
              <div className="group rounded border border-rule bg-paper shadow-card transition-colors duration-120 hover:border-rule-strong hover:bg-portal-tint flex flex-col justify-between" style={{ padding: '22px 26px' }}>
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-portal/10 px-2.5 py-1 text-[13px] font-semibold text-portal uppercase">
                      {t('roles.member', 'MP')}
                    </span>
                    <span className="text-xs text-ink-muted">{t('landing.scopeOwnWorks', 'Own works')}</span>
                  </div>
                  <h3 className="mt-4 font-display text-[22px] font-semibold text-navy">
                    {t('roles.memberOfParliament', 'Member of Parliament')}
                  </h3>
                  <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                    {t('landing.roleDescMember', 'Own account utilisation and stalled recommendations, in a read-only audit view.')}
                  </p>
                </div>
                <Link
                  to="/sign-in?role=member_of_parliament"
                  className="mt-6 inline-block text-[15px] font-semibold text-portal hover:underline"
                >
                  {t('landing.signInAs', 'Sign in as {{role}}', { role: t('roles.member', 'Member') })}
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* §5 How a case is scored — paper, 2×3 grid                                 */}
        {/* ========================================================================= */}
        <section id="how-it-works" className="bg-paper py-18 border-b border-rule">
          <div className="mx-auto max-w-[1240px] px-6">
            <div>
              <h2 className="font-display type-section text-navy font-semibold">{t('landing.scoringHeading', 'How a case is scored')}</h2>
              <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
            </div>

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">{t('landing.scoreCard1Step', '01 · Fund ladder')}</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  {t('landing.scoreCard1Title', 'Sanctioned → Disbursed → Certified')}
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  {t('landing.scoreCard1Desc', 'The system names which hop the money stalled at, comparing signed variance against measured tolerances.')}
                </p>
              </div>

              <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">{t('landing.scoreCard2Step', '02 · Lifecycle')}</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  {t('landing.scoreCard2Title', 'Recommended → Sanctioned → Paid → Done')}
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  {t('landing.scoreCard2Desc', 'Identifies which administrative or execution stage lost the time, so criticism lands on the responsible desk.')}
                </p>
              </div>

              <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">{t('landing.scoreCard3Step', '03 · Rulebook')}</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  {t('landing.scoreCard3Title', 'An editable threshold matrix')}
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  {t('landing.scoreCard3Desc', 'Ten thresholds in YAML, each carrying the count of works it fires on. The Ministry edits them live with versioning.')}
                </p>
              </div>

              <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">{t('landing.scoreCard4Step', '04 · Coverage')}</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  {t('landing.scoreCard4Title', 'Coverage, stated honestly')}
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  {t('landing.scoreCard4Desc', 'A rule with no reading is reported as not published, never as passed. Mean signal coverage today is 58.47%.')}
                </p>
              </div>

              <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">{t('landing.scoreCard5Step', '05 · Duplicates')}</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  {t('landing.scoreCard5Title', 'Duplicates, cited not accused')}
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  {t('landing.scoreCard5Desc', 'Opens candidate work IDs side by side for manual review. 447 clusters found across agencies.')}
                </p>
              </div>

              <div className="rounded border border-rule bg-paper py-card-y px-card-x shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">{t('landing.scoreCard6Step', '06 · Audit trail')}</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  {t('landing.scoreCard6Title', 'An append-only trail')}
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  {t('landing.scoreCard6Desc', '84,666 hash-chained events. A score re-derives months later against the stored rulebook snapshot in force that day.')}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* §6 The wall — portal, full bleed                                          */}
        {/* ========================================================================= */}
        <section id="the-wall" className="bg-portal py-18 text-white border-b border-portal-deep">
          <div className="mx-auto max-w-[1240px] px-6">
            <div>
              <h2 className="font-display type-section text-white font-semibold">
                {t('landing.wallHeading', 'Four detection tiers, and the wall between them')}
              </h2>
              <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
            </div>

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-8 relative">
              {/* Left tier (Contributing to Score) */}
              <div className="space-y-4 rounded border border-white/20 bg-portal-deep/50 p-6">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <span className="text-[14px] font-bold uppercase tracking-wider text-saffron">
                    {t('landing.wallDeterministic', 'Tiers 1 & 2 · Deterministic scoring')}
                  </span>
                  <span className="rounded bg-coral px-2.5 py-0.5 text-[12px] font-bold uppercase text-white">
                    {t('landing.wallScores', 'Scores')}
                  </span>
                </div>
                <div className="space-y-3 type-body-lg text-[#C9D8E4]">
                  <p>
                    <strong className="text-white">{t('landing.tier1Label', 'Tier 1 — The Rulebook:')}</strong> {t('landing.tier1Desc', '10 domain rules evaluating fund gaps, execution delays, and missing milestones.')}
                  </p>
                  <p>
                    <strong className="text-white">{t('landing.tier2Label', 'Tier 2 — Duplicate Detection:')}</strong>{' '}{t('landing.tier2Desc', 'Syntactic & semantic clustering with cited candidate works.')}
                  </p>
                </div>
              </div>

              {/* Right tier (Badges, zero weight) */}
              <div className="space-y-4 rounded border border-white/20 bg-portal-deep/50 p-6 border-l-4 border-l-coral">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <span className="text-[14px] font-bold uppercase tracking-wider text-[#C9D8E4]">
                    {t('landing.wallStatistical', 'Tiers 3 & 4 · Statistical & Graph')}
                  </span>
                  <span className="rounded bg-white/20 px-2.5 py-0.5 text-[12px] font-bold uppercase text-white">
                    {t('landing.wallBadges', 'Badges, worth zero')}
                  </span>
                </div>
                <div className="space-y-3 type-body-lg text-[#C9D8E4]">
                  <p>
                    <strong className="text-white">{t('landing.tier3Label', 'Tier 3 — Anomaly & Delay:')}</strong> {t('landing.tier3Desc', 'Isolation forest and gradient-boosted delay forecast.')}
                  </p>
                  <p>
                    <strong className="text-white">{t('landing.tier4Label', 'Tier 4 — Graph Centrality:')}</strong> {t('landing.tier4Desc', 'Co-occurrence centrality and vendor concentration (HHI).')}
                  </p>
                </div>
              </div>
            </div>

            {/* Inset formula block */}
            <div className="mt-8 rounded border border-white/15 bg-portal-deep p-6 text-center font-mono text-[16px] text-portal-tint">
              <p className="font-semibold">
                score = Σ w(fired rules) + corroboration bonus, capped at 100
              </p>
              <p className="mt-1 text-white/70">
                anomaly · forecast · centrality → contribute 0
              </p>
            </div>

            <p className="mt-6 type-body-lg text-white/90 leading-relaxed text-center max-w-3xl mx-auto">
              {t('landing.wallIntegrity', 'An automated test walks the import graph and fails the build if the scoring engine ever imports the machine-learning package. The number in the corner cannot come from a model.')}
            </p>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* §7 Live signal — paper, two columns                                       */}
        {/* ========================================================================= */}
        <section id="live-signal" className="bg-paper py-18 border-b border-rule">
          <div className="mx-auto max-w-[1240px] px-6">
            <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
              <div>
                <h2 className="font-display type-section text-navy font-semibold">{t('landing.liveSignalHeading', 'Live signal')}</h2>
                <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
              </div>
              <span className="text-[13px] font-medium uppercase tracking-wider text-ink-muted">
                {t('landing.liveSignalSample', 'Sample from the committed corpus')}
              </span>
            </div>

            <div className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left: High risk cases */}
              <div className="rounded border border-rule bg-paper shadow-card py-card-y px-card-x">
                <h3 className="font-display text-[20px] font-semibold text-navy mb-4">
                  {t('landing.liveSignalHighCases', 'High-risk cases in sample')}
                </h3>
                <ul className="divide-y divide-rule type-body-lg">
                  <li className="py-3 flex items-center justify-between">
                    <div>
                      <span className="font-mono text-[14px] text-portal font-semibold">
                        WS/MP847/2025-2026/160261
                      </span>
                      <span className="block text-[13px] text-ink-secondary">Jalaun · Uttar Pradesh</span>
                    </div>
                    <div className="text-right">
                      <span className="num font-bold text-coral text-[18px]">92</span>
                      <span className="block text-[12px] uppercase text-ink-muted">{t('landing.ruleHitUtilisation', 'Utilisation shortfall')}</span>
                    </div>
                  </li>
                  <li className="py-3 flex items-center justify-between">
                    <div>
                      <span className="font-mono text-[14px] text-portal font-semibold">
                        WS/MP219/2024-2025/110482
                      </span>
                      <span className="block text-[13px] text-ink-secondary">Kanpur Nagar · Uttar Pradesh</span>
                    </div>
                    <div className="text-right">
                      <span className="num font-bold text-coral text-[18px]">88</span>
                      <span className="block text-[12px] uppercase text-ink-muted">{t('landing.ruleHitExecution', 'Execution delay')}</span>
                    </div>
                  </li>
                  <li className="py-3 flex items-center justify-between">
                    <div>
                      <span className="font-mono text-[14px] text-portal font-semibold">
                        WS/MP541/2023-2024/094122
                      </span>
                      <span className="block text-[13px] text-ink-secondary">Patna · Bihar</span>
                    </div>
                    <div className="text-right">
                      <span className="num font-bold text-coral text-[18px]">85</span>
                      <span className="block text-[12px] uppercase text-ink-muted">{t('landing.ruleHitDuplicate', 'Duplicate work')}</span>
                    </div>
                  </li>
                  <li className="py-3 flex items-center justify-between">
                    <div>
                      <span className="font-mono text-[14px] text-portal font-semibold">
                        WS/MP104/2025-2026/184910
                      </span>
                      <span className="block text-[13px] text-ink-secondary">Jaipur · Rajasthan</span>
                    </div>
                    <div className="text-right">
                      <span className="num font-bold text-coral text-[18px]">82</span>
                      <span className="block text-[12px] uppercase text-ink-muted">{t('landing.ruleHitAdminLag', 'Administrative lag')}</span>
                    </div>
                  </li>
                  <li className="py-3 flex items-center justify-between">
                    <div>
                      <span className="font-mono text-[14px] text-portal font-semibold">
                        WS/MP703/2024-2025/142099
                      </span>
                      <span className="block text-[13px] text-ink-secondary">Thane · Maharashtra</span>
                    </div>
                    <div className="text-right">
                      <span className="num font-bold text-coral text-[18px]">79</span>
                      <span className="block text-[12px] uppercase text-ink-muted">{t('landing.ruleHitVendorConc', 'Vendor concentration')}</span>
                    </div>
                  </li>
                </ul>
              </div>

              {/* Right: Reporting gaps */}
              <div className="rounded border border-rule bg-paper shadow-card py-card-y px-card-x">
                <h3 className="font-display text-[20px] font-semibold text-navy mb-4">
                  {t('landing.liveSignalGaps', 'Reporting gaps we found')}
                </h3>
                <div className="space-y-4 type-body-lg">
                  <div className="rounded border border-rule bg-paper-sunk p-4">
                    <div className="flex justify-between items-baseline">
                      <span className="font-semibold text-ink">{t('landing.gap1Title', 'Expenditure linkage missing')}</span>
                      <span className="num text-coral font-bold">+30.44 pp</span>
                    </div>
                    <p className="mt-1 text-ink-secondary text-[14px]">
                      {t('landing.gap1Desc', '70,647 skips across 23,549 works. Linking expenditure increases mean coverage from 58.47% to 88.91%.')}
                    </p>
                  </div>

                  <div className="rounded border border-rule bg-paper-sunk p-4">
                    <div className="flex justify-between items-baseline">
                      <span className="font-semibold text-ink">{t('landing.gap2Title', 'Asset completion evidence')}</span>
                      <span className="num text-coral font-bold">+3.65 pp</span>
                    </div>
                    <p className="mt-1 text-ink-secondary text-[14px]">
                      {t('landing.gap2Desc', '14,104 skips. Unrecorded physical progress certificates stall certification verification.')}
                    </p>
                  </div>

                  <div className="rounded border border-rule bg-paper-sunk p-4">
                    <div className="flex justify-between items-baseline">
                      <span className="font-semibold text-ink">{t('landing.gap3Title', 'Unpublished zero fields')}</span>
                      <span className="num text-ink-secondary font-bold">{t('landing.sevenFields', '7 fields')}</span>
                    </div>
                    <p className="mt-1 text-ink-secondary text-[14px]">
                      {t('landing.gap3Desc', '7 fields published as zero rather than omitting or explaining unmeasured hops.')}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* §8 Documentation directory — paper-sunk, five icon tiles                 */}
        {/* ========================================================================= */}
        <section id="docs" className="bg-paper-sunk py-18 border-b border-rule">
          <div className="mx-auto max-w-[1240px] px-6">
            <div>
              <h2 className="font-display type-section text-navy font-semibold">
                {t('landing.docHeading', 'Documentation & reference')}
              </h2>
              <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
            </div>

            <div className="mt-10 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5" style={{ gap: '20px' }}>
              <Link
                to="/rulebook"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
                style={{ padding: '28px 20px' }}
              >
                <img src={docRulebook} alt="" aria-hidden="true" className="doc-tile__icon" style={{ width: '40px', height: '40px', marginBottom: '14px' }} />
                <span className="font-semibold text-[1.05rem] text-navy group-hover:text-white" style={{ fontWeight: '600' }}>
                  {t('common.rulebook', 'Rulebook')}
                </span>
                <span className="text-[0.9rem] text-ink-secondary group-hover:text-white/80" style={{ marginTop: '6px' }}>
                  {t('landing.docRulebookSub', 'v1.0.0 thresholds')}
                </span>
              </Link>

              <Link
                to="/docs/data-profile"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
                style={{ padding: '28px 20px' }}
              >
                <img src={docDataProfile} alt="" aria-hidden="true" className="doc-tile__icon" style={{ width: '40px', height: '40px', marginBottom: '14px' }} />
                <span className="font-semibold text-[1.05rem] text-navy group-hover:text-white" style={{ fontWeight: '600' }}>
                  {t('landing.docDataProfile', 'Data profile')}
                </span>
                <span className="text-[0.9rem] text-ink-secondary group-hover:text-white/80" style={{ marginTop: '6px' }}>
                  {t('landing.docDataProfileSub', '12 dataset schema')}
                </span>
              </Link>

              <Link
                to="/reports/data-gap"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
                style={{ padding: '28px 20px' }}
              >
                <img src={docDataGap} alt="" aria-hidden="true" className="doc-tile__icon" style={{ width: '40px', height: '40px', marginBottom: '14px' }} />
                <span className="font-semibold text-[1.05rem] text-navy group-hover:text-white" style={{ fontWeight: '600' }}>
                  {t('common.dataGapReport', 'Data-gap report')}
                </span>
                <span className="text-[0.9rem] text-ink-secondary group-hover:text-white/80" style={{ marginTop: '6px' }}>
                  {t('landing.docDataGapSub', 'MoSPI ablation findings')}
                </span>
              </Link>

              <Link
                to="/docs/api-reference"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
                style={{ padding: '28px 20px' }}
              >
                <img src={docApi} alt="" aria-hidden="true" className="doc-tile__icon" style={{ width: '40px', height: '40px', marginBottom: '14px' }} />
                <span className="font-semibold text-[1.05rem] text-navy group-hover:text-white" style={{ fontWeight: '600' }}>
                  {t('landing.docApiRef', 'API reference')}
                </span>
                <span className="text-[0.9rem] text-ink-secondary group-hover:text-white/80" style={{ marginTop: '6px' }}>
                  {t('landing.docApiRefSub', 'Role-scoped endpoints')}
                </span>
              </Link>

              <Link
                to="/docs/audit-trail"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
                style={{ padding: '28px 20px' }}
              >
                <img src={docAudit} alt="" aria-hidden="true" className="doc-tile__icon" style={{ width: '40px', height: '40px', marginBottom: '14px' }} />
                <span className="font-semibold text-[1.05rem] text-navy group-hover:text-white" style={{ fontWeight: '600' }}>
                  {t('common.auditTrail', 'Audit trail')}
                </span>
                <span className="text-[0.9rem] text-ink-secondary group-hover:text-white/80" style={{ marginTop: '6px' }}>
                  {t('landing.docAuditSub', '84,666 chained logs')}
                </span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Standards strip and Footer */}
      <Footer />
    </div>
  )
}
