# US22 QA record — unanswered question inbox

Date: 2026-10-15. Local run: full Docker stack on `feature/sprint-4-staff-area`. Live run: after deployment.

| Check | Result |
| --- | --- |
| `tests/test_inbox.py`: 401 on every endpoint, grouping and counts, e-mail redacted, no session ids, period filter, dismiss handles the whole group (with who and when) and 404 the second time, answering needs a published FAQ item (409 for a draft or unknown id), answered groups list their `faq_id`, a later ask starts a new group | 7 passed |
| `tests/test_export_unanswered.py` after moving the grouping into `app/followups/inbox.py` | passed |
| `frontend/e2e/staff-qa.mjs` at 1280 px, US22 part | **6/6 PASS** |

Browser checks: a new off-FAQ question asked in the chat has no FAQ source and appears in the inbox; "Answer" opens the FAQ editor with the question filled in; saving the draft and publishing it marks the inbox question as answered; the same question in the chat now cites the new item; the question is listed under "Answered". The test item is retired at the end of the run.

Cut for Sprint 4 (one developer): thumbs-down answers are not listed in the inbox; they stay in `scripts/export_negative_feedback.py` and the dashboard reasons.

US22QATest: Pass (a question the assistant could not answer appears with its count; the officer answers it, publishes, and the same question gets that answer with its source) — PASS locally. Fail case (a session id or e-mail/phone in the inbox; an answered question left in "new") — does not happen.
