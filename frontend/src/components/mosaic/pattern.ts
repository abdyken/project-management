import { ALATAU_ANGLES, ALATAU_FIRST_BEARING, ALATAU_STEP } from "@/components/mosaic/alatau"

export type Tile = "field" | "deep" | "tint" | "white" | null

type RidgeOptions = {
  // Tiles across. Wider than the screen is fine: the edge is centred and the sides are cut.
  columns: number
  // Tiles up at the highest point.
  rows: number
  // Compass bearing at the centre column (163° is the highest stretch seen from the campus).
  bearing?: number
  // Degrees of the panorama per column: smaller is a closer, more detailed view.
  degreesPerColumn?: number
  // Above 1 the summits rise more sharply above the shoulders of the range.
  peaks?: number
  // Columns around the centre the heights are scaled to: what a laptop screen actually shows.
  scaleTo?: number
  cap?: Tile
  body?: Tile
}

// The Alatau signature: the real skyline seen from the SDU campus (alatau.ts), laid in tiles.
// Each column takes the horizon angle at its bearing, scaled within the visible window and
// snapped to whole tiles, with a cap tile on a body that joins the band below.
export function ridgeSteps({ columns, rows, bearing = 163, degreesPerColumn = 0.4, peaks = 2.2, scaleTo = 180, cap = "deep", body = "field" }: RidgeOptions): Tile[][] {
  const last = ALATAU_ANGLES.length - 1
  const angleAt = (degrees: number) => {
    const position = Math.min(last, Math.max(0, (degrees - ALATAU_FIRST_BEARING) / ALATAU_STEP))
    const index = Math.min(last - 1, Math.floor(position))
    const fraction = position - index
    return ALATAU_ANGLES[index] * (1 - fraction) + ALATAU_ANGLES[index + 1] * fraction
  }
  const angles = Array.from({ length: columns }, (_, column) => angleAt(bearing + (column - columns / 2) * degreesPerColumn))
  const start = Math.max(0, Math.floor((columns - scaleTo) / 2))
  const visible = angles.slice(start, start + Math.min(columns, scaleTo))
  const low = Math.min(...visible)
  const range = Math.max(...visible) - low || 1
  const scale = (angle: number) => Math.min(1, Math.max(0, (angle - low) / range))
  const heights = angles.map((angle) => 1 + Math.round(scale(angle) ** peaks * (rows - 1)))
  return Array.from({ length: rows }, (_, row) =>
    heights.map((columnHeight) => {
      const top = rows - columnHeight
      return row < top ? null : row === top ? cap : body
    }),
  )
}
