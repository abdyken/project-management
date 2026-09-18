export const ADMISSIONS_CONTACT = {
  name: "SDU Admissions Office",
  address: "Abylai Khan 1/1, 040900 Kaskelen, Almaty Region",
  phone: "+7 727 307 95 65",
  phoneAlt: "+7 702 000 11 33",
  website: "https://sdu.edu.kz/en/admission-3-2/",
  email: "admissions@sdu.edu.kz",
} as const

export const FACULTIES = [
  "School of Engineering and Natural Sciences",
  "School of Education and Humanities",
  "School of Law and Social Sciences",
  "SDU Business School",
] as const

export const DEGREE_LEVELS = ["bachelor", "master"] as const
export const PROGRAM_LANGUAGES = ["en", "kk", "ru"] as const

export const MESSAGE_MAX_LENGTH = 500
export const ASSISTANT_TIMEOUT_MS = 10_000
export const SIMILARITY_THRESHOLD = 0.45

export const TIMEOUT_MESSAGE =
  "The assistant is not responding, please try again or contact the admissions office"

export const FALLBACK_MESSAGE = `I could not find this, please contact the admissions office. ${ADMISSIONS_CONTACT.name}, ${ADMISSIONS_CONTACT.address}. Tel. ${ADMISSIONS_CONTACT.phone}.`

export const LANGUAGE_LABELS: Record<(typeof PROGRAM_LANGUAGES)[number], string> = {
  en: "English",
  kk: "Kazakh",
  ru: "Russian",
}

export const DEGREE_LABELS: Record<(typeof DEGREE_LEVELS)[number], string> = {
  bachelor: "Bachelor",
  master: "Master",
}
