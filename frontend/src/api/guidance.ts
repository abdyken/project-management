import { request } from "@/api/client"
import type { Program } from "@/api/types"
export const SUBJECT_PAIRS = [
  "math_informatics",
  "math_physics",
  "chemistry_biology",
  "biology_geography",
  "law_history",
  "math_geography",
  "english_history",
  "russian_literature",
  "history_geography",
] as const

export type Evidence = {
  url: string
  quote: string
  academic_year: string
  checked_on: string
  status: "confirmed" | "pending" | "conflict"
}
export type Scope = {
  applicant_type?: "local" | "international" | null
  education_route?: "school" | "college" | "bachelor" | "master" | null
  track?: "scientific" | "profile" | null
  admission_basis?: "paid" | "grant" | null
}
export type Metric =
  | "unt_total"
  | "phd_total"
  | "toefl_ibt"
  | "toefl_pbt"
  | "toeic"
  | "duolingo"
  | "work_months"
  | "kaztest"
  | "ct_total"
  | "gpa"
  | "ielts_overall"
  | "ielts_component_min"
  | "sdu_english"
  | "interview"
  | "special_exam"
  | "creative_exam"
  | "subject_pair"
export type Scores = Partial<Record<Metric, number | boolean | string | null>>
export type Condition = {
  metric: Metric
  minimum?: number | null
  equals?: string | boolean | null
}
export type Rule = Scope & {
  key: string
  alternatives: Condition[][]
  evidence: Evidence
}
export type Guidance = {
  rules: Rule[]
  complete_for: Scope[]
  total_ects?: number | null
  credits_evidence?: Evidence | null
  mde_kzt?: number | null
  mde_usd?: number | null
  mde_evidence?: Evidence | null
  language_tariffs: {
    language_group: string
    kzt: number | null
    usd: number | null
    evidence: Evidence
  }[]
  sources: Record<string, Evidence>
  gaps: string[]
}
export type Profile = {
  applicant_type: "local" | "international"
  education_route: "school" | "college" | "bachelor" | "master"
  track: "scientific" | "profile" | null
  admission_basis: "paid" | "grant"
  scores: Scores
  language: "en" | "ru" | "kk"
}
export type Eligibility = {
  program_id: string
  status: "meets_published_requirements" | "does_not_meet" | "insufficient_data"
  checks: (Rule & { status: "pass" | "fail" | "unknown" })[]
  gaps: string[]
  admission_guaranteed: false
}
export type CostInput = {
  currency: "KZT" | "USD"
  professional_ects: number
  mde_ects: number
  language_group?: string
  language: Profile["language"]
}
export type Cost = {
  currency: string
  components: {
    component: string
    ects: number
    rate: number | null
    amount: number | null
    evidence: Evidence | null
  }[]
  known_subtotal: number
  estimated_total: number | null
  gaps: string[]
  assumptions: string[]
  published_total_ects: number | null
  credits_evidence: Evidence | null
}
export type Recommendations = {
  items: {
    program: Program
    eligibility: Eligibility
    reasons: string[]
    gaps: string[]
  }[]
  explanation_mode: string
}
export type FundingItem = {
  faq_id: string
  title: string
  text: string
  source_url: string
  last_checked: string
  content_language: string
  translation_missing: boolean
  status: string
}
export type AdmissionRequest = {
  id: number
  question: string
  language: string
  answer: string | null
  created_at: string
  answered_at: string | null
  notification_sent_at: string | null
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 35000,
  })
export const checkEligibility = (body: Profile & { program_id: string }) =>
  post<Eligibility>("/api/eligibility/check", body)
export const recommendPrograms = (
  body: Profile & {
    degree_level: string
    interests: string[]
    teaching_language?: string
  },
) => post<Recommendations>("/api/recommendations", body)
export const estimateCost = (id: string, body: CostInput) =>
  post<Cost>(`/api/programs/${encodeURIComponent(id)}/cost-estimate`, body)
export const getGuidance = (id: string, staff = false, signal?: AbortSignal) =>
  request<Guidance>(
    `/api/${staff ? "staff/" : ""}programs/${encodeURIComponent(id)}/guidance`,
    { signal },
  )
export const saveGuidance = (id: string, body: Guidance) =>
  request<Guidance>(`/api/staff/programs/${encodeURIComponent(id)}/guidance`, {
    method: "PUT",
    body: JSON.stringify(body),
  })
export const getFunding = (
  language: string,
  degree?: string,
  applicant?: string,
  signal?: AbortSignal,
) =>
  request<{ items: FundingItem[] }>("/api/funding", {
    query: {
      language,
      degree_level: degree || undefined,
      applicant_type: applicant || undefined,
    },
    signal,
  })
export const listRequests = (
  staff = false,
  status = "all",
  offset = 0,
  signal?: AbortSignal,
) =>
  request<{ items: AdmissionRequest[]; total: number }>(
    `/api/${staff ? "staff" : "applicant"}/requests`,
    { query: { ...(staff ? { status } : {}), offset: String(offset) }, signal },
  )
export const sendRequest = (
  question: string,
  language: Profile["language"],
  client_key: string,
) =>
  post<AdmissionRequest>("/api/applicant/requests", {
    question,
    language,
    client_key,
  })
export const answerRequest = (id: number, answer: string) =>
  post<AdmissionRequest>(`/api/staff/requests/${id}/answer`, { answer })
