import { ArrowRight } from "lucide-react"
import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import { cn } from "@/lib/utils"

// A linked colour-field tile: title, one line of purpose, one hard fact with an arrow.
// Used for paths on the home page and tools on the admissions hub.
const TONES = {
  field: "on-field bg-field text-field-foreground hover:bg-field-deep",
  glacier: "bg-glacier text-ink hover:bg-[#1597a0]",
  ochre: "bg-ochre text-ink hover:bg-ochre-hover",
  terracotta: "bg-terracotta text-white hover:bg-[#b2482a] [--ring:#fff]",
  card: "bg-card text-card-foreground outline-2 -outline-offset-2 outline-transparent hover:outline-primary",
} as const

export type MosaicTone = keyof typeof TONES

export function MosaicTile({
  to,
  tone,
  title,
  text,
  fact,
  className,
  large,
  headingLevel = 3,
}: {
  to: string
  tone: MosaicTone
  title: string
  text: string
  fact?: ReactNode
  className?: string
  large?: boolean
  headingLevel?: 2 | 3
}) {
  const Heading = headingLevel === 2 ? "h2" : "h3"
  return (
    <Link
      to={to}
      className={cn("group relative flex min-h-56 min-w-0 flex-col justify-between p-6 transition-colors duration-200 sm:p-8 lg:p-6 xl:p-8", TONES[tone], className)}
    >
      <div>
        <Heading className={cn("font-display font-extrabold uppercase", large ? "text-[clamp(2.75rem,5vw,4.5rem)]" : "text-[clamp(1.375rem,1.9vw,2.125rem)]", "leading-[0.9]")}>
          {title}
        </Heading>
        <p className={cn("mt-3 max-w-[34ch]", large ? "text-xl" : "text-lg")}>{text}</p>
      </div>
      <p className="tabular mt-8 flex items-center justify-between gap-4 font-display text-2xl font-bold uppercase">
        {fact === undefined ? <span /> : (fact ?? "…")}
        <ArrowRight className="size-6 shrink-0 transition-transform duration-200 group-hover:translate-x-1" aria-hidden="true" />
      </p>
    </Link>
  )
}
