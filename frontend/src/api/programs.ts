import { request } from "@/api/client"
import type {
  ApplicantType,
  ChecklistResponse,
  Program,
  ProgramListResponse,
  ProgramQuery,
} from "@/api/types"

export function listPrograms(query: ProgramQuery = {}) {
  return request<ProgramListResponse>("/api/programs", { query })
}

export function getProgram(programId: string) {
  return request<Program>(`/api/programs/${encodeURIComponent(programId)}`)
}

export function getChecklist(programId: string, applicantType: ApplicantType) {
  return request<ChecklistResponse>(`/api/programs/${encodeURIComponent(programId)}/checklist`, {
    query: { applicant_type: applicantType },
  })
}
