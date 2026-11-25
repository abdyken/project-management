// Whether a catalogue deadline (ISO date) is still ahead, already passed, or not published.
// "Today" is the calendar day in Almaty, where the admissions office works; the deadline day
// itself still counts as open.
export type DeadlineStatus = "upcoming" | "closed" | "unpublished"

export function almatyToday(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Almaty", year: "numeric", month: "2-digit", day: "2-digit" }).format(now)
}

export function deadlineStatus(value: string | null | undefined, today: string = almatyToday()): DeadlineStatus {
  const match = value ? /^(\d{4}-\d{2}-\d{2})/.exec(value) : null
  if (!match) return "unpublished"
  return match[1] < today ? "closed" : "upcoming"
}
