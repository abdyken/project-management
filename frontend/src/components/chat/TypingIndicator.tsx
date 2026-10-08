import { useI18n } from "@/i18n"

export function TypingIndicator() {
  const { t } = useI18n()
  return (
    <div className="flex justify-start">
      <div className="border border-border bg-card px-3.5 py-3">
        <p className="sr-only">{t("chat.preparing")}</p>
        <div className="flex gap-1">
          <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
          <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
          <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground" />
        </div>
      </div>
    </div>
  )
}
