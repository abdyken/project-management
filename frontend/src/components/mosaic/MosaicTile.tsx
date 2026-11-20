import { ArrowRight } from "lucide-react"
import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import { cn } from "@/lib/utils"

// A linked tile: title, one line of purpose, one hard fact with an arrow. One tile per
// group may be the turquoise field (the main path); the rest are quiet white cards.
// Used for paths on the home page and tools on the admissions hub.
const TONES = {
  field: "on-field bg-field text-field-foreground hover:bg-field-deep",
  card: "border border-border bg-card text-card-foreground hover:border-primary",
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
  image,
}: {
  to: string
  tone: MosaicTone
  title: string
  text: string
  fact?: ReactNode
  className?: string
  large?: boolean
  headingLevel?: 2 | 3
  // Optional real photograph across the top of the tile (decorative; the title carries meaning).
  image?: { src: string; srcSet: string; position?: string }
}) {
  const Heading = headingLevel === 2 ? "h2" : "h3"
  return (
    <Link
      to={to}
      className={cn("group relative flex min-h-48 min-w-0 flex-col justify-between p-6 transition-colors duration-200 sm:p-8 lg:p-6 xl:p-8", TONES[tone], className)}
    >
      <div>
        {image ? (
          <img
            src={image.src}
            srcSet={image.srcSet}
            sizes="(min-width: 1024px) 45vw, 100vw"
            alt=""
            loading="lazy"
            style={image.position ? { objectPosition: image.position } : undefined}
            className="-mx-6 -mt-6 mb-6 block h-44 w-[calc(100%+3rem)] max-w-none object-cover sm:-mx-8 sm:-mt-8 sm:mb-8 sm:h-56 sm:w-[calc(100%+4rem)] lg:-mx-6 lg:-mt-6 lg:mb-6 lg:w-[calc(100%+3rem)] xl:-mx-8 xl:-mt-8 xl:mb-8 xl:h-64 xl:w-[calc(100%+4rem)]"
          />
        ) : null}
        <Heading className={cn("font-heading font-medium", large ? "text-[clamp(1.75rem,2.6vw,2.25rem)]" : "text-[clamp(1.25rem,1.6vw,1.5rem)]", "leading-[1.15]")}>
          {title}
        </Heading>
        <p className={cn("mt-3 max-w-[38ch]", large ? "text-lg" : "text-base", tone === "card" && "text-muted-foreground")}>{text}</p>
      </div>
      <p className={cn("label tabular mt-8 flex items-center justify-between gap-4", tone === "card" && "text-primary")}>
        {fact === undefined ? <span /> : (fact ?? "…")}
        <ArrowRight className="size-5 shrink-0 transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
      </p>
    </Link>
  )
}
