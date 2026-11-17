import { MessageCircle, Minus, SquarePen, X } from "lucide-react"
import { useEffect, useRef } from "react"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { useMediaQuery } from "@/hooks/use-media-query"
import { useI18n } from "@/i18n"
import { useChatStore } from "@/store/chat"

const TITLE_ID = "chat-title"
const iconButton = "rounded p-1 text-muted-foreground hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring/40"
const fabClass =
  "fixed z-50 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md outline-none focus-visible:ring-4 focus-visible:ring-ring/30"

function NewConversationButton() {
  const { t } = useI18n()
  const startNewConversation = useChatStore((state) => state.startNewConversation)
  return (
    <button type="button" aria-label={t("chat.newConversation")} className={iconButton} onClick={startNewConversation}>
      <SquarePen className="size-4" />
    </button>
  )
}

function MobileChat() {
  const { t } = useI18n()
  const open = useChatStore((state) => state.open)
  const setOpen = useChatStore((state) => state.setOpen)
  const fabRef = useRef<HTMLButtonElement>(null)

  return (
    <>
      <button
        ref={fabRef}
        type="button"
        onClick={() => setOpen(true)}
        aria-label={t("chat.open")}
        className={`${fabClass} right-4 bottom-4`}
      >
        <MessageCircle className="size-5" />
      </button>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent
          side="bottom"
          className="flex flex-col"
          onCloseAutoFocus={(event) => {
            event.preventDefault()
            fabRef.current?.focus()
          }}
        >
          <SheetHeader className="pr-12">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <SheetTitle>{t("chat.title")}</SheetTitle>
                <SheetDescription>{t("chat.subtitle")}</SheetDescription>
              </div>
              <NewConversationButton />
            </div>
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
  const { t } = useI18n()
  const open = useChatStore((state) => state.open)
  const minimized = useChatStore((state) => state.minimized)
  const setOpen = useChatStore((state) => state.setOpen)
  const setMinimized = useChatStore((state) => state.setMinimized)
  const panelRef = useRef<HTMLElement>(null)
  const fabRef = useRef<HTMLButtonElement>(null)
  const restoreRef = useRef<HTMLButtonElement>(null)
  const showPanel = open && !minimized
  const wasShowingPanel = useRef(showPanel)

  useEffect(() => {
    if (wasShowingPanel.current && !showPanel) (minimized ? restoreRef : fabRef).current?.focus()
    wasShowingPanel.current = showPanel
  }, [showPanel, minimized])

  useEffect(() => {
    if (!showPanel) return
    function onKeyDown(event: globalThis.KeyboardEvent) {
      const focus = document.activeElement
      const focusInPanel = Boolean(panelRef.current?.contains(focus))
      if (event.key === "Escape" && focusInPanel) setOpen(false)
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [showPanel, setOpen])

  if (minimized) {
    return (
      <div className="fixed right-6 bottom-6 z-50 flex h-12 w-[260px] items-center gap-1 border border-border bg-background pr-2 shadow-lg">
        <button
          type="button"
          ref={restoreRef}
          onClick={() => setMinimized(false)}
          className="flex h-full min-w-0 flex-1 items-center gap-2 px-3 text-left text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
          aria-label={t("chat.restore")}
        >
          <MessageCircle className="size-4 shrink-0" />
          <span className="truncate">{t("chat.title")}</span>
        </button>
        <button type="button" aria-label={t("chat.close")} className={iconButton} onClick={() => setOpen(false)}>
          <X className="size-4" />
        </button>
      </div>
    )
  }

  if (!open) {
    return (
      <button
        type="button"
        ref={fabRef}
        onClick={() => setOpen(true)}
        aria-label={t("chat.open")}
        className={`${fabClass} right-6 bottom-6`}
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
      tabIndex={-1}
      className="fixed right-6 bottom-6 z-50 flex h-[min(560px,70vh)] w-[min(380px,calc(100vw-1rem))] flex-col border border-border bg-background shadow-lg outline-none"
    >
      <div className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 id={TITLE_ID} className="text-lg font-semibold tracking-tight">
            {t("chat.title")}
          </h2>
          <p className="text-xs text-muted-foreground">{t("chat.subtitle")}</p>
        </div>
        <div className="flex items-center gap-1">
          <NewConversationButton />
          <button type="button" aria-label={t("chat.minimise")} className={iconButton} onClick={() => setMinimized(true)}>
            <Minus className="size-4" />
          </button>
          <button type="button" aria-label={t("chat.close")} className={iconButton} onClick={() => setOpen(false)}>
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
