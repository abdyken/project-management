export type Tile = "field" | "deep" | "tint" | "white" | null

// The portal's mosaic signature: a stepped edge of 16px tesserae, after the step profiles of
// Almaty's modernist mosaic panels. Short runs (2-5 tiles) step up or down one tile at a
// time from the very first column, so even a phone shows several steps. Each column has a
// cap tile on a body that joins the band below. Deterministic and monochrome turquoise;
// used at most twice per page.
export function signatureSteps(length: number, rows = 3, cap: Tile = "deep", body: Tile = "field", seed = 1996): Tile[][] {
  let state = seed >>> 0 || 1
  const next = () => {
    state ^= state << 13
    state ^= state >>> 17
    state ^= state << 5
    return (state >>> 0) / 4294967296
  }
  const heights: number[] = []
  let height = 1
  while (heights.length < length) {
    const run = 2 + Math.floor(next() * 4)
    for (let i = 0; i < run && heights.length < length; i++) heights.push(height)
    const step = height === 1 ? 1 : height === rows ? -1 : next() < 0.5 ? 1 : -1
    height += step
  }
  return Array.from({ length: rows }, (_, row) =>
    heights.map((columnHeight) => {
      const top = rows - columnHeight
      return row < top ? null : row === top ? cap : body
    }),
  )
}
