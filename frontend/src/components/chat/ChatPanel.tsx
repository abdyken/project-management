import { useEffect, useRef, type FormEvent, type KeyboardEvent } from "react"
import { askAssistant } from "@/api/assistant"
import { chatErrorMessage } from "@/api/errors"
import { Button } from "@/components/ui/button"
import { ChatMessage } from "@/components/chat/ChatMessage"
import { TypingIndicator } from "@/components/chat/TypingIndicator"
import { MESSAGE_MAX_LENGTH } from "@/lib/constants"
import { useChatStore } from "@/store/chat"

export function ChatPanel({ autoFocus = false }: { autoFocus?: boolean }) {
  const messages = useChatStore((state) => state.messages)
  const draft = useChatStore((state) => state.draft)
  const sending = useChatStore((state) => state.sending)
  const sessionId = useChatStore((state) => state.sessionId)
  const setDraft = useChatStore((state) => state.setDraft)
  const setSending = useChatStore((state) => state.setSending)
  const addMessage = useChatStore((state) => state.addMessage)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const canSend = draft.trim().length > 0 && draft.trim().length <= MESSAGE_MAX_LENGTH && !sending

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, sending])

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus()
  }, [autoFocus])

  async function submitQuestion() {
    const question = draft.trim()
    if (!question || sending) return

    addMessage({ role: "applicant", text: question })
    setDraft("")
    setSending(true)

    try {
      const response = await askAssistant(question, sessionId)
      addMessage({
        role: "assistant",
        text: response.answer,
        sourceLink: response.source_link,
      })
    } catch (error) {
      if (!useChatStore.getState().draft.trim()) setDraft(question)
      addMessage({ role: "assistant", text: chatErrorMessage(error), isError: true })
    } finally {
      setSending(false)
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submitQuestion()
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      void submitQuestion()
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
          <p className="text-sm leading-relaxed text-muted-foreground">
            Ask about deadlines, UNT, English requirements, or which documents you need for a program — for
            example, “Which documents do I need for Computer Science as an international applicant?”
          </p>
        ) : (
          messages.map((message) => <ChatMessage key={message.id} message={message} />)
        )}
        {sending ? <TypingIndicator /> : null}
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
