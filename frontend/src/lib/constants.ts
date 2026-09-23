import type { DegreeLevel } from "@/api/types"

export const ADMISSIONS_CONTACT = {
  name: "SDU Admissions Office",
  address: "Abylai Khan 1/1, 040900 Kaskelen, Almaty Region",
  phone: "+7 727 307 95 65",
  website: "https://sdu.edu.kz/en/admission-3-2/",
} as const

export const MESSAGE_MAX_LENGTH = 500
export const ASSISTANT_TIMEOUT_MS = 10_000

export const DEGREE_LABELS: Record<DegreeLevel, string> = {
  bachelor: "Bachelor",
  master: "Master",
  phd: "PhD",
}
