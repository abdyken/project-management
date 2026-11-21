import { MessageCircle, Minus, SquarePen, X } from "lucide-react"
import { useEffect, useRef } from "react"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { ApplyAction } from "@/components/common/ApplyAction"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { useMediaQuery } from "@/hooks/use-media-query"
import { useI18n } from "@/i18n"
import { useChatStore } from "@/store/chat"

const TITLE_ID = "chat-title"
const iconButton = "grid size-9 place-items-center text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground outline-none focus-visible:outline-2 focus-visible:outline-ring"
const fieldIconButton = "grid size-9 place-items-center text-field-foreground transition-colors hover:bg-field-deep outline-none focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-white"
const fabClass =
  "fixed z-50 flex size-14 items-center justify-center bg-primary text-primary-foreground shadow-overlay outline-none transition-colors hover:bg-field-deep focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"

function NewConversationButton({ onField = false }: { onField?: boolean }) {
  const { t } = useI18n()
  const startNewConversation = useChatStore((state) => state.startNewConversation)
  return (
    <button type="button" aria-label={t("chat.newConversation")} className={onField ? fieldIconButton : iconButton} onClick={startNewConversation}>
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
      {/* Phones: one bottom bar instead of a floating button, so nothing covers the content and
          Apply stays one tap away. The compare tray, when present, sits directly above it. */}
      <div className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-[minmax(0,1fr)_auto] gap-2 border-t border-field-foreground/15 bg-field-deep px-4 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        <ApplyAction label={t("header.apply")} className="w-full justify-center" />
        <button
          ref={fabRef}
          type="button"
          onClick={() => setOpen(true)}
          aria-label={`${t("nav.ask")}: ${t("chat.open")}`}
          className="inline-flex min-h-12 items-center gap-2 border-2 border-field-foreground px-4 font-semibold text-field-foreground transition-colors hover:bg-field-foreground hover:text-field-deep focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
        >
          <MessageCircle className="size-5" aria-hidden="true" />
          {t("nav.ask")}
        </button>
      </div>
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
      <div className="on-field fixed right-6 bottom-6 z-50 flex h-12 w-[260px] items-center gap-1 bg-field pr-2 shadow-overlay">
        <button
          type="button"
          ref={restoreRef}
          onClick={() => setMinimized(false)}
          className="flex h-full min-w-0 flex-1 items-center gap-2 px-3 text-left font-semibold outline-none focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-white"
          aria-label={t("chat.restore")}
        >
          <MessageCircle className="size-4 shrink-0" />
          <span className="truncate">{t("chat.title")}</span>
        </button>
        <button type="button" aria-label={t("chat.close")} className={fieldIconButton} onClick={() => setOpen(false)}>
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
      className="fixed right-6 bottom-6 z-50 flex h-[min(600px,72vh)] w-[min(400px,calc(100vw-1rem))] flex-col bg-background shadow-overlay outline-none"
    >
      <div className="on-field flex items-start justify-between gap-3 bg-field px-4 py-3">
        <div>
          <h2 id={TITLE_ID} className="text-xl leading-tight font-medium">
            {t("chat.title")}
          </h2>
          <p className="mt-1 text-sm text-field-muted">{t("chat.subtitle")}</p>
        </div>
        <div className="flex items-center gap-1">
          <NewConversationButton onField />
          <button type="button" aria-label={t("chat.minimise")} className={fieldIconButton} onClick={() => setMinimized(true)}>
            <Minus className="size-4" />
          </button>
          <button type="button" aria-label={t("chat.close")} className={fieldIconButton} onClick={() => setOpen(false)}>
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
