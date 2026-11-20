export type Tile = "field" | "deep" | "tint" | "white" | null

// The portal's mosaic signature: a quiet tonal band of small turquoise tesserae (field and
// deep only), laid irregularly like a real mosaic. Deterministic, so it never changes between
// renders. Used at most twice per page (hero band edge, footer edge); never warm hues.
export function signatureBand(rows: number, length: number, seed = 1996, share = 0.38): Tile[][] {
  let state = seed >>> 0 || 1
  const next = () => {
    state ^= state << 13
    state ^= state >>> 17
    state ^= state << 5
    return (state >>> 0) / 4294967296
  }
  return Array.from({ length: rows }, () => Array.from({ length }, () => (next() < share ? "field" : "deep")))
}
