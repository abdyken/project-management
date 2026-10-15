import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { isApiError } from "@/api/errors"
import { getMe, login, logout } from "@/api/staff"

export const STAFF_ME_KEY = ["staff", "me"] as const

export function isNotLoggedIn(error: unknown) {
  return isApiError(error) && error.status === 401
}

export function useStaffMe() {
  return useQuery({ queryKey: STAFF_ME_KEY, queryFn: ({ signal }) => getMe(signal) })
}

export function useStaffLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) => login(email, password),
    onSuccess: (user) => queryClient.setQueryData(STAFF_ME_KEY, user),
  })
}

export function useStaffLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: logout,
    // Drop every cached staff response, so the back button cannot show staff data.
    onSettled: () => queryClient.removeQueries({ queryKey: ["staff"] }),
  })
}
