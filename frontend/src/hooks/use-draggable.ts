import { useRef, type MouseEvent as ReactMouseEvent, type PointerEvent as ReactPointerEvent } from "react"
import { viewportSize } from "@/hooks/use-window-size"

export type Point = {
  x: number
  y: number
}

export type Size = {
  width: number
  height: number
}

const MARGIN = 8
const DRAG_THRESHOLD = 3

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

export function clampPosition(position: Point, size: Size): Point {
  const viewport = viewportSize()
  const maxX = Math.max(MARGIN, viewport.width - size.width - MARGIN)
  const maxY = Math.max(MARGIN, viewport.height - size.height - MARGIN)
  return {
    x: clamp(position.x, MARGIN, maxX),
    y: clamp(position.y, MARGIN, maxY),
  }
}

type DragSession = {
  pointerId: number
  startX: number
  startY: number
  originX: number
  originY: number
  moved: boolean
}

export function useDraggable(position: Point, size: Size, onMove: (next: Point) => void) {
  const drag = useRef<DragSession | null>(null)
  const lastDragMoved = useRef(false)

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
    lastDragMoved.current = false
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function onPointerMove(event: ReactPointerEvent<HTMLElement>) {
    const session = drag.current
    if (!session || session.pointerId !== event.pointerId) return
    const dx = event.clientX - session.startX
    const dy = event.clientY - session.startY
    if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) session.moved = true
    if (session.moved) onMove(clampPosition({ x: session.originX + dx, y: session.originY + dy }, size))
  }

  function endDrag(event: ReactPointerEvent<HTMLElement>) {
    const session = drag.current
    if (!session || session.pointerId !== event.pointerId) return
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
    lastDragMoved.current = session.moved
    drag.current = null
  }

  function wasDragged(event: ReactMouseEvent) {
    const moved = lastDragMoved.current
    lastDragMoved.current = false
    return event.detail !== 0 && moved
  }

  return {
    handlers: { onPointerDown, onPointerMove, onPointerUp: endDrag, onPointerCancel: endDrag },
    wasDragged,
  }
}
