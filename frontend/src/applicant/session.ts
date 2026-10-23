import { useQuery } from "@tanstack/react-query"
import { getApplicant } from "@/api/applicant"

export const APPLICANT_KEY = ["applicant"] as const
export const APPLICANT_ME_KEY = [...APPLICANT_KEY, "me"] as const
export const SAVED_PROGRAMS_KEY = [...APPLICANT_KEY, "programs"] as const

export function useApplicant() {
  return useQuery({
    queryKey: APPLICANT_ME_KEY,
    queryFn: ({ signal }) => getApplicant(signal),
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: true,
  })
}
