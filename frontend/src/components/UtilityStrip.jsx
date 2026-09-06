import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '../i18n/LanguageSwitcher.jsx'

const SIZES = ['sm', 'md', 'lg']
const SIZE_LABELS = { sm: 'A−', md: 'A', lg: 'A+' }
const SIZE_ARIA = { sm: 'Small text', md: 'Standard text', lg: 'Large text' }

export default function UtilityStrip() {
  const { t } = useTranslation()

  const [textSize, setTextSize] = useState(() => {
    try {
      return localStorage.getItem('nigrani_text_size') || 'md'
    } catch {
      return 'md'
    }
  })

  const [highContrast, setHighContrast] = useState(() => {
    try {
      return localStorage.getItem('nigrani_contrast') === 'high'
    } catch {
      return false
    }
  })

  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('text-size-sm', 'text-size-md', 'text-size-lg')
    root.classList.add(`text-size-${textSize}`)
    try {
      localStorage.setItem('nigrani_text_size', textSize)
    } catch {}
  }, [textSize])

  useEffect(() => {
    const root = document.documentElement
    if (highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }
    try {
      localStorage.setItem('nigrani_contrast', highContrast ? 'high' : 'normal')
    } catch {}
  }, [highContrast])

  function cycleTextSize() {
    const nextIndex = (SIZES.indexOf(textSize) + 1) % SIZES.length
    setTextSize(SIZES[nextIndex])
  }

  function toggleContrast() {
    setHighContrast((curr) => !curr)
  }

  return (
    <div className="relative z-50 flex h-9 items-center justify-between bg-portal-deep px-4 sm:px-6 text-[12px] text-[#C9D8E4]">
      {/* Skip to main link — visually hidden until focused */}
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-1 focus:left-4 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-1 focus:text-ink focus:font-semibold focus:shadow-card"
      >
        {t('utility.skipToContent', 'Skip to main content')}
      </a>

      {/* Left: Ministry identity */}
      <div className="flex items-center gap-2 truncate">
        <span className="font-normal truncate">
          {t('utility.officialPortal', 'Government of India · Ministry of Statistics and Programme Implementation')}
        </span>
      </div>

      {/* Right: Accessibility affordances & Language Switcher */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          type="button"
          onClick={cycleTextSize}
          aria-label={`Current text size: ${SIZE_ARIA[textSize]}. Click to change.`}
          title={`Text size: ${SIZE_ARIA[textSize]}`}
          className="rounded border border-[#C9D8E4]/30 px-2 py-0.5 font-medium text-[#C9D8E4] transition-colors hover:border-[#C9D8E4] hover:bg-[#C9D8E4]/10"
        >
          {SIZE_LABELS[textSize]}
        </button>

        <button
          type="button"
          onClick={toggleContrast}
          aria-label={`High contrast: ${highContrast ? 'On' : 'Off'}. Click to toggle.`}
          aria-pressed={highContrast}
          title="Toggle high contrast"
          className={`rounded border px-2 py-0.5 font-medium transition-colors ${
            highContrast
              ? 'border-white bg-white text-portal-deep'
              : 'border-[#C9D8E4]/30 text-[#C9D8E4] hover:border-[#C9D8E4] hover:bg-[#C9D8E4]/10'
          }`}
        >
          {t('utility.contrast', 'Contrast')}
        </button>

        <span className="h-4 w-px bg-[#C9D8E4]/30" aria-hidden="true" />

        {/* Compact Language Switcher dropdown */}
        <LanguageSwitcher variant="compact" />
      </div>
    </div>
  )
}
