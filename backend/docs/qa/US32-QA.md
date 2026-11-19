# US32 - Document upload QA

**Record:** 19.11.2026. **Status:** implemented and verified locally and in CI; live run and PO acceptance open.

## Acceptance scenarios

- PDF, JPEG and PNG scans up to 10 MB each and 40 MB per application upload to a checklist document or as "other document"; the scan ticks that document in the tracker.
- A file whose content is not PDF/JPEG/PNG is refused whatever its name; empty and oversized files are refused; nothing is left on disk.
- Downloads return the exact bytes as an attachment with nosniff and no-store; folder parts and control characters are removed from names.
- Another applicant gets 404 for the application and the file; staff never see drafts; deleting a document, a draft or the account deletes the files.

## Verification evidence

- Backend: `backend/tests/test_applications.py` (25 cases) on a fresh PostgreSQL/pgvector database after `alembic upgrade head`; migration 0020 also checked down to 0019 and up again.
- Mutation checks: removing the owner filter, letting staff see drafts, or skipping the content check each makes the suite fail.
- Browser: `frontend/e2e/applications-qa.mjs`, **63/63** checks on the local stack with Mailpit: Chromium at 360 and 1280 px, Firefox at 360 and 1280 px; EN, RU and KK headings; no horizontal overflow; no runtime errors. Backend CI runs it on every pull request.
- Decisions: `docs/adr/0001`-`0004`; API contract: `backend/docs/api/applications.md`.

## Boundaries

- Local and CI results, not production: `APPLICATIONS_ENABLED` stays false on the VM until a daily backup of the database and the uploads volume runs (ADR 0003, Sprint 7 CO.7).
- No admission decisions, payments, antivirus scanning or connection to the university's own application system.
