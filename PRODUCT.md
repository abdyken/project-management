# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Primary: Kazakh school leavers and their parents.**
  - Grade-11 students choosing a bachelor's programme at SDU University with a UNT score.
  - The parent who often pays and decides alongside them.
  - They arrive on a phone, often in Kazakh or Russian.
  - Their jobs: find a programme, check whether they qualify, see what it costs and
    which documents are due when, then apply and follow the application.
  - *Delegated decision, 20.11.2026.*
- **Secondary paths:**
  - master's and PhD applicants (24 and 7 programmes)
  - international applicants (separate deadlines and documents)
  - transfer or college-diploma holders
- **Staff:** admissions officers. They answer private questions, review submitted
  applications and documents, and maintain the FAQ and programme data in the staff area.

## Product Purpose
The portal gives applicants one place, in Kazakh, Russian and English, to:
- browse SDU University's full official programme catalogue (64 programmes: 33
  bachelor's, 24 master's, 7 PhD) with documents, deadlines and tuition
- compare programmes
- check eligibility and estimate cost and funding
- ask an assistant that answers only from the official FAQ and catalogue
- send a private question to the admissions office
- submit an online application with document scans and follow its status

Success: an applicant gets from "which programme?" to a submitted, complete application
without phoning the office, and staff spend their time on real reviews.

## Positioning
Every fact is traceable to an official SDU source:
- the catalogue audit marks confirmed vs missing vs conflicting requirements
- checks never promise admission or a grant
- the assistant quotes official answers word for word, or grounds model answers in them,
  and keeps the source link

The status answer in the chat is built from the database, not from a model.

**Presentation (delegated decision, 20.11.2026):**
- the portal looks and reads as SDU University's admissions portal
- a discreet footer line states it is an INF451 course project and that sdu.edu.kz is
  the official source

## Operating Context
- **Applicant accounts:** verified e-mail. Applicants save programmes, track prepared
  documents, get deadline reminders and export checklists as PDF.
- **Applications:**
  - statuses per ADR 0002: draft → submitted → in review → changes requested →
    accepted / not accepted. "Accepted" means the documents are complete, not admission.
  - document rules per ADR 0003: PDF/JPEG/PNG, 10 MB per file, 40 MB per application.
  - e-mails carry a link only, never the content.
- **Staff area:** application queue, private question inbox, FAQ editor, programme
  editor, dashboard.
- **Hosting:** live on a single free Oracle VM (1 GB RAM). Feature switches control
  accounts and applications.

## Capabilities and Constraints
- **Stack:** React 19 + TypeScript + Vite + Tailwind v4 SPA (`frontend/`) and a FastAPI
  API. The API contract lives in `backend/docs/api/`.
- **Languages:** EN, RU and KK must stay complete. The RU/KK dictionaries are typed
  against EN.
- **Browser QA:** the `frontend/e2e/*.mjs` scripts select by accessible role names,
  labels and visible text at 360/768/1280 px in Chrome and Firefox. Copy or role changes
  must update the scripts in the same PR.
- **No personal ID numbers:** no IIN or passport numbers are collected (ADR 0001).
- **Out of scope:** admission decisions, payments, the university's own application
  system.

## Brand Commitments
- **Name:** SDU University (formerly Suleyman Demirel University), Kaskelen, Almaty
  Region, founded 1996.
- **Logo:** the SDU logo (feather-V emblem with diamond; "SDU UNIVERSITY" wordmark),
  taken from sdu.edu.kz.
  - No public brandbook exists.
  - The 30th-anniversary marks are temporary and are not the core logo.
- **Independent look (team decision, 20.11.2026):** the portal must not copy the look of
  sdu.edu.kz.
  - The official navy/peach palette is not used.
  - The logo appears in one colour (white or ink), keeping SDU's letterforms and emblem
    unchanged.
  - The portal's own identity is built in DESIGN.md.
- **Portal headline (team decision, 21.11.2026):** "Study at the foot of the Alatau" /
  "Алатау баурайында оқы" / "Учитесь у подножия Алатау". It is original to the portal and
  place-true: the campus sits under the Zailiysky Alatau. SDU's own tagline ("Making your
  dreams a reality") is not used, to keep the portal's voice its own.
- **Voice:** warm and encouraging when addressing applicants; precise and formal for
  requirements, deadlines and money.
- **Structure reference:** Purdue University undergraduate admissions (IA and page
  patterns, not its look). Chosen by the team on 20.11.2026.

## Evidence on Hand
- **Catalogue:** `backend/app/data/catalogue.json`, 64 programmes with source URLs,
  KK/RU titles, documents, local/international deadlines, tuition per ECTS in KZT/USD.
- **Source audit:** `backend/app/data/catalogue_review.md`, `docs/sprint-6-data-review.md`.
- **FAQ:** `backend/app/data/faq.json`, plus admissions guidance data in
  `backend/app/data/guidance.json`.
- **Official contact:** SDU Admissions Office, Abylai Khan 1/1, 040900 Kaskelen;
  admissions@sdu.edu.kz.
- **Photography:** public SDU photos from sdu.edu.kz, credited "Photo: SDU University".
  No licence is stated, so the PR Office (pr@sdu.edu.kz) should be told.
- **SDU facts and rankings from sdu.edu.kz:** may be shown only when re-verified at build
  time and labelled with source and year.
- **Absent:** no student testimonials, no named student stories, no admissions-office
  staff photos. Do not fabricate quotes, people, statistics or rankings.

## Product Principles
1. **Truth over persuasion.** Every number, deadline and requirement shows where it comes
   from. When data is missing, say so instead of guessing.
2. **The next step is always visible.** At every point the applicant can see what to do
   next: apply, check status or ask admissions.
3. **Three languages are equal.** Kazakh and Russian are first-class, not translations
   bolted on.
4. **Phone first, low bandwidth.** Pages must work on a mid-range phone on mobile data.
5. **Staff tools are for daily work.** They should be dense, consistent and quiet.

## Accessibility & Inclusion
- WCAG 2.2 AA.
- The accessibility work already shipped must be kept:
  - chat focus return and Escape to close
  - `aria-live` announcers
  - focus management on application forms
  - reduced-motion support
  - 16px inputs on mobile
  - status never shown by colour alone
- Every visible string exists in KK/RU/EN, with a correct `lang` attribute on
  mixed-language content.
