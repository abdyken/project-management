# US11 QA record — follow-up questions in context

Date: 2026-10-08. Local run of the whole stack (API on `fix/sprint-2-wrap-up`, Vite app, official catalogue and FAQ, no `GEMINI_API_KEY`). The dev environment run is still open: it needs the Sprint 2 branches deployed.

## 11.3 Integration tests

`uv run pytest tests/test_conversation.py tests/test_conversation_context.py tests/test_follow_ups_api.py tests/test_retention.py`:

| Area | Covered |
| --- | --- |
| Storage (11.1) | Turns stored per session with role, text and sources; the last 6 turns are read, oldest first; turns older than 30 days are deleted (by the API on start and every 24 h, and by `scripts/purge_chat_turns.py`) |
| Follow-ups (11.2) | Applicant type, program, document and catalogue topics carried into "and as an international applicant?", "and for 6B06101?", "and the fee?", "and the deadline?"; questions with their own subject are never rewritten |
| FAQ follow-ups | "And when do I have to apply for it?" after the dormitory cost answer gets the dormitory deadline item (faq-023); an unrelated question after it still gets the fallback |
| Session isolation | A follow-up in another session never uses the earlier program or FAQ topic; a new session id forgets the program |
| Time budget | A request that times out stores no turns, so a resend does not duplicate the conversation |

## US11QATest (widget, `frontend/e2e/widget-qa.mjs`)

| Scenario | Expected | Chrome (Chromium) | Firefox |
| --- | --- | --- | --- |
| "Which documents do I need for 6B06102 as a local applicant?", then "and as an international applicant?" | International list for 6B06102, program named | PASS at 360, 768, 1280 px | PASS at 360, 768, 1280 px |
| *New conversation*, then "and for international?" | Asks which program; earlier turns gone | PASS | PASS |
| Fail case: another session's context | Never used | PASS (API tests above) | — |
| Deferred: the conversation continues on another device | Not built | — | — |

The evaluation set's follow-up case ("And when do I have to apply for it?") now passes: 35/40 against the local API without a model, up from 34/40.
