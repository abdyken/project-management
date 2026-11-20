import type { ChecklistResponse } from "@/api/types"
import { useI18n } from "@/i18n"
import { requirementNotes } from "@/lib/checklist"

export function DocumentChecklist({ checklist }: { checklist: ChecklistResponse }) {
  const { t } = useI18n()
  const note = t("checklist.publishedInEnglish")

  if (checklist.warning) {
    return (
      <div role="status" className="border-2 border-ochre bg-ochre/10 p-5">
        <p className="text-sm">{t("checklist.missing")}</p>
        {checklist.contact ? <p className="mt-3 text-sm text-muted-foreground">{checklist.contact}</p> : null}
      </div>
    )
  }

  return (
    <>
      {note ? <p className="mb-4 text-sm text-muted-foreground">{note}</p> : null}
      <ol className="divide-y divide-border border-y-2 border-ink sm:hidden">
        {checklist.items.map((item) => (
          <li key={item.name} className="py-4">
            <p className="font-semibold" lang="en">
              {item.name}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{requirementNotes(item, t)}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {t("checklist.deadline")}: <span lang="en">{item.deadline}</span>
            </p>
          </li>
        ))}
      </ol>
      <div className="hidden border-t-2 border-ink sm:block">
        <table className="w-full text-left text-[0.9375rem]">
          <thead className="border-b border-ink text-sm text-muted-foreground">
            <tr>
              <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.document")}</th>
              <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.format")}</th>
              <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.translationColumn")}</th>
              <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.notary")}</th>
              <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.deadline")}</th>
            </tr>
          </thead>
          <tbody>
            {checklist.items.map((item) => (
              <tr key={item.name} className="border-b border-border align-top">
                <td className="px-3 py-4 font-medium" lang="en">
                  {item.name}
                </td>
                <td className="px-3 py-4">{item.format === "original" ? t("checklist.original") : t("checklist.copy")}</td>
                <td className="px-3 py-4">{item.translation ? t("checklist.required") : "—"}</td>
                <td className="px-3 py-4">{item.notarisation ? t("checklist.required") : "—"}</td>
                <td className="px-3 py-4 text-muted-foreground" lang="en">
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
