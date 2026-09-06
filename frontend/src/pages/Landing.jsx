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

              {/* Real Lookup Bar (White fill, dark text inside) */}
              <form onSubmit={handleSearch} className="mt-8">
                <div className="flex flex-col sm:flex-row shadow-card rounded border border-white/30 bg-paper overflow-hidden">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t('landing.searchPlaceholder', 'Search a work ID, district, agency or member…')}
                    aria-label={t('common.search', 'Search')}
                    className="flex-1 px-4 py-3.5 text-body text-ink placeholder-ink-muted focus:outline-none"
                  />

                  <select
                    value={searchCategory}
                    onChange={(e) => setSearchCategory(e.target.value)}
                    aria-label="Search filter category"
                    className="border-t sm:border-t-0 sm:border-l border-rule bg-paper-sunk px-3 py-3.5 text-[15px] font-medium text-ink focus:outline-none"
                  >
                    <option value="all">All records</option>
                    <option value="works">Works</option>
                    <option value="districts">Districts</option>
                    <option value="agencies">Agencies</option>
                    <option value="members">Members</option>
                  </select>

                  <button
                    type="submit"
                    className="bg-portal px-7 py-3.5 text-[16px] font-semibold text-white transition-colors hover:bg-portal-deep focus:outline-none shrink-0"
                  >
                    {t('landing.searchButton', 'Look up')}
                  </button>
                </div>
              </form>

              {/* Voice Quote */}
              <p className="mt-5 font-display text-[20px] italic text-[#FFFFFF]">
                &ldquo;{t('landing.evidenceVoice', 'Every flag carries its evidence.')}&rdquo;
              </p>

              {/* Jump to: Chips in india.gov.in style (Solid white, 4px corners, hover invert) */}
              <div className="mt-8 flex flex-wrap items-center gap-3 type-body-lg text-[#D6E2EC]">
                <span className="font-semibold text-white mr-1">{t('landing.jumpTo', 'Jump to:')}</span>
                <Link to="/ministry" className="hero-chip-btn">
                  {t('roles.ministry', 'Ministry')} {t('common.overview', 'overview')}
                </Link>
                <Link to="/district" className="hero-chip-btn">
                  {t('common.district', 'District')} {t('common.queue', 'queue')}
                </Link>
                <Link to="/reports/data-gap" className="hero-chip-btn">
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
          className="bg-portal text-white border-b border-portal-deep py-4"
          style={{ minHeight: '176px' }}
        >
          <div className="mx-auto max-w-[1920px] px-6 sm:px-10 lg:px-12 flex flex-col justify-center h-full">
            {/* Main Flex Row: Left Emblem + Divider + Full Width Metrics */}
            <div className="flex flex-col md:flex-row items-center gap-6">
              {/* Left: Emblem */}
              <div className="shrink-0 flex items-center justify-center">
                <img
                  src={mospiEmblem}
                  alt={t('landing.emblemAlt', 'Government of India / MoSPI Emblem')}
                  className="h-[96px] w-auto object-contain rounded"
                />
              </div>

              {/* Vertical divider */}
              <div
                className="hidden md:block h-20 w-px bg-white/22 shrink-0"
                style={{ backgroundColor: 'rgba(255,255,255,0.22)' }}
                aria-hidden="true"
              />

              {/* Metrics: flex: 1 with space-between spanning remaining width */}
              <div className="flex-1 w-full grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
                <div className="px-2">
                  <p className="num font-display type-stat font-semibold text-white">
                    {num(animatedStats.works, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statWorks', 'works scored')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display type-stat font-semibold text-white">
                    {num(animatedStats.rows, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statRows', 'rows ingested')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display type-stat font-semibold text-white">
                    {num(animatedStats.datasets, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statSets', 'portal sets')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display type-stat font-semibold text-white">
                    {num(animatedStats.agencies, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statAgencies', 'agencies')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display type-stat font-semibold text-white">
                    {num(animatedStats.states, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statStates', 'states & UTs')}</p>
                </div>

                <div className="px-2">
                  <p className="num font-display type-stat font-semibold text-white">
                    {formatRupees(CORPUS.sanctionedCrore * 1e7, lang)}
                  </p>
                  <p className="mt-1 type-stat-lbl text-[#C9D8E4]">{t('landing.statSanctioned', 'sanctioned in sample')}</p>
                </div>
              </div>
            </div>

            {/* Caveat line centered beneath */}
            <p className="mt-4 text-center text-[13px] text-[#9FB6C8]">
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
                    <span>{t('common.recommended', 'Recommended amount')}</span>
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
                    <span>{t('common.sanctioned', 'Sanctioned amount')}</span>
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
                    of 14,831 matched works identical
                  </p>
                  <p className="mt-2 text-[14px] text-ink-secondary">
                    Every matched work where both numbers are published has zero variance.
                  </p>
                </div>
              </div>

              {/* Text column (6 cols) */}
              <div className="md:col-span-6 space-y-4">
                <div>
                  <h2 className="font-display type-section text-navy font-semibold">
                    What we found before we built
                  </h2>
                  <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
                </div>

                <p className="type-lede text-ink leading-relaxed">
                  Across every work where both figures are published, the recommended amount and the
                  sanctioned amount are the same number. Not close — identical.
                </p>

                <p className="type-body-lg text-ink-secondary leading-relaxed">
                  The portal publishes no revised estimate, so cost overrun cannot be detected from
                  public MPLADS data at all.
                </p>

                <p className="type-body-lg text-ink font-medium leading-relaxed">
                  MPLADS data is financially flat and temporally rich. The signal is in time and
                  repetition — and that is what NIGRANI reads.
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
                Built for four authorities
              </h2>
              <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
              <p className="mt-3 type-lede text-ink-secondary max-w-[72ch]">
                Each sees only what their office is responsible for. Scoping is enforced in the
                database query, not in the interface.
              </p>
            </div>

            <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Ministry */}
              <div className="group rounded border border-rule bg-paper p-6 shadow-card transition-colors duration-120 hover:border-rule-strong hover:bg-portal-tint flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-portal/10 px-2.5 py-1 text-[13px] font-semibold text-portal uppercase">
                      {t('roles.ministry', 'Ministry')}
                    </span>
                    <span className="text-xs text-ink-muted">Unrestricted</span>
                  </div>
                  <h3 className="mt-4 font-display text-[22px] font-semibold text-navy">
                    MoSPI Analyst
                  </h3>
                  <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                    National risk map, state league table, and a reporting-gap report on MoSPI&rsquo;s
                    own data format.
                  </p>
                </div>
                <Link
                  to="/sign-in?role=ministry"
                  className="mt-6 inline-block text-[15px] font-semibold text-portal hover:underline"
                >
                  {t('common.signIn', 'Sign in')} as {t('roles.ministry', 'Ministry')}
                </Link>
              </div>

              {/* State Nodal */}
              <div className="group rounded border border-rule bg-paper p-6 shadow-card transition-colors duration-120 hover:border-rule-strong hover:bg-portal-tint flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-portal/10 px-2.5 py-1 text-[13px] font-semibold text-portal uppercase">
                      {t('roles.stateNodal', 'State Nodal')}
                    </span>
                    <span className="text-xs text-ink-muted">One state</span>
                  </div>
                  <h3 className="mt-4 font-display text-[22px] font-semibold text-navy">
                    State Officer
                  </h3>
                  <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                    District comparison and utilisation trend, so slow districts surface before
                    financial year-end.
                  </p>
                </div>
                <Link
                  to="/sign-in?role=state_nodal"
                  className="mt-6 inline-block text-[15px] font-semibold text-portal hover:underline"
                >
                  {t('common.signIn', 'Sign in')} as {t('roles.stateNodal', 'State Nodal')}
                </Link>
              </div>

              {/* District Authority */}
              <div className="group rounded border border-rule bg-paper p-6 shadow-card transition-colors duration-120 hover:border-rule-strong hover:bg-portal-tint flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-portal/10 px-2.5 py-1 text-[13px] font-semibold text-portal uppercase">
                      {t('roles.district', 'District')}
                    </span>
                    <span className="text-xs text-ink-muted">One district</span>
                  </div>
                  <h3 className="mt-4 font-display text-[22px] font-semibold text-navy">
                    District Magistrate
                  </h3>
                  <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                    A ranked, evidence-ordered queue that replaces rotation-based inspection with
                    evidence triage.
                  </p>
                </div>
                <Link
                  to="/sign-in?role=district_authority"
                  className="mt-6 inline-block text-[15px] font-semibold text-portal hover:underline"
                >
                  {t('common.signIn', 'Sign in')} as {t('roles.district', 'District')}
                </Link>
              </div>

              {/* Member of Parliament */}
              <div className="group rounded border border-rule bg-paper p-6 shadow-card transition-colors duration-120 hover:border-rule-strong hover:bg-portal-tint flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-portal/10 px-2.5 py-1 text-[13px] font-semibold text-portal uppercase">
                      {t('roles.member', 'MP')}
                    </span>
                    <span className="text-xs text-ink-muted">Own works</span>
                  </div>
                  <h3 className="mt-4 font-display text-[22px] font-semibold text-navy">
                    Member of Parliament
                  </h3>
                  <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                    Own account utilisation and stalled recommendations, in a read-only audit view.
                  </p>
                </div>
                <Link
                  to="/sign-in?role=member_of_parliament"
                  className="mt-6 inline-block text-[15px] font-semibold text-portal hover:underline"
                >
                  {t('common.signIn', 'Sign in')} as {t('roles.member', 'Member')}
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
              <h2 className="font-display type-section text-navy font-semibold">How a case is scored</h2>
              <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
            </div>

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="rounded border border-rule bg-paper p-6 shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">01 · Fund ladder</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  Sanctioned → Disbursed → Certified
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  The system names which hop the money stalled at, comparing signed variance
                  against measured tolerances.
                </p>
              </div>

              <div className="rounded border border-rule bg-paper p-6 shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">02 · Lifecycle</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  Recommended → Sanctioned → Paid → Done
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  Identifies which administrative or execution stage lost the time, so criticism
                  lands on the responsible desk.
                </p>
              </div>

              <div className="rounded border border-rule bg-paper p-6 shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">03 · Rulebook</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  An editable threshold matrix
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  Ten thresholds in YAML, each carrying the count of works it fires on. The
                  Ministry edits them live with versioning.
                </p>
              </div>

              <div className="rounded border border-rule bg-paper p-6 shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">04 · Coverage</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  Coverage, stated honestly
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  A rule with no reading is reported as not published, never as passed. Mean signal
                  coverage today is 58.47%.
                </p>
              </div>

              <div className="rounded border border-rule bg-paper p-6 shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">05 · Duplicates</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  Duplicates, cited not accused
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  Opens candidate work IDs side by side for manual review. 447 clusters found across
                  agencies.
                </p>
              </div>

              <div className="rounded border border-rule bg-paper p-6 shadow-card">
                <span className="text-[13px] font-bold uppercase text-portal">06 · Audit trail</span>
                <h3 className="mt-2 font-display text-[20px] font-semibold text-navy">
                  An append-only trail
                </h3>
                <p className="mt-2 type-body-lg text-ink-secondary leading-relaxed">
                  84,666 hash-chained events. A score re-derives months later against the stored
                  rulebook snapshot in force that day.
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
                Four detection tiers, and the wall between them
              </h2>
              <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
            </div>

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-8 relative">
              {/* Left tier (Contributing to Score) */}
              <div className="space-y-4 rounded border border-white/20 bg-portal-deep/50 p-6">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <span className="text-[14px] font-bold uppercase tracking-wider text-saffron">
                    Tiers 1 & 2 · Deterministic scoring
                  </span>
                  <span className="rounded bg-coral px-2.5 py-0.5 text-[12px] font-bold uppercase text-white">
                    Scores
                  </span>
                </div>
                <div className="space-y-3 type-body-lg text-[#C9D8E4]">
                  <p>
                    <strong className="text-white">Tier 1 — The Rulebook:</strong> 10 domain rules
                    evaluating fund gaps, execution delays, and missing milestones.
                  </p>
                  <p>
                    <strong className="text-white">Tier 2 — Duplicate Detection:</strong>{' '}
                    Syntactic & semantic clustering with cited candidate works.
                  </p>
                </div>
              </div>

              {/* Right tier (Badges, zero weight) */}
              <div className="space-y-4 rounded border border-white/20 bg-portal-deep/50 p-6 border-l-4 border-l-coral">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <span className="text-[14px] font-bold uppercase tracking-wider text-[#C9D8E4]">
                    Tiers 3 & 4 · Statistical & Graph
                  </span>
                  <span className="rounded bg-white/20 px-2.5 py-0.5 text-[12px] font-bold uppercase text-white">
                    Badges, worth zero
                  </span>
                </div>
                <div className="space-y-3 type-body-lg text-[#C9D8E4]">
                  <p>
                    <strong className="text-white">Tier 3 — Anomaly & Delay:</strong> Isolation
                    forest and gradient-boosted delay forecast.
                  </p>
                  <p>
                    <strong className="text-white">Tier 4 — Graph Centrality:</strong> Co-occurrence
                    centrality and vendor concentration (HHI).
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
              An automated test walks the import graph and fails the build if the scoring engine
              ever imports the machine-learning package. The number in the corner cannot come from
              a model.
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
                <h2 className="font-display type-section text-navy font-semibold">Live signal</h2>
                <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
              </div>
              <span className="text-[13px] font-medium uppercase tracking-wider text-ink-muted">
                Sample from the committed corpus
              </span>
            </div>

            <div className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left: High risk cases */}
              <div className="rounded border border-rule bg-paper shadow-card p-6">
                <h3 className="font-display text-[20px] font-semibold text-navy mb-4">
                  High-risk cases in sample
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
                      <span className="block text-[12px] uppercase text-ink-muted">Utilisation shortfall</span>
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
                      <span className="block text-[12px] uppercase text-ink-muted">Execution delay</span>
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
                      <span className="block text-[12px] uppercase text-ink-muted">Duplicate work</span>
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
                      <span className="block text-[12px] uppercase text-ink-muted">Administrative lag</span>
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
                      <span className="block text-[12px] uppercase text-ink-muted">Vendor concentration</span>
                    </div>
                  </li>
                </ul>
              </div>

              {/* Right: Reporting gaps */}
              <div className="rounded border border-rule bg-paper shadow-card p-6">
                <h3 className="font-display text-[20px] font-semibold text-navy mb-4">
                  Reporting gaps we found
                </h3>
                <div className="space-y-4 type-body-lg">
                  <div className="rounded border border-rule bg-paper-sunk p-4">
                    <div className="flex justify-between items-baseline">
                      <span className="font-semibold text-ink">Expenditure linkage missing</span>
                      <span className="num text-coral font-bold">+30.44 pp</span>
                    </div>
                    <p className="mt-1 text-ink-secondary text-[14px]">
                      70,647 skips across 23,549 works. Linking expenditure increases mean coverage
                      from 58.47% to 88.91%.
                    </p>
                  </div>

                  <div className="rounded border border-rule bg-paper-sunk p-4">
                    <div className="flex justify-between items-baseline">
                      <span className="font-semibold text-ink">Asset completion evidence</span>
                      <span className="num text-coral font-bold">+3.65 pp</span>
                    </div>
                    <p className="mt-1 text-ink-secondary text-[14px]">
                      14,104 skips. Unrecorded physical progress certificates stall certification
                      verification.
                    </p>
                  </div>

                  <div className="rounded border border-rule bg-paper-sunk p-4">
                    <div className="flex justify-between items-baseline">
                      <span className="font-semibold text-ink">Unpublished zero fields</span>
                      <span className="num text-ink-secondary font-bold">7 fields</span>
                    </div>
                    <p className="mt-1 text-ink-secondary text-[14px]">
                      7 fields published as zero rather than omitting or explaining unmeasured hops.
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
                Documentation & reference
              </h2>
              <div className="mt-1 h-[3px] w-20 bg-saffron" aria-hidden="true" />
            </div>

            <div className="mt-10 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
              <Link
                to="/rulebook"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper p-6 text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
              >
                <span className="text-2xl mb-2 group-hover:text-white">📜</span>
                <span className="font-semibold text-[16px] text-navy group-hover:text-white">
                  {t('common.rulebook', 'Rulebook')}
                </span>
                <span className="mt-1 text-[13px] text-ink-secondary group-hover:text-white/80">
                  v1.0.0 thresholds
                </span>
              </Link>

              <Link
                to="/docs/data-profile"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper p-6 text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
              >
                <span className="text-2xl mb-2 group-hover:text-white">📊</span>
                <span className="font-semibold text-[16px] text-navy group-hover:text-white">
                  Data profile
                </span>
                <span className="mt-1 text-[13px] text-ink-secondary group-hover:text-white/80">
                  12 dataset schema
                </span>
              </Link>

              <Link
                to="/reports/data-gap"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper p-6 text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
              >
                <span className="text-2xl mb-2 group-hover:text-white">📋</span>
                <span className="font-semibold text-[16px] text-navy group-hover:text-white">
                  {t('common.dataGapReport', 'Data-gap report')}
                </span>
                <span className="mt-1 text-[13px] text-ink-secondary group-hover:text-white/80">
                  MoSPI ablation findings
                </span>
              </Link>

              <Link
                to="/docs/api-reference"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper p-6 text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
              >
                <span className="text-2xl mb-2 group-hover:text-white">⚡</span>
                <span className="font-semibold text-[16px] text-navy group-hover:text-white">
                  API reference
                </span>
                <span className="mt-1 text-[13px] text-ink-secondary group-hover:text-white/80">
                  Role-scoped endpoints
                </span>
              </Link>

              <Link
                to="/docs/audit-trail"
                className="group flex flex-col items-center justify-center rounded border border-rule bg-paper p-6 text-center shadow-card transition-colors duration-120 hover:border-portal hover:bg-portal hover:text-white"
              >
                <span className="text-2xl mb-2 group-hover:text-white">🔒</span>
                <span className="font-semibold text-[16px] text-navy group-hover:text-white">
                  {t('common.auditTrail', 'Audit trail')}
                </span>
                <span className="mt-1 text-[13px] text-ink-secondary group-hover:text-white/80">
                  84,666 chained logs
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
