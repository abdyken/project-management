import { MessageCircle, X } from "lucide-react"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { useMediaQuery } from "@/hooks/use-media-query"
import { useChatStore } from "@/store/chat"
import { cn } from "@/lib/utils"

export function ChatWidget() {
  const open = useChatStore((state) => state.open)
  const setOpen = useChatStore((state) => state.setOpen)
  const toggleOpen = useChatStore((state) => state.toggleOpen)
  const isNarrow = useMediaQuery("(max-width: 639px)")

  return (
    <>
      <button
        type="button"
        onClick={toggleOpen}
        aria-expanded={open}
        aria-label={open ? "Close admissions chat" : "Open admissions chat"}
        className={cn(
          "fixed right-4 bottom-4 z-50 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md sm:right-6 sm:bottom-6",
          isNarrow && open && "hidden",
        )}
      >
        {open ? <X className="size-5" /> : <MessageCircle className="size-5" />}
      </button>

      {isNarrow ? (
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent side="bottom" className="flex flex-col">
            <SheetHeader className="sr-only">
              <SheetTitle>Admissions desk</SheetTitle>
              <SheetDescription>Ask an official FAQ question</SheetDescription>
            </SheetHeader>
            <div className="min-h-0 flex-1">
              <ChatPanel />
            </div>
          </SheetContent>
        </Sheet>
      ) : open ? (
        <div className="fixed right-6 bottom-24 z-50 flex h-[min(560px,70dvh)] w-[min(380px,calc(100vw-2rem))] flex-col border border-border bg-background shadow-lg">
          <ChatPanel />
        </div>
      ) : null}
    </>
  )
}
