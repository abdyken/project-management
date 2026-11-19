# US33 - Application review queue QA

**Record:** 19.11.2026. **Status:** implemented and verified locally and in CI; live run and PO acceptance open.

## Acceptance scenarios

- Staff see submitted applications oldest first, filter by status and programme, open one, read the form and download each document.
- Allowed changes only: submitted → in review, changes requested, accepted, not accepted; in review → the last three. "Changes requested" and "not accepted" need a note.
- The applicant reads the note in the account; e-mails for changes requested, accepted and not accepted go out right after the change, contain only a link, and are retried hourly if sending fails.
- Accepted and not-accepted applications are closed; after not accepted the applicant may apply again.

## Verification evidence

- Backend: `backend/tests/test_applications.py` (25 cases) on a fresh PostgreSQL/pgvector database after `alembic upgrade head`; migration 0020 also checked down to 0019 and up again.
- Mutation checks: removing the owner filter, letting staff see drafts, or skipping the content check each makes the suite fail.
- Browser: `frontend/e2e/applications-qa.mjs`, **63/63** checks on the local stack with Mailpit: Chromium at 360 and 1280 px, Firefox at 360 and 1280 px; EN, RU and KK headings; no horizontal overflow; no runtime errors. Backend CI runs it on every pull request.
- Decisions: `docs/adr/0001`-`0004`; API contract: `backend/docs/api/applications.md`.

## Boundaries

- Local and CI results, not production: `APPLICATIONS_ENABLED` stays false on the VM until a daily backup of the database and the uploads volume runs (ADR 0003, Sprint 7 CO.7).
- No admission decisions, payments, antivirus scanning or connection to the university's own application system.
