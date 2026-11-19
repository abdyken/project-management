import { useQuery } from "@tanstack/react-query"
import { request } from "@/api/client"

// Optional features switched on for this deployment (GET /api/features).
export type Features = { applicant_accounts: boolean; applications: boolean }

export function useFeatures() {
  return useQuery({
    queryKey: ["features"],
    queryFn: ({ signal }) => request<Features>("/api/features", { signal }),
    staleTime: 5 * 60_000,
    retry: false,
  })
}
