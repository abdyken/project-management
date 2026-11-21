import type { FaqStatus } from "@/api/staff"
import { Badge } from "@/components/ui/badge"
import { useStaffT } from "@/staff/i18n"

export function StatusBadge({ status }: { status: FaqStatus }) {
  const t = useStaffT()
  return (
    <Badge tone={status === "published" ? "field" : status === "draft" ? "ochre" : "neutral"} className={status === "retired" ? "line-through" : undefined}>
      {t(`status.${status}`)}
    </Badge>
  )
}
