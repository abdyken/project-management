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

export type AnswerSource = {
  faq_id: string | null
  question: string | null
  link: string
}

export type AssistantResponse = {
  answer: string
  sources: AnswerSource[]
  answer_id: string
  /** @deprecated v1, removed in Sprint 3: read `sources` */
  source_link: string | null
  /** @deprecated v1, removed in Sprint 3: read `sources` */
  faq_id: string | null
  similarity_score: number | null
}

export type StreamDone = {
  answer_id: string
  sources: AnswerSource[]
  faq_id: string | null
  source_link: string | null
  similarity_score: number | null
}

export type SuggestionsResponse = {
  suggestions: string[]
}

export type FeedbackRating = "up" | "down"

export type FeedbackReason = "wrong" | "outdated" | "unclear" | "other"

export type FeedbackRequest = {
  answer_id: string
  session_id: string
  rating: FeedbackRating
  reason?: FeedbackReason
}

export type ComparedProgram = Program & {
  documents_local: number
  documents_international: number
}

export type CompareResponse = {
  programs: ComparedProgram[]
}
