import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"

type ConnectionErrorProps = {
  message: string
  retrying: boolean
  onRetry: () => void
}

export function ConnectionError({ message, retrying, onRetry }: ConnectionErrorProps) {
  const { t } = useI18n()
  return (
    <div role="alert" className="border border-border bg-card p-6">
      <p className="text-2xl font-semibold tracking-tight">{t("error.connection")}</p>
      <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      <Button className="mt-5" onClick={onRetry} disabled={retrying}>
        {retrying ? t("error.tryingAgain") : t("error.tryAgain")}
      </Button>
    </div>
  )
}
