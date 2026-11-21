import { LANGUAGES, useI18n, useLanguageStore } from "@/i18n"
import { cn } from "@/lib/utils"

// Three square tiles. On a turquoise field (header) the chosen language is a white tile;
// on light surfaces (staff area) it is a turquoise tile.
export function LanguageSwitcher({ tone = "light" }: { tone?: "light" | "field" }) {
  const { t, language } = useI18n()
  const setLanguage = useLanguageStore((state) => state.setLanguage)
  const onField = tone === "field"

  return (
    <div
      role="group"
      aria-label={t("language.switch")}
      className={cn("flex items-stretch text-[0.8125rem] font-semibold", onField ? "border border-field-foreground/50" : "border border-input")}
    >
      {LANGUAGES.map((option) => {
        const active = language === option.code
        return (
          <button
            key={option.code}
            type="button"
            lang={option.code}
            aria-label={option.label}
            aria-pressed={active}
            onClick={() => setLanguage(option.code)}
            className={cn(
              "min-h-9 min-w-10 px-2 transition-colors duration-200",
              onField
                ? active
                  ? "bg-field-foreground text-field"
                  : "text-field-muted hover:bg-field-deep hover:text-field-foreground"
                : active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground",
            )}
          >
            {option.short}
          </button>
        )
      })}
    </div>
  )
}
