import { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { SUPPORTED_LANGUAGES, SUPPORTED_CODES } from './index.js'

export function useLanguage() {
  const { i18n, t } = useTranslation()
  const lang = i18n.language && SUPPORTED_CODES.includes(i18n.language) ? i18n.language : 'en'

  const setLang = useCallback(
    (code) => {
      if (SUPPORTED_CODES.includes(code)) {
        i18n.changeLanguage(code)
      }
    },
    [i18n],
  )

  return {
    lang,
    setLang,
    languages: SUPPORTED_LANGUAGES,
    t,
  }
}
