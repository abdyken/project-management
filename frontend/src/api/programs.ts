import { request } from "@/api/client"
import type {
  ApplicantType,
  ChecklistResponse,
  DegreeLevel,
  Program,
  ProgramListResponse,
  ProgramQuery,
} from "@/api/types"

export type FilterOptions = {
  faculties: string[]
  degreeLevels: DegreeLevel[]
  languages: string[]
}

const DEGREE_ORDER: DegreeLevel[] = ["bachelor", "master", "phd"]

export function listPrograms(query: ProgramQuery = {}) {
  return request<ProgramListResponse>("/api/programs", { query })
}

export const allProgramsQuery = {
  queryKey: ["programs", "all"],
  queryFn: () => listPrograms(),
}

export function filterOptions(programs: Program[]): FilterOptions {
  const unique = (values: string[]) => [...new Set(values)].sort((a, b) => a.localeCompare(b))
  const degrees = new Set(programs.map((program) => program.degree_level))
  return {
    faculties: unique(programs.map((program) => program.faculty)),
    degreeLevels: DEGREE_ORDER.filter((level) => degrees.has(level)),
    languages: unique(programs.map((program) => program.language)),
  }
}

export function getProgram(programId: string) {
  return request<Program>(`/api/programs/${encodeURIComponent(programId)}`)
}

export function getChecklist(programId: string, applicantType: ApplicantType) {
  return request<ChecklistResponse>(`/api/programs/${encodeURIComponent(programId)}/checklist`, {
    query: { applicant_type: applicantType },
  })
}
