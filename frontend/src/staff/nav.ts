import { useFeatures } from "@/api/features"
import type { StaffKey } from "@/staff/i18n"

// Staff pages in the header and on the start page; each story adds its own entry
// (US20 FAQ, US22 inbox, US9 dashboard).
export const STAFF_NAV: { to: string; label: StaffKey }[] = [
  { to: "/staff/applications", label: "nav.applications" },
  { to: "/staff/requests", label: "nav.requests" },
  { to: "/staff/inbox", label: "nav.inbox" },
  { to: "/staff/faq", label: "nav.faq" },
  { to: "/staff/programs", label: "nav.catalogue" },
  { to: "/staff/dashboard", label: "nav.dashboard" },
]

// Online applications (Sprint 7) stay out of the menu while the feature is switched off.
export function useStaffNav() {
  const features = useFeatures()
  return STAFF_NAV.filter((item) => item.to !== "/staff/applications" || features.data?.applications === true)
}
