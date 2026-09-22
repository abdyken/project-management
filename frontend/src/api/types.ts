export type DegreeLevel = "bachelor" | "master" | "phd"
export type ProgramLanguage = "English" | "Kazakh" | "Russian"
export type ApplicantType = "local" | "international"
export type DocumentFormat = "original" | "copy"

export type Program = {
  program_id: string
  title: string
  faculty: string
  degree_level: DegreeLevel
  language: ProgramLanguage
  tuition_fee: number | null
  application_deadline: string | null
  is_active: boolean
}

export type ProgramListResponse = {
  programs: Program[]
  total: number
}

export type ProgramQuery = {
  q?: string
  faculty?: string
  degree_level?: string
  language?: string
  force?: string
}

export type DocumentRequirement = {
  name: string
  format: DocumentFormat
  translation: boolean
  notarisation: boolean
  deadline: string
}

export type AdmissionsContact = {
  name: string
  address: string
  phone: string
  website: string
}

export type ChecklistResponse = {
  program_id: string
  applicant_type: ApplicantType
  items: DocumentRequirement[]
  warning?: string | null
  contact?: AdmissionsContact
}

export type AssistantRequest = {
  question: string
  session_id: string
}

export type AssistantResponse = {
  answer: string
  source_link: string | null
  faq_id: string | null
  similarity_score: number
}

export type HealthResponse = { status: "ok" | "unavailable"; database: "ok" | "unavailable" }
