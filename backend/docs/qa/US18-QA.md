# US18 QA record — expanded FAQ base

Date: 2026-10-09. Local run, no `GEMINI_API_KEY` (answers are the FAQ text word for word). Dev run still open.

## Data

40 new official items (faq-036 … faq-075) from sdu.edu.kz with verbatim evidence quotes: grants and discounts, travel allowance, language of instruction, diploma, ECTS, creative and special exams, English test, military service documents, bank details, dormitory fee contents, transfer (4), visa (5), Foundation (3), PhD exam, master's grant competition, academic calendar (2), military department, student ID, exchange, medical center, inclusion, ISPT registration, double degree. Not found on the site, so not added: refunds, tuition instalments, health insurance, office hours, master/PhD 2026 deadlines.

## Checks

| Check | Result |
| --- | --- |
| Evaluation set v3 (70 cases = v2 + 14 new-topic paraphrases + 15 Kazakh/Russian + 5 catalogue), local API | **63/70 (90%)**, 9/9 correct fallbacks, **0 invented facts**, new topics 14/14 |
| Evaluation set v2 on the same API | 34/40, 0 invented facts (Sprint 2 baseline 35/40; changes: Kazakh +1, "tuition for Computer Science" now asks which of 3 programs, one injection case now answered from the new dormitory-fee item) |
| `scripts/export_unanswered.py` (grouping, counts, redaction, no session ids) | `tests/test_export_unanswered.py` 2 passed |

Remaining v3 failures: 3 combined questions (answered fully only with the model), the Sprint 1 faq-007 retrieval miss, "tuition for Computer Science" (intended "which program?"), and two near-miss picks between related items (dormitory fee vs cost; IELTS vs Foundation English). Decision for the PO: whether the v2 tuition case should expect the "which program?" answer now that the catalogue has three Computer Science programs.

US18QATest: v2 questions keep their score within one case and the new topics are answered with their sources — PASS locally. Fail case (an invented fact in the evaluation set) — 0 in both sets.
