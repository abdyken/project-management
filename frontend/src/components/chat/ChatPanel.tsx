import { useEffect, useRef, type FormEvent, type KeyboardEvent } from "react"
import { getSuggestions, streamAssistant } from "@/api/assistant"
import { chatErrorMessage } from "@/api/errors"
import { Button } from "@/components/ui/button"
import { ChatMessage } from "@/components/chat/ChatMessage"
import { TypingIndicator } from "@/components/chat/TypingIndicator"
import { abortReason, finishRequest, isCurrent, nextRequest } from "@/lib/chat-request"
import { MESSAGE_MAX_LENGTH } from "@/lib/constants"
import { sourcesFromApi, useChatStore, type ChatMessage as ChatMessageType } from "@/store/chat"

export function ChatPanel({ autoFocus = false }: { autoFocus?: boolean }) {
  const messages = useChatStore((state) => state.messages)
  const suggestions = useChatStore((state) => state.suggestions)
  const draft = useChatStore((state) => state.draft)
  const sending = useChatStore((state) => state.sending)
  const sessionId = useChatStore((state) => state.sessionId)
  const setDraft = useChatStore((state) => state.setDraft)
  const setSending = useChatStore((state) => state.setSending)
  const setSuggestions = useChatStore((state) => state.setSuggestions)
  const addMessage = useChatStore((state) => state.addMessage)
  const appendAssistantText = useChatStore((state) => state.appendAssistantText)
  const completeAssistantMessage = useChatStore((state) => state.completeAssistantMessage)
  const interruptMessage = useChatStore((state) => state.interruptMessage)
  const failMessage = useChatStore((state) => state.failMessage)
  const removeMessage = useChatStore((state) => state.removeMessage)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const canSend = draft.trim().length > 0 && draft.trim().length <= MESSAGE_MAX_LENGTH && !sending
  const answered = messages.some((message) => message.role === "assistant" && message.answerId)
  const visibleSuggestions = suggestions.slice(0, answered ? 3 : 4)
  const waitingForFirstChunk = sending && messages.some((message) => message.streaming && !message.text)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, sending, visibleSuggestions.length])

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus()
  }, [autoFocus])

  useEffect(() => {
    const controller = new AbortController()
    getSuggestions(sessionId, controller.signal)
      .then((next) => {
        if (useChatStore.getState().sessionId === sessionId) setSuggestions(next)
      })
      .catch(() => {
        if (!controller.signal.aborted && useChatStore.getState().sessionId === sessionId) setSuggestions([])
      })
    return () => controller.abort()
  }, [sessionId, answered, setSuggestions])

  async function ask(question: string, options?: { keepUserMessage?: boolean }) {
    if (!question || useChatStore.getState().sending) return

    if (!options?.keepUserMessage) {
      addMessage({ role: "applicant", text: question })
      setDraft("")
    }

    const assistantId = addMessage({ role: "assistant", text: "", streaming: true, replyTo: question })
    setSending(true)
    const { signal, token } = nextRequest()

    try {
      const outcome = await streamAssistant(question, sessionId, signal, {
        onChunk: (text) => {
          if (isCurrent(token)) appendAssistantText(assistantId, text)
        },
        onDone: (done) => {
          if (!isCurrent(token)) return
          completeAssistantMessage(assistantId, {
            sources: sourcesFromApi(done.sources, done.source_link),
            sourceLink: done.source_link,
            answerId: done.answer_id,
          })
        },
      })
      if (!isCurrent(token)) return
      if (outcome === "interrupted" || outcome === "aborted") interruptMessage(assistantId)
    } catch (error) {
      if (!isCurrent(token) || abortReason() === "new") return
      if (!useChatStore.getState().draft.trim()) setDraft(question)
      failMessage(assistantId, chatErrorMessage(error))
    } finally {
      finishRequest(token)
      if (isCurrent(token)) setSending(false)
    }
  }

  function submitQuestion() {
    const question = draft.trim()
    if (!question || sending) return
    void ask(question)
  }

  function onResend(message: ChatMessageType) {
    if (!message.replyTo || sending) return
    removeMessage(message.id)
    void ask(message.replyTo, { keepUserMessage: true })
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    submitQuestion()
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      submitQuestion()
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div
        ref={listRef}
        role="log"
        aria-live="polite"
        aria-label="Conversation"
        className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4"
      >
        {messages.length === 0 ? (
          <p className="text-sm leading-relaxed break-words text-muted-foreground">
            Ask about deadlines, UNT, English requirements, or which documents you need for a program — for
            example, “Which documents do I need for Computer Science as an international applicant?”
          </p>
        ) : (
          messages.map((message) => <ChatMessage key={message.id} message={message} onResend={onResend} />)
        )}
        {waitingForFirstChunk ? <TypingIndicator /> : null}
        {!sending && visibleSuggestions.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {visibleSuggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => void ask(suggestion)}
                className="max-w-full rounded-full border border-border px-3 py-1.5 text-left text-xs break-words text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                {suggestion}
              </button>
            ))}
          </div>
        ) : null}
      </div>
      <form onSubmit={onSubmit} className="border-t border-border p-3 transition-colors focus-within:bg-card">
        <textarea
          ref={inputRef}
          aria-label="Your question"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
          maxLength={MESSAGE_MAX_LENGTH}
          rows={3}
          placeholder="Write a question"
          className="w-full resize-none bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
        <p className="mt-2 text-[11px] text-muted-foreground">Do not enter personal data</p>
        <div className="mt-2 flex items-center justify-between gap-3">
          <span className="text-[11px] text-muted-foreground">
            {draft.length}/{MESSAGE_MAX_LENGTH}
          </span>
          <Button type="submit" size="sm" disabled={!canSend}>
            Send
          </Button>
        </div>
      </form>
    </div>
  )
}
