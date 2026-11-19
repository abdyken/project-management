import { apiUrl, errorFromResponse, request } from "@/api/client"
import { ApiError } from "@/api/errors"
import type { ApplicantType, DocumentFormat, Program } from "@/api/types"
import type { Language } from "@/i18n"

// Sprint 7 (US31-US33, US6); decisions in docs/adr/0001-0004.
export type ApplicationStatus = "draft" | "submitted" | "in_review" | "needs_changes" | "accepted" | "rejected"
export type EducationLevel = "school" | "college" | "bachelor" | "master"
export const EDUCATION_LEVELS: EducationLevel[] = ["school", "college", "bachelor", "master"]
export const MAX_FILE_BYTES = 10 * 1024 * 1024
export const ACCEPTED_FILES = ".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"

export type ApplicationFields = {
  full_name: string | null
  date_of_birth: string | null
  citizenship: string | null
  phone: string | null
  education_level: EducationLevel | null
  graduation_year: number | null
  exam_total: number | null
  consent: boolean
}
export type ApplicationDocument = {
  id: number
  requirement_id: number | null
  original_name: string
  content_type: string
  size_bytes: number
  uploaded_at: string
}
export type ApplicationRequirement = {
  id: number
  name: string
  format: DocumentFormat
  translation: boolean
  notarisation: boolean
  deadline: string
  uploaded: boolean
}
export type Application = ApplicationFields & {
  id: number
  program: Program
  applicant_type: ApplicantType
  status: ApplicationStatus
  language: Language
  staff_note: string | null
  editable: boolean
  created_at: string
  updated_at: string
  submitted_at: string | null
  status_changed_at: string | null
  requirements: ApplicationRequirement[]
  documents: ApplicationDocument[]
  bytes_used: number
  bytes_limit: number
  missing: string[]
}
export type ApplicationSummary = {
  id: number
  program: Program
  applicant_type: ApplicantType
  status: ApplicationStatus
  updated_at: string
  submitted_at: string | null
  documents: number
}
export type StaffApplicationSummary = ApplicationSummary & { applicant_email: string; full_name: string | null }
export type StaffApplication = Application & { applicant_email: string }
export type StaffQueueFilter = "open" | "submitted" | "in_review" | "needs_changes" | "accepted" | "rejected" | "all"
export type StaffStatusChange = "in_review" | "needs_changes" | "accepted" | "rejected"

const ROOT = "/api/applicant/applications"
const STAFF = "/api/staff/applications"
const options = { credentials: "include" as const }
const json = (method: string, body: unknown) => ({ ...options, method, body: JSON.stringify(body) })

export const applicationsKey = ["applicant", "applications"] as const
export const listApplications = (signal?: AbortSignal) =>
  request<{ items: ApplicationSummary[]; total: number }>(ROOT, { ...options, signal })
export const getApplication = (id: number, signal?: AbortSignal) =>
  request<Application>(`${ROOT}/${id}`, { ...options, signal })
export const startApplication = (program_id: string, applicant_type: ApplicantType, language: Language) =>
  request<Application>(ROOT, json("POST", { program_id, applicant_type, language }))
export const saveApplication = (id: number, fields: ApplicationFields, language: Language) =>
  request<Application>(`${ROOT}/${id}`, json("PUT", { ...fields, language }))
export const submitApplication = (id: number) => request<Application>(`${ROOT}/${id}/submit`, { ...options, method: "POST" })
export const deleteDraft = (id: number) => request<void>(`${ROOT}/${id}`, { ...options, method: "DELETE" })
export const deleteDocument = (id: number, documentId: number) =>
  request<void>(`${ROOT}/${id}/documents/${documentId}`, { ...options, method: "DELETE" })
export const documentUrl = (id: number, documentId: number, staff = false) =>
  apiUrl(`${staff ? STAFF : ROOT}/${id}/documents/${documentId}`)
export const applicationStatus = (language: Language, signal?: AbortSignal) =>
  request<{ answer: string }>(`${ROOT}/status`, { ...options, query: { language }, signal })

// The shared request helper always sends JSON; uploads send multipart form data.
export async function uploadDocument(id: number, file: File, requirementId: number | null): Promise<ApplicationDocument> {
  const body = new FormData()
  body.append("file", file)
  if (requirementId !== null) body.append("requirement_id", String(requirementId))
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 120_000)
  try {
    const res = await fetch(apiUrl(`${ROOT}/${id}/documents`), {
      ...options,
      method: "POST",
      body,
      headers: { Accept: "application/json" },
      signal: controller.signal,
    })
    if (!res.ok) throw await errorFromResponse(res)
    return (await res.json()) as ApplicationDocument
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === "AbortError") throw new ApiError(0, "TIMEOUT", "Upload timed out")
    throw new ApiError(0, "NETWORK", "Network error")
  } finally {
    window.clearTimeout(timer)
  }
}

export const listStaffApplications = (status: StaffQueueFilter, offset: number, signal?: AbortSignal) =>
  request<{ items: StaffApplicationSummary[]; total: number }>(STAFF, {
    ...options,
    query: { status, offset: String(offset), limit: "30" },
    signal,
  })
export const getStaffApplication = (id: number, signal?: AbortSignal) =>
  request<StaffApplication>(`${STAFF}/${id}`, { ...options, signal })
export const setApplicationStatus = (id: number, status: StaffStatusChange, note: string) =>
  request<StaffApplication>(`${STAFF}/${id}/status`, json("POST", { status, note: note.trim() || null }))
