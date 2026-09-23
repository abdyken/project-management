import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const deadlineFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
})

export function formatDeadline(value: string | null | undefined) {
  if (!value) return "Not published"
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
  if (!match) return value
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])))
  return deadlineFormat.format(date)
}

export function formatTuition(kzt: number | null, usd: number | null) {
  const parts = [kzt === null ? null : `${kzt.toLocaleString("en-US")} KZT`, usd === null ? null : `${usd} USD`]
  const known = parts.filter(Boolean)
  return known.length ? `${known.join(" · ")} per ECTS credit` : "Not published"
}
