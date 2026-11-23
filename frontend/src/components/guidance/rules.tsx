import type { Condition, Evidence } from "@/api/guidance"
import { useGuidanceT } from "@/guidance/i18n"

// Shared by the guidance tools and the program page's entry requirements.
export function EvidenceView({
  evidence,
}: {
  evidence: Evidence | null | undefined
}) {
  const t = useGuidanceT()
  if (!evidence) return null
  return (
    <details className="mt-2 text-xs text-muted-foreground">
      <summary className="cursor-pointer">
        {t("evidence")} · {evidence.academic_year} · {t(evidence.status)}
      </summary>
      <a
        className="my-2 inline-block break-all underline"
        href={evidence.url}
        target="_blank"
        rel="noreferrer"
      >
        {t("sources")}
      </a>
      <blockquote className="whitespace-pre-wrap break-words border-l-2 border-border pl-3">
        {evidence.quote}
      </blockquote>
      <p className="mt-2">
        {t("checked")}: {evidence.checked_on}
      </p>
    </details>
  )
}

export function ConditionText({ condition }: { condition: Condition }) {
  const t = useGuidanceT()
  return (
    <span>
      {t(condition.metric)}{" "}
      {condition.minimum != null
        ? `≥ ${condition.minimum}`
        : `= ${typeof condition.equals === "boolean" ? t(condition.equals ? "yes" : "no") : t.code(String(condition.equals))}`}
    </span>
  )
}
