import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import hi from './locales/hi.json'
import mr from './locales/mr.json'
import gu from './locales/gu.json'
import { makePseudo } from './pseudo.js'

export const STORAGE_KEY = 'nigrani.lang'
export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', nativeName: 'English' },
  { code: 'hi', label: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'mr', label: 'Marathi', nativeName: 'मराठी' },
  { code: 'gu', label: 'Gujarati', nativeName: 'ગુજરાતી' },
  ...(import.meta.env.DEV ? [{ code: 'zz', label: 'Pseudo (Audit)', nativeName: '»Pseudo«' }] : []),
]

export const SUPPORTED_CODES = SUPPORTED_LANGUAGES.map((l) => l.code)

const stored = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null
const initialLang = SUPPORTED_CODES.includes(stored) ? stored : 'en'

// Sync <html lang="..."> attribute
if (typeof document !== 'undefined') {
  document.documentElement.lang = initialLang
}

const resources = {
  en: { translation: en },
  hi: { translation: hi },
  mr: { translation: mr },
  gu: { translation: gu },
}

if (import.meta.env.DEV) {
  resources.zz = { translation: makePseudo(en) }
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: initialLang,
    fallbackLng: 'en',
    returnEmptyString: false,
    interpolation: {
      escapeValue: false, // React already escapes values
    },
  })

i18n.on('languageChanged', (lng) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, lng)
    document.documentElement.lang = lng
  }
})

export default i18n
