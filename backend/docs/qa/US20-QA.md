# US20 QA record — FAQ management

Date: 2026-10-15. Local run: full Docker stack on `feature/sprint-4-staff-area`. Live run: after deployment.

| Check | Result |
| --- | --- |
| `tests/test_faq_admin.py`: migration 0015 moved all 75 items unchanged (same `FaqItem`s as `faq.json`), 401 on every endpoint, list filters and languages, an edited answer is used by `/ask` at once, new items are drafts until published, unpublish and retire remove an item from the index and the chat suggestions, Russian text indexed in Russian, invalid items rejected (http link, empty question, half a translation, unknown degree, bad category) | 19 passed |
| API start on the Docker stack | "Indexed 75 published FAQ items from the faq_item table" |
| Evaluation set v3 after the move (`run_accuracy_test.py --set v3`, local API without a Gemini key, as in the Sprint 3 baseline) | **63/70 (90%)**, 9/9 correct fallbacks, **0 invented facts** — identical to Sprint 3, the same 7 failures |
| `frontend/e2e/staff-qa.mjs` at 1280 px, US20 part | **4/4 PASS** |

Browser checks: the category filter shows the 3 dormitory items; changing the dormitory fee in faq-022 to 552,777 KZT and saving makes the assistant (with Gemini) answer 552,777 on the next question, without a restart; reverting it brings 552,500 back; a Russian version with a question but no answer is flagged and cannot be saved.

US20QATest: Pass (an officer changes the dormitory answer, publishes, and the chat answers with the new text within a minute; a retired item is no longer used; a restart keeps the change) — PASS locally (the restart case is covered by the start indexing from the table). Fail case (old text after an edit, a draft used in an answer) — does not happen.
