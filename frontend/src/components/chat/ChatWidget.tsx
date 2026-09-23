import { MessageCircle, Minus, X } from "lucide-react"
import { useEffect, useRef } from "react"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { clampPosition, useDraggable, type Size } from "@/hooks/use-draggable"
import { useMediaQuery } from "@/hooks/use-media-query"
import { useWindowSize } from "@/hooks/use-window-size"
import { useChatStore, type ChatPosition } from "@/store/chat"

const FAB_SIZE: Size = { width: 56, height: 56 }
const MINI_SIZE: Size = { width: 260, height: 48 }
const EDGE = 24
const TITLE_ID = "chat-title"
const iconButton = "rounded p-1 text-muted-foreground hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring/40"
const fabClass =
  "fixed z-50 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md outline-none focus-visible:ring-4 focus-visible:ring-ring/30"

function bottomRight(viewport: { width: number; height: number }, size: Size): ChatPosition {
  return { x: viewport.width - size.width - EDGE, y: viewport.height - size.height - EDGE }
}

function MobileChat() {
  const open = useChatStore((state) => state.open)
  const setOpen = useChatStore((state) => state.setOpen)

  return (
    <>
      {open ? null : (
        <button type="button" onClick={() => setOpen(true)} aria-label="Open admissions chat" className={`${fabClass} right-4 bottom-4`}>
          <MessageCircle className="size-5" />
        </button>
      )}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="bottom" className="flex flex-col">
          <SheetHeader className="pr-12">
            <SheetTitle>Admissions desk</SheetTitle>
            <SheetDescription>Answers come from the official FAQ</SheetDescription>
          </SheetHeader>
          <div className="min-h-0 flex-1">
            <ChatPanel />
          </div>
        </SheetContent>
      </Sheet>
    </>
  )
}

function DesktopChat() {
  const open = useChatStore((state) => state.open)
  const minimized = useChatStore((state) => state.minimized)
  const position = useChatStore((state) => state.position)
  const fabPosition = useChatStore((state) => state.fabPosition)
  const setOpen = useChatStore((state) => state.setOpen)
  const setMinimized = useChatStore((state) => state.setMinimized)
  const setPosition = useChatStore((state) => state.setPosition)
  const setFabPosition = useChatStore((state) => state.setFabPosition)
  const viewport = useWindowSize()

  const panelSize: Size = {
    width: Math.min(380, viewport.width - 16),
    height: Math.min(560, Math.round(viewport.height * 0.7)),
  }
  const panelBox = minimized ? MINI_SIZE : panelSize
  const panelPos = clampPosition(position ?? bottomRight(viewport, panelSize), panelBox)
  const fabPos = clampPosition(fabPosition ?? bottomRight(viewport, FAB_SIZE), FAB_SIZE)

  const panelDrag = useDraggable(panelPos, panelBox, setPosition)
  const fabDrag = useDraggable(fabPos, FAB_SIZE, setFabPosition)
  const panelRef = useRef<HTMLElement>(null)
  const showPanel = open && !minimized

  useEffect(() => {
    if (!showPanel) return
    function onKeyDown(event: globalThis.KeyboardEvent) {
      const focus = document.activeElement
      const focusInPanel = focus === document.body || Boolean(panelRef.current?.contains(focus))
      if (event.key === "Escape" && focusInPanel) setOpen(false)
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [showPanel, setOpen])

  if (minimized) {
    return (
      <div
        className="fixed z-50 flex h-12 w-[260px] items-center gap-1 border border-border bg-background pr-2 shadow-lg"
        style={{ left: panelPos.x, top: panelPos.y }}
      >
        <button
          type="button"
          {...panelDrag.handlers}
          onClick={() => {
            if (!panelDrag.consumeDrag()) setMinimized(false)
          }}
          className="flex h-full min-w-0 flex-1 cursor-grab touch-none items-center gap-2 px-3 text-left text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/40 active:cursor-grabbing"
          aria-label="Restore admissions chat"
        >
          <MessageCircle className="size-4 shrink-0" />
          <span className="truncate">Admissions desk</span>
        </button>
        <button type="button" aria-label="Close chat" className={iconButton} onClick={() => setOpen(false)}>
          <X className="size-4" />
        </button>
      </div>
    )
  }

  if (!open) {
    return (
      <button
        type="button"
        {...fabDrag.handlers}
        onClick={() => {
          if (!fabDrag.consumeDrag()) setOpen(true)
        }}
        aria-label="Open admissions chat"
        className={`${fabClass} cursor-grab touch-none active:cursor-grabbing`}
        style={{ left: fabPos.x, top: fabPos.y }}
      >
        <MessageCircle className="size-5" />
      </button>
    )
  }

  return (
    <section
      ref={panelRef}
      role="dialog"
      aria-labelledby={TITLE_ID}
      className="fixed z-50 flex flex-col border border-border bg-background shadow-lg"
      style={{ left: panelPos.x, top: panelPos.y, width: panelSize.width, height: panelSize.height }}
    >
      <div
        {...panelDrag.handlers}
        className="flex cursor-grab touch-none items-start justify-between gap-3 border-b border-border px-4 py-3 active:cursor-grabbing"
      >
        <div>
          <h2 id={TITLE_ID} className="text-lg font-semibold tracking-tight">
            Admissions desk
          </h2>
          <p className="text-xs text-muted-foreground">Answers come from the official FAQ</p>
        </div>
        <div className="flex items-center gap-1" onPointerDown={(event) => event.stopPropagation()}>
          <button type="button" aria-label="Minimise chat" className={iconButton} onClick={() => setMinimized(true)}>
            <Minus className="size-4" />
          </button>
          <button type="button" aria-label="Close chat" className={iconButton} onClick={() => setOpen(false)}>
            <X className="size-4" />
          </button>
        </div>
      </div>
      <div className="min-h-0 flex-1">
        <ChatPanel autoFocus />
      </div>
    </section>
  )
}

export function ChatWidget() {
  const isNarrow = useMediaQuery("(max-width: 639px)")
  return isNarrow ? <MobileChat /> : <DesktopChat />
}
