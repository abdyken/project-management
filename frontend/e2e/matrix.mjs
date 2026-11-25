import { chromium, firefox } from "playwright"

// One switch for every browser suite. QA_RUNS lists browser:width pairs, for example
// QA_RUNS=chromium:360,chromium:1280 (what CI runs on pull requests). Unset, a suite runs the
// full matrix: Chromium and Firefox at 360, 768 and 1280 px (the nightly run). The older
// RUNS, BROWSERS and WIDTHS variables still work.
const FULL = ["chromium", "firefox"].flatMap((browser) => [360, 768, 1280].map((width) => `${browser}:${width}`))

export function qaRuns(fallback = FULL) {
  let runs = fallback
  const spec = process.env.QA_RUNS ?? process.env.RUNS
  if (spec) {
    runs = spec.split(",").map((run) => run.trim()).filter(Boolean)
  } else if (process.env.BROWSERS || process.env.WIDTHS) {
    const browsers = (process.env.BROWSERS ?? "chromium,firefox").split(",")
    const widths = (process.env.WIDTHS ?? "360,768,1280").split(",")
    runs = browsers.flatMap((browser) => widths.map((width) => `${browser.trim()}:${width.trim()}`))
  }
  return runs.map((run) => {
    const [name, width] = run.split(":")
    if (!["chromium", "firefox"].includes(name) || !Number(width)) throw new Error(`Unknown QA run "${run}"`)
    return { type: name === "firefox" ? firefox : chromium, name, width: Number(width) }
  })
}
