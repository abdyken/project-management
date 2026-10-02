import type { DegreeLevel } from "@/api/types"

export const ADMISSIONS_CONTACT = {
  name: "SDU Admissions Office",
  address: "Abylai Khan 1/1, 040900 Kaskelen, Almaty Region",
  phone: "+7 727 307 95 65",
  website: "https://sdu.edu.kz/en/admission-3-2/",
} as const

export const MESSAGE_MAX_LENGTH = 500
// Counted to the first streamed chunk. The API answers within 15 s (ASSISTANT_TIMEOUT_SECONDS);
// a Gemini answer (US10) takes about 6-8 s on the free tier.
export const ASSISTANT_TIMEOUT_MS = 20_000

export const DEGREE_LABELS: Record<DegreeLevel, string> = {
  bachelor: "Bachelor",
  master: "Master",
  phd: "PhD",
}
