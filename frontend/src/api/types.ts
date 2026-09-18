export type DegreeLevel = "bachelor" | "master"
export type ProgramLanguage = "en" | "kk" | "ru"
export type ApplicantType = "local" | "international"
export type DocumentFormat = "original" | "copy"

export type Program = {
  program_id: string
  title: string
  faculty: string
  degree_level: DegreeLevel
  language: ProgramLanguage
  tuition_fee: string
  application_deadline: string
  is_active: boolean
}

export type ProgramListResponse = {
  items: Program[]
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
  warning?: string
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
  similarity: number
}

export type HealthResponse = {
  status: "ok" | "degraded"
}
