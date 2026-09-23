# US1 QA run — program catalogue (T1.6)

Owner: Dinmukhamed (backend). Covers the backend side of US1QATest; the UI side (catalogue page states) is checked by Daniyar in T2.6/T2.7.

Product Owner rule: the story is accepted only when these scenarios pass **on the deployed dev environment**, not on a local machine.

## Before the run

| # | Prerequisite                                                       | Owner   | Done |
| - | ------------------------------------------------------------------ | ------- | ---- |
| 1 | Dev environment deployed, API URL known (T0.5)                     | Nurmek  | ☐    |
| 2 | Official program data imported into the dev database (T0.6, T1.2)  | Askhat  | ☐    |
| 3 | Latest `backend` code deployed (migrations at head)                | Nurmek  | ☐    |
| 4 | `curl <API>/api/health` returns `{"status":"ok","database":"ok"}`   | —       | ☐    |

The free Render server sleeps after 15 minutes idle: call `/api/health` and wait for the answer (up to ~50 s) before starting.

## Scenarios

| ID    | Scenario                     | Steps (API)                                                                                   | Expected                                                                                     | UI counterpart (Daniyar)                                  |
| ----- | ---------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| US1-1 | Full catalogue               | `GET /api/programs`                                                                           | 200; only active programs; `total` = number of items                                         | Catalogue shows "`total` programs found" and the list     |
| US1-2 | Keyword search               | `GET /api/programs?q=<word from a title>` in original, lower and upper case                   | 200; exactly the programs whose title, faculty or id contains the word; same result for all cases | Typing the keyword filters the list                       |
| US1-3 | Combined filters             | Every combination of `faculty`, `degree_level`, `language` taken from one real program        | 200; exactly the programs matching **all** given filters (AND); `total` correct              | Selecting several filters narrows the list                |
| US1-4 | No results                   | `GET /api/programs?q=zzz-qa-no-such-program`; a faculty + degree level with no program        | 200 `{"total": 0, "programs": []}` — not an error                                            | "No programs found", not an empty screen                  |
| US1-5 | Database unavailable         | Stop the database (see below), `GET /api/programs?q=computer`                                 | 503 `{"error_code": "DATABASE_UNAVAILABLE", ...}`, `Retry-After` header                      | Connection error with **Try again**; text and filters kept |
| US1-6 | Program detail               | `GET /api/programs/<id from the list>`; `GET /api/programs/zzz-qa-no-such-program`            | 200 with the same data as in the list; 404 `PROGRAM_NOT_FOUND`                               | Detail page opens; unknown id shows "Program not found"   |

US1-1 to US1-4 and US1-6 are automated in `scripts/qa_us1.py`. Expected results are computed from the catalogue the API returns, so the script works with the real imported data without editing.

## Running it

From `backend/`:

```bash
# US1-1..4, US1-6
uv run python scripts/qa_us1.py --base-url https://<dev-api> --report docs/qa/us1-results-dev.md
```

**US1-5 — database unavailable on the dev environment.** Agree a 5-minute window with Nurmek (the whole team's dev environment is affected), then one of:

- temporarily change `DATABASE_URL` of the API service to a wrong password and redeploy, or
- suspend the database in the hosting dashboard, if the provider allows it.

```bash
uv run python scripts/qa_us1.py --base-url https://<dev-api> --db-down --report docs/qa/us1-results-dev.md
```

Then restore the setting and confirm `/api/health` is `ok` again.

The script prints PASS/FAIL per scenario and exits with code 1 if anything failed. `--report` writes (and for `--db-down`, appends) a Markdown table — commit it as the written result.

## Catalogue export for the Product Owner

```bash
DATABASE_URL=<dev database url> uv run python scripts/export_catalogue.py --out catalogue-dev.csv
```

CSV with every program (inactive ones too), one row per program, empty cell = unknown value. Opens directly in Excel / Google Sheets. Send it to Askhat to compare with the official list. Do not commit it if the database URL or data is not meant to be public.

## Result

| Item                                   | Result | Date | Notes |
| -------------------------------------- | ------ | ---- | ----- |
| Unit and integration tests (`uv run pytest`) | ☐ |  |  |
| US1-1 … US1-4, US1-6 on dev            | ☐      |      | see `us1-results-dev.md` |
| US1-5 on dev                           | ☐      |      |       |
| Export handed to Askhat                | ☐      |      |       |

### Local dry run — 2026-09-18

Against `http://localhost:8000` (docker compose) with 5 temporary sample programs (4 active, 1 inactive): US1-1, US1-2, US1-3, US1-4, US1-6 PASS; US1-5 PASS with the database container stopped; export produced 5 rows with blank unknown values. This only checks the tooling — it does not replace the run on dev.

## Local run — 2026-09-24

Run against the Docker stack (`docker compose up --build`, official catalogue imported). All six scenarios **PASS**: [us1-results-local.md](us1-results-local.md). UI counterparts checked in Chrome: "12 programs found", filters narrow the list and stay in the URL, "No programs found", and "Connection error" with **Try again** (filters kept) while the API was down.

This does not replace the run on the deployed dev environment required above.
