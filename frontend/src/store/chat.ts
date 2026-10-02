import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import type { AnswerSource, FeedbackRating, FeedbackReason } from "@/api/types"
import { abortRequest } from "@/lib/chat-request"
import { MESSAGE_MAX_LENGTH } from "@/lib/constants"
import { randomId } from "@/lib/utils"

export type ChatRole = "applicant" | "assistant"

export type ChatSource = {
  faqId: string | null
  question: string | null
  link: string | null
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
  sourceLink?: string | null
  answerId?: string | null
  replyTo?: string
  rating?: ChatRating | null
  createdAt: number
  isError?: boolean
  interrupted?: boolean
  streaming?: boolean
}

export type CornerOffset = {
  right: number
  bottom: number
}

type ChatState = {
  open: boolean
  minimized: boolean
  panelOffset: CornerOffset | null
  fabOffset: CornerOffset | null
  sessionId: string
  messages: ChatMessage[]
  suggestions: string[]
  draft: string
  sending: boolean
  setOpen: (open: boolean) => void
  setMinimized: (minimized: boolean) => void
  setPanelOffset: (offset: CornerOffset) => void
  setFabOffset: (offset: CornerOffset) => void
  setDraft: (draft: string) => void
  setSending: (sending: boolean) => void
  setSuggestions: (suggestions: string[]) => void
  addMessage: (message: Omit<ChatMessage, "id" | "createdAt" | "sources"> & { sources?: ChatSource[] }) => string
  appendAssistantText: (id: string, text: string) => void
  completeAssistantMessage: (
    id: string,
    patch: { text?: string; sources: ChatSource[]; sourceLink: string | null; answerId: string },
  ) => void
  interruptMessage: (id: string) => void
  failMessage: (id: string, text: string) => void
  removeMessage: (id: string) => void
  rateMessage: (id: string, rating: ChatRating) => void
  startNewConversation: () => void
}

function settleStreaming(message: ChatMessage): ChatMessage {
  if (!message.streaming) return message
  return { ...message, streaming: false, interrupted: true }
}

export function sourcesFromApi(sources: AnswerSource[] | null | undefined, sourceLink: string | null): ChatSource[] {
  const mapped = (sources ?? [])
    .map((source) => ({
      faqId: source.faq_id ?? null,
      question: source.question ?? null,
      link: source.link ?? null,
    }))
    .filter((source) => source.link || source.question || source.faqId)
  if (mapped.length > 0) return mapped
  if (sourceLink) return [{ faqId: null, question: null, link: sourceLink }]
  return []
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      open: false,
      minimized: false,
      panelOffset: null,
      fabOffset: null,
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
      setPanelOffset: (panelOffset) => set({ panelOffset }),
      setFabOffset: (fabOffset) => set({ fabOffset }),
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
      failMessage: (id, text) =>
        set((state) => ({
          messages: state.messages.map((message) =>
            message.id === id ? { ...message, text, streaming: false, isError: true, interrupted: false } : message,
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
      migrate: (persisted) => {
        const stored = persisted as Partial<ChatState>
        return {
          sessionId: stored.sessionId,
          messages: (stored.messages ?? []).map((message) => {
            const settled = settleStreaming({
              ...message,
              sources:
                message.sources?.length
                  ? message.sources
                  : message.sourceLink
                    ? [{ faqId: null, question: null, link: message.sourceLink }]
                    : [],
            })
            return settled
          }),
          suggestions: stored.suggestions ?? [],
          draft: stored.draft,
          minimized: stored.minimized,
          panelOffset: stored.panelOffset,
          fabOffset: stored.fabOffset,
        } as ChatState
      },
      partialize: (state) => ({
        sessionId: state.sessionId,
        messages: state.messages.map(settleStreaming),
        suggestions: state.suggestions,
        draft: state.draft,
        minimized: state.minimized,
        panelOffset: state.panelOffset,
        fabOffset: state.fabOffset,
      }),
    },
  ),
)
