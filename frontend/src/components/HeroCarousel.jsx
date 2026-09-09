import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'

import hero1 from '../assets/hero/hero-1.jpeg'
import hero2 from '../assets/hero/hero-2.jpeg'
import hero3 from '../assets/hero/hero-3.jpeg'
import hero4 from '../assets/hero/hero-4.jpeg'
import hero5 from '../assets/hero/hero-5.jpeg'

const HERO_IMAGES = [hero1, hero2, hero3, hero4, hero5]
const INTERVAL_MS = 3000

export default function HeroCarousel({ isPausedExternal = false }) {
  const { t } = useTranslation()
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isHovered, setIsHovered] = useState(false)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)
  const timerRef = useRef(null)

  // Check reduced-motion preference
  useEffect(() => {
    if (typeof window === 'undefined') return
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handler = (e) => setPrefersReducedMotion(e.matches)
    mediaQuery.addEventListener?.('change', handler)
    return () => mediaQuery.removeEventListener?.('change', handler)
  }, [])

  // Auto-advance interval
  useEffect(() => {
    if (prefersReducedMotion || isHovered || isPausedExternal) {
      if (timerRef.current) clearInterval(timerRef.current)
      return
    }

    timerRef.current = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % HERO_IMAGES.length)
    }, INTERVAL_MS)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [prefersReducedMotion, isHovered, isPausedExternal])

  return (
    <div
      className="absolute inset-0 overflow-hidden pointer-events-auto"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsHovered(true)}
      onBlur={() => setIsHovered(false)}
    >
      {/* 1. Sliding filmstrip */}
      <div
        aria-hidden="true"
        className="flex h-full w-full"
        style={{
          transform: `translateX(-${currentIndex * 100}%)`,
          transition: prefersReducedMotion ? 'none' : 'transform 900ms cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        {HERO_IMAGES.map((src, i) => (
          <div key={i} className="relative h-full w-full shrink-0 flex-none">
            <img
              src={src}
              alt=""
              loading={i === 0 ? 'eager' : 'lazy'}
              className="h-full w-full object-cover"
            />
          </div>
        ))}
      </div>

      {/* 2. Flat Solid Scrim: rgba(7, 31, 54, 0.68) */}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-portal-deep/68"
        style={{ backgroundColor: 'rgba(7, 31, 54, 0.68)' }}
      />

      {/* 3. Dot Indicator Controls (Bottom-Right) */}
      <div
        role="group"
        aria-label={t('landing.carouselNav', 'Carousel navigation')}
        className="absolute bottom-6 right-6 z-20 flex items-center gap-2 rounded bg-portal-deep/60 px-3 py-1.5 backdrop-blur-xs border border-white/20"
      >
        {HERO_IMAGES.map((_, i) => {
          const isActive = currentIndex === i
          return (
            <button
              key={i}
              type="button"
              onClick={() => setCurrentIndex(i)}
              aria-label={t('landing.slideNum', { num: i + 1, defaultValue: `Slide ${i + 1}` })}
              aria-current={isActive ? 'true' : undefined}
              className={`h-2.5 rounded transition-all duration-200 ${
                isActive ? 'w-6 bg-paper' : 'w-2.5 bg-white/40 hover:bg-white/80'
              }`}
            />
          )
        })}
      </div>
    </div>
  )
}
