// Subject photographs for program pages (Unsplash, credited in
// frontend/public/images/programs/CREDITS.md). One photo per subject area keeps the
// catalogue consistent; programs are mapped by their official code.

export type ProgramSubject =
  | "computing"
  | "systems"
  | "data"
  | "mathematics"
  | "physics"
  | "chemistry"
  | "biology"
  | "law"
  | "international"
  | "management"
  | "healthcare"
  | "finance"
  | "economics"
  | "marketing"
  | "media"
  | "languages"
  | "literature-kk"
  | "literature-ru"
  | "history"
  | "psychology"
  | "education"

const SUBJECT_BY_PROGRAM: Record<string, ProgramSubject> = {
  "6B04103": "finance",
  "8D04201": "law",
  "6B04201": "law",
  "6B02304": "languages",
  "6B03103": "psychology",
  "7M01504": "biology",
  "6B06107": "systems",
  "6B01506": "chemistry",
  "7M01502": "chemistry",
  "8D06102": "computing",
  "6B06102": "computing",
  "7M06102": "computing",
  "7M06104": "data",
  "6B04105": "marketing",
  "6B04101": "economics",
  "7M04110": "economics",
  "7M04114": "management",
  "7M04105": "healthcare",
  "6B04104": "finance",
  "7M01702": "languages",
  "6B01703": "languages",
  "6B01601": "history",
  "6B01504": "systems",
  "7M01505": "education",
  "6B06101": "systems",
  "7M06101": "systems",
  "7M04202": "law",
  "7M04204": "law",
  "6B04202": "international",
  "6B03101": "international",
  "8D01701": "literature-kk",
  "7M01701": "literature-kk",
  "6B01701": "literature-kk",
  "6B04203": "law",
  "6B04102": "management",
  "7M04115": "management",
  "8D04101": "management",
  "7M04112": "education",
  "6B06103": "data",
  "8D05401": "mathematics",
  "6B01501": "mathematics",
  "6B05401": "mathematics",
  "7M01501": "mathematics",
  "7M04113": "management",
  "7M04104": "healthcare",
  "7M03205": "media",
  "7M03201": "media",
  "6B03205": "media",
  "6B06104": "media",
  "8D01501": "mathematics",
  "6B01301": "education",
  "6B01101": "psychology",
  "6B01505": "physics",
  "7M01503": "physics",
  "7M04201": "law",
  "7M04109": "management",
  "6B01707": "literature-ru",
  "6B01802": "education",
  "6B06105": "computing",
  "7M06105": "computing",
  "6B05402": "data",
  "6B02302": "languages",
  "6B01702": "languages",
  "8D01702": "languages",
}

// Photographer credits (Unsplash); sources in public/images/programs/CREDITS.md.
const CREDITS: Record<ProgramSubject, string> = {
  "computing": "Jakub Żerdzicki",
  "systems": "Kevin Ache",
  "data": "Conny Schneider",
  "mathematics": "Erwan Hesry",
  "physics": "5010 (isoten)",
  "chemistry": "Egor Myznik",
  "biology": "Fayette Reynolds",
  "law": "Giammarco Boscaro",
  "international": "Maxim Klimashin",
  "management": "Benjamin Child",
  "healthcare": "Tasha Kostyuk",
  "finance": "Aaron Lefler",
  "economics": "Paul Lichtblau",
  "marketing": "Luke Chesser",
  "media": "Brad Weaver",
  "languages": "Waldemar Brandt",
  "literature-kk": "T Y",
  "literature-ru": "Egor Myznik",
  "history": "Andrew Neel",
  "psychology": "Patrick Perkins",
  "education": "Far Chinberdiev",
}

export type ProgramImage = { src: string; srcSet: string; credit: string | null }

export function programImage(programId: string): ProgramImage | null {
  const subject = SUBJECT_BY_PROGRAM[programId]
  if (!subject) return null
  const base = `/images/programs/${subject}`
  return {
    src: `${base}-1280.webp`,
    srcSet: `${base}-800.webp 800w, ${base}-1280.webp 1280w, ${base}-1920.webp 1920w`,
    credit: CREDITS[subject],
  }
}
