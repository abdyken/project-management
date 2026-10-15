import type { FaqStatus } from "@/api/staff"
import { cn } from "@/lib/utils"
import { useStaffT } from "@/staff/i18n"

export function StatusBadge({ status }: { status: FaqStatus }) {
  const t = useStaffT()
  return (
    <span
      className={cn(
        "inline-block rounded px-1.5 py-0.5 text-xs",
        status === "published" && "bg-primary/10 text-primary",
        status === "draft" && "bg-gold/20 text-foreground",
        status === "retired" && "bg-muted text-muted-foreground line-through",
      )}
    >
      {t(`status.${status}`)}
    </span>
  )
}
