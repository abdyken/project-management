import type { ChecklistResponse, DocumentRequirement } from "@/api/types"
import { useI18n, type I18n } from "@/i18n"

function requirementNotes(item: DocumentRequirement, t: I18n["t"]) {
  return [
    item.format === "original" ? t("checklist.original") : t("checklist.copy"),
    item.translation && t("checklist.translation"),
    item.notarisation && t("checklist.notarised"),
  ]
    .filter(Boolean)
    .join(" · ")
}

export function DocumentChecklist({ checklist }: { checklist: ChecklistResponse }) {
  const { t } = useI18n()
  const note = t("checklist.publishedInEnglish")

  if (checklist.warning) {
    return (
      <div role="status" className="border border-gold/50 bg-gold/10 p-5">
        <p className="text-sm">{t("checklist.missing")}</p>
        {checklist.contact ? <p className="mt-3 text-sm text-muted-foreground">{checklist.contact}</p> : null}
      </div>
    )
  }

  return (
    <>
      {note ? <p className="mb-4 text-xs text-muted-foreground">{note}</p> : null}
      <ol className="divide-y divide-border border-y border-border sm:hidden">
        {checklist.items.map((item) => (
          <li key={item.name} className="py-4">
            <p className="text-sm font-medium" lang="en">
              {item.name}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">{requirementNotes(item, t)}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {t("checklist.deadline")}: <span lang="en">{item.deadline}</span>
            </p>
          </li>
        ))}
      </ol>
      <div className="hidden border border-border sm:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-secondary/70 text-[11px] tracking-[0.12em] text-muted-foreground uppercase">
            <tr>
              <th scope="col" className="px-4 py-3 font-medium">{t("checklist.document")}</th>
              <th scope="col" className="px-4 py-3 font-medium">{t("checklist.format")}</th>
              <th scope="col" className="px-4 py-3 font-medium">{t("checklist.translationColumn")}</th>
              <th scope="col" className="px-4 py-3 font-medium">{t("checklist.notary")}</th>
              <th scope="col" className="px-4 py-3 font-medium">{t("checklist.deadline")}</th>
            </tr>
          </thead>
          <tbody>
            {checklist.items.map((item) => (
              <tr key={item.name} className="border-t border-border">
                <td className="px-4 py-3" lang="en">
                  {item.name}
                </td>
                <td className="px-4 py-3">{item.format === "original" ? t("checklist.original") : t("checklist.copy")}</td>
                <td className="px-4 py-3">{item.translation ? t("checklist.required") : "—"}</td>
                <td className="px-4 py-3">{item.notarisation ? t("checklist.required") : "—"}</td>
                <td className="px-4 py-3 text-muted-foreground" lang="en">
                  {item.deadline}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
