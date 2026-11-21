import { Check, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { cn } from "@/lib/utils"
import { MAX_COMPARED, useCompareStore } from "@/store/compare"

export function CompareToggle({
  programId,
  title,
  className,
  tone = "light",
}: {
  programId: string
  title: string
  className?: string
  tone?: "light" | "field"
}) {
  const { t } = useI18n()
  const ids = useCompareStore((state) => state.ids)
  const toggle = useCompareStore((state) => state.toggle)
  const selected = ids.includes(programId)
  const full = !selected && ids.length >= MAX_COMPARED

  return (
    <Button
      type="button"
      size="sm"
      variant={tone === "field" ? "onField" : selected ? "default" : "outline"}
      aria-pressed={selected}
      aria-label={selected ? t("compare.removeAria", { title }) : t("compare.addAria", { title })}
      title={full ? t("compare.full", { max: MAX_COMPARED }) : undefined}
      disabled={full}
      onClick={() => toggle(programId)}
      // Selected on the turquoise band: a filled white button, never ochre (ochre is only for Apply).
      className={cn("relative z-10", tone === "field" && selected && "bg-field-foreground text-field", className)}
    >
      {selected ? <Check className="size-3.5" /> : <Plus className="size-3.5" />}
      {selected ? t("compare.selected") : t("compare.add")}
    </Button>
  )
}
