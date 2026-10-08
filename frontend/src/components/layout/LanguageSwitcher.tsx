import { LANGUAGES, useI18n, useLanguageStore } from "@/i18n"
import { cn } from "@/lib/utils"

export function LanguageSwitcher() {
  const { t, language } = useI18n()
  const setLanguage = useLanguageStore((state) => state.setLanguage)

  return (
    <div role="group" aria-label={t("language.switch")} className="flex items-center border border-border text-xs">
      {LANGUAGES.map((option) => (
        <button
          key={option.code}
          type="button"
          lang={option.code}
          aria-label={option.label}
          aria-pressed={language === option.code}
          onClick={() => setLanguage(option.code)}
          className={cn(
            "px-2 py-1 transition-colors",
            language === option.code ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {option.short}
        </button>
      ))}
    </div>
  )
}
