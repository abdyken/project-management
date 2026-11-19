import type { Language } from "@/i18n"

const UNITS: Record<Language, [string, string]> = { en: ["KB", "MB"], ru: ["КБ", "МБ"], kk: ["КБ", "МБ"] }

// File sizes for uploaded documents: KB below 1 MB, otherwise MB with one decimal, in the page language.
export function fileSize(bytes: number, language: Language) {
  const [kb, mb] = UNITS[language]
  const format = new Intl.NumberFormat(language === "kk" ? "kk-KZ" : language, { maximumFractionDigits: 1 })
  return bytes < 1024 * 1024
    ? `${format.format(Math.max(1, Math.round(bytes / 1024)))} ${kb}`
    : `${format.format(Math.round((bytes / (1024 * 1024)) * 10) / 10)} ${mb}`
}
