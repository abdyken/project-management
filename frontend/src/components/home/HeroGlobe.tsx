import createGlobe from "cobe"
import { useEffect, useRef } from "react"
import { useI18n } from "@/i18n"

const ALMATY: [number, number] = [43.24, 76.95]

export function HeroGlobe() {
  const { t } = useI18n()
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    if (!container || !canvas) return

    let width = canvas.offsetWidth
    let phi = 2.1
    let theta = 0.28
    let frame = 0
    let dragging = false
    let touch = false
    let lastX = 0
    let lastY = 0
    let visible = true
    const spin = !window.matchMedia("(prefers-reduced-motion: reduce)").matches

    const globe = createGlobe(canvas, {
      devicePixelRatio: Math.min(window.devicePixelRatio, 2),
      width: width * 2,
      height: width * 2,
      phi,
      theta,
      // Drawn on the turquoise International band (--field #0a6c74): glacier sphere, white land dots.
      dark: 0,
      diffuse: 1.6,
      mapSamples: 16000,
      mapBrightness: 5,
      baseColor: [0.098, 0.655, 0.659],
      markerColor: [0.89, 0.639, 0.227],
      glowColor: [0.039, 0.424, 0.455],
      markers: [{ location: ALMATY, size: 0.028, id: "sdu" }],
    })

    // Spin only while the globe is on screen and the tab is visible; with reduced motion,
    // draw a frame only when the globe is resized or dragged.
    const running = () => spin && visible && !document.hidden

    const tick = () => {
      frame = 0
      if (spin && !dragging) phi += 0.0015
      globe.update({
        phi,
        theta,
        width: width * 2,
        height: width * 2,
      })
      if (running()) schedule()
    }

    const schedule = () => {
      if (!frame) frame = window.requestAnimationFrame(tick)
    }

    const onResize = () => {
      width = canvas.offsetWidth
      schedule()
    }

    const onPointerDown = (event: PointerEvent) => {
      dragging = true
      touch = event.pointerType === "touch"
      lastX = event.clientX
      lastY = event.clientY
      container.setPointerCapture(event.pointerId)
      container.style.cursor = "grabbing"
    }

    const onPointerMove = (event: PointerEvent) => {
      if (!dragging) return
      const dx = event.clientX - lastX
      const dy = event.clientY - lastY
      phi += dx * 0.006
      // Vertical swipes scroll the page on touch screens, so a finger only spins the globe.
      if (!touch) theta = Math.max(-0.8, Math.min(0.8, theta + dy * 0.004))
      lastX = event.clientX
      lastY = event.clientY
      schedule()
    }

    const onPointerUp = (event: PointerEvent) => {
      dragging = false
      if (container.hasPointerCapture(event.pointerId)) container.releasePointerCapture(event.pointerId)
      container.style.cursor = "grab"
    }

    const onVisibility = () => {
      if (running()) schedule()
    }

    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting
      onVisibility()
    })

    onResize()
    window.addEventListener("resize", onResize)
    document.addEventListener("visibilitychange", onVisibility)
    observer.observe(container)
    container.addEventListener("pointerdown", onPointerDown)
    container.addEventListener("pointermove", onPointerMove)
    container.addEventListener("pointerup", onPointerUp)
    container.addEventListener("pointercancel", onPointerUp)

    return () => {
      window.cancelAnimationFrame(frame)
      observer.disconnect()
      globe.destroy()
      window.removeEventListener("resize", onResize)
      document.removeEventListener("visibilitychange", onVisibility)
      container.removeEventListener("pointerdown", onPointerDown)
      container.removeEventListener("pointermove", onPointerMove)
      container.removeEventListener("pointerup", onPointerUp)
      container.removeEventListener("pointercancel", onPointerUp)
    }
  }, [])

  return (
    <div className="relative mx-auto w-full max-w-sm">
      <div
        ref={containerRef}
        className="relative aspect-square w-full cursor-grab touch-pan-y select-none"
        role="img"
        aria-label={t("home.globe")}
      >
        <canvas ref={canvasRef} className="relative h-full w-full" style={{ contain: "layout paint size" }} />
        <div className="sdu-globe-marker" aria-hidden>
          <span className="sdu-globe-marker__ring" />
          <span className="sdu-globe-marker__stem" />
          <div className="sdu-globe-marker__card">
            <img src="/brand/sdu-emblem-white.svg" alt="" className="sdu-globe-marker__logo" width={40} height={40} draggable={false} />
          </div>
        </div>
      </div>
    </div>
  )
}
