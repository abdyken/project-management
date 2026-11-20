import { useEffect, useRef, useState, type CSSProperties } from "react"
import { cn } from "@/lib/utils"

// The mosaic signature: a decorative run of square tiles in turquoise shades (null = gap).
// It fades in once when it enters the viewport (static under reduced motion; see index.css).
// Purely decorative, so hidden from assistive technology.
import type { Tile } from "@/components/mosaic/pattern"

export type { Tile }

const TILE_CLASS: Record<Exclude<Tile, null>, string> = {
  field: "bg-field",
  deep: "bg-field-deep",
  tint: "bg-field-tint",
  white: "bg-white",
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
          return (
            <span
              key={`${r}-${c}`}
              className={tile ? TILE_CLASS[tile] : undefined}
            />
          )
        }),
      )}
    </div>
  )
}
