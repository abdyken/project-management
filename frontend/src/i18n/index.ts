import { useMemo } from "react"
import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import type { DegreeLevel, Program } from "@/api/types"
import { MESSAGES, type MessageKey } from "@/i18n/messages"

export type Language = "kk" | "ru" | "en"

export const LANGUAGES: { code: Language; label: string; short: string }[] = [
  { code: "kk", label: "Қазақша", short: "Қаз" },
  { code: "ru", label: "Русский", short: "Рус" },
  { code: "en", label: "English", short: "Eng" },
]

const LOCALES: Record<Language, string> = { kk: "kk-KZ", ru: "ru-RU", en: "en-US" }

type Params = Record<string, string | number>
type PluralKey<K> = K extends `${infer Base}.other` ? Base : never

export function isLanguage(value: unknown): value is Language {
  return LANGUAGES.some((option) => option.code === value)
}

function detectLanguage(): Language {
  const preferred = typeof navigator === "undefined" ? [] : (navigator.languages ?? [navigator.language])
  for (const tag of preferred.map((value) => value.toLowerCase())) {
    if (tag.startsWith("kk")) return "kk"
    if (tag.startsWith("ru")) return "ru"
    if (tag.startsWith("en")) return "en"
  }
  return "en"
}

type LanguageState = {
  language: Language
  setLanguage: (language: Language) => void
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      language: detectLanguage(),
      setLanguage: (language) => set({ language }),
    }),
    {
      name: "sdu-admissions-language",
      storage: createJSONStorage(() => localStorage),
      merge: (persisted, current) => {
        const language = (persisted as Partial<LanguageState> | undefined)?.language
        return isLanguage(language) ? { ...current, language } : current
      },
    },
  ),
)

export function translate(language: Language, key: MessageKey, params?: Params) {
  const template = MESSAGES[language][key] || MESSAGES.en[key]
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match))
}

const KAZAKH_MONTHS = [
  "қаңтар",
  "ақпан",
  "наурыз",
  "сәуір",
  "мамыр",
  "маусым",
  "шілде",
  "тамыз",
  "қыркүйек",
  "қазан",
  "қараша",
  "желтоқсан",
]

function makeI18n(language: Language) {
  const locale = LOCALES[language]
  const plural = new Intl.PluralRules(locale)
  const numbers = new Intl.NumberFormat(language === "kk" ? LOCALES.ru : locale)
  const dates =
    language === "kk"
      ? { format: (date: Date) => `${date.getUTCDate()} ${KAZAKH_MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()} ж.` }
      : new Intl.DateTimeFormat(locale, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })
  const t = (key: MessageKey, params?: Params) => translate(language, key, params)
  const notPublished = t("format.notPublished")

  return {
    language,
    t,
    tn: (key: PluralKey<MessageKey>, count: number, params?: Params) => {
      const form = plural.select(count)
      const candidate = `${key}.${form}` as MessageKey
      const chosen = candidate in MESSAGES.en ? candidate : (`${key}.other` as MessageKey)
      return t(chosen, { count: numbers.format(count), ...params })
    },
    deadline: (value: string | null | undefined) => {
      if (!value) return notPublished
      const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
      if (!match) return value
      return dates.format(new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]))))
    },
    tuitionKzt: (kzt: number | null) =>
      kzt === null ? notPublished : t("format.tuitionKzt", { amount: numbers.format(kzt) }),
    tuitionUsd: (usd: number | null) =>
      usd === null ? notPublished : t("format.tuitionUsd", { amount: numbers.format(usd) }),
    degree: (level: DegreeLevel) => t(`degree.${level}`),
    programTitle: (program: Pick<Program, "title" | "title_ru" | "title_kk">) =>
      (language === "kk" ? program.title_kk : language === "ru" ? program.title_ru : null) || program.title,
    languages: (value: string | null) =>
      value === null
        ? notPublished
        : value
            .split(",")
            .map((name) => name.trim())
            .map((name) => {
              const key = `languageName.${name}` as MessageKey
              return key in MESSAGES.en ? t(key) : name
            })
            .join(", "),
  }
}

export type I18n = ReturnType<typeof makeI18n>

export function useI18n(): I18n {
  const language = useLanguageStore((state) => state.language)
  return useMemo(() => makeI18n(language), [language])
}
