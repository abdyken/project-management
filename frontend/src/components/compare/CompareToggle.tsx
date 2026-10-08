import { Check, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { MAX_COMPARED, useCompareStore } from "@/store/compare"

export function CompareToggle({ programId, title, className }: { programId: string; title: string; className?: string }) {
  const ids = useCompareStore((state) => state.ids)
  const toggle = useCompareStore((state) => state.toggle)
  const selected = ids.includes(programId)
  const full = !selected && ids.length >= MAX_COMPARED

  return (
    <Button
      type="button"
      size="sm"
      variant={selected ? "default" : "outline"}
      aria-pressed={selected}
      aria-label={selected ? `Remove ${title} from comparison` : `Add ${title} to comparison`}
      title={full ? `You can compare up to ${MAX_COMPARED} programs` : undefined}
      disabled={full}
      onClick={() => toggle(programId)}
      className={cn("relative z-10", className)}
    >
      {selected ? <Check className="size-3.5" /> : <Plus className="size-3.5" />}
      {selected ? "Comparing" : "Compare"}
    </Button>
  )
}
