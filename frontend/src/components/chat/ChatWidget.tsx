import { Minus, MessageCircle, X } from "lucide-react"
import { useMemo } from "react"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { useDraggable, clampPosition } from "@/hooks/use-draggable"
import { useMediaQuery } from "@/hooks/use-media-query"
import { useChatStore, type ChatPosition } from "@/store/chat"
import { cn } from "@/lib/utils"

const FAB_SIZE = { width: 56, height: 56 }
const MINI_SIZE = { width: 260, height: 48 }

function panelSize() {
  return {
    width: Math.min(380, window.innerWidth - 16),
    height: Math.min(560, Math.round(window.innerHeight * 0.7)),
  }
}

function defaultFabPosition(): ChatPosition {
  return {
    x: window.innerWidth - FAB_SIZE.width - 24,
    y: window.innerHeight - FAB_SIZE.height - 24,
  }
}

function defaultPanelPosition(): ChatPosition {
  const size = panelSize()
  return {
    x: window.innerWidth - size.width - 24,
    y: window.innerHeight - size.height - 24,
  }
}

export function ChatWidget() {
  const open = useChatStore((state) => state.open)
  const hidden = useChatStore((state) => state.hidden)
  const minimized = useChatStore((state) => state.minimized)
  const position = useChatStore((state) => state.position)
  const fabPosition = useChatStore((state) => state.fabPosition)
  const setOpen = useChatStore((state) => state.setOpen)
  const toggleOpen = useChatStore((state) => state.toggleOpen)
  const hide = useChatStore((state) => state.hide)
  const setMinimized = useChatStore((state) => state.setMinimized)
  const setPosition = useChatStore((state) => state.setPosition)
  const setFabPosition = useChatStore((state) => state.setFabPosition)
  const isNarrow = useMediaQuery("(max-width: 639px)")

  const size = useMemo(() => (typeof window === "undefined" ? { width: 380, height: 560 } : panelSize()), [open])
  const panelPos = position ?? (typeof window === "undefined" ? { x: 0, y: 0 } : defaultPanelPosition())
  const fabPos = fabPosition ?? (typeof window === "undefined" ? { x: 0, y: 0 } : defaultFabPosition())

  const panelDrag = useDraggable(panelPos, minimized ? MINI_SIZE : size, setPosition)
  const fabDrag = useDraggable(fabPos, FAB_SIZE, setFabPosition)

  if (hidden && !isNarrow) {
    return null
  }

  if (isNarrow) {
    return (
      <>
        {hidden ? null : (
          <button
            type="button"
            onClick={toggleOpen}
            aria-expanded={open}
            aria-label={open ? "Close admissions chat" : "Open admissions chat"}
            className={cn(
              "fixed right-4 bottom-4 z-50 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md",
              open && "hidden",
            )}
          >
            <MessageCircle className="size-5" />
          </button>
        )}
        <Sheet open={open && !hidden} onOpenChange={setOpen}>
          <SheetContent side="bottom" className="flex flex-col">
            <SheetHeader className="pr-24">
              <SheetTitle>Admissions desk</SheetTitle>
              <SheetDescription>Ask an official FAQ question</SheetDescription>
              <button
                type="button"
                onClick={hide}
                className="absolute top-3.5 right-12 text-xs text-muted-foreground hover:text-foreground"
              >
                Hide
              </button>
            </SheetHeader>
            <div className="min-h-0 flex-1">
              <ChatPanel showTitle={false} />
            </div>
          </SheetContent>
        </Sheet>
      </>
    )
  }

  return (
    <>
      {!open && !minimized ? (
        <button
          type="button"
          onPointerDown={fabDrag.onPointerDown}
          onPointerMove={fabDrag.onPointerMove}
          onPointerUp={(event) => {
            const moved = fabDrag.onPointerUp(event)
            if (!moved) toggleOpen()
          }}
          aria-expanded={open}
          aria-label="Open admissions chat"
          className="fixed z-50 flex size-14 cursor-grab items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md active:cursor-grabbing"
          style={{ left: fabPos.x, top: fabPos.y }}
        >
          <MessageCircle className="size-5" />
        </button>
      ) : null}

      {minimized ? (
        <div
          className="fixed z-50 flex h-12 w-[260px] cursor-grab items-center gap-2 border border-border bg-background px-3 shadow-lg active:cursor-grabbing"
          style={{ left: clampPosition(panelPos, MINI_SIZE).x, top: clampPosition(panelPos, MINI_SIZE).y }}
          onPointerDown={panelDrag.onPointerDown}
          onPointerMove={panelDrag.onPointerMove}
          onPointerUp={(event) => {
            const moved = panelDrag.onPointerUp(event)
            if (!moved) setMinimized(false)
          }}
        >
          <MessageCircle className="size-4 shrink-0" />
          <span className="flex-1 truncate text-sm">Admissions desk</span>
          <button
            type="button"
            aria-label="Hide chat"
            className="rounded p-1 text-muted-foreground hover:bg-secondary"
            onPointerDown={(event) => event.stopPropagation()}
            onClick={(event) => {
              event.stopPropagation()
              hide()
            }}
          >
            <X className="size-4" />
          </button>
        </div>
      ) : null}

      {open && !minimized ? (
        <div
          className="fixed z-50 flex flex-col border border-border bg-background shadow-lg"
          style={{
            left: clampPosition(panelPos, size).x,
            top: clampPosition(panelPos, size).y,
            width: size.width,
            height: size.height,
          }}
        >
          <div
            className="flex cursor-grab items-start justify-between gap-3 border-b border-border px-4 py-3 active:cursor-grabbing"
            onPointerDown={panelDrag.onPointerDown}
            onPointerMove={panelDrag.onPointerMove}
            onPointerUp={panelDrag.onPointerUp}
          >
            <div>
              <p className="text-lg font-semibold tracking-tight">Admissions desk</p>
              <p className="text-xs text-muted-foreground">Drag to move · official FAQ only</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                aria-label="Minimise chat"
                className="rounded p-1 text-muted-foreground hover:bg-secondary"
                onPointerDown={(event) => event.stopPropagation()}
                onClick={() => setMinimized(true)}
              >
                <Minus className="size-4" />
              </button>
              <button
                type="button"
                aria-label="Hide chat"
                className="rounded p-1 text-muted-foreground hover:bg-secondary"
                onPointerDown={(event) => event.stopPropagation()}
                onClick={hide}
              >
                <X className="size-4" />
              </button>
            </div>
          </div>
          <div className="min-h-0 flex-1">
            <ChatPanel showTitle={false} />
          </div>
        </div>
      ) : null}
    </>
  )
}
