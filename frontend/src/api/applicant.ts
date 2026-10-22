import { apiUrl, errorFromResponse, request } from "@/api/client"
import type { ApplicantType, DocumentRequirement, Program } from "@/api/types"
import type { Language } from "@/i18n"

export type Applicant = { id: number; email: string; language: Language; reminders_enabled: boolean }
export type SavedChecklist = {
  program: Program
  applicant_type: ApplicantType
  items: (DocumentRequirement & { id: number; prepared: boolean })[]
  prepared: number
  total: number
  warning: string | null
  contact: string | null
}
const ROOT = "/api/applicant"
const options = { credentials: "include" as const }
export const getApplicant = (signal?: AbortSignal) => request<Applicant>(`${ROOT}/me`, { ...options, signal })
export const loginApplicant = (email: string, password: string) =>
  request<Applicant>(`${ROOT}/login`, {
    ...options,
    method: "POST",
    body: JSON.stringify({ email, password }),
  })
export const registerApplicant = (email: string, password: string, language: Language) =>
  request<{ message: string }>(`${ROOT}/register`, {
    ...options,
    method: "POST",
    body: JSON.stringify({ email, password, language }),
    timeoutMs: 20_000,
  })
export const verifyApplicant = (token: string) =>
  request<Applicant>(`${ROOT}/verify`, { ...options, method: "POST", body: JSON.stringify({ token }) })
export const logoutApplicant = () => request<void>(`${ROOT}/logout`, { ...options, method: "POST" })
export const deleteApplicant = () => request<void>(`${ROOT}/me`, { ...options, method: "DELETE" })
export const updatePreferences = (body: Pick<Applicant, "language" | "reminders_enabled">) =>
  request<Applicant>(`${ROOT}/me`, { ...options, method: "PATCH", body: JSON.stringify(body) })
export const getSavedPrograms = (signal?: AbortSignal) =>
  request<{ items: SavedChecklist[] }>(`${ROOT}/programs`, { ...options, signal })
export const checklistPath = (id: string, type: ApplicantType) =>
  `${ROOT}/programs/${encodeURIComponent(id)}/${type}`
export const saveProgram = (id: string, type: ApplicantType) =>
  request<SavedChecklist>(checklistPath(id, type), { ...options, method: "PUT" })
export const removeProgram = (id: string, type: ApplicantType) =>
  request<void>(checklistPath(id, type), { ...options, method: "DELETE" })
export const setPrepared = (id: string, type: ApplicantType, documentId: number, prepared: boolean) =>
  request<SavedChecklist>(`${checklistPath(id, type)}/documents/${documentId}`, {
    ...options,
    method: "PUT",
    body: JSON.stringify({ prepared }),
  })

export async function downloadChecklist(path: string) {
  const response = await fetch(apiUrl(path), { credentials: "include" })
  if (!response.ok) throw await errorFromResponse(response)
  const url = URL.createObjectURL(await response.blob())
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = "SDU-checklist.pdf"
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
