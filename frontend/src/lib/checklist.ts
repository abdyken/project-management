import type { DocumentRequirement } from "@/api/types"
import type { I18n } from "@/i18n"

export function requirementNotes(item: DocumentRequirement, t: I18n["t"]) {
  return [
    item.format === "original" ? t("checklist.original") : t("checklist.copy"),
    item.translation && t("checklist.translation"),
    item.notarisation && t("checklist.notarised"),
  ]
    .filter(Boolean)
    .join(" · ")
}
