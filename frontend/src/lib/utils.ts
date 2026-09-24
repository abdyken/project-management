import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function randomId() {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID()
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, "0")).join("")
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

export function formatTuitionLocal(kzt: number | null) {
  return kzt === null ? "Not published" : `${kzt.toLocaleString("en-US")} KZT per ECTS credit`
}

export function formatTuitionInternational(usd: number | null) {
  return usd === null ? "Not published" : `${usd} USD per ECTS credit`
}
