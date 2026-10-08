import { ArrowUpRight, RotateCcw, ThumbsDown, ThumbsUp } from "lucide-react"
import { useState } from "react"
import { sendFeedback } from "@/api/assistant"
import type { FeedbackReason } from "@/api/types"
import { AnswerBody } from "@/components/chat/AnswerBody"
import { Button } from "@/components/ui/button"
import { useI18n, type I18n } from "@/i18n"
import { cn } from "@/lib/utils"
import { useChatStore, type ChatMessage as ChatMessageType, type ChatSource } from "@/store/chat"

const REASONS: FeedbackReason[] = ["wrong", "outdated", "unclear", "other"]

function sourceLabel(source: ChatSource, index: number, total: number, t: I18n["t"]) {
  if (source.question) return source.question
  return total > 1 ? t("chat.sourceN", { n: index + 1 }) : t("chat.source")
}

function Sources({ sources }: { sources: ChatSource[] }) {
  const { t } = useI18n()
  const visible = sources.filter((source) => source.link || source.question)
  if (visible.length === 0) return null

  return (
    <ul className="space-y-1">
      {visible.map((source, index) => {
        const label = sourceLabel(source, index, visible.length, t)
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
  const { t } = useI18n()
  const rateMessage = useChatStore((state) => state.rateMessage)
  const sessionId = useChatStore((state) => state.sessionId)
  const [picking, setPicking] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(false)
  if (!message.answerId || message.isError || message.interrupted || message.streaming) return null

  async function commit(rating: "up" | "down", reason: FeedbackReason | null) {
    if (!message.answerId || message.rating || sending) return
    setSending(true)
    setError(false)
    try {
      await sendFeedback({
        answer_id: message.answerId,
        session_id: sessionId,
        rating,
        ...(reason ? { reason } : {}),
      })
      rateMessage(message.id, { rating, reason })
      setPicking(false)
    } catch {
      setError(true)
    } finally {
      setSending(false)
    }
  }

  const selected = message.rating

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        <button
          type="button"
          aria-label={t("chat.helpful")}
          aria-pressed={selected?.rating === "up"}
          disabled={Boolean(selected) || sending}
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
          aria-label={t("chat.notHelpful")}
          aria-pressed={selected?.rating === "down"}
          disabled={Boolean(selected) || sending}
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
            {t(`chat.reason.${selected.reason}`)}
          </span>
        ) : null}
      </div>
      {picking && !selected ? (
        <div className="flex flex-wrap gap-1.5">
          {REASONS.map((reason) => (
            <button
              key={reason}
              type="button"
              disabled={sending}
              onClick={() => commit("down", reason)}
              className="rounded-full border border-border px-2.5 py-1 text-[11px] text-muted-foreground hover:bg-secondary hover:text-foreground"
            >
              {t(`chat.reason.${reason}`)}
            </button>
          ))}
          <button
            type="button"
            disabled={sending}
            onClick={() => commit("down", null)}
            className="rounded-full px-2.5 py-1 text-[11px] text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
          >
            {t("chat.skipReason")}
          </button>
        </div>
      ) : null}
      {error ? <p className="text-[11px] text-destructive">{t("chat.ratingError")}</p> : null}
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
  const { t } = useI18n()
  const isApplicant = message.role === "applicant"
  if (message.streaming && !message.text) return null

  return (
    <article className={cn("flex min-w-0", isApplicant ? "justify-end" : "justify-start")}>
      <div className={cn("min-w-0 space-y-1.5", isApplicant ? "max-w-[85%] text-right" : "max-w-full text-left")}>
        <p className="text-[10px] tracking-[0.14em] text-muted-foreground uppercase">
          {isApplicant ? t("chat.you") : t("chat.title")}
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
        {message.interrupted || (message.isError && message.replyTo) ? (
          <div className="flex flex-wrap items-center gap-2">
            {message.interrupted ? <p className="text-xs text-muted-foreground">{t("chat.interrupted")}</p> : null}
            {message.replyTo && onResend ? (
              <Button type="button" variant="outline" size="sm" onClick={() => onResend(message)}>
                <RotateCcw className="size-3" />
                {t("chat.resend")}
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
