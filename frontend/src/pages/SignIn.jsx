import { useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { LogoMark } from '../components/Logo.jsx'
import UtilityStrip from '../components/UtilityStrip.jsx'
import Footer from '../components/Footer.jsx'
import { AUTH_LOADING, AUTH_SIGNED_IN, useAuth } from '../auth.jsx'
import { ROLE_HOME } from '../roles.js'
import { useLanguage } from '../i18n/useLanguage.js'

import signinLoop from '../assets/video/signin-loop.mp4'
import signinPoster from '../assets/video/signin-poster.jpg'

export default function SignIn() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { lang } = useLanguage()
  const { status, user, signIn, endedReason } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Reduced motion: show poster instead of autoplay
  const [reducedMotion, setReducedMotion] = useState(false)
  const [videoPlaying, setVideoPlaying] = useState(false)
  const videoRef = useRef(null)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
      setReducedMotion(mq.matches)
      const handler = (e) => setReducedMotion(e.matches)
      mq.addEventListener('change', handler)
      return () => mq.removeEventListener('change', handler)
    }
  }, [])

  // Somebody already signed in who navigates back to the door goes to their
  // own landing screen instead of being asked to sign in twice.
  if (status === AUTH_SIGNED_IN && user) {
    return <Navigate to={ROLE_HOME[user.role] ?? '/'} replace />
  }

  async function submit(event) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const identity = await signIn(email.trim(), password)
      navigate(ROLE_HOME[identity.role] ?? '/', { replace: true })
    } catch (failure) {
      setError(failure.message)
    } finally {
      setSubmitting(false)
    }
  }

  function handlePlayVideo() {
    if (videoRef.current) {
      videoRef.current.play()
      setVideoPlaying(true)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-paper">
      {/* E5: Utility strip for language switching before login */}
      <UtilityStrip />

      {/* E1: Split-screen layout */}
      <div
        className="flex-1 grid grid-cols-1 lg:grid-cols-[58%_42%]"
        style={{ minHeight: 'calc(100vh - 36px)' }}
      >
        {/* Left: Video panel (240px top band below 1024px, 58% column on desktop) */}
        <div
          className="relative overflow-hidden h-[240px] lg:h-auto lg:min-h-[400px]"
        >
          {/* E2: Video at full clarity */}
          {reducedMotion && !videoPlaying ? (
            <>
              <img
                src={signinPoster}
                alt=""
                aria-hidden="true"
                className="absolute inset-0 w-full h-full object-cover"
              />
              <button
                type="button"
                onClick={handlePlayVideo}
                className="absolute bottom-8 right-8 z-20 rounded bg-white/90 px-4 py-2 text-[14px] font-semibold text-portal shadow-card transition-colors hover:bg-white"
                aria-label={t('signin.playVideo', 'Play background video')}
              >
                ▶ {t('signin.playLabel', 'Play')}
              </button>
            </>
          ) : null}

          <video
            ref={videoRef}
            className="absolute inset-0 w-full h-full object-cover"
            src={signinLoop}
            poster={signinPoster}
            autoPlay={!reducedMotion}
            muted
            loop
            playsInline
            preload="auto"
            aria-hidden="true"
            tabIndex={-1}
            style={{
              opacity: 1,
              filter: 'none',
              display: reducedMotion && !videoPlaying ? 'none' : 'block',
            }}
          />

          {/* E3: Wordmark block over the video — lower-left with localized scrim */}
          <div
            className="absolute z-10 hidden lg:block"
            style={{
              left: '48px',
              bottom: '64px',
              maxWidth: '560px',
              padding: '28px 32px',
              background: 'rgba(7, 31, 54, 0.55)',
              borderRadius: '4px',
            }}
          >
            {/* NIGRANI + निगरानी */}
            <div className="flex items-baseline gap-3">
              <span
                className="font-display font-semibold text-white"
                style={{ fontSize: 'clamp(2.4rem, 3.4vw, 3.4rem)' }}
              >
                {t('landing.title', 'NIGRANI')}
              </span>
              <span
                className="font-devanagari font-semibold"
                style={{
                  fontSize: 'clamp(2.4rem, 3.4vw, 3.4rem)',
                  color: '#F4B860',
                }}
              >
                {t('common.appHindi', 'निगरानी')}
              </span>
            </div>

            {/* Saffron rule */}
            <div
              aria-hidden="true"
              style={{
                marginTop: '16px',
                height: '4px',
                width: '96px',
                backgroundColor: '#F4B860',
              }}
            />

            {/* Subtitle */}
            <p
              className="font-display font-semibold text-white"
              style={{
                marginTop: '18px',
                fontSize: 'clamp(1.3rem, 1.9vw, 1.8rem)',
              }}
            >
              {t('landing.slogan', 'National Project Monitoring System')}
            </p>

            {/* Attribution */}
            <p
              className="font-sans"
              style={{
                marginTop: '8px',
                fontSize: '1rem',
                color: '#D6E2EC',
                fontWeight: '400',
              }}
            >
              {t('landing.attribution', 'Ministry of Statistics and Programme Implementation · Government of India')}
            </p>
          </div>
        </div>

        {/* Right: Form panel */}
        <div
          className="flex items-center justify-center bg-paper"
          style={{ padding: '40px 24px' }}
        >
          {/* E4: Form card */}
          <div
            className="w-full"
            style={{
              maxWidth: '440px',
              padding: '44px 40px',
              border: '1px solid #D5DEE6',
              borderRadius: '4px',
              backgroundColor: '#FFFFFF',
            }}
          >
            {/* 1. NIGRANI mark */}
            <div className="flex justify-center">
              <LogoMark size={56} className="text-navy" />
            </div>

            {/* 2. NIGRANI title */}
            <h1
              className="text-center font-display text-navy"
              style={{ marginTop: '20px', fontSize: '2.1rem', fontWeight: '600' }}
            >
              {t('landing.title', 'NIGRANI')}
            </h1>

            {/* 3. Subtitle */}
            <p
              className="text-center font-sans text-ink-secondary"
              style={{ marginTop: '8px', fontSize: '1.05rem', fontWeight: '500' }}
            >
              {t('landing.slogan', 'National Project Monitoring System')}
            </p>

            {/* 4. Divider */}
            <div
              aria-hidden="true"
              style={{
                marginTop: '28px',
                marginBottom: '28px',
                height: '1px',
                backgroundColor: '#D5DEE6',
              }}
            />

            {/* Error state */}
            {endedReason && !error ? (
              <div
                className="rounded"
                style={{
                  marginBottom: '20px',
                  padding: '12px 16px',
                  border: '1px solid #C8952B',
                  borderLeftWidth: '4px',
                  backgroundColor: '#FFF9F0',
                }}
              >
                <p className="text-[14px] text-ink">{endedReason}</p>
              </div>
            ) : null}

            {error ? (
              <div
                className="rounded"
                role="alert"
                style={{
                  marginBottom: '20px',
                  padding: '12px 16px',
                  border: '1px solid #D4573D',
                  backgroundColor: '#FFF5F3',
                }}
              >
                <p className="text-[14px] font-medium text-coral">{t('signin.couldNotSignIn', 'Could not sign in')}</p>
                <p className="mt-1 text-[14px] text-ink-secondary">{error}</p>
              </div>
            ) : null}

            <form onSubmit={submit}>
              {/* 5. Email field */}
              <div>
                <label
                  htmlFor="email"
                  className="block font-sans"
                  style={{ fontSize: '0.85rem', color: '#94989E', marginBottom: '6px' }}
                >
                  {t('signin.emailLabel', 'Email address')}
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded border border-rule bg-white text-ink focus:border-portal focus:outline-none"
                  style={{ height: '52px', padding: '0 16px', fontSize: '1rem' }}
                />
              </div>

              {/* 6. Password field */}
              <div style={{ marginTop: '20px' }}>
                <label
                  htmlFor="password"
                  className="block font-sans"
                  style={{ fontSize: '0.85rem', color: '#94989E', marginBottom: '6px' }}
                >
                  {t('signin.passwordLabel', 'Password')}
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="w-full rounded border border-rule bg-white text-ink focus:border-portal focus:outline-none"
                    style={{ height: '52px', paddingLeft: '16px', paddingRight: '48px', fontSize: '1rem' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    aria-label={showPassword ? t('signin.hidePassword', 'Hide password') : t('signin.showPassword', 'Show password')}
                    aria-pressed={showPassword}
                    className="absolute top-1/2 -translate-y-1/2 flex items-center justify-center text-ink-secondary hover:text-ink focus:text-ink transition-colors rounded"
                    style={{ width: '44px', height: '44px', right: '4px' }}
                  >
                    {showPassword ? (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
                        <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
                        <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
                        <line x1="2" y1="2" x2="22" y2="22" />
                      </svg>
                    ) : (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* 7. Sign in button */}
              <button
                type="submit"
                disabled={submitting || status === AUTH_LOADING}
                className="w-full rounded text-white font-semibold disabled:cursor-not-allowed disabled:opacity-50"
                style={{
                  marginTop: '28px',
                  height: '52px',
                  backgroundColor: '#0B2E4F',
                  fontSize: '1.05rem',
                  fontWeight: '600',
                  transition: 'background-color 120ms ease',
                }}
                onMouseEnter={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.backgroundColor = '#134672' }}
                onMouseLeave={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.backgroundColor = '#0B2E4F' }}
              >
                {submitting ? t('signin.signingIn', 'Signing in…') : t('common.signIn', 'Sign in')}
              </button>
            </form>

            {/* 8. Ministry attribution */}
            <p
              className="text-center font-sans text-ink-secondary"
              style={{
                marginTop: '24px',
                fontSize: '0.9rem',
                lineHeight: '1.5',
              }}
            >
              {t('landing.attribution', 'Ministry of Statistics and Programme Implementation · Government of India')}
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer />
    </div>
  )
}
