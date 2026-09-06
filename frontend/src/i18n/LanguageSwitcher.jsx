import { useState, useRef, useEffect } from 'react'
import { useLanguage } from './useLanguage.js'

export default function LanguageSwitcher({ variant = 'compact', className = '' }) {
  const { lang, setLang, languages, t } = useLanguage()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef(null)

  // Handle click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false)
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [dropdownOpen])

  // Handle Escape key
  function handleKeyDown(e) {
    if (e.key === 'Escape') {
      setDropdownOpen(false)
    }
  }

  if (variant === 'prominent') {
    return (
      <div
        role="group"
        aria-label={t('utility.language', 'Language')}
        className={`inline-flex flex-wrap items-center gap-2 ${className}`}
      >
        {languages.map((item) => {
          const isActive = lang === item.code
          return (
            <button
              key={item.code}
              type="button"
              onClick={() => setLang(item.code)}
              aria-current={isActive ? 'true' : undefined}
              className={`rounded px-4 py-1.5 text-[15px] font-semibold transition-all duration-150 border ${
                isActive
                  ? 'bg-paper text-portal border-paper shadow-sm'
                  : 'bg-portal-deep/60 text-white border-white/30 hover:bg-portal-deep hover:border-white'
              }`}
            >
              {item.nativeName}
            </button>
          )
        })}
      </div>
    )
  }

  // Default: compact dropdown variant
  const currentItem = languages.find((l) => l.code === lang) || languages[0]

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef} onKeyDown={handleKeyDown}>
      <button
        type="button"
        onClick={() => setDropdownOpen((prev) => !prev)}
        aria-expanded={dropdownOpen}
        aria-haspopup="listbox"
        aria-label={`${t('utility.language', 'Language')}: ${currentItem.nativeName}`}
        className="inline-flex items-center gap-1.5 px-2 py-1 text-[13px] font-medium text-white/90 hover:text-white transition-colors"
      >
        <span className="font-semibold text-[14px]">अ / A</span>
        <span className="hidden sm:inline">{currentItem.nativeName}</span>
        <span className="text-[10px] opacity-75" aria-hidden="true">▼</span>
      </button>

      {dropdownOpen && (
        <ul
          role="listbox"
          aria-label={t('utility.language', 'Language')}
          className="absolute right-0 top-full z-50 mt-1 min-w-[130px] rounded border border-rule bg-paper py-1 shadow-card"
        >
          {languages.map((item) => {
            const isActive = lang === item.code
            return (
              <li key={item.code} role="option" aria-selected={isActive}>
                <button
                  type="button"
                  onClick={() => {
                    setLang(item.code)
                    setDropdownOpen(false)
                  }}
                  className={`w-full px-3 py-1.5 text-left text-[14px] transition-colors ${
                    isActive
                      ? 'bg-portal-tint font-bold text-navy'
                      : 'text-ink hover:bg-portal-tint/50'
                  }`}
                >
                  {item.nativeName}
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
