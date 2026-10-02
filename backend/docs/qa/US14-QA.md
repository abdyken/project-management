# US14 QA record — streaming answers and suggested questions

Local run on 2026-10-02 against the Vite app (`http://127.0.0.1:5173`) and the API on port 8000. Chrome only. Firefox was not run in this pass.

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

Firefox at the same three widths is still open.
