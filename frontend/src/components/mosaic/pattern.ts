export type Tile = "field" | "deep" | "tint" | "white" | null

// The portal's mosaic signature: a stepped edge of 16px tesserae, after the step profiles of
// Almaty's modernist mosaic panels. Runs of 3-8 tiles step up and down one tile at a time and
// rise across the first ~90 columns. Each column has a darker cap tile on a body that joins
// the band below. Deterministic, monochrome turquoise, used at most twice per page.
export function signatureSteps(length: number, rows = 3, cap: Tile = "deep", body: Tile = "field", seed = 1996): Tile[][] {
  let state = seed >>> 0 || 1
  const next = () => {
    state ^= state << 13
    state ^= state >>> 17
    state ^= state << 5
    return (state >>> 0) / 4294967296
  }
  const heights: number[] = []
  while (heights.length < length) {
    const column = heights.length
    const rising = 1 + Math.floor((Math.min(column, 89) / 90) * rows)
    const height = Math.max(1, Math.min(rows, rising - (next() < 0.3 ? 1 : 0)))
    const run = 3 + Math.floor(next() * 6)
    for (let i = 0; i < run && heights.length < length; i++) heights.push(height)
  }
  return Array.from({ length: rows }, (_, row) =>
    heights.map((height) => {
      const top = rows - height
      return row < top ? null : row === top ? cap : body
    }),
  )
}
