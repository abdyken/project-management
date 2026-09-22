import { useEffect, useRef, type PointerEvent as ReactPointerEvent } from "react"
import type { ChatPosition } from "@/store/chat"

type Size = {
  width: number
  height: number
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

export function clampPosition(position: ChatPosition, size: Size): ChatPosition {
  const margin = 8
  const maxX = Math.max(margin, window.innerWidth - size.width - margin)
  const maxY = Math.max(margin, window.innerHeight - size.height - margin)
  return {
    x: clamp(position.x, margin, maxX),
    y: clamp(position.y, margin, maxY),
  }
}

export function useDraggable(position: ChatPosition, size: Size, onMove: (next: ChatPosition) => void) {
  const drag = useRef<{
    pointerId: number
    startX: number
    startY: number
    originX: number
    originY: number
    moved: boolean
  } | null>(null)

  const latest = useRef({ position, size, onMove })
  latest.current = { position, size, onMove }

  useEffect(() => {
    const onResize = () => {
      const { position: current, size: currentSize, onMove: move } = latest.current
      move(clampPosition(current, currentSize))
    }
    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
  }, [])

  function onPointerDown(event: ReactPointerEvent<HTMLElement>) {
    if (event.button !== 0) return
    drag.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      originX: position.x,
      originY: position.y,
      moved: false,
    }
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function onPointerMove(event: ReactPointerEvent<HTMLElement>) {
    const session = drag.current
    if (!session || session.pointerId !== event.pointerId) return
    const dx = event.clientX - session.startX
    const dy = event.clientY - session.startY
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) session.moved = true
    if (!session.moved) return
    onMove(
      clampPosition(
        {
          x: session.originX + dx,
          y: session.originY + dy,
        },
        size,
      ),
    )
  }

  function onPointerUp(event: ReactPointerEvent<HTMLElement>) {
    const session = drag.current
    if (!session || session.pointerId !== event.pointerId) return
    event.currentTarget.releasePointerCapture(event.pointerId)
    const moved = session.moved
    drag.current = null
    return moved
  }

  return { onPointerDown, onPointerMove, onPointerUp }
}
