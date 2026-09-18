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

type ChatState = {
  open: boolean
  sessionId: string
  messages: ChatMessage[]
  draft: string
  sending: boolean
  setOpen: (open: boolean) => void
  toggleOpen: () => void
  setDraft: (draft: string) => void
  setSending: (sending: boolean) => void
  addMessage: (message: Omit<ChatMessage, "id" | "createdAt"> & Partial<Pick<ChatMessage, "id" | "createdAt">>) => string
}

function createSessionId() {
  return crypto.randomUUID()
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      open: false,
      sessionId: createSessionId(),
      messages: [],
      draft: "",
      sending: false,
      setOpen: (open) => set({ open }),
      toggleOpen: () => set((state) => ({ open: !state.open })),
      setDraft: (draft) => set({ draft: draft.slice(0, MESSAGE_MAX_LENGTH) }),
      setSending: (sending) => set({ sending }),
      addMessage: (message) => {
        const id = message.id ?? crypto.randomUUID()
        set((state) => ({
          messages: [
            ...state.messages,
            {
              createdAt: Date.now(),
              ...message,
              id,
            },
          ],
        }))
        return id
      },
    }),
    {
      name: "sdu-admissions-chat",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        sessionId: state.sessionId,
        messages: state.messages,
        draft: state.draft,
      }),
    },
  ),
)
