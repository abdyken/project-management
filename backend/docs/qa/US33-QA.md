# US33 - Application review queue QA

**Record:** 19.11.2026, updated 20.11.2026 after the code reviews. **Status:** implemented, verified locally and in CI, switched on in production 20.11.2026 with live smoke checks (`docs/sprint-7-review.md`); logged-in live run passed and accepted by the Product Owner 20.11.2026.

## Acceptance scenarios

- Staff see submitted applications oldest first, filter by status and programme, open one, read the form and download each document.
- Allowed changes only: submitted → in review, changes requested, accepted, not accepted; in review → the last three. "Changes requested" and "not accepted" need a note.
- The applicant reads the note in the account; e-mails for changes requested, accepted and not accepted go out right after the change, contain only a link, and are retried hourly if sending fails.
- Accepted and not-accepted applications are closed; after not accepted the applicant may apply again.

## Verification evidence

- Backend: `backend/tests/test_applications.py` (62 cases; full backend suite 733 passed) on a fresh PostgreSQL/pgvector database after `alembic upgrade head`; migration 0020 also checked down to 0019 and up again.
- Mutation checks: removing the owner filter, letting staff see drafts, or skipping the content check each makes the suite fail.
- Browser: `frontend/e2e/applications-qa.mjs`, 36 checks per run, **180/180** on 20.11.2026 on the local stack with Mailpit (Chrome at 360, 768 and 1280 px, Firefox at 360 and 1280 px): validation, upload through the file picker, removing a scan, deleting a draft, changes requested and resubmitted, accepted, rejected (opened by URL), the programme filter, the chat for a logged-in applicant and for a visitor, EN/RU/KK, no horizontal overflow, no console or runtime errors. Backend CI runs it on every pull request in Chromium at 360 and 1280 px and Firefox at 1280 px.
- Decisions: `docs/adr/0001`-`0004`; API contract: `backend/docs/api/applications.md`.

## Boundaries

- Production: switched on 20.11.2026 after the daily backup of the database and uploads (CO.7) and the hosting record in `docs/applicant-hosting.md`.
- No admission decisions, payments, antivirus scanning or connection to the university's own application system.
