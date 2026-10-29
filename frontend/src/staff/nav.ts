import type { StaffKey } from "@/staff/i18n"

// Staff pages in the header and on the start page; each story adds its own entry
// (US20 FAQ, US22 inbox, US9 dashboard).
export const STAFF_NAV: { to: string; label: StaffKey }[] = [
  { to: "/staff/requests", label: "nav.requests" },
  { to: "/staff/inbox", label: "nav.inbox" },
  { to: "/staff/faq", label: "nav.faq" },
  { to: "/staff/programs", label: "nav.catalogue" },
  { to: "/staff/dashboard", label: "nav.dashboard" },
]
