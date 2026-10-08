# Sprint 3 — review, acceptance and retro

**Sprint:** 03.10 – 09.10.2026. **Record written:** 09.10.2026.

## Sprint goal

> An applicant can use the portal and the assistant in Kazakh, Russian or English, find every SDU program (not a demo subset), compare up to three programs side by side, and rarely gets the "could not find" answer — with Sprint 2 accepted on the deployed dev environment.

**Result:** everything except the dev part is built and checked locally, including a full run of the Docker stack. Sprint 2 and Sprint 3 are not on dev yet, so no story is accepted under the Definition of Done.

## Stories (PO.4)

| Story | Built | Local QA | Status |
| --- | --- | --- | --- |
| US17 Program Comparison | `GET /api/programs/compare`, compare toggle and bar, `/compare` page (table / stacked on phones), shareable link, stale-id recovery | `US17-QA.md` — 9 API tests, 60/60 browser checks | Done, not accepted |
| US15 Portal in Kazakh, Russian and English | Language switch, every interface label in kk/ru/en (typed dictionaries), official program titles per language, Kazakh dates and numbers, chat starters in the chosen language | 144/144 browser checks (Chromium + Firefox, 3 widths); no English label left | Done, not accepted |
| US16 Full Program Catalogue | 64 official programs (33 bachelor, 24 master, 7 PhD) with titles in three languages, shared document lists, nullable language; migration 0012 | `US16-QA.md` — 192/192 catalogue answers match | Done, not accepted |
| US8 Multilingual Assistant | Answers in the question's language; official RU/KK FAQ texts (66 / 57 items); per-language index (migration 0013) and hybrid retrieval; kk/ru fixed answers | `US8-QA.md` — own-question hit rate en 74/75, ru 66/66, kk 56/57 | Done, not accepted |
| US18 Expanded FAQ Base | 40 new official items, unanswered-questions report, evaluation set v3 | `US18-QA.md` — v3 63/70 (90%), 0 invented facts | Done, not accepted |
| 10.6 Chat API contract v3 | v1 fields removed, source titles | contract docs, `openapi.json`, widget | Done |

**Carry-over to Sprint 4:** the dev run of Sprint 2 and Sprint 3 (CO.1/CO.2 again), and the open questions to the admissions office below.

## Decisions recorded (Product Owner)

- **Data source.** The admissions office has not answered the PO.3 request, so Sprint 3 uses the official texts published on sdu.edu.kz in all three languages, with quotes, marked pending review. Interface labels were translated by the team; admission facts never are.
- **Duplicate code 7M01501.** The catalogue keeps "Mathematics" (School of Education and Humanities); "Mathematics (Science)" waits for its real code.
- **Unknown values stay `null`.** The language of 17 master/PhD programs and every master/PhD deadline are not published, so the portal and the assistant say so. The old "English" for 7M06101 came from a bachelor-page sentence and was dropped.
- **Shared program titles.** "Computer Science" now names a bachelor, a master and a PhD program; without a degree word or code the assistant asks which one (as it already did for Information Systems). The evaluation case "How much is tuition for Computer Science?" therefore no longer matches its Sprint 2 expectation — to confirm before it is changed.
- **Kazakh retrieval.** The embedding model barely understands Kazakh. Instead of a bigger model (memory on the free host), a word-overlap score is combined with the embedding score; Kazakh questions went from mostly falling back to 8/8 in the evaluation set.

## Questions for the admissions office

`backend/app/data/catalogue_review.md` (catalogue: duplicate code, two master fee orders, fees split by group language, missing values, site errors) and `backend/app/data/faq_review.md` (missing translations, 20 conflicts between the English, Russian and Kazakh pages — e.g. master's IELTS 5.5 vs 6.0, master's ECTS 120 vs 240).

## Retro (SM.6)

| Went well | Went badly | Action for Sprint 4 |
| --- | --- | --- |
| Every value came with a source and a quote, so gaps and site conflicts were found instead of guessed | Still no dev deployment: two sprints of work wait for acceptance | Deploy first in Sprint 4, before any new story |
| Scripted browser QA (widget, compare, languages) ran in both browsers on the Docker stack | The full catalogue broke tests that assumed 12 programs; they had to be pinned to a fixed test catalogue | Tests that need fixed data use `tests/data/`; tests of the real data are named as such |
| Kazakh support measured, not assumed: the weak embedding model was caught by tests | Branches are stacked five deep | Merge each PR as soon as it is reviewed |
