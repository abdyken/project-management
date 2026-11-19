# US32 - Document upload QA

**Record:** 19.11.2026, updated 20.11.2026 after the code reviews. **Status:** implemented and verified locally and in CI; live run and PO acceptance open.

## Acceptance scenarios

- PDF, JPEG and PNG scans up to 10 MB each, 40 MB per application and 100 MB per account upload to a checklist document or as "other document"; the scan ticks that document in the tracker.
- A file whose content is not PDF/JPEG/PNG is refused whatever its name; empty and oversized files are refused; nothing is left on disk.
- Downloads return the exact bytes as an attachment with nosniff and no-store; folder parts and control characters are removed from names and the extension always matches the detected type.
- Uploads pause with 507 when the volume has under 2 GB free; abandoned drafts (30 days) and orphaned files are cleaned up hourly.
- Another applicant gets 404 for the application and the file; staff never see drafts; deleting a document, a draft or the account deletes the files.

## Verification evidence

- Backend: `backend/tests/test_applications.py` (62 cases; full backend suite 733 passed) on a fresh PostgreSQL/pgvector database after `alembic upgrade head`; migration 0020 also checked down to 0019 and up again.
- Mutation checks: removing the owner filter, letting staff see drafts, or skipping the content check each makes the suite fail; after the review, 17 more mutations (limits off by one, a document reachable through another application, the account deletion lock, the download extension, the JPEG signature and others) are all caught.
- Browser: `frontend/e2e/applications-qa.mjs`, 36 checks per run, **180/180** on 20.11.2026 on the local stack with Mailpit (Chrome at 360, 768 and 1280 px, Firefox at 360 and 1280 px): validation, upload through the file picker, removing a scan, deleting a draft, changes requested and resubmitted, accepted, rejected (opened by URL), the programme filter, the chat for a logged-in applicant and for a visitor, EN/RU/KK, no horizontal overflow, no console or runtime errors. Backend CI runs it on every pull request in Chromium at 360 and 1280 px and Firefox at 1280 px.
- Decisions: `docs/adr/0001`-`0004`; API contract: `backend/docs/api/applications.md`.

## Boundaries

- Local and CI results, not production: `APPLICATIONS_ENABLED` stays false on the VM until a daily backup of the database and the uploads volume runs (ADR 0003, Sprint 7 CO.7).
- No admission decisions, payments, antivirus scanning or connection to the university's own application system.
