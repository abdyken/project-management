import { useMemo } from "react"
import { ridgeSteps } from "@/components/mosaic/pattern"
import { Tesserae } from "@/components/mosaic/Tesserae"

// The Alatau, lower: the bottom edge of an inner page's turquoise title band, in tiles of the
// deeper turquoise. Each page centres a different bearing, so moving
// through the site walks along the range. Drawn still; the laying motion belongs to the home page.
export function RidgeHorizon({ bearing = 163 }: { bearing?: number }) {
  const rows = useMemo(
    () => ridgeSteps({ columns: 400, rows: 9, bearing, degreesPerColumn: 0.25, peaks: 1.1, cap: "deep", body: "deep" }),
    [bearing],
  )
  return (
    <div className="flex justify-center overflow-hidden">
      <Tesserae size={8} rows={rows} still className="shrink-0" />
    </div>
  )
}
