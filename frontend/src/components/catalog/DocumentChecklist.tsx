import type { ChecklistResponse } from "@/api/types"
import { useI18n } from "@/i18n"
import { requirementNotes } from "@/lib/checklist"

// The deadline most rows share, stated once above the list; rows show their own only when it differs.
function sharedDeadline(deadlines: string[]): string | null {
  const counts = new Map<string, number>()
  for (const value of deadlines) counts.set(value, (counts.get(value) ?? 0) + 1)
  let best: string | null = null
  for (const [value, count] of counts) if (best === null || count > (counts.get(best) ?? 0)) best = value
  return best !== null && (counts.get(best) ?? 0) >= 2 ? best : null
}

export function DocumentChecklist({ checklist }: { checklist: ChecklistResponse }) {
  const { t } = useI18n()
  const note = t("checklist.publishedInEnglish")

  if (checklist.warning) {
    return (
      <div role="status" className="border border-primary bg-field-tint p-5">
        <p>{t("checklist.missing")}</p>
        {checklist.contact ? <p className="mt-3 text-muted-foreground">{checklist.contact}</p> : null}
      </div>
    )
  }

  const items = checklist.items
  const shared = sharedDeadline(items.map((item) => item.deadline))
  // Columns that would read "—" on every row are left out.
  const showTranslation = items.some((item) => item.translation)
  const showNotary = items.some((item) => item.notarisation)
  const ownDeadline = (deadline: string) => (shared !== null && deadline === shared ? null : deadline)
  // When every row has the shared deadline, the column would repeat it; it is left out.
  const showDeadline = items.some((item) => ownDeadline(item.deadline) !== null)

  return (
    <>
      {note ? <p className="mb-4 text-sm text-muted-foreground">{note}</p> : null}
      {shared ? (
        <p className="mb-5 bg-secondary p-4">
          <span className="font-semibold">{t("checklist.sharedDeadline")}</span> <span lang="en">{shared}</span>
        </p>
      ) : null}
      <ol className="divide-y divide-border border-y-2 border-ink sm:hidden">
        {items.map((item) => {
          const own = ownDeadline(item.deadline)
          return (
            <li key={item.name} className="py-4">
              <p className="font-semibold" lang="en">
                {item.name}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{requirementNotes(item, t)}</p>
              {own ? (
                <p className="mt-1 text-sm text-muted-foreground">
                  {t("checklist.deadline")}: <span lang="en">{own}</span>
                </p>
              ) : null}
            </li>
          )
        })}
      </ol>
      <div className="hidden border-t-2 border-ink sm:block">
        <table className="w-full text-left text-[0.9375rem]">
          <thead className="border-b border-ink text-sm text-muted-foreground">
            <tr>
              <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.document")}</th>
              <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.format")}</th>
              {showTranslation ? <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.translationColumn")}</th> : null}
              {showNotary ? <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.notary")}</th> : null}
              {showDeadline ? <th scope="col" className="px-3 py-3 font-semibold">{t("checklist.deadline")}</th> : null}
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const own = ownDeadline(item.deadline)
              return (
                <tr key={item.name} className="border-b border-border align-top">
                  <td className="px-3 py-4 font-medium" lang="en">
                    {item.name}
                  </td>
                  <td className="px-3 py-4">{item.format === "original" ? t("checklist.original") : t("checklist.copy")}</td>
                  {showTranslation ? <td className="px-3 py-4">{item.translation ? t("checklist.required") : "—"}</td> : null}
                  {showNotary ? <td className="px-3 py-4">{item.notarisation ? t("checklist.required") : "—"}</td> : null}
                  {showDeadline ? (
                    <td className="px-3 py-4 text-muted-foreground">
                      {own ? <span lang="en">{own}</span> : t("checklist.sameDeadline")}
                    </td>
                  ) : null}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </>
  )
}
