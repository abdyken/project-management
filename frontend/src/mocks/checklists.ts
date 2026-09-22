import { ADMISSIONS_CONTACT } from "@/lib/constants"
import type { ApplicantType, ChecklistResponse, DocumentRequirement } from "@/api/types"

const bachelorLocal: DocumentRequirement[] = [
  {
    name: "Admission application form (admissions.sdu.edu.kz)",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Before visiting the Admissions Office",
  },
  {
    name: "School certificate with transcript",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "UNT certificate",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "Medical certificate (Form 075)",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "Chest fluorography with physician’s report",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "Vaccination record (Form 063)",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "Photographs 3×4 cm, 6 copies",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "IELTS or SDU Language School certificate (if available)",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application",
  },
]

const bachelorInternational: DocumentRequirement[] = [
  {
    name: "Passport",
    format: "copy",
    translation: false,
    notarisation: true,
    deadline: "31 July 2026 (fall intake)",
  },
  {
    name: "School diploma / certificate and transcript",
    format: "original",
    translation: true,
    notarisation: true,
    deadline: "31 July 2026 (fall intake)",
  },
  {
    name: "Motivational letter",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application",
  },
  {
    name: "Letter of recommendation",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application",
  },
  {
    name: "Electronic photograph 3×4 cm",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application",
  },
  {
    name: "IELTS 5.5 (min 5.0 per section) or SDU Extension Center B1",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application / placement test waiver",
  },
  {
    name: "Student fee receipt (200 USD)",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application",
  },
  {
    name: "Medical Form 075 and X-ray result (upon arrival)",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "20 August 2026",
  },
]

const masterLocal: DocumentRequirement[] = [
  {
    name: "Bachelor’s diploma and transcript",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "Photographs 3×4 cm, 6 copies",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "Medical card No. 075 and X-ray result",
    format: "original",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "Copy of national ID",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Enrolment",
  },
  {
    name: "Complex Test (CT) certificate, if available",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Grant competition",
  },
]

const masterInternational: DocumentRequirement[] = [
  {
    name: "Passport",
    format: "copy",
    translation: false,
    notarisation: true,
    deadline: "Application",
  },
  {
    name: "Bachelor’s diploma and transcript",
    format: "original",
    translation: true,
    notarisation: true,
    deadline: "Application",
  },
  {
    name: "IELTS 5.5 or SDU Extension Center B1",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application",
  },
  {
    name: "Student fee receipt (200 USD)",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application",
  },
  {
    name: "Electronic photograph 3×4 cm",
    format: "copy",
    translation: false,
    notarisation: false,
    deadline: "Application",
  },
]

const pedagogyExtra: DocumentRequirement = {
  name: "Pedagogical examination result",
  format: "original",
  translation: false,
  notarisation: false,
  deadline: "Application",
}

const PROGRAMS_WITHOUT_CHECKLIST = new Set(["7M04101"])

export function getMockChecklist(
  programId: string,
  applicantType: ApplicantType,
  degreeLevel: "bachelor" | "master",
): ChecklistResponse {
  if (PROGRAMS_WITHOUT_CHECKLIST.has(programId)) {
    return {
      program_id: programId,
      applicant_type: applicantType,
      items: [],
      warning:
        "Document requirements for this programme are not stored yet. Please contact the admissions office instead of relying on an empty list.",
      contact: ADMISSIONS_CONTACT,
    }
  }

  let items =
    degreeLevel === "master"
      ? applicantType === "international"
        ? masterInternational
        : masterLocal
      : applicantType === "international"
        ? bachelorInternational
        : bachelorLocal

  if (programId === "6B01101" && applicantType === "local") {
    items = [...items, pedagogyExtra]
  }

  return {
    program_id: programId,
    applicant_type: applicantType,
    items,
  }
}
