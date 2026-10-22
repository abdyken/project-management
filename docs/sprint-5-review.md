# Sprint 5 — implementation review and QA

**Sprint:** 17.10–23.10.2026. **Record:** 22.10.2026, before the scheduled review.

## Goal and implementation

Verified applicants can save separate local/international program checklists, keep prepared-document progress, opt into e-mail deadline reminders and download printable checklists. The public catalogue and staff area retain their existing behavior.

| Story | Built | Local verification | Acceptance |
| --- | --- | --- | --- |
| US23 Applicant Account | Registration/verification, isolated sessions, login/logout, account deletion and privacy information | `backend/docs/qa/US23-QA.md` | Live hosting/SMTP decision and PO sign-off open |
| US24 Saved Programs | Idempotent save/list/remove per applicant and type, archived-program handling | `backend/docs/qa/US24-QA.md` | Live QA open |
| US25 Personal Document Tracker | Current official requirements, prepared flags, progress, replacement reconciliation | `backend/docs/qa/US25-QA.md` | Live QA open |
| US7 Deadline Reminders | Opt-in, hourly worker, 7/1/0-day milestones, multilingual e-mail, ledger and retry | `backend/docs/qa/US7-QA.md` | Real live sender and acceptance open |
| US26 Checklist PDF | Public and personal PDF, Unicode EN/RU/KK, official source/contact and unknown-data warnings | `backend/docs/qa/US26-QA.md` | Live QA open |

## Verification

| Check | Result |
| --- | --- |
| Initial backend suite, isolated PostgreSQL database | **592 passed, 1 existing catalogue-import prerequisite skip**; CI now seeds the official catalogue so that check also runs |
| Sprint 5 integration cases (`test_applicant.py`) | **34 passed**, included above |
| Applicant browser QA, Chromium/Firefox × 360/768/1280 px | **97/97**; also tests EN/RU/KK account labels |
| Existing compare / language / widget / staff browser regressions | **60/60**, **144/144**, **78/78**, **88/88** |
| Frontend lint, TypeScript and production build | PASS; existing Vite large-chunk advisory remains |
| New backend static checks and formatting | PASS |
| Migration from empty DB; 0018 downgrade to 0017 and upgrade | PASS on a separate disposable database |
| Real SMTP delivery to local Mailpit | PASS: verification and Kazakh deadline reminder; official deadline and remaining documents; repeated job sends nothing |
| PDF text extraction and rendered international Kazakh checklist | PASS; both pages visually inspected |
| Backlog workbook preservation | Only the five Sprint 5 QA references changed in original sheets; five story cards and five QA sheets added using the existing format |
| Running assistant catalogue checks | **192/192** |
| Evaluation set v3, no Gemini key | **63/70 (90%)**, **9/9** correct fallbacks, **0** invented facts; same recorded baseline |
| Docker API and web production images | PASS, including slim-model equivalence and precomputed FAQ embeddings |
| Applicant browser matrix against the built nginx/API stack on local port 8081 | **97/97** |

The machine ran out of disk space during the first Docker build and its test services temporarily reported storage errors. The unused full browser download from this task was removed; Docker Desktop was restarted without deleting volumes, and the built-in `desktop-linux` builder successfully built both images. The database and mail inbox recovered; checks above were completed against healthy services. The existing custom builder was not removed or reconfigured.

## Carry-over fixes and boundaries

- Questions about unpublished teaching languages now use the explicit catalogue unknown response even with a model configured. This addresses the two recorded 7M01701/8D01701 cases without guessing from their titles. Two model-blocking regression tests cover them.
- The standalone catalogue import now registers the staff-editor foreign-key target, fixing startup into an empty catalogue.
- The full legacy browser matrix passes, including Firefox, which was unavailable for the original Sprint 4 local run. These remain local results; earlier sprint PO acceptance is not invented.
- The assistant's seven existing v3 evaluation misses remain unchanged. This sprint does not claim perfect model accuracy.
- Reminder delivery uses ordinary SMTP and an idempotent database ledger; a crash between external acceptance and commit can still cause a retry. The worker does not backfill a milestone after a full-day outage.
- Applicant accounts default off on the VM until the project owner records the hosting/SMTP decision described in `applicant-hosting.md`. No remote data, deployment or PO acceptance was changed by local implementation.

## Review and retro actions

1. Review the feature PR and its CI results before merging to `main`.
2. Record the applicant hosting decision and configure the real mail sender; enable accounts and repeat the story scenarios on the live site.
3. Record accepted/returned stories at the Product Owner review. Continue the Sprint 2–4 live-acceptance carry-over explicitly rather than treating local success as sign-off.

Browser QA found and resolved immediate checkbox feedback, the reminder-language label and multilingual mobile-header wrapping. Keep the applicant matrix in CI so these flows are checked on every PR.
