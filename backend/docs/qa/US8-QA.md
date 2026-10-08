# US8 QA record — multilingual assistant

Date: 2026-10-09. Local run: API on `feature/us8-us18-multilingual-faq`, 75 FAQ items (66 with official Russian, 57 with official Kazakh text), 64-program catalogue, no `GEMINI_API_KEY`. Dev run still open.

## What changed

- The answer comes in the language of the applicant's own question (Kazakh / Russian / English), also for follow-ups.
- FAQ items carry the official RU/KZ text of their source page; items without one answer in English with a note saying so. Nothing is machine-translated (`app/data/faq_review.md` lists every gap and why).
- Every item is indexed per language; Kazakh and Russian questions are searched against their own language plus English, with an IDF-weighted word overlap next to the embedding similarity, because the embedding model barely understands Kazakh.
- Fallback, checklist and catalogue answers have fixed Russian and Kazakh wording with the official program titles.

## Checks

| Check | Result |
| --- | --- |
| Each item's own question in its language finds the item (no model) | en 74/75, ru 66/66, kk 56/57 — before US8 Kazakh questions mostly fell back |
| `tests/test_multilingual.py` (detection, kk/ru answers and sources, English-with-note, kk/ru fallback, checklist, catalogue, Kazakh titles, model prompt language, follow-up keeps the language, kk/ru suggestions) | 20 passed |
| Evaluation set v3, Kazakh / Russian cases | 8/8, 6/7 |
| `frontend/e2e/language-qa.mjs` (Chromium + Firefox, 360/768/1280 px): Kazakh and Russian starter questions, clicked, answered in that language | 144/144 |

US8QATest: "Жатақхана қанша тұрады?" → Kazakh answer from the dormitory item with its Kazakh source — PASS; "Нужно ли сдавать ЕНТ?" → Russian answer — PASS. Fail case (answer in another language, or a fact missing from the official RU/KZ page) — an item without an official translation is given in English with a note, never translated.
