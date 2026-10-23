# Sprint 5 — applicant accounts and personal checklists

**Sprint:** 17.10–23.10.2026. **Implementation record:** 22.10.2026.

**Sprint goal:** applicants verify an e-mail account, save programs, track the documents they have prepared, receive opted-in deadline reminders and download printable checklists.

**Stories:** US23 Applicant Account, US24 Saved Programs, US25 Personal Document Tracker, US7 Deadline Reminders and US26 Checklist PDF. Story and QA cards are in `table.xlsx`; the original owners and deadlines are retained there.

## Order and tasks

| ID | Story | Task | Implementation |
| --- | --- | --- | --- |
| 23.0 | US23 | Hosting prerequisite | [applicant-hosting.md](applicant-hosting.md); live accounts default off until the decision and SMTP are recorded |
| 23.1 | US23 | Accounts, verification and isolated sessions | Migration 0018, existing scrypt password hashing, single-use hashed 24-hour verification token, 7-day HttpOnly/Secure/Strict applicant cookie, throttling and origin checks |
| 23.2 | US23 | Registration, verification, login, logout and deletion pages | `/account/register`, `/account/verify`, `/account/login`, `/account`; EN/RU/KK labels; private cache cleared on logout |
| 24.1 | US24 | Save/list/remove programs | Idempotent save per program and applicant type; user-owned records; archived programs remain visible with a warning |
| 24.2 | US24 | Program detail and account integration | Save action, return links, removal and empty/error states |
| 25.1 | US25 | Current checklist and prepared status | Existing requirements are the source of truth; owner/type/document checks; deleting/replacing requirements cascades old progress |
| 25.2 | US25 | Personal tracker | Accessible checkboxes, immediate feedback, persisted completed/total count, missing-data and archive warnings |
| 7.1 | US7 | E-mail transport and delivery ledger | Configurable SMTP/TLS; verified accounts only; explicit opt-in; published dates only; milestones at 7, 1 and 0 days; retry failures; deduplicate delivered milestones |
| 7.2 | US7 | Scheduler and preferences | Hourly API worker, manual `backend/scripts/send_reminders.py`; EN/RU/KK message language, opt-out, current remaining documents |
| 26.1 | US26 | Printable PDFs | Shared current-checklist snapshot, public and authenticated personal exports, EN/RU/KK labels, bundled licensed Unicode font, source/contact and unknown-value warnings |
| QA | all | API, browser, mail, PDF and migration checks | `backend/tests/test_applicant.py`, `frontend/e2e/applicant-qa.mjs`; story-specific QA records |
| CI | all | Reproducible browser checks | Locked Playwright dependency; Backend CI starts local SMTP/API/frontend and runs the applicant matrix |
| CO | US16 | Do not infer a teaching language from a program title | Missing-language questions bypass model rephrasing; regression cases for 7M01701 and 8D01701 |

The Sprint 4 standalone catalogue import also needed its staff-editor foreign-key model registered. This is fixed so the real start command can import an empty database.

## Local run

```bash
docker compose up --build
# Portal: http://localhost:8080
# Local mail inbox: http://localhost:8025
```

Register with an e-mail address, open its message in Mailpit, follow the link and press **Verify e-mail**. Local messages stay inside Mailpit. The local Docker stack enables applicant accounts; the VM deployment defaults them off.

For host development, start `docker compose up -d db mailpit`, use `backend/.env.example`, set `APPLICANT_ACCOUNTS_ENABLED=true` and `PUBLIC_BASE_URL=http://localhost:5173`, then follow the root README. Keep the cookie Secure setting enabled on localhost.

## Acceptance

| Story | Pass scenario | Fail scenario |
| --- | --- | --- |
| US23 | Register, receive and verify the e-mail, log out and log in again; reload preserves the session | Unverified/expired/logged-out credentials or another cookie cannot read account data; reused verification fails; deleting the account removes all dependent records |
| US24 | Save local and international lists, reload and return to each program; remove one without changing the other | Repeated saves create no duplicates; another applicant cannot see or remove the list; missing/archived programs cannot be newly saved |
| US25 | Mark/unmark documents, reload and see matching progress, PDF and reminder contents | A document of another program/type is rejected; replacing requirements removes stale progress; an unpublished list warns |
| US7 | Opt in, receive a due message with the official date and remaining documents; repeat the job without a duplicate | Opted-out/unverified/deleted users, archived programs and unpublished dates produce no mail; delivery failure is retried |
| US26 | Download public/personal PDFs in all three languages; current facts and personal progress match the portal | Missing/invalid program, type or language is rejected; private PDF requires login; unknown data stays explicit |

**Definition of Done:** reviewed PR with green CI; migrations and API contract in the same change; official facts only; live QA and PO sign-off before acceptance. Local tests do not establish live acceptance. Sprint 2–4 live acceptance remains open in the records; this sprint does not fabricate their sign-off.

Known delivery boundary: the database ledger prevents repeated successful scheduled sends and overlapping jobs. As with ordinary SMTP, a process crash after SMTP accepts a message but before the database commit can cause a retry; exactly-once external delivery is not claimed. The hourly job checks the current local calendar day in Asia/Almaty; it does not backfill milestones missed during a full-day outage.
