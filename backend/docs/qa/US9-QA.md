# US9 QA record — admissions analytics dashboard

Date: 2026-10-15. Local run: full Docker stack on `feature/sprint-4-staff-area`. Live run: after deployment.

| Check | Result |
| --- | --- |
| `tests/test_analytics.py`: fixed dataset counted by hand — 5 questions, 4 conversations, 2 unanswered in 7 days; per day in Kazakhstan time (a question at 23:30 local counts for that day); repeated questions grouped and phone numbers redacted; most cited FAQ item; languages en 3 / ru 1 / kk 1; ratings and thumbs-down reasons; 1-day window; 401 without login; `days=31` rejected; no session ids | 3 passed |
| `frontend/e2e/staff-qa.mjs` at 1280 px, US9 part | **3/3 PASS** |

Browser checks: the chart has one column per day of the period; hovering a day shows its answered and unanswered counts; the question count is shown. Chart colours (#2a78d6 answered, #eb6834 not answered) pass the palette checks on the card surface (lightness, chroma, colour-blind separation, 3:1 contrast); every series has a legend, and the per-day numbers are also available as a table.

US9QATest: Pass (7 days: questions per day, answered/unanswered share, top questions and thumbs-down reasons match the test dataset) — PASS locally. Fail case (a number differs from the hand count, the dashboard opens without login) — does not happen.
