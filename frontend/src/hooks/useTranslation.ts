import { translations, type Lang, type TranslationKey } from '../i18n/translations'

function detectLang(): Lang {
  const lang = navigator.language.toLowerCase()
  if (lang.startsWith('de')) return 'de'
  return 'en'
}

const lang = detectLang()

export function useTranslation() {
  const t = (key: TranslationKey): string => translations[lang][key]
  return { t, lang }
}
