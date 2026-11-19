# US31 - Online application form QA

**Record:** 19.11.2026. **Status:** implemented and verified locally and in CI; live run and PO acceptance open.

## Acceptance scenarios

- From a saved checklist the applicant starts an application (one per programme and applicant type, until it is rejected), fills in the form and saves it as a draft.
- Submit stays blocked, with the list of what is missing, until every required field, consent and at least one document are there; then the application is submitted and read-only.
- Invalid input is refused: phone format, a future date of birth, out-of-range years or scores, unknown fields (e.g. an IIN).
- After "changes requested" the applicant edits and submits again; a draft can be deleted with its files.

## Verification evidence

- Backend: `backend/tests/test_applications.py` (25 cases) on a fresh PostgreSQL/pgvector database after `alembic upgrade head`; migration 0020 also checked down to 0019 and up again.
- Mutation checks: removing the owner filter, letting staff see drafts, or skipping the content check each makes the suite fail.
- Browser: `frontend/e2e/applications-qa.mjs`, **63/63** checks on the local stack with Mailpit: Chromium at 360 and 1280 px, Firefox at 360 and 1280 px; EN, RU and KK headings; no horizontal overflow; no runtime errors. Backend CI runs it on every pull request.
- Decisions: `docs/adr/0001`-`0004`; API contract: `backend/docs/api/applications.md`.

## Boundaries

- Local and CI results, not production: `APPLICATIONS_ENABLED` stays false on the VM until a daily backup of the database and the uploads volume runs (ADR 0003, Sprint 7 CO.7).
- No admission decisions, payments, antivirus scanning or connection to the university's own application system.
