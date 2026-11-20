import { Check } from "lucide-react"
import type { ApplicationStatus } from "@/api/applications"
import { useApplicationsT } from "@/applications/i18n"
import { cn } from "@/lib/utils"

// ADR 0002: draft → submitted → in review (or changes requested) → accepted / not accepted.
// The current step carries the status label; the status text appears once on the page.
const CURRENT_STEP: Record<ApplicationStatus, number> = {
  draft: 0,
  submitted: 1,
  in_review: 2,
  needs_changes: 2,
  accepted: 3,
  rejected: 3,
}

export function ApplicationStepper({ status }: { status: ApplicationStatus }) {
  const t = useApplicationsT()
  const current = CURRENT_STEP[status]
  // Only the current step names the status; the others use stage names that never repeat a
  // status word, so "Submitted" (for example) is on the page only once it is true.
  const stages = [t("step.form"), t("step.sent"), t("step.review"), t("step.decision")]
  const labels = stages.map((stage, index) => (index === current ? t(`status.${status}`) : stage))
  const currentTile =
    status === "needs_changes" ? "bg-ochre text-ink" : status === "rejected" ? "bg-terracotta text-white" : "bg-primary text-primary-foreground"

  return (
    <ol aria-label={t("progress")} className="grid grid-cols-4 gap-1">
      {labels.map((label, index) => {
        const done = index < current
        const active = index === current
        return (
          <li key={index} aria-current={active ? "step" : undefined} className="min-w-0">
            <span
              className={cn(
                "flex h-10 items-center justify-center font-display text-lg font-bold",
                active ? currentTile : done ? "bg-field-deep text-field-foreground" : "border-2 border-dashed border-input text-muted-foreground",
              )}
            >
              {done ? <Check className="size-5" aria-hidden="true" /> : <span className="tabular">{index + 1}</span>}
            </span>
            <span className={cn("mt-2 block text-sm leading-tight", active ? "font-semibold text-foreground" : "text-muted-foreground")}>
              {label}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
