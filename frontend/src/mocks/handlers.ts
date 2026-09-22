import { ApiError } from "@/api/errors"
import type {
  ApplicantType,
  AssistantRequest,
  AssistantResponse,
  ChecklistResponse,
  HealthResponse,
  Program,
  ProgramListResponse,
} from "@/api/types"
import { ADMISSIONS_CONTACT, FALLBACK_MESSAGE, SIMILARITY_THRESHOLD } from "@/lib/constants"
import { getMockChecklist } from "@/mocks/checklists"
import { MOCK_FAQ } from "@/mocks/faq"
import { MOCK_PROGRAMS } from "@/mocks/programs"

function delay(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const timer = window.setTimeout(() => resolve(), ms)
    const onAbort = () => {
      window.clearTimeout(timer)
      reject(new DOMException("Aborted", "AbortError"))
    }
    if (signal?.aborted) {
      onAbort()
      return
    }
    signal?.addEventListener("abort", onAbort, { once: true })
  })
}

function normalize(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9а-яёәғқңөұүһі\s]/gi, " ").replace(/\s+/g, " ").trim()
}

function parsePath(path: string) {
  return new URL(path, "http://mock.local")
}

function scoreFaq(question: string) {
  const q = normalize(question)
  const words = q.split(" ").filter((word) => word.length > 2)

  return MOCK_FAQ.map((item) => {
    const hay = normalize(`${item.question} ${item.answer} ${item.category}`)
    const hits = words.filter((word) => hay.includes(word)).length
    const similarity = words.length === 0 ? 0 : hits / words.length
    return { item, similarity }
  }).sort((a, b) => b.similarity - a.similarity)[0]
}

function findProgram(question: string) {
  const q = normalize(question)
  return MOCK_PROGRAMS.find((program) => {
    const title = normalize(program.title)
    return q.includes(title) || title.split(" ").filter((w) => w.length > 3).every((word) => q.includes(word))
  })
}

function formatChecklistAnswer(program: Program, checklist: ChecklistResponse) {
  if (checklist.warning) {
    return `${checklist.warning} ${ADMISSIONS_CONTACT.name}, ${ADMISSIONS_CONTACT.address}. Tel. ${ADMISSIONS_CONTACT.phone}.`
  }

  const lines = checklist.items.map((item) => {
    const extras = [
      item.format,
      item.translation ? "translation required" : null,
      item.notarisation ? "notarisation required" : null,
      item.deadline,
    ]
      .filter(Boolean)
      .join(", ")
    return `• ${item.name} (${extras})`
  })

  return `Documents required for ${program.title} (${checklist.applicant_type} applicant):\n${lines.join("\n")}`
}

async function handleAssistant(body: AssistantRequest, signal?: AbortSignal): Promise<AssistantResponse> {
  const question = body.question.trim()

  if (/timeout/i.test(question)) {
    await delay(12_000, signal)
  }

  if (/error 400/i.test(question)) {
    throw new ApiError(400, "BAD_REQUEST", "The question could not be processed.")
  }

  if (/error 500/i.test(question)) {
    throw new ApiError(500, "INTERNAL", "The assistant service failed.")
  }

  const wantsDocuments = /\b(documents?|checklist|papers?)\b/i.test(question)
  const program = wantsDocuments ? findProgram(question) : undefined

  if (wantsDocuments && program) {
    const applicantType: ApplicantType = /international/i.test(question) ? "international" : "local"
    const checklist = getMockChecklist(program.program_id, applicantType, program.degree_level)
    return {
      answer: formatChecklistAnswer(program, checklist),
      source_link: checklist.warning ? ADMISSIONS_CONTACT.website : "https://sdu.edu.kz/en/admission-3-2/",
      faq_id: checklist.warning ? null : "faq-documents-from-checklist",
      similarity_score: 0.92,
    }
  }

  const match = scoreFaq(question)
  if (match && match.similarity >= SIMILARITY_THRESHOLD) {
    return {
      answer: match.item.answer,
      source_link: match.item.source_link,
      faq_id: match.item.faq_id,
      similarity_score: Number(match.similarity.toFixed(2)),
    }
  }

  return {
    answer: FALLBACK_MESSAGE,
    source_link: ADMISSIONS_CONTACT.website,
    faq_id: null,
    similarity_score: match?.similarity ?? 0,
  }
}

export async function mockRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const jitter = 220 + Math.round(Math.random() * 380)
  await delay(jitter, init.signal ?? undefined)

  const url = parsePath(path)
  const method = (init.method ?? "GET").toUpperCase()

  if (url.pathname === "/api/health" && method === "GET") {
    return { status: "ok", database: "ok" } satisfies HealthResponse as T
  }

  if (url.pathname === "/api/programs" && method === "GET") {
    if (url.searchParams.get("force") === "503") {
      throw new ApiError(503, "SERVICE_UNAVAILABLE", "Database unavailable")
    }

    if (url.searchParams.get("force") === "empty") {
      return { programs: [], total: 0 } satisfies ProgramListResponse as T
    }

    const q = normalize(url.searchParams.get("q") ?? "")
    const faculty = url.searchParams.get("faculty") ?? ""
    const degree = url.searchParams.get("degree_level") ?? ""
    const language = url.searchParams.get("language") ?? ""

    const items = MOCK_PROGRAMS.filter((program) => {
      if (!program.is_active) return false
      if (faculty && program.faculty !== faculty) return false
      if (degree && program.degree_level !== degree) return false
      if (language && program.language !== language) return false
      if (!q) return true
      const hay = normalize(`${program.title} ${program.faculty} ${program.program_id}`)
      return q.split(" ").every((word) => hay.includes(word))
    })

    return { programs: items, total: items.length } satisfies ProgramListResponse as T
  }

  const programMatch = url.pathname.match(/^\/api\/programs\/([^/]+)$/)
  if (programMatch && method === "GET") {
    const program = MOCK_PROGRAMS.find((item) => item.program_id === decodeURIComponent(programMatch[1]))
    if (!program) {
      throw new ApiError(404, "NOT_FOUND", "Programme not found")
    }
    return program as T
  }

  const checklistMatch = url.pathname.match(/^\/api\/programs\/([^/]+)\/checklist$/)
  if (checklistMatch && method === "GET") {
    const programId = decodeURIComponent(checklistMatch[1])
    const program = MOCK_PROGRAMS.find((item) => item.program_id === programId)
    if (!program) {
      throw new ApiError(404, "NOT_FOUND", "Programme not found")
    }
    const applicantType = (url.searchParams.get("applicant_type") ?? "local") as ApplicantType
    return getMockChecklist(programId, applicantType, program.degree_level) as T
  }

  if (url.pathname === "/api/assistant/ask" && method === "POST") {
    const body = JSON.parse(String(init.body ?? "{}")) as AssistantRequest
    if (!body.question?.trim()) {
      throw new ApiError(400, "BAD_REQUEST", "Question is required")
    }
    return (await handleAssistant(body, init.signal ?? undefined)) as T
  }

  throw new ApiError(404, "NOT_FOUND", `No mock for ${method} ${url.pathname}`)
}
