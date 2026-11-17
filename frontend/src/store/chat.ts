import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import type { AnswerSource, FeedbackRating, FeedbackReason } from "@/api/types"
import type { MessageKey } from "@/i18n/messages"
import { abortRequest } from "@/lib/chat-request"
import { MESSAGE_MAX_LENGTH } from "@/lib/constants"
import { randomId } from "@/lib/utils"

export type ChatRole = "applicant" | "assistant"

export type ChatSource = {
  faqId: string | null
  question: string | null
  link: string | null
  title?: string | null
}

export type ChatRating = {
  rating: FeedbackRating
  reason: FeedbackReason | null
}

export type ChatMessage = {
  id: string
  role: ChatRole
  text: string
  sources: ChatSource[]
  answerId?: string | null
  replyTo?: string
  rating?: ChatRating | null
  createdAt: number
  isError?: boolean
  errorKey?: MessageKey
  interrupted?: boolean
  streaming?: boolean
}

type ChatState = {
  open: boolean
  minimized: boolean
  sessionId: string
  messages: ChatMessage[]
  suggestions: string[]
  draft: string
  sending: boolean
  setOpen: (open: boolean) => void
  setMinimized: (minimized: boolean) => void
  setDraft: (draft: string) => void
  setSending: (sending: boolean) => void
  setSuggestions: (suggestions: string[]) => void
  addMessage: (message: Omit<ChatMessage, "id" | "createdAt" | "sources"> & { sources?: ChatSource[] }) => string
  appendAssistantText: (id: string, text: string) => void
  completeAssistantMessage: (
    id: string,
    patch: { text?: string; sources: ChatSource[]; answerId: string },
  ) => void
  interruptMessage: (id: string) => void
  failMessage: (id: string, errorKey: MessageKey) => void
  removeMessage: (id: string) => void
  rateMessage: (id: string, rating: ChatRating) => void
  startNewConversation: () => void
}

function settleStreaming(message: ChatMessage): ChatMessage {
  if (!message.streaming) return message
  return { ...message, streaming: false, interrupted: true }
}

export function sourcesFromApi(sources: AnswerSource[] | null | undefined): ChatSource[] {
  return (sources ?? [])
    .map((source) => ({
      faqId: source.faq_id ?? null,
      question: source.question ?? null,
      link: source.link ?? null,
      title: source.title ?? null,
    }))
    .filter((source) => source.link || source.question || source.faqId)
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      open: false,
      minimized: false,
      sessionId: randomId(),
      messages: [],
      suggestions: [],
      draft: "",
      sending: false,
      setOpen: (open) => {
        if (!open) abortRequest("close")
        set({ open, minimized: false })
      },
      setMinimized: (minimized) => set({ minimized, open: !minimized }),
      setDraft: (draft) => set({ draft: draft.slice(0, MESSAGE_MAX_LENGTH) }),
      setSending: (sending) => set({ sending }),
      setSuggestions: (suggestions) => set({ suggestions }),
      addMessage: (message) => {
        const id = randomId()
        set((state) => ({
          messages: [...state.messages, { sources: [], ...message, id, createdAt: Date.now() }],
        }))
        return id
      },
      appendAssistantText: (id, text) =>
        set((state) => ({
          messages: state.messages.map((message) =>
            message.id === id ? { ...message, text: message.text + text } : message,
          ),
        })),
      completeAssistantMessage: (id, patch) =>
        set((state) => ({
          messages: state.messages.map((message) =>
            message.id === id ? { ...message, ...patch, streaming: false, interrupted: false } : message,
          ),
        })),
      interruptMessage: (id) =>
        set((state) => ({
          messages: state.messages.map((message) => {
            if (message.id !== id || !message.streaming) return message
            return { ...message, streaming: false, interrupted: true }
          }),
        })),
      failMessage: (id, errorKey) =>
        set((state) => ({
          messages: state.messages.map((message) =>
            message.id === id ? { ...message, text: "", errorKey, streaming: false, isError: true, interrupted: false } : message,
          ),
        })),
      removeMessage: (id) =>
        set((state) => ({ messages: state.messages.filter((message) => message.id !== id) })),
      rateMessage: (id, rating) =>
        set((state) => ({
          messages: state.messages.map((message) =>
            message.id === id && !message.rating ? { ...message, rating } : message,
          ),
        })),
      startNewConversation: () => {
        abortRequest("new")
        set({
          sessionId: randomId(),
          messages: [],
          suggestions: [],
          draft: "",
          sending: false,
        })
      },
    }),
    {
      name: "sdu-admissions-chat",
      version: 2,
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        sessionId: state.sessionId,
        messages: state.messages.map(settleStreaming),
        suggestions: state.suggestions,
        draft: state.draft,
        minimized: state.minimized,
      }),
    },
  ),
)
