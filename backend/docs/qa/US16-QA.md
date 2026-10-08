# US16 QA record — full program catalogue

Date: 2026-10-09. Local run: API and Vite app on `feature/us16-full-catalogue`, catalogue imported from `app/data/catalogue.json` (64 programs). Dev run still open.

## Data

- 64 programs from the 2026–2027 fee orders, price sheets, passing-score table and program pages: 33 bachelor, 24 master, 7 PhD. Each field has a source and a verbatim quote in `catalogue_evidence.json`; quotes from scanned PDFs are visual transcriptions and say so.
- Official Russian and Kazakh titles for all 64 programs (from the RU/KZ twin pages).
- Document lists: the 12 Sprint 1 programs keep their own lists; 41 programs share the official list of their degree level and applicant type (`documents_from`); 11 (MBA/EMBA and PhD) have no published list and show the warning.
- `null` where nothing official exists: language of 17 master/PhD programs, all master/PhD deadlines, 3 bachelor KZT fees, 2 USD fees.
- Left out and listed for the office in `catalogue_review.md`: the second program under code 7M01501 and programs no 2026–2027 document lists.

## Checks

| Check | Result |
| --- | --- |
| `uv run pytest` (incl. `tests/test_full_catalogue.py`: counts, shared lists, three-language titles, ambiguity across degree levels, `documents_from` validation) | 453 passed |
| Migration 0012 upgrade → downgrade → upgrade on the local database | PASS |
| `scripts/check_catalogue_answers.py` against the local API: fee, deadline and language of every program | **192/192** |
| `frontend/e2e/compare-qa.mjs`, `language-qa.mjs`, `widget-qa.mjs` (Chromium + Firefox, 360/768/1280 px) on the full catalogue | 54/54, 120/120, 78/78 |
| Evaluation set v2 against the local API, no model | 34/40, 0 invented facts. One change from 35/40: "How much is tuition for Computer Science?" now matches the bachelor, master and PhD program and the assistant asks which one (expected with the full catalogue; to be decided in evaluation set v3) |

US16QATest: Pass (filtering by master shows every official master program with fee and language; a program without a published list shows the warning) — PASS locally. Fail case (a program from the fee order missing) — every fee-order program is present except the duplicate-code row, recorded for the office.
