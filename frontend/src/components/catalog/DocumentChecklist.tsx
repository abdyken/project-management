import type { ChecklistResponse, DocumentRequirement } from "@/api/types"

function requirementNotes(item: DocumentRequirement) {
  return [item.format === "original" ? "Original" : "Copy", item.translation && "Translation", item.notarisation && "Notarised"]
    .filter(Boolean)
    .join(" · ")
}

export function DocumentChecklist({ checklist }: { checklist: ChecklistResponse }) {
  if (checklist.warning) {
    return (
      <div role="status" className="border border-gold/50 bg-gold/10 p-5">
        <p className="text-sm">{checklist.warning}</p>
        {checklist.contact ? <p className="mt-3 text-sm text-muted-foreground">{checklist.contact}</p> : null}
      </div>
    )
  }

  return (
    <>
      <ol className="divide-y divide-border border-y border-border sm:hidden">
        {checklist.items.map((item) => (
          <li key={item.name} className="py-4">
            <p className="text-sm font-medium">{item.name}</p>
            <p className="mt-1 text-xs text-muted-foreground">{requirementNotes(item)}</p>
            <p className="mt-1 text-xs text-muted-foreground">Deadline: {item.deadline}</p>
          </li>
        ))}
      </ol>
      <div className="hidden border border-border sm:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-secondary/70 text-[11px] tracking-[0.12em] text-muted-foreground uppercase">
            <tr>
              <th scope="col" className="px-4 py-3 font-medium">Document</th>
              <th scope="col" className="px-4 py-3 font-medium">Format</th>
              <th scope="col" className="px-4 py-3 font-medium">Translation</th>
              <th scope="col" className="px-4 py-3 font-medium">Notary</th>
              <th scope="col" className="px-4 py-3 font-medium">Deadline</th>
            </tr>
          </thead>
          <tbody>
            {checklist.items.map((item) => (
              <tr key={item.name} className="border-t border-border">
                <td className="px-4 py-3">{item.name}</td>
                <td className="px-4 py-3 capitalize">{item.format}</td>
                <td className="px-4 py-3">{item.translation ? "Required" : "—"}</td>
                <td className="px-4 py-3">{item.notarisation ? "Required" : "—"}</td>
                <td className="px-4 py-3 text-muted-foreground">{item.deadline}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
