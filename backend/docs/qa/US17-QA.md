# US17 QA record — program comparison

Date: 2026-10-08. Local run: API and Vite app on `feature/us17-program-comparison`, official catalogue (12 programs). Dev run still open.

| Check | Result |
| --- | --- |
| `GET /api/programs/compare` (`tests/test_compare_api.py`): requested order, document counts, empty values `null`, 2–3 different ids, unknown id named in the 404 | 9 passed |
| `frontend/e2e/compare-qa.mjs` — Chromium and Firefox at 360, 768 and 1280 px | **54/54 PASS** |

Scripted checks per browser and width: three programs added from the catalogue cards and a fourth disabled; the compare bar shows 3/3; `/compare` shows the programs side by side (a table from 640 px, one block per field on phones); unpublished deadlines and lists read "Not published"; fees match the catalogue; no horizontal overflow; the selection survives a reload; removing a program keeps the other two without a reload; fewer than two programs show the "Pick two or three programs" state; a link with an unknown id shows "Program not found".

US17QATest: Pass (three programs side by side with fee, language, deadlines and documents; works at 360 px) — PASS locally. Fail case (a fourth program can be added, or an empty value shown as a number) — does not happen.
