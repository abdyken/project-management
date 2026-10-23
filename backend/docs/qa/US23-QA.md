# US23 QA record — applicant account

Date: 2026-10-22. Environment: local PostgreSQL 16/pgvector and Mailpit, Python API and Vite frontend. Branch: `feature/sprint-5-applicant-area`. Live acceptance remains open.

| Check | Result |
| --- | --- |
| `tests/test_applicant.py` (34 integration cases across Sprint 5) | PASS: registration validation; salted scrypt; normalized e-mail; verification expiry and single use; resend token/password rotation; verified-account registration unchanged; unverified login rejected; login throttling; cookie flags and hash storage; expiry/logout; origin protection; staff-cookie isolation; private endpoints require applicant login; no-store; SMTP failure rollback; absent SMTP/disabled-feature errors; cascading deletion |
| `frontend/e2e/applicant-qa.mjs`, Chromium and Firefox at 360/768/1280 px | **97/97** across Sprint 5: actual SMTP registration, verification, session reload, login/logout and protected browser-back behavior; EN/RU/KK labels; no horizontal overflow or runtime errors |
| Fresh migration through 0018; 0018 → 0017 → 0018 on a disposable database | PASS |
| Initial complete backend suite on isolated `admissions_sprint5_tests` | **592 passed, 1 skipped**; the existing catalogue-import check needs a populated catalogue, now seeded by CI |
| Frontend lint / TypeScript / production build | PASS |

US23QATest pass and fail cases pass locally. A test account is deleted at the end of browser QA. Live hosting choice, real sender configuration and PO acceptance are not inferred from these local runs; see `docs/applicant-hosting.md`.
