# US12 QA record — catalogue facts in the chat

Date: 2026-10-08. Local run: API on `feature/us12-catalogue-tools` with the official catalogue (12 programs) and FAQ (35 items), no `GEMINI_API_KEY` (catalogue answers built from the catalogue records). The dev environment run is still open: it needs this branch deployed.

## 12.3 Catalogue answer check

`ASSISTANT_BASE_URL=http://localhost:8000 uv run python scripts/check_catalogue_answers.py` asks the fee, deadline and language of every program (12 × 3 = 36 questions) and compares each answer with `catalogue.json`: every published fee and date must be in the answer, an empty value must be answered as not published, no other number may appear, and the program page must be linked.

| Environment | Result |
| --- | --- |
| Local API, no model | **36/36 PASS** |
| pytest (`tests/test_catalogue_check.py`, same check in-process) | 38 passed |
| Dev | PENDING — deploy, then run the script with `ASSISTANT_BASE_URL=<dev-url>`; with `GEMINI_API_KEY` set the same check covers model answers |

## US12QATest

| Scenario | Expected | Local result |
| --- | --- | --- |
| "How much does one ECTS cost for Information Systems (7M06101)?" | KZT and USD fee per ECTS from the catalogue, program link | PASS — "Information Systems (master, 7M06101) costs 27,000 KZT (about USD 90) per ECTS credit…", source `https://sdu.edu.kz/en/information-systems/` |
| "Compare 6B06101 and 6B06102" | Fee, language and both deadlines side by side | PASS — one line each for tuition, language, local and international deadline and faculty, both program pages cited |
| A fee or deadline that is empty in the catalogue | "Not published yet" and the office contact, no number | PASS — "When is the application deadline for 7M06101?" → "…local applicants not published yet, international applicants not published yet. SDU Admissions Office…"; no source cited |
| Deferred: total cost of the degree | Moved to US28 | Not built; a model answer with a computed total is rejected by the grounding check |

## Evaluation set v2 (no regression)

`scripts/run_accuracy_test.py` against the same local API, no model: **34/40**, 9/9 correct fallbacks, 0 invented facts, tuition 2/2 — identical to the Sprint 1 baseline in `docs/serdar-ai-tasks/T10.5-evaluation-set-v2.md`. The 6 failures are the known ones listed there (combined questions without a model, Kazakh wording, the dormitory follow-up).
