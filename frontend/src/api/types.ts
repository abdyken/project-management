export type DegreeLevel = "bachelor" | "master" | "phd"
export type ApplicantType = "local" | "international"
export type DocumentFormat = "original" | "copy"

export type Program = {
  program_id: string
  title: string
  faculty: string
  degree_level: DegreeLevel
  language: string
  tuition_per_ects_kzt: number | null
  tuition_per_ects_usd: number | null
  deadline_local: string | null
  deadline_international: string | null
  source_url: string | null
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
}

export type DocumentRequirement = {
  name: string
  format: DocumentFormat
  translation: boolean
  notarisation: boolean
  deadline: string
}

export type ChecklistResponse = {
  program_id: string
  applicant_type: ApplicantType
  items: DocumentRequirement[]
  warning: string | null
  contact: string | null
}

export type AssistantResponse = {
  answer: string
  source_link: string | null
  faq_id: string | null
  similarity_score: number | null
}
