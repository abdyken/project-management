import type { ChecklistResponse } from "@/api/types"

export function DocumentChecklist({ checklist }: { checklist: ChecklistResponse }) {
  if (checklist.warning) {
    return (
      <div className="border border-gold/50 bg-gold/10 p-5">
        <p className="text-sm">{checklist.warning}</p>
        {checklist.contact ? (
          <p className="mt-3 text-sm text-muted-foreground">
            {checklist.contact.name}
            <br />
            {checklist.contact.address}
            <br />
            {checklist.contact.phone}
          </p>
        ) : null}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto border border-border">
      <table className="w-full min-w-[520px] text-left text-sm">
        <thead className="bg-secondary/70 text-[11px] tracking-[0.12em] text-muted-foreground uppercase">
          <tr>
            <th className="px-4 py-3 font-medium">Document</th>
            <th className="px-4 py-3 font-medium">Format</th>
            <th className="px-4 py-3 font-medium">Translation</th>
            <th className="px-4 py-3 font-medium">Notary</th>
            <th className="px-4 py-3 font-medium">Deadline</th>
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
  )
}
