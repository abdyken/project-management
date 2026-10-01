import { ArrowUpRight, RotateCcw, ThumbsDown, ThumbsUp } from "lucide-react"
import { useState } from "react"
import { sendFeedback } from "@/api/assistant"
import type { FeedbackReason } from "@/api/types"
import { AnswerBody } from "@/components/chat/AnswerBody"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useChatStore, type ChatMessage as ChatMessageType, type ChatSource } from "@/store/chat"

const REASONS: { id: FeedbackReason; label: string }[] = [
  { id: "outdated", label: "Outdated" },
  { id: "incorrect", label: "Incorrect" },
  { id: "incomplete", label: "Incomplete" },
  { id: "unclear", label: "Unclear" },
]

function sourceLabel(source: ChatSource, index: number, total: number) {
  if (source.question) return source.question
  return total > 1 ? `Source ${index + 1}` : "Source"
}

function Sources({ sources }: { sources: ChatSource[] }) {
  const visible = sources.filter((source) => source.link || source.question)
  if (visible.length === 0) return null

  return (
    <ul className="space-y-1">
      {visible.map((source, index) => {
        const label = sourceLabel(source, index, visible.length)
        return (
          <li key={`${source.faqId ?? source.link ?? label}-${index}`} className="min-w-0">
            {source.link ? (
              <a
                href={source.link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex max-w-full items-start gap-1 text-xs break-words text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
              >
                <span>{label}</span>
                <ArrowUpRight className="mt-0.5 size-3 shrink-0" />
              </a>
            ) : (
              <span className="text-xs break-words text-muted-foreground">{label}</span>
            )}
          </li>
        )
      })}
    </ul>
  )
}

function RatingControls({ message }: { message: ChatMessageType }) {
  const rateMessage = useChatStore((state) => state.rateMessage)
  const [picking, setPicking] = useState(false)
  if (!message.answerId || message.isError || message.interrupted || message.streaming) return null

  function commit(rating: "up" | "down", reason: FeedbackReason | null) {
    if (!message.answerId || message.rating) return
    rateMessage(message.id, { rating, reason })
    setPicking(false)
    void sendFeedback({
      answer_id: message.answerId,
      rating,
      ...(reason ? { reason } : {}),
    }).catch(() => {
      // The rating stays in the session store even when the feedback endpoint is unavailable.
    })
  }

  const selected = message.rating

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        <button
          type="button"
          aria-label="Helpful"
          aria-pressed={selected?.rating === "up"}
          disabled={Boolean(selected)}
          onClick={() => commit("up", null)}
          className={cn(
            "rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-100",
            selected?.rating === "up" && "text-foreground",
          )}
        >
          <ThumbsUp className="size-3.5" />
        </button>
        <button
          type="button"
          aria-label="Not helpful"
          aria-pressed={selected?.rating === "down"}
          disabled={Boolean(selected)}
          onClick={() => {
            if (selected) return
            setPicking(true)
          }}
          className={cn(
            "rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-100",
            selected?.rating === "down" && "text-foreground",
          )}
        >
          <ThumbsDown className="size-3.5" />
        </button>
        {selected?.reason ? (
          <span className="text-[11px] text-muted-foreground">
            {REASONS.find((reason) => reason.id === selected.reason)?.label}
          </span>
        ) : null}
      </div>
      {picking && !selected ? (
        <div className="flex flex-wrap gap-1.5">
          {REASONS.map((reason) => (
            <button
              key={reason.id}
              type="button"
              onClick={() => commit("down", reason.id)}
              className="rounded-full border border-border px-2.5 py-1 text-[11px] text-muted-foreground hover:bg-secondary hover:text-foreground"
            >
              {reason.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export function ChatMessage({
  message,
  onResend,
}: {
  message: ChatMessageType
  onResend?: (message: ChatMessageType) => void
}) {
  const isApplicant = message.role === "applicant"
  if (message.streaming && !message.text) return null

  return (
    <article className={cn("flex min-w-0", isApplicant ? "justify-end" : "justify-start")}>
      <div className={cn("min-w-0 space-y-1.5", isApplicant ? "max-w-[85%] text-right" : "max-w-full text-left")}>
        <p className="text-[10px] tracking-[0.14em] text-muted-foreground uppercase">
          {isApplicant ? "You" : "Admissions desk"}
        </p>
        {message.text ? (
          <div
            className={cn(
              "px-3.5 py-2.5 text-sm leading-relaxed",
              isApplicant
                ? "bg-primary text-primary-foreground"
                : message.isError
                  ? "border border-destructive/30 bg-card text-destructive"
                  : "border border-border bg-card",
            )}
          >
            {isApplicant ? <p className="break-words whitespace-pre-wrap">{message.text}</p> : <AnswerBody text={message.text} />}
          </div>
        ) : null}
        {message.interrupted ? (
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs text-muted-foreground">This answer was interrupted.</p>
            {message.replyTo && onResend ? (
              <Button type="button" variant="outline" size="sm" onClick={() => onResend(message)}>
                <RotateCcw className="size-3" />
                Resend
              </Button>
            ) : null}
          </div>
        ) : null}
        {!isApplicant && !message.streaming ? <Sources sources={message.sources} /> : null}
        {!isApplicant ? <RatingControls message={message} /> : null}
      </div>
    </article>
  )
}
