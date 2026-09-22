export type FaqItem = {
  faq_id: string
  question: string
  answer: string
  category: string
  source_link: string
  updated_at: string
}

export const MOCK_FAQ: FaqItem[] = [
  {
    faq_id: "faq-unt",
    question: "How do local applicants apply after school?",
    answer:
      "Admission to SDU University after school is based on Unified National Testing (UNT) results. State educational grants are awarded through the Ministry competition. Complete the application on admissions.sdu.edu.kz before visiting the Admissions Office.",
    category: "bachelor",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-college",
    question: "How do college graduates apply?",
    answer:
      "College graduates who want a state grant must submit UNT results. To enter the grant competition they need at least 35 points overall and no less than 5 points in each UNT subject. Tuition-based applicants after college go through an interview.",
    category: "bachelor",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-deadline-fall",
    question: "What is the fall intake deadline for international applicants?",
    answer:
      "The fall intake application deadline is 31 July 2026. Original documents must be submitted by 20 August 2026.",
    category: "international",
    source_link: "https://sdu.edu.kz/en/international-admissions/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-deadline-spring",
    question: "What is the spring intake deadline?",
    answer:
      "The spring intake application deadline is 30 November 2026. Original documents must be submitted by 20 December 2026.",
    category: "international",
    source_link: "https://sdu.edu.kz/en/international-admissions/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-ielts",
    question: "What English level is required?",
    answer:
      "International applicants may submit IELTS 5.5 with at least 5.0 in each section, or an SDU Extension Center certificate at B1. Without a certificate, applicants take a placement test and an English interview.",
    category: "language",
    source_link: "https://sdu.edu.kz/en/international-admissions/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-fee-international",
    question: "Is there an application fee for international students?",
    answer:
      "Yes. International applicants pay a student fee of 200 USD and upload the receipt to the admissions portal before the file is processed.",
    category: "international",
    source_link: "https://sdu.edu.kz/en/international-admissions/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-portal",
    question: "Where do I submit the application?",
    answer:
      "Applications are submitted through the SDU admissions portal at admissions.sdu.edu.kz. Print the form and bring it to the Admissions Office after you complete the online file.",
    category: "process",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-master-ct",
    question: "How does master’s admission work?",
    answer:
      "Master’s applicants sit a Complex Test (CT): foreign language (waived with IELTS 5.5 or equivalent TOEFL), a test of readiness for graduate school, and profile subjects. The passing score is 75 for scientific-pedagogical programmes and 50 for profile programmes.",
    category: "master",
    source_link: "https://sdu.edu.kz/en/master/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-master-docs",
    question: "Which documents are needed for a master’s application?",
    answer:
      "Typical master’s papers are the original bachelor’s diploma and transcript, six 3×4 photographs, medical card No. 075 and an X-ray, a copy of the national ID, and a CT certificate if you have one.",
    category: "master",
    source_link: "https://sdu.edu.kz/en/master/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-code",
    question: "What is the SDU university code?",
    answer: "The SDU university code used for national testing and grant applications is 302.",
    category: "process",
    source_link: "https://sdu.edu.kz/en/master/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-contact",
    question: "How can I contact the admissions office?",
    answer:
      "SDU Admissions is at Abylai Khan 1/1, Kaskelen. Telephone +7 727 307 95 65 or +7 702 000 11 33. Official pages are published on sdu.edu.kz.",
    category: "contact",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-campus",
    question: "Where is the campus?",
    answer:
      "The main campus is in Kaskelen, about 20 km from Almaty city centre: Abylai Khan 1/1, Karasai district, Almaty Region, 040900.",
    category: "contact",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-language-of-study",
    question: "What is the language of instruction?",
    answer:
      "SDU runs a trilingual system. Most degree programmes are taught in English; a smaller share is offered in Kazakh or Russian. Check the language field on each programme card.",
    category: "language",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-grants",
    question: "Are state grants available?",
    answer:
      "Yes. State educational grants are awarded on UNT results for bachelor’s programmes and on Complex Test results for master’s programmes, through the Ministry competition.",
    category: "bachelor",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-placement",
    question: "Do I have to take a placement test?",
    answer:
      "International applicants take an English placement test and interview unless they already hold IELTS 5.5 (minimum 5.0 in each section) or an SDU Extension Center B1 certificate.",
    category: "international",
    source_link: "https://sdu.edu.kz/en/international-admissions/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-photos",
    question: "How many photographs do I need?",
    answer:
      "Local bachelor’s and master’s files usually require six 3×4 cm photographs. International applicants upload one electronic 3×4 photo with the online form and bring six prints on arrival.",
    category: "documents",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-medical",
    question: "Which medical documents are required?",
    answer:
      "Local enrolment typically needs medical certificate Form 075, chest fluorography with a physician’s report, and vaccination record Form 063. International students submit Form 075 and an X-ray on arrival.",
    category: "documents",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-tuition",
    question: "How much is tuition?",
    answer:
      "Tuition differs by school and degree. The figures in this catalogue are indicative public-page values and must be confirmed with the Admissions Office before you pay.",
    category: "fees",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-originals",
    question: "When do I bring original documents?",
    answer:
      "International fall-intake originals are due by 20 August 2026; spring-intake originals by 20 December 2026. Local applicants bring originals when they enrol after the portal application.",
    category: "documents",
    source_link: "https://sdu.edu.kz/en/international-admissions/",
    updated_at: "2026-03-01",
  },
  {
    faq_id: "faq-schools",
    question: "Which schools does SDU have?",
    answer:
      "SDU has four schools: Engineering and Natural Sciences, Education and Humanities, Law and Social Sciences, and the SDU Business School.",
    category: "programmes",
    source_link: "https://sdu.edu.kz/en/admission-3-2/",
    updated_at: "2026-03-01",
  },
]
