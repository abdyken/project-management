export type Tile = "field" | "deep" | "glacier" | "ochre" | "terracotta" | "white" | "ink" | null

// A deterministic pseudo-random tile row (same seed, same edge on every render and server).
export function mosaicRow(seed: number, length: number, density = 0.45, palette: Tile[] = ["field", "glacier", "ochre", "field", "terracotta", "deep"]): Tile[] {
  let state = seed >>> 0 || 1
  const next = () => {
    state ^= state << 13
    state ^= state >>> 17
    state ^= state << 5
    return (state >>> 0) / 4294967296
  }
  return Array.from({ length }, () => (next() < density ? palette[Math.floor(next() * palette.length)] : null))
}
