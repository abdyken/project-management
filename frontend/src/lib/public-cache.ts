import type { QueryClient } from "@tanstack/react-query"
import { SAVED_PROGRAMS_KEY } from "@/applicant/session"

// Pages that show programme facts or documents; staff edits must refresh them.
const PROGRAM_DATA_KEYS = [["programs"], ["program"], ["checklist"], ["compare"], ["guidance"], ["staff", "guidance"], SAVED_PROGRAMS_KEY]

export function invalidateProgramData(queryClient: QueryClient) {
  for (const queryKey of PROGRAM_DATA_KEYS) void queryClient.invalidateQueries({ queryKey })
}
