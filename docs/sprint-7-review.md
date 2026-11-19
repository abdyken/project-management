# Sprint 7 - implementation review and QA

**Sprint:** 20-27.11.2026 (re-planned, Product Owner decision). **Delivered by:** Dinmukhamed.
**Implementation, code review and local verification:** 19-20.11.2026.
**Branch:** `feature/sprint-7-online-application`.

## Result

All four planned stories are implemented: US31 online application form, US32 document
upload, US33 staff review queue and US6 application status in the chat. An applicant with
a verified account starts an application from a saved programme checklist, fills in the
form (no IIN or passport numbers, ADR 0001), attaches PDF/JPEG/PNG scans and submits it.
An admissions officer works through the queue (oldest first, filter by status and
programme), downloads the scans and sets a status with a note. The applicant is e-mailed
a link (never the note), corrects and resubmits when changes are requested, and can ask
the chat "What is the status of my application?" to get the stage and next step from the
database, not from the model.

| Story | Implementation | Evidence | Acceptance |
| --- | --- | --- | --- |
| US31 | Draft/edit/submit API and RU/KK/EN form; one live application per programme and type; read-only after submitting; browser and server validation | `backend/docs/qa/US31-QA.md` | Live QA / PO open |
| US32 | Content-checked uploads to the `uploads` volume, per-file/application/account limits, disk floor, downloads as attachments, cleanup of abandoned drafts and orphaned files | `backend/docs/qa/US32-QA.md` | CO.7 backup, live QA / PO open |
| US33 | Staff queue and detail, status rules (ADR 0002), required notes, link-only e-mail with retry | `backend/docs/qa/US33-QA.md` | Live QA / PO open |
| US6 | Status questions in EN/RU/KK recognised without the model; own status for a logged-in applicant, a general pointer for visitors | `backend/docs/qa/US6-QA.md` | Live QA / PO open |

Decisions: `docs/adr/0001`-`0004`. API contract: `backend/docs/api/applications.md`.

## Code review

Five independent reviews ran on the first version: security, backend, frontend and
accessibility, test quality (including mutation testing) and a pre-landing review. All
findings that changed behaviour were fixed on this branch:

- **Data safety.** Account deletion now locks the applicant's applications before
  collecting their files, so an upload in flight cannot leave a file behind. Deleting a
  programme with applications is refused (`ON DELETE RESTRICT`) instead of silently
  deleting them. Indexes were added for the two foreign keys used by deletes.
- **Uploads.** The file is written without holding the row lock and all limits are
  checked again under it. A 100 MB per-account limit, a 2 GB free-disk floor
  (`507 UPLOADS_PAUSED`) and an hourly cleanup of 30-day-old drafts and orphaned files
  protect the shared disk. The download name always carries the detected type's
  extension. nginx accepts 11 MB bodies on the upload route only; other API routes keep 1 MB.
- **E-mails.** Every status change resets the "already e-mailed" marker, so a second
  "changes requested" is e-mailed too. The row lock is released before talking to SMTP.
- **Chat (US6).** Recognition now needs the visitor's own application ("my application",
  "моя заявка", "өтінішім") plus a status word, so general questions such as "How do I
  submit my application?" or "Какие этапы подачи заявки?" still reach the FAQ (0 of 198
  FAQ and evaluation questions trigger it). It needs both feature switches.
- **Switches.** `GET /api/features` lets the frontend hide the applications links while
  `APPLICATIONS_ENABLED` is off, as it is in production.
- **Frontend.** Valid phone pattern, birth date not in the future, server field errors
  shown at the field, unsaved-changes warning, focus moved to the result after save,
  submit, upload, remove, delete and staff status changes, announcements for screen
  readers, hidden file inputs out of the Tab order, "not found" for bad links, localised
  file sizes and staff dates, staff programme filter, a note marked as "from the earlier
  review" after a resubmission.

## Verification (20.11.2026)

| Check | Result |
| --- | --- |
| Full backend suite on isolated PostgreSQL/pgvector | **733 passed** (62 in `test_applications.py`) |
| Mutation checks on the Sprint 7 code | **17/17** review mutations caught (limits off by one, cross-application document id, staff origin check, required notes, filters, queue order, e-mail reset, intent rule, feature switch, download extension, deletion lock) |
| Migration 0020: downgrade to 0019 and upgrade again; `alembic check` | PASS, no drift |
| Sprint 7 browser QA (`applications-qa.mjs`, 36 checks per run) | **180/180**: Chrome at 360/768/1280 px, Firefox at 360/1280 px |
| Existing applicant browser QA | **97/97** |
| Existing guidance and private request browser QA | **72/72** |
| Existing staff browser QA | Chrome 360/768/1280 and Firefox 360/768/1280 all pass (Firefox 44/44 after a restart; see note) |
| Existing chat widget browser QA | **78/78** |
| Frontend lint, TypeScript, production build | PASS |
| nginx configuration (`nginx -t` in the production image) | PASS |
| Visual inspection | Applicant form at 360 px inspected; no clipping or horizontal scroll |

Notes: browser runs used a disposable local database, Mailpit and local file storage,
never production. The staff suite needed two resets of local test state, not code fixes.
Synthetic archived programmes left by earlier guidance runs changed the expected
programme count, and the suite's deliberate wrong-password checks reached the
five-failure login limit after several runs in a row.

## Open before production

- **CO.7:** a daily backup of the database and the `uploads` volume on the VM, then
  `APPLICATIONS_ENABLED=true` in the VM's `.env`. Until then the feature stays off in
  production and its links are hidden.
- The data-hosting record in `docs/applicant-hosting.md` for uploaded documents.
- Live QA on the VM and Product Owner acceptance for US31, US32, US33 and US6.
- Not in scope: antivirus scanning (staff open files in the browser's viewer only),
  admission decisions, payments, the university's own application system.
