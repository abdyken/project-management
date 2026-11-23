import { useEffect, useRef, useState, type CSSProperties, type RefObject } from "react"
import type { Tile } from "@/components/mosaic/pattern"
import { hasFinePointer, observeOnce, prefersReducedMotion } from "@/lib/motion"
import { cn } from "@/lib/utils"

export type { Tile }

// The mosaic signature: square tiles in turquoise shades (null = gap), each with a faint 1px
// grout line so the 16px module reads as laid tesserae. Purely decorative (aria-hidden).
// Motion: the first time it enters view, the frame around it (.tesserae-frame) sweeps it in from
// the left in one smooth 1.6s reveal (index.css), then it settles. With a fine pointer over `lightFrom`,
// tiles within three columns of the cursor catch the light; they brighten, never move.
// Under reduced motion the edge is simply there.
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
  // Element whose pointer movement lights nearby tiles (fine pointers only).
  lightFrom?: RefObject<HTMLElement | null>
  // Drawn settled, without the laying animation (the footer on inner pages).
  still?: boolean
}

// The grout line is fainter on small tiles, so 8px tesserae read as a surface, not as dots.
const GROUT = (size: number) =>
  size >= 16 ? "shadow-[inset_0_0_0_1px_rgb(255_255_255/0.12)]" : "shadow-[inset_0_0_0_1px_rgb(255_255_255/0.05)]"

export function Tesserae({ rows, size = 24, className, style, lightFrom, still = false }: TesseraeProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [state, setState] = useState<"waiting" | "laying" | "settled">(() =>
    still || typeof IntersectionObserver === "undefined" || prefersReducedMotion() ? "settled" : "waiting",
  )

  useEffect(() => {
    const node = ref.current
    if (!node || state !== "waiting") return
    // Watch the band the frame sits on: the frame itself is clipped away until the sweep starts,
    // and a fully clipped element never counts as in view.
    const watched = node.closest(".tesserae-frame")?.parentElement ?? node
    return observeOnce(watched, () => setState("laying"), 0.01)
  }, [state])

  // Once the 1.6s sweep is done, the tiles settle and can catch the light.
  useEffect(() => {
    if (state !== "laying") return
    const timer = window.setTimeout(() => setState("settled"), 1700)
    return () => window.clearTimeout(timer)
  }, [state])

  useEffect(() => {
    const node = ref.current
    const area = lightFrom?.current
    if (!node || !area || !hasFinePointer()) return
    const byColumn = new Map<number, HTMLElement[]>()
    node.querySelectorAll<HTMLElement>("span[data-col]").forEach((span) => {
      const column = Number(span.dataset.col)
      byColumn.set(column, [...(byColumn.get(column) ?? []), span])
    })
    let lit: HTMLElement[] = []
    let frame = 0
    const light = (columns: number[]) => {
      lit.forEach((span) => span.removeAttribute("data-lit"))
      lit = columns.flatMap((column) => byColumn.get(column) ?? [])
      lit.forEach((span) => span.setAttribute("data-lit", ""))
    }
    const move = (event: PointerEvent) => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        const box = node.getBoundingClientRect()
        const column = Math.floor((event.clientX - box.left) / size)
        light([-3, -2, -1, 0, 1, 2, 3].map((offset) => column + offset))
      })
    }
    const leave = () => {
      cancelAnimationFrame(frame)
      light([])
    }
    area.addEventListener("pointermove", move)
    area.addEventListener("pointerleave", leave)
    return () => {
      cancelAnimationFrame(frame)
      area.removeEventListener("pointermove", move)
      area.removeEventListener("pointerleave", leave)
    }
  }, [lightFrom, size])

  const columns = Math.max(...rows.map((row) => row.length))

  return (
    <div
      ref={ref}
      aria-hidden="true"
      data-tesserae={state}
      className={cn("pointer-events-none grid", className)}
      style={{ gridTemplateColumns: `repeat(${columns}, ${size}px)`, gridAutoRows: `${size}px`, ...style }}
    >
      {rows.flatMap((row, r) =>
        Array.from({ length: columns }, (_, c) => {
          const tile = row[c] ?? null
          return tile ? (
            <span
              key={`${r}-${c}`}
              data-col={c}
              className={`${TILE_CLASS[tile]} ${GROUT(size)}`}
            />
          ) : (
            <span key={`${r}-${c}`} />
          )
        }),
      )}
    </div>
  )
}
