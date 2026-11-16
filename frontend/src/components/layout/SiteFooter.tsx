import { useI18n } from "@/i18n"
import { ADMISSIONS_PHONE, ADMISSIONS_WEBSITE } from "@/lib/constants"

export function SiteFooter() {
  const { t, language } = useI18n()

  return (
    <footer className="mt-auto border-t border-border/80">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 pt-10 pb-24 text-sm text-muted-foreground sm:flex-row sm:justify-between sm:px-6 sm:pb-10">
        <div>
          <p className="text-base font-semibold text-foreground">{t("contact.name")}</p>
          <p className="mt-2 max-w-xs">{t("contact.address")}</p>
          <p className="mt-1">
            <a className="hover:text-foreground" href={`tel:${ADMISSIONS_PHONE.replace(/\s/g, "")}`}>{ADMISSIONS_PHONE}</a>
          </p>
        </div>
        <div className="space-y-2">
          <a className="block hover:text-foreground" href={ADMISSIONS_WEBSITE[language]} target="_blank" rel="noreferrer">
            {t("footer.officialAdmissions")}
          </a>
          <a className="block hover:text-foreground" href="https://admissions.sdu.edu.kz" target="_blank" rel="noreferrer">
            {t("footer.applicationPortal")}
          </a>
        </div>
      </div>
    </footer>
  )
}
