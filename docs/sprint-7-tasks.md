# Sprint 7 - online application

**Original sprint:** 31.10-06.11.2026 (not started; no practice sessions in early November).
**Re-planned:** 20.11-27.11.2026, confirmed by the Product Owner; Sprint 8 moves to
28.11-04.12.2026.
**Delivery:** the team now gives each sprint to one member (Product Owner decision);
Sprint 7 is delivered by Dinmukhamed. The backlog owners below stay as story contacts.

Goal: an applicant with a verified account submits an application for one programme,
attaches scans of the required documents, and follows its status; an admissions
officer reviews submitted applications and sets their status.

| Tasks | Story / owner | Implementation and acceptance |
| --- | --- | --- |
| 7.0 | All / Askhat | Agree the form fields (below), statuses and file rules before coding; record them in this file |
| 31.1-31.4 | US31 / Daniyar | Migration 0020 `application`; draft, edit and submit API under `/api/applicant/applications`; form page in RU/KK/EN with validation; one active application per programme and applicant type; submitted applications are read-only |
| 32.1-32.4 | US32 / Dinmukhamed | Migration 0020 `application_document`; upload, list, download and delete API; files on a Docker volume, never served directly; type and size checks; uploading a scan marks that document prepared in the tracker (US25) |
| 33.1-33.3 | US33 / Nurmek | Staff queue under `/api/staff/applications` (filter by status and programme, oldest first); detail view with documents; status change with a note to the applicant; e-mail notification through the hourly worker (same pattern as US30) |
| 6.1-6.2 | US6 / Serdar | "Status of my application" answer for a logged-in applicant, built from the database, not from the model; chat and account page show the current stage and next step |
| 7.QA | All | Backend tests per story, isolation (another applicant's files and applications return 404), browser QA in RU/KK/EN at 360/768/1280 px, QA cards `US31-QA.md` to `US33-QA.md` and `US6-QA.md` |
| CO.7 | Dinmukhamed / Askhat | Daily database and uploads backup on the VM before uploads go live (done 20.11.2026: `deploy/oracle-vm/backup.sh`, restore tested); record the data-hosting decision in `applicant-hosting.md` (done 20.11.2026); applications switched on in production 20.11.2026 |

Delivery order: 7.0 → 31 (model and API first, so 32 and 33 can start in parallel) →
32 and 33 → 6 → QA. If time runs out, US6 moves to Sprint 8 first; US31-US33 are one
feature and ship together.

## Decisions (7.0), accepted 19.11.2026

Recorded as decision records in `docs/adr/0001`-`0004`.

1. **Form fields.** Proposal until the admissions office gives the official form:
   full name, date of birth, citizenship, phone, programme and applicant type (from a
   saved checklist), education (school/college/bachelor/master), graduation year, UNT or
   CT total if known, consent to data processing. No national ID (IIN) or passport
   numbers: they are not needed to test the flow and are the most sensitive data.
2. **Statuses.** `draft` → `submitted` → `in_review` → `needs_changes` (back to the
   applicant, who can resubmit) → `accepted` or `rejected`. Only `draft` and
   `needs_changes` are editable. "Accepted" means the documents are complete, not
   admission.
3. **Files.** PDF, JPEG or PNG, checked by content (magic bytes), up to 10 MB each and
   40 MB per application; stored under random names on the `uploads` volume; downloaded
   only through the API with `Content-Disposition: attachment`. Deleted with the
   application or the account. No antivirus scanning on the free VM: staff open files
   in the browser's viewer only.
4. **Where the chat gets the status (US6).** The applicant session cookie is scoped to
   `/api/applicant`, so `/api/assistant` cannot see who is asking. Options: a status
   endpoint under `/api/applicant` that the chat widget calls when the question is about
   an application, or widening the cookie path. The first keeps the cookie scope.

## Boundaries

- One server, 1 GB RAM, 35 GB free disk in Dubai (see `applicant-hosting.md`). Uploads
  are the first personal documents the portal stores, so the backup in CO.7 and the
  hosting record are prerequisites for enabling uploads in production.
- No payments, no admission decisions, no integration with the university's real
  application system. The flow is complete inside the portal.
- Reuse what exists: applicant sessions and origin checks (US23), the document tracker
  (US25), the staff area and roles (US19), and the request queue plus notification
  worker (US30).

## Development and QA

Same workflow as Sprints 5-6: a branch per story, PR with the story number, required CI
green, at least one teammate review for PRs over 300 lines, browser QA on the local
stack with Mailpit. Never run QA scripts against the live database.

DoD: reviewed PR, passing CI, migration with downgrade, API contract in
`backend/docs/api/applications.md`, QA card, story and QA sheets in `docs/table.xlsx`,
live check after deploy.
