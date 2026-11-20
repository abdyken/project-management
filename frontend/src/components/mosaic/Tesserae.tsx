import { useEffect, useRef, useState, type CSSProperties } from "react"
import { cn } from "@/lib/utils"

// A decorative run of square mosaic tiles. Each cell is one token colour, or null for a
// gap. Tiles "set" once when the band first enters the viewport (static under reduced
// motion; see index.css). Purely decorative, so hidden from assistive technology.
import type { Tile } from "@/components/mosaic/pattern"

export type { Tile }

const TILE_CLASS: Record<Exclude<Tile, null>, string> = {
  field: "bg-field",
  deep: "bg-field-deep",
  glacier: "bg-glacier",
  ochre: "bg-ochre",
  terracotta: "bg-terracotta",
  white: "bg-white",
  ink: "bg-ink",
}

type TesseraeProps = {
  // Rows of tiles, top to bottom.
  rows: Tile[][]
  // Tile edge in px (the 8px module times n).
  size?: number
  className?: string
  style?: CSSProperties
}

export function Tesserae({ rows, size = 24, className, style }: TesseraeProps) {
  const ref = useRef<HTMLDivElement>(null)
  // Without IntersectionObserver the tiles are simply shown.
  const [set, setSet] = useState(() => typeof IntersectionObserver === "undefined")

  useEffect(() => {
    const node = ref.current
    if (!node || set) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setSet(true)
          observer.disconnect()
        }
      },
      { rootMargin: "0px 0px -10% 0px" },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [set])

  const columns = Math.max(...rows.map((row) => row.length))

  return (
    <div
      ref={ref}
      aria-hidden="true"
      data-tesserae=""
      data-set={set ? "true" : "false"}
      className={cn("pointer-events-none grid", className)}
      style={{ gridTemplateColumns: `repeat(${columns}, ${size}px)`, gridAutoRows: `${size}px`, ...style }}
    >
      {rows.flatMap((row, r) =>
        Array.from({ length: columns }, (_, c) => {
          const tile = row[c] ?? null
          // Scattered, short stagger: tiles set in a loose order, never in a long sweep.
          const i = (c * 7 + r * 11) % 17
          return (
            <span
              key={`${r}-${c}`}
              className={tile ? TILE_CLASS[tile] : undefined}
              style={{ "--i": i } as CSSProperties}
            />
          )
        }),
      )}
    </div>
  )
}
