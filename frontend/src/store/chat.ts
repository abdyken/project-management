import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import { MESSAGE_MAX_LENGTH } from "@/lib/constants"

export type ChatRole = "applicant" | "assistant"

export type ChatMessage = {
  id: string
  role: ChatRole
  text: string
  sourceLink?: string | null
  createdAt: number
  isError?: boolean
}

export type ChatPosition = {
  x: number
  y: number
}

type ChatState = {
  open: boolean
  minimized: boolean
  position: ChatPosition | null
  fabPosition: ChatPosition | null
  sessionId: string
  messages: ChatMessage[]
  draft: string
  sending: boolean
  setOpen: (open: boolean) => void
  setMinimized: (minimized: boolean) => void
  setPosition: (position: ChatPosition) => void
  setFabPosition: (position: ChatPosition) => void
  setDraft: (draft: string) => void
  setSending: (sending: boolean) => void
  addMessage: (message: Omit<ChatMessage, "id" | "createdAt">) => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      open: false,
      minimized: false,
      position: null,
      fabPosition: null,
      sessionId: crypto.randomUUID(),
      messages: [],
      draft: "",
      sending: false,
      setOpen: (open) => set({ open, minimized: false }),
      setMinimized: (minimized) => set({ minimized, open: !minimized }),
      setPosition: (position) => set({ position }),
      setFabPosition: (fabPosition) => set({ fabPosition }),
      setDraft: (draft) => set({ draft: draft.slice(0, MESSAGE_MAX_LENGTH) }),
      setSending: (sending) => set({ sending }),
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, { ...message, id: crypto.randomUUID(), createdAt: Date.now() }],
        })),
    }),
    {
      name: "sdu-admissions-chat",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        sessionId: state.sessionId,
        messages: state.messages,
        draft: state.draft,
        minimized: state.minimized,
        position: state.position,
        fabPosition: state.fabPosition,
      }),
    },
  ),
)
