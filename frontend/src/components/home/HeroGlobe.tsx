import createGlobe from "cobe"
import { useEffect, useRef } from "react"

const ALMATY: [number, number] = [43.24, 76.95]

export function HeroGlobe() {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    if (!container || !canvas) return

    let width = 0
    let phi = 2.1
    let theta = 0.28
    let frame = 0
    let dragging = false
    let lastX = 0
    let lastY = 0

    const onResize = () => {
      width = canvas.offsetWidth
    }

    const onPointerDown = (event: PointerEvent) => {
      dragging = true
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
      theta = Math.max(-0.8, Math.min(0.8, theta + dy * 0.004))
      lastX = event.clientX
      lastY = event.clientY
    }

    const onPointerUp = (event: PointerEvent) => {
      dragging = false
      container.releasePointerCapture(event.pointerId)
      container.style.cursor = "grab"
    }

    onResize()
    window.addEventListener("resize", onResize)
    container.addEventListener("pointerdown", onPointerDown)
    container.addEventListener("pointermove", onPointerMove)
    container.addEventListener("pointerup", onPointerUp)
    container.addEventListener("pointercancel", onPointerUp)

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches

    const marker = container.querySelector<HTMLElement>(".sdu-globe-marker")
    const wrapper = canvas.parentElement
    if (marker && wrapper && marker.parentElement !== wrapper) {
      wrapper.appendChild(marker)
    }

    const globe = createGlobe(canvas, {
      devicePixelRatio: Math.min(window.devicePixelRatio, 2),
      width: width * 2,
      height: width * 2,
      phi,
      theta,
      dark: 0,
      diffuse: 1.15,
      mapSamples: 14000,
      mapBrightness: 4.5,
      baseColor: [0.106, 0.227, 0.294],
      markerColor: [0.769, 0.647, 0.455],
      glowColor: [0.965, 0.953, 0.933],
      markers: [{ location: ALMATY, size: 0.028, id: "sdu" }],
    })

    const tick = () => {
      if (!dragging && !reducedMotion) {
        phi += 0.0015
      }
      globe.update({
        phi,
        theta,
        width: width * 2,
        height: width * 2,
      })
      frame = window.requestAnimationFrame(tick)
    }

    frame = window.requestAnimationFrame(tick)

    return () => {
      window.cancelAnimationFrame(frame)
      globe.destroy()
      window.removeEventListener("resize", onResize)
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
        className="relative aspect-square w-full cursor-grab touch-none select-none"
        role="img"
        aria-label="Interactive globe with SDU University marker on Almaty"
      >
        <div className="absolute inset-[12%] rounded-full bg-primary/5 blur-2xl" aria-hidden />
        <canvas ref={canvasRef} className="relative h-full w-full" style={{ contain: "layout paint size" }} />
        <div className="sdu-globe-marker" aria-hidden>
          <span className="sdu-globe-marker__ring" />
          <span className="sdu-globe-marker__stem" />
          <div className="sdu-globe-marker__card">
            <img src="/logo.svg" alt="" className="sdu-globe-marker__logo" width={40} height={40} draggable={false} />
          </div>
        </div>
      </div>
    </div>
  )
}
