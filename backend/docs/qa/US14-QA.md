# US14 QA record — streaming answers and suggested questions

## Run 1 — 2026-10-02, Chrome

Local run against the Vite app (`http://127.0.0.1:5173`) and the API on port 8000. Chrome only.

| ID | Scenario | Expected | Result |
| --- | --- | --- | --- |
| 14.2 | Suggested question, then watch the answer | Typing indicator until the first chunk, then the text, then a source | PASS — "What English level do I need for bachelor's admission?" showed the preparing indicator, then the FAQ answer and a source link |
| 14.2 | Close while the answer is still arriving | The message is not left broken; resend is offered | PASS — partial text kept, "This answer was interrupted.", Resend completed the same question with a source |
| 14.3 | Document checklist | Several lines render as a list and stay inside the panel at 360 px | PASS — Computer Science (6B06102) local documents rendered as a list; no horizontal overflow at 360 px |
| 14.3 | Note under the input | "Do not enter personal data" | PASS — visible at 360, 768 and 1280 px |
| 14.4 | Starters and follow-ups | 4 starters, then up to 3 follow-up chips; a click sends the question | PASS — four starters on a new session; three follow-ups after an answer; a chip returned a sourced FAQ answer |
| 11.4 | New conversation | New session, dialogue cleared | PASS — messages cleared, a new session id, the previous program answer was gone, four starters returned |
| 13.2 | Rating | One rating per answer, reason on thumbs down, kept across navigation | PASS — thumbs down + Outdated disabled both buttons; the rating was still pressed on `/programs` |
| Layout | Widget at 360, 768 and 1280 px | Chat usable, text wraps | PASS in Chrome — 360 px bottom sheet, 768 px and desktop panel (380 px) with wrapped chips and the personal-data note |

## Run 2 — 2026-10-08, Chromium and Firefox (14.5)

Scripted run with `frontend/e2e/widget-qa.mjs` (Playwright 1.55: Chromium and Firefox 141) against the Vite app and the API on `fix/sprint-2-wrap-up`, at 360, 768 and 1280 px. To make the close-mid-answer case deterministic, the stream request is held for 1.5 s and the chat is closed while it waits.

| ID | Check | Chromium 360 / 768 / 1280 | Firefox 360 / 768 / 1280 |
| --- | --- | --- | --- |
| 14.4 | 4 starter questions; a starter gets a sourced answer; up to 3 follow-up chips | PASS / PASS / PASS | PASS / PASS / PASS |
| 14.3 | "Do not enter personal data"; checklist renders as a list; no horizontal overflow | PASS / PASS / PASS | PASS / PASS / PASS |
| 11.2 | Follow-up "and as an international applicant?" keeps 6B06102 | PASS / PASS / PASS | PASS / PASS / PASS |
| 12 | "Compare 6B06101 and 6B06102" renders side by side as a list | PASS / PASS / PASS | PASS / PASS / PASS |
| 13.2 | Thumbs down + Outdated, one rating, kept after navigating to `/programs` | PASS / PASS / PASS | PASS / PASS / PASS |
| 11.4 | New conversation forgets the program | PASS / PASS / PASS | PASS / PASS / PASS |
| 14.2 | Closing mid-answer leaves "This answer was interrupted." with Resend, never a half answer; Resend completes it | PASS / PASS / PASS | PASS / PASS / PASS |

**78/78 checks passed.** Still open: the same run on the deployed dev environment (`BASE_URL=<dev-url>`) and the "first words within 2 s" scenario with a Gemini key. With a model the first words appear only after the model call (about 1–6 s on the free tier), because the grounding check needs the whole answer before any of it is shown; answers without a model start within a second.
