import type { DegreeLevel, Program } from "@/api/types"

export const LEVELS: DegreeLevel[] = ["bachelor", "master", "phd"]

// The most common non-empty value: the date most programs of a level share.
export function mode(values: (string | null)[]): string | null {
  const counts = new Map<string, number>()
  for (const value of values) if (value) counts.set(value, (counts.get(value) ?? 0) + 1)
  let best: string | null = null
  for (const [value, count] of counts) if (best === null || count > (counts.get(best) ?? 0)) best = value
  return best
}

export type LevelDeadlines = Record<DegreeLevel, { local: string | null; international: string | null; count: number }>

// The local and international document deadline most programs of each level share.
export function levelDeadlines(programs: Program[]): LevelDeadlines {
  return Object.fromEntries(
    LEVELS.map((level) => {
      const items = programs.filter((program) => program.degree_level === level)
      return [
        level,
        {
          count: items.length,
          local: mode(items.map((program) => program.deadline_local)),
          international: mode(items.map((program) => program.deadline_international)),
        },
      ]
    }),
  ) as LevelDeadlines
}
