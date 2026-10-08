import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"

export const MAX_COMPARED = 3

type CompareState = {
  ids: string[]
  toggle: (id: string) => void
  remove: (id: string) => void
  clear: () => void
}

export const useCompareStore = create<CompareState>()(
  persist(
    (set) => ({
      ids: [],
      toggle: (id) =>
        set((state) => {
          if (state.ids.includes(id)) return { ids: state.ids.filter((current) => current !== id) }
          if (state.ids.length >= MAX_COMPARED) return state
          return { ids: [...state.ids, id] }
        }),
      remove: (id) => set((state) => ({ ids: state.ids.filter((current) => current !== id) })),
      clear: () => set({ ids: [] }),
    }),
    { name: "sdu-admissions-compare", storage: createJSONStorage(() => sessionStorage) },
  ),
)
