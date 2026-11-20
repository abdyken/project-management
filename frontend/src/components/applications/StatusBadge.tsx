import type { ApplicationStatus } from "@/api/applications"
import { useApplicationsT } from "@/applications/i18n"
import { Badge, type BadgeTone } from "@/components/ui/badge"

const STATUS_TONE: Record<ApplicationStatus, BadgeTone> = {
  draft: "neutral",
  submitted: "field",
  in_review: "glacier",
  needs_changes: "ochre",
  accepted: "solid",
  rejected: "terracotta",
}

// The label is text, so the status never depends on colour alone.
export function StatusBadge({ status, label }: { status: ApplicationStatus; label?: string }) {
  const t = useApplicationsT()
  return <Badge tone={STATUS_TONE[status]}>{label ?? t(`status.${status}`)}</Badge>
}
