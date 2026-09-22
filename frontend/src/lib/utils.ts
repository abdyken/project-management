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
  if (!value) return "Not specified"
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
  if (!match) return value
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])))
  return deadlineFormat.format(date)
}

export function formatTuition(fee: number | string | null | undefined) {
  if (fee === null || fee === undefined || fee === "") return null
  const amount = typeof fee === "number" ? fee : Number(fee)
  if (Number.isNaN(amount)) return null
  return amount.toLocaleString("en-US")
}
