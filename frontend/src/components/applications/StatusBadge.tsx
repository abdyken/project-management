import type { ApplicationStatus } from "@/api/applications"
import { useApplicationsT } from "@/applications/i18n"
import { cn } from "@/lib/utils"

const STATUS_STYLE: Record<ApplicationStatus, string> = {
  draft: "bg-muted text-muted-foreground",
  submitted: "bg-primary/10 text-primary",
  in_review: "bg-primary/10 text-primary",
  needs_changes: "bg-gold/20 text-foreground",
  accepted: "bg-primary text-primary-foreground",
  rejected: "bg-destructive/10 text-destructive",
}

// The label is text, so the status never depends on colour alone.
export function StatusBadge({ status, label }: { status: ApplicationStatus; label?: string }) {
  const t = useApplicationsT()
  return (
    <span className={cn("inline-block rounded px-2 py-0.5 text-xs font-medium", STATUS_STYLE[status])}>
      {label ?? t(`status.${status}`)}
    </span>
  )
}
