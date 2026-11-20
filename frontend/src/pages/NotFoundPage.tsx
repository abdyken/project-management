import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"

export function NotFoundPage() {
  const { t } = useI18n()
  return (
    <div className="mx-auto max-w-5xl px-4 pt-12 pb-20 sm:px-6 sm:pt-16 sm:pb-24">
      <h1 className="text-[clamp(2.25rem,4vw,3.5rem)] leading-[1.08] font-medium">{t("notFound.title")}</h1>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-muted-foreground">{t("notFound.text")}</p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Button asChild>
          <Link to="/">{t("notFound.home")}</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/programs">{t("home.browse")}</Link>
        </Button>
      </div>
    </div>
  )
}
