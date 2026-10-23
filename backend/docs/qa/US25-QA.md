# US25 QA record — personal document tracker

Date: 2026-10-22. Local API, PostgreSQL, Vite and Mailpit on `feature/sprint-5-applicant-area`. Live acceptance open.

| Check | Result |
| --- | --- |
| `tests/test_applicant.py` | PASS: mark/unmark and idempotence; ordered current requirements; prepared/total counts; per-account and per-applicant-type isolation; unsaved/wrong-type/deleted document rejected; staff replacement cascades stale progress; new requirements start unprepared; missing-list warning; archived lists read-only |
| Applicant browser matrix (part of **97/97**) | PASS: immediate checkbox feedback, prepared state survives reload, international state stays separate, personal PDF includes progress; EN/RU/KK and 360/768/1280 px in Chromium/Firefox |
| Existing staff-area browser regression | **88/88**, including catalogue/checklist editing and restart-safe data ownership |

The first browser run exposed delayed checkbox feedback; the UI now holds the pending choice and applies the server-returned snapshot to the shared query cache. A failed update restores the stored state and shows an error. Requirement details reuse the existing checklist note formatter rather than duplicate labels.

US25QATest pass and fail cases pass locally. Actual document files are not collected.
