import { request } from "@/api/client"

// Staff API (US19), contract: backend/docs/api/staff.md. The session is an HttpOnly
// cookie on /api/staff, sent by the browser on these same-origin requests.

export type StaffRole = "admin" | "officer"

export type StaffUser = {
  id: number
  email: string
  name: string
  role: StaffRole
}

export function login(email: string, password: string) {
  return request<StaffUser>("/api/staff/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  })
}

export function logout() {
  return request<void>("/api/staff/logout", { method: "POST" })
}

export function getMe(signal?: AbortSignal) {
  return request<StaffUser>("/api/staff/me", { signal })
}

// FAQ management (US20)

export type FaqStatus = "draft" | "published" | "retired"
export type FaqLanguage = "en" | "ru" | "kk"

export type FaqItemInput = {
  category: string
  question: string
  answer: string
  source_link: string
  evidence: string | null
  question_ru: string | null
  answer_ru: string | null
  source_link_ru: string | null
  evidence_ru: string | null
  question_kk: string | null
  answer_kk: string | null
  source_link_kk: string | null
  evidence_kk: string | null
  degrees: ("bachelor" | "master" | "phd")[]
  applicant_types: ("local" | "international")[]
}

export type FaqItem = FaqItemInput & {
  faq_id: string
  status: FaqStatus
  last_update: string
  updated_at: string
  updated_by: string | null
}

export type FaqListItem = {
  faq_id: string
  status: FaqStatus
  category: string
  question: string
  languages: FaqLanguage[]
  last_update: string
  updated_at: string
  updated_by: string | null
}

export type FaqListResponse = { items: FaqListItem[]; categories: string[] }

export function listFaq(params: { q?: string; status?: FaqStatus; category?: string }, signal?: AbortSignal) {
  return request<FaqListResponse>("/api/staff/faq", { query: params, signal })
}

export function getFaq(faqId: string, signal?: AbortSignal) {
  return request<FaqItem>(`/api/staff/faq/${encodeURIComponent(faqId)}`, { signal })
}

export function createFaq(item: FaqItemInput) {
  return request<FaqItem>("/api/staff/faq", { method: "POST", body: JSON.stringify(item) })
}

export function updateFaq(faqId: string, item: FaqItemInput) {
  return request<FaqItem>(`/api/staff/faq/${encodeURIComponent(faqId)}`, { method: "PUT", body: JSON.stringify(item) })
}

export function setFaqStatus(faqId: string, action: "publish" | "retire" | "unpublish") {
  return request<FaqItem>(`/api/staff/faq/${encodeURIComponent(faqId)}/${action}`, { method: "POST" })
}

// Unanswered question inbox (US22)

export type InboxStatus = "new" | "answered" | "dismissed"

export type InboxGroup = {
  key: string
  question: string
  count: number
  language: FaqLanguage
  best_score: number | null
  first_asked: string
  last_asked: string
  faq_id: string | null
}

export function listInbox(params: { status: InboxStatus; days: number }, signal?: AbortSignal) {
  return request<{ items: InboxGroup[]; total_asks: number }>("/api/staff/inbox", {
    query: { status: params.status, days: String(params.days) },
    signal,
  })
}

export function dismissInboxGroup(key: string) {
  return request<{ updated: number }>("/api/staff/inbox/dismiss", { method: "POST", body: JSON.stringify({ key }) })
}

export function answerInboxGroup(key: string, faqId: string) {
  return request<{ updated: number }>("/api/staff/inbox/answer", {
    method: "POST",
    body: JSON.stringify({ key, faq_id: faqId }),
  })
}

// Admissions dashboard (US9)

export type Analytics = {
  days: number
  since: string
  questions: number
  sessions: number
  unanswered: number
  per_day: { date: string; questions: number; unanswered: number }[]
  top_questions: { question: string; count: number }[]
  top_sources: { faq_id: string; question: string | null; count: number }[]
  languages: Record<FaqLanguage, number>
  ratings: { up: number; down: number }
  down_reasons: Record<string, number>
}

export function getAnalytics(days: number, signal?: AbortSignal) {
  return request<Analytics>("/api/staff/analytics", { query: { days: String(days) }, signal })
}

// Catalogue and checklist management (US21)

export type ApplicantType = "local" | "international"

export type StaffDocument = {
  name: string
  format: "original" | "copy"
  translation: boolean
  notarisation: boolean
  deadline: string
}

export type StaffProgramFields = {
  title: string
  title_ru: string | null
  title_kk: string | null
  faculty: string
  degree_level: "bachelor" | "master" | "phd"
  language: string | null
  tuition_per_ects_kzt: number | null
  tuition_per_ects_usd: number | null
  deadline_local: string | null
  deadline_international: string | null
  source_url: string | null
  is_active: boolean
}

export type StaffProgram = StaffProgramFields & {
  program_id: string
  documents: Record<ApplicantType, StaffDocument[]>
  updated_at: string | null
  updated_by: string | null
}

export type StaffProgramListItem = {
  program_id: string
  title: string
  degree_level: string
  faculty: string
  is_active: boolean
  documents_local: number
  documents_international: number
  updated_at: string | null
  updated_by: string | null
}

export function listStaffPrograms(params: { q?: string; degree_level?: string; active?: string }, signal?: AbortSignal) {
  return request<{ items: StaffProgramListItem[] }>("/api/staff/programs", { query: params, signal })
}

export function getStaffProgram(programId: string, signal?: AbortSignal) {
  return request<StaffProgram>(`/api/staff/programs/${encodeURIComponent(programId)}`, { signal })
}

export function createStaffProgram(program: StaffProgramFields & { program_id: string }) {
  return request<StaffProgram>("/api/staff/programs", { method: "POST", body: JSON.stringify(program) })
}

export function updateStaffProgram(programId: string, fields: StaffProgramFields) {
  return request<StaffProgram>(`/api/staff/programs/${encodeURIComponent(programId)}`, {
    method: "PUT",
    body: JSON.stringify(fields),
  })
}

export function replaceStaffDocuments(programId: string, applicantType: ApplicantType, documents: StaffDocument[]) {
  return request<StaffProgram>(`/api/staff/programs/${encodeURIComponent(programId)}/documents/${applicantType}`, {
    method: "PUT",
    body: JSON.stringify({ documents }),
  })
}
