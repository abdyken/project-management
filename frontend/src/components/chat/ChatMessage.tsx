import { ArrowUpRight } from "lucide-react"
import type { ChatMessage as ChatMessageType } from "@/store/chat"
import { cn } from "@/lib/utils"

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isApplicant = message.role === "applicant"

  return (
    <article className={cn("flex", isApplicant ? "justify-end" : "justify-start")}>
      <div className={cn("max-w-[85%] space-y-1.5", isApplicant ? "text-right" : "text-left")}>
        <p className="text-[10px] tracking-[0.14em] text-muted-foreground uppercase">
          {isApplicant ? "You" : "Admissions desk"}
        </p>
        <div
          className={cn(
            "whitespace-pre-wrap px-3.5 py-2.5 text-sm leading-relaxed",
            isApplicant
              ? "bg-primary text-primary-foreground"
              : message.isError
                ? "border border-destructive/30 bg-card text-destructive"
                : "border border-border bg-card",
          )}
        >
          {message.text}
        </div>
        {message.sourceLink ? (
          <a
            href={message.sourceLink}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
          >
            Source
            <ArrowUpRight className="size-3" />
          </a>
        ) : null}
      </div>
    </article>
  )
}
