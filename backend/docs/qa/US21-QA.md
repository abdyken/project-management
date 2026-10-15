# US21 QA record — catalogue and checklist management

Date: 2026-10-16. Local run: full Docker stack on `feature/sprint-4-staff-area`. Live run: after deployment.

| Check | Result |
| --- | --- |
| `tests/test_catalogue_admin.py`: 401 on every endpoint; list with document counts, degree filter, archived programs; a fee edit is used at once by `/api/programs` and by `/ask`; blank values stay `null` ("not published"); archiving removes a program from the catalogue; a document list is replaced in order and shows in the public checklist; an empty list brings back the missing-data warning; another program that shared the same official list keeps its own copy; new program and duplicate code (409); invalid fields and documents rejected; the start import skips a filled catalogue | 18 passed |
| API start on the Docker stack | "Catalogue already in the database (edited in the staff area); import skipped" |
| `frontend/e2e/staff-qa.mjs` at 1280 px, US21 part | **6/6 PASS** |

Browser checks: the degree filter shows the 7 PhD programs; changing the local fee of 6B04104 Finance from 41,500 to 43,000 KZT reaches the public catalogue at once and the assistant answers "one ECTS costs 43,000 KZT"; a document added to the international list and moved up appears in the public checklist in that place and on the public program page; the program is put back through the API in a `finally` block, so a failed step never leaves test data behind.

Source of truth: the API start runs `scripts/import_catalogue.py --if-empty`, which only fills an empty catalogue. Running the import without the flag overwrites every staff edit with `app/data/catalogue.json`.

US21QATest: Pass (an officer edits a program's fee, deadline or document list in the staff area and applicants see it without a developer or a deployment) — PASS locally. Fail case (a deployment overwrites a staff edit; an empty value shown as a number) — does not happen.
