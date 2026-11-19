# Online applications - Sprint 7 (US31, US32, US33, US6)

Decisions: `docs/adr/0001` (form fields), `0002` (statuses), `0003` (document storage),
`0004` (status in the chat). All paths start with `/api`; errors use `{error_code, message}`.

Everything here needs `APPLICANT_ACCOUNTS_ENABLED=true` and `APPLICATIONS_ENABLED=true`;
otherwise `503 APPLICATIONS_UNAVAILABLE` (checked before the login cookie). `GET /api/features`
(public) returns `{applicant_accounts, applications}` so the frontend hides switched-off links. Applicant routes use the applicant cookie and its
origin check (US23); staff routes use the staff cookie (US19). Private responses are
`Cache-Control: no-store`.

## Applicant: `/applicant/applications`

| Method and path | Input | Result |
| --- | --- | --- |
| GET `` | - | `{items: [ApplicationSummary], total}`, newest change first |
| POST `` | `{program_id, applicant_type, language?}` | 201 `Application` in `draft`. 404 `PROGRAM_NOT_FOUND` for unknown or archived programmes; 409 `APPLICATION_EXISTS` while a non-rejected application exists for the same programme and type; 409 `TOO_MANY_APPLICATIONS` above 10 |
| GET `/{id}` | - | `Application`; another applicant's id is 404 `APPLICATION_NOT_FOUND` |
| PUT `/{id}` | form fields (below), optional `language` | `Application`. 409 `APPLICATION_LOCKED` unless `draft` or `needs_changes` |
| POST `/{id}/submit` | - | `Application` in `submitted`. 422 `APPLICATION_INCOMPLETE` lists what is missing (`missing` in the response says the same before submitting) |
| DELETE `/{id}` | - | 204; drafts only, with their files. Otherwise 409 `APPLICATION_LOCKED` |
| POST `/{id}/documents` | multipart `file`, optional `requirement_id` | 201 `Document`. Editable applications only. Errors below |
| GET `/{id}/documents/{document_id}` | - | the file as an attachment |
| DELETE `/{id}/documents/{document_id}` | - | 204; editable applications only; the file is removed |
| GET `/status?language=en` | `en`, `ru` or `kk` | US6: `{answer, items: [{id, program_id, status, stage, next_step}]}` |

**Form fields** (all optional in a draft; ADR 0001): `full_name` (≤200), `date_of_birth`
(1900-01-01 to today), `citizenship` (≤100), `phone` (`^\+?[0-9 ()-]{6,30}$`),
`education_level` (`school`, `college`, `bachelor`, `master`), `graduation_year`
(1950-2100), `exam_total` (0-150, optional), `consent` (boolean). Unknown fields are 422.
Submitting needs every field except `exam_total`, `consent: true` and at least one document.

**Application** adds `program` (ProgramOut), `applicant_type`, `status`, `language`,
`staff_note`, `editable`, timestamps, `requirements` (the programme's checklist for that
applicant type, each with `uploaded`), `documents`, `bytes_used`, `bytes_limit` and `missing`.

## Documents (US32, ADR 0003)

- PDF, JPEG or PNG, recognised by the first bytes; the name and the browser's type are not
  trusted. Otherwise 415 `UNSUPPORTED_FILE_TYPE`; an empty file is 422 `EMPTY_FILE`.
- At most 10 MB per file (`UPLOAD_MAX_BYTES`), 40 MB per application
  (`APPLICATION_MAX_BYTES`) and 100 MB per account (`APPLICANT_MAX_BYTES`): 413
  `FILE_TOO_LARGE`, `APPLICATION_FULL` or `ACCOUNT_STORAGE_FULL`, whichever limit the file
  hits first. At most 20 documents: 409 `TOO_MANY_DOCUMENTS`. With less than
  `UPLOAD_MIN_FREE_BYTES` (2 GB) free on the volume, uploads are 507 `UPLOADS_PAUSED`.
  nginx accepts bodies up to 11 MB on the upload route only; every other API route keeps 1 MB.
- The file is written without holding the application's row lock, then every limit is checked
  again under the lock before the row is committed; a file that loses that race is deleted.
- `requirement_id` must be on the application's checklist (422 `INVALID_REQUIREMENT`);
  the upload also ticks that document in the tracker (US25). Without it the scan is an
  "other document".
- Files are streamed in 64 KB chunks to `UPLOAD_DIR` (the `uploads` volume) under a random
  32-hex name; the original name is cleaned of folders and control characters and its
  extension is replaced by the detected type's (`Diploma.bat` that is a PDF becomes
  `Diploma.pdf`). Downloads are `Content-Disposition: attachment`,
  `X-Content-Type-Options: nosniff`, `no-store`. A file missing on disk is logged and is 404.
- Files are deleted with their document, the draft, or the account (`DELETE /applicant/me`
  locks the applicant's applications first, so an upload in flight is either collected or fails).
- The hourly worker deletes drafts unchanged for `DRAFT_RETENTION_DAYS` (30) with their files,
  and files older than an hour that no document refers to (including leftover `.part` files).

## Staff: `/staff/applications` (US33)

| Method and path | Input | Result |
| --- | --- | --- |
| GET `` | `status` = `open` (default: submitted and in review), one status, or `all`; `program_id`; `offset`; `limit` (≤100) | `{items, total}`, oldest submission first; items add `applicant_email` and `full_name`. Drafts never appear |
| GET `/{id}` | - | `Application` plus `applicant_email`; drafts are 404 |
| GET `/{id}/documents/{document_id}` | - | the file as an attachment |
| POST `/{id}/status` | `{status, note?}` | `submitted` → `in_review`, `needs_changes`, `accepted`, `rejected`; `in_review` → the last three. Otherwise 409 `INVALID_STATUS_CHANGE`. `needs_changes` and `rejected` need a note (422 `NOTE_REQUIRED`). Cross-origin requests are 403 |

Statuses (ADR 0002): only `draft` and `needs_changes` are editable by the applicant;
`accepted` means the documents are complete, not an admission decision; after `rejected`
the applicant may start again.

**E-mails:** `needs_changes`, `accepted` and `rejected` send "your application status
changed" right after the change (a background task), with the stage, the next step and a
link to the application, never the note. The hourly worker retries failed sends; the
`notified_status` column makes each status e-mail go out once. Every staff status change
resets it, so a second "changes requested" is e-mailed again. The row is claimed and the
lock released before talking to SMTP; a failed send gives the claim back for the retry.

Deleting a programme that has applications is refused by the database (`ON DELETE RESTRICT`):
archive it instead.

## Status in the chat (US6, ADR 0004)

`POST /assistant/ask` and `/ask/stream` recognise status questions in English, Russian and
Kazakh when both switches are on: the visitor's own application ("my application", "моя
заявка", "өтінішім") plus a status word ("status", "accepted", "где", "қайда" in "where is
my…", …), e.g. "What is the status of my application?", "Моя заявка принята?",
"Өтінішім қабылданды ма?". General questions ("How do I submit my application?", "Какие
этапы подачи заявки?") still go to the FAQ. They answer without the model and without
personal data (a pointer to My applications), and
add `intent: "application_status"` to the response and the stream's `done` event (absent
for all other answers). The widget then calls `GET /applicant/applications/status` when the
visitor is logged in and shows the stage and next step for each application.
