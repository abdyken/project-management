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
  hidden: boolean
  minimized: boolean
  position: ChatPosition | null
  fabPosition: ChatPosition | null
  sessionId: string
  messages: ChatMessage[]
  draft: string
  sending: boolean
  setOpen: (open: boolean) => void
  toggleOpen: () => void
  hide: () => void
  setMinimized: (minimized: boolean) => void
  setPosition: (position: ChatPosition) => void
  setFabPosition: (position: ChatPosition) => void
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
      hidden: false,
      minimized: false,
      position: null,
      fabPosition: null,
      sessionId: createSessionId(),
      messages: [],
      draft: "",
      sending: false,
      setOpen: (open) =>
        set((state) => ({
          open,
          hidden: open ? false : state.hidden,
          minimized: open ? false : state.minimized,
        })),
      toggleOpen: () =>
        set((state) => {
          if (state.hidden) {
            return { hidden: false, open: true, minimized: false }
          }
          if (state.minimized) {
            return { open: true, minimized: false }
          }
          return { open: !state.open }
        }),
      hide: () => set({ hidden: true, open: false, minimized: false }),
      setMinimized: (minimized) => set({ minimized, open: !minimized, hidden: false }),
      setPosition: (position) => set({ position }),
      setFabPosition: (fabPosition) => set({ fabPosition }),
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
        hidden: state.hidden,
        minimized: state.minimized,
        position: state.position,
        fabPosition: state.fabPosition,
      }),
    },
  ),
)
