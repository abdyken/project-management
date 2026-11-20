# US6 - Application status in the chat QA

**Record:** 19.11.2026, updated 20.11.2026 after the code reviews. **Status:** implemented, verified locally and in CI, switched on in production 20.11.2026 with live smoke checks (`docs/sprint-7-review.md`); logged-in live run passed and accepted by the Product Owner 20.11.2026.

## Acceptance scenarios

- "What is the status of my application?", "Статус моей заявки?" and "Өтінішімнің мәртебесі қандай?" are recognised; "What is the application deadline?" still goes to the FAQ.
- The answer comes without the model and without personal data, marked `intent: "application_status"`; anonymous visitors are told to log in.
- A logged-in applicant then sees, in the chat, each application's stage and next step in their language, built from the database.

## Verification evidence

- Backend: `backend/tests/test_applications.py` (62 cases; full backend suite 733 passed) on a fresh PostgreSQL/pgvector database after `alembic upgrade head`; migration 0020 also checked down to 0019 and up again.
- Mutation checks: removing the owner filter, letting staff see drafts, or skipping the content check each makes the suite fail.
- Browser: `frontend/e2e/applications-qa.mjs`, 36 checks per run, **180/180** on 20.11.2026 on the local stack with Mailpit (Chrome at 360, 768 and 1280 px, Firefox at 360 and 1280 px): validation, upload through the file picker, removing a scan, deleting a draft, changes requested and resubmitted, accepted, rejected (opened by URL), the programme filter, the chat for a logged-in applicant and for a visitor, EN/RU/KK, no horizontal overflow, no console or runtime errors. Backend CI runs it on every pull request in Chromium at 360 and 1280 px and Firefox at 1280 px.
- Decisions: `docs/adr/0001`-`0004`; API contract: `backend/docs/api/applications.md`.

## Boundaries

- Production: switched on 20.11.2026 after the daily backup of the database and uploads (CO.7) and the hosting record in `docs/applicant-hosting.md`.
- No admission decisions, payments, antivirus scanning or connection to the university's own application system.
