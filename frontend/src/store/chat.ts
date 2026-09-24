import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import { MESSAGE_MAX_LENGTH } from "@/lib/constants"
import { randomId } from "@/lib/utils"

export type ChatRole = "applicant" | "assistant"

export type ChatMessage = {
  id: string
  role: ChatRole
  text: string
  sourceLink?: string | null
  createdAt: number
  isError?: boolean
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
  draft: string
  sending: boolean
  setOpen: (open: boolean) => void
  setMinimized: (minimized: boolean) => void
  setPanelOffset: (offset: CornerOffset) => void
  setFabOffset: (offset: CornerOffset) => void
  setDraft: (draft: string) => void
  setSending: (sending: boolean) => void
  addMessage: (message: Omit<ChatMessage, "id" | "createdAt">) => void
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
      draft: "",
      sending: false,
      setOpen: (open) => set({ open, minimized: false }),
      setMinimized: (minimized) => set({ minimized, open: !minimized }),
      setPanelOffset: (panelOffset) => set({ panelOffset }),
      setFabOffset: (fabOffset) => set({ fabOffset }),
      setDraft: (draft) => set({ draft: draft.slice(0, MESSAGE_MAX_LENGTH) }),
      setSending: (sending) => set({ sending }),
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, { ...message, id: randomId(), createdAt: Date.now() }],
        })),
    }),
    {
      name: "sdu-admissions-chat",
      version: 1,
      storage: createJSONStorage(() => sessionStorage),
      migrate: (persisted) => {
        const { sessionId, messages, draft } = persisted as Partial<ChatState>
        return { sessionId, messages, draft } as ChatState
      },
      partialize: (state) => ({
        sessionId: state.sessionId,
        messages: state.messages,
        draft: state.draft,
        minimized: state.minimized,
        panelOffset: state.panelOffset,
        fabOffset: state.fabOffset,
      }),
    },
  ),
)
