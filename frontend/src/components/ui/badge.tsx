import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

// A square status label: one tessera of colour plus the words, so the status never
// depends on colour alone. Tones map to the mosaic palette.
const TONES = {
  neutral: { box: "bg-muted text-foreground", tile: "border-2 border-input" },
  field: { box: "bg-secondary text-secondary-foreground", tile: "bg-field" },
  glacier: { box: "bg-secondary text-secondary-foreground", tile: "bg-glacier" },
  ochre: { box: "bg-ochre/20 text-foreground", tile: "bg-ochre" },
  terracotta: { box: "bg-terracotta/12 text-destructive", tile: "bg-terracotta" },
  solid: { box: "bg-primary text-primary-foreground", tile: "bg-ochre" },
} as const

export type BadgeTone = keyof typeof TONES

export function Badge({ tone = "neutral", children, className }: { tone?: BadgeTone; children: ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 px-2 py-1 text-sm font-semibold", TONES[tone].box, className)}>
      <span aria-hidden="true" className={cn("size-2.5 shrink-0", TONES[tone].tile)} />
      {children}
    </span>
  )
}
