import { useEffect, useState, type RefObject } from "react"

// Motion helpers. Every effect is optional: with reduced motion or without
// IntersectionObserver, content renders in its final state.

export function prefersReducedMotion() {
  return typeof window === "undefined" || window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

export function hasFinePointer() {
  return typeof window !== "undefined" && window.matchMedia("(hover: hover) and (pointer: fine)").matches
}

// Calls back once, the first time the element is at least `ratio` in view.
export function observeOnce(element: Element, callback: () => void, ratio = 0.12) {
  if (typeof IntersectionObserver === "undefined") {
    callback()
    return () => {}
  }
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        callback()
        observer.disconnect()
      }
    },
    { threshold: ratio },
  )
  observer.observe(element)
  return () => observer.disconnect()
}

// Reveals every [data-reveal] / [data-reveal-list] inside the scope as it scrolls into view.
// The hidden state only applies once <html> has the `motion-ready` class (set in main.tsx),
// so a failed script never hides content. CSS lives in index.css.
export function useRevealScope(scope: RefObject<HTMLElement | null>, key: unknown = null) {
  useEffect(() => {
    const root = scope.current
    if (!root) return
    const targets = [...root.querySelectorAll<HTMLElement>("[data-reveal], [data-reveal-list]")].filter(
      (element) => element.dataset.revealed !== "true",
    )
    const stops = targets.map((element) =>
      observeOnce(element, () => {
        element.dataset.revealed = "true"
      }),
    )
    return () => stops.forEach((stop) => stop())
  }, [scope, key])
}

// Counts from 0 to `value` once the element is in view (750ms, ease-out cubic).
export function useCountUp(ref: RefObject<HTMLElement | null>, value: number | null) {
  const [display, setDisplay] = useState<number | null>(() => (value === null || prefersReducedMotion() ? value : 0))

  useEffect(() => {
    const element = ref.current
    if (value === null || !element) return
    if (prefersReducedMotion()) return
    let frame = 0
    const stop = observeOnce(
      element,
      () => {
        const start = performance.now()
        const tick = (now: number) => {
          const progress = Math.min(1, (now - start) / 750)
          setDisplay(Math.round(value * (1 - Math.pow(1 - progress, 3))))
          if (progress < 1) frame = requestAnimationFrame(tick)
        }
        frame = requestAnimationFrame(tick)
      },
      0.4,
    )
    return () => {
      stop()
      cancelAnimationFrame(frame)
    }
  }, [ref, value])

  // With reduced motion (or before data arrives) the final value is shown as is.
  return prefersReducedMotion() ? value : (display ?? (value === null ? null : 0))
}

// Reveals a single [data-reveal-list] element (its own ref) as it scrolls into view.
export function useRevealList(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const element = ref.current
    if (!element) return
    return observeOnce(element, () => {
      element.dataset.revealed = "true"
    })
  }, [ref])
}

