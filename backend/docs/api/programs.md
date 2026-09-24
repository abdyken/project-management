# Program catalogue API (US1) — contract

Owner: Dinmukhamed (backend). Task T1.5.
For: Daniyar (catalogue and program pages, T2.6), Nurmek (document checklist, T4.1–T4.2), Serdar (assistant program lookup, T3.6).

**Status:** published 2026-09-18 — waiting for confirmation from Daniyar and Nurmek (see the end of this file).

- Base URL, local: `http://localhost:8000` (run `docker compose up --build` in the repository root)
- Base URL, dev environment: _set when T0.5 is deployed_
- Interactive docs: `<base URL>/docs` (Swagger UI)
- Machine-readable description: [`openapi.json`](openapi.json) — regenerate with `uv run python scripts/export_openapi.py`
- All responses are JSON. CORS allows the origins in `CORS_ORIGINS` (default `http://localhost:5173`, `http://localhost:3000`) — tell backend the deployed front-end URL.

---

## Program object

Every endpoint below returns programs in this shape.

| Field                  | Type                                    | Always set | Notes                                                                     |
| ---------------------- | --------------------------------------- | ---------- | ------------------------------------------------------------------------- |
| `program_id`           | string (max 64)                         | yes        | Official program code, e.g. `"6B06102"`. Use it in URLs.                  |
| `title`                | string                                  | yes        | e.g. `"Computer Science"`                                                  |
| `faculty`              | string                                  | yes        | School, e.g. `"School of Information Technologies and Applied Mathematics"` |
| `degree_level`         | `"bachelor"` \| `"master"` \| `"phd"`   | yes        | Lower-case code — the front-end chooses the display label                 |
| `language`             | string                                  | yes        | Language(s) of instruction, comma-separated, e.g. `"English"`, `"Kazakh, Russian"` |
| `tuition_per_ects_kzt` | integer \| `null`                       | no         | Program course fee in KZT per ECTS credit (2026-2027 fee order)           |
| `tuition_per_ects_usd` | integer \| `null`                       | no         | Same for international students, in USD per ECTS credit                   |
| `deadline_local`       | string `YYYY-MM-DD` \| `null`           | no         | Application deadline for local applicants                                 |
| `deadline_international` | string `YYYY-MM-DD` \| `null`         | no         | Application deadline for international applicants                         |
| `source_url`           | string \| `null`                        | no         | Official sdu.edu.kz page the record was taken from                        |
| `is_active`            | boolean                                 | yes        | Always `true` in responses — inactive programs are never returned         |

`null` means "not published" in the official data — show it that way, never as `0` or an empty date.

```json
{
  "program_id": "6B06102",
  "title": "Computer Science",
  "faculty": "School of Information Technologies and Applied Mathematics",
  "degree_level": "bachelor",
  "language": "English",
  "tuition_per_ects_kzt": 33000,
  "tuition_per_ects_usd": 90,
  "deadline_local": "2026-08-25",
  "deadline_international": "2026-07-31",
  "source_url": "https://sdu.edu.kz/en/computer-science-3/",
  "is_active": true
}
```

---

## `GET /api/programs` — search and filter

All parameters are optional and combine with **AND**. Blank values (`?q=`) are ignored.

| Parameter      | Matching                                                                   | Example                          |
| -------------- | -------------------------------------------------------------------------- | -------------------------------- |
| `q`            | Case-insensitive substring of the **title, the faculty or the `program_id`** (max 100 chars) | `q=computer`, `q=6B061` |
| `faculty`      | Case-insensitive **exact** faculty name                                    | `faculty=School of Social Sciences, Business and Law` |
| `degree_level` | `bachelor`, `master` or `phd` — anything else returns 422                  | `degree_level=master`            |
| `language`     | Case-insensitive; matches programs taught in this language (one of the comma-separated values) | `language=Kazakh`                |

Results: only active programs, ordered by title. No pagination — the whole result is returned (10–15 programs in iteration 1).

### 200 OK

`total` is **always** present and equals the number of items in `programs`.

```json
{
  "total": 2,
  "programs": [
    { "program_id": "6B06103", "title": "Mathematical and Computer Modelling", "...": "..." },
    { "program_id": "6B06102", "title": "Computer Science", "...": "..." }
  ]
}
```

No match is **not** an error:

```json
{ "total": 0, "programs": [] }
```

### Examples

```
GET /api/programs
GET /api/programs?q=law
GET /api/programs?faculty=School%20of%20Information%20Technologies%20and%20Applied%20Mathematics&degree_level=bachelor
GET /api/programs?q=science&degree_level=master&language=English
```

### Filter options for the dropdowns

There is no separate endpoint for the list of faculties / languages. Call `GET /api/programs` once without filters and take the distinct `faculty` and `degree_level` values and the distinct languages (split `language` on `, `) from the result. With the iteration-1 catalogue size this is one small request. (If this becomes a problem, ask backend for a `/api/programs/filters` endpoint.)

---

## `GET /api/programs/{program_id}` — one program

For the program detail page (and for direct links / page refresh).

- **200 OK** — the program object above.
- **404 Not Found** — no program with this id, or the program is inactive:

```json
{ "error_code": "PROGRAM_NOT_FOUND", "message": "Program not found." }
```

---

## Errors (both endpoints)

Error bodies always have this shape:

```json
{ "error_code": "SOME_CODE", "message": "Human-readable text" }
```

Build the UI on `error_code` (stable), not on `message` (wording may change).

| Status | `error_code`           | When                                   | Front-end should                                                        |
| ------ | ---------------------- | -------------------------------------- | ----------------------------------------------------------------------- |
| 503    | `DATABASE_UNAVAILABLE` | Database unreachable                   | Show the connection error with **Try again**; keep the entered text and filters. Response has a `Retry-After: 5` header. |
| 404    | `PROGRAM_NOT_FOUND`    | Detail endpoint, unknown/inactive id   | Show "Program not found" with a link back to the catalogue              |
| 422    | `INVALID_REQUEST`      | Invalid parameter, e.g. `degree_level=diploma` or `q` longer than 100; `message` names the field | Should not happen from the UI — dropdowns only send valid values |

Mapping for the catalogue page (US1QATest):

| Response                     | Catalogue page state                   |
| ---------------------------- | -------------------------------------- |
| 200 and `total > 0`          | "`total` programs found" + list        |
| 200 and `total == 0`         | "No programs found"                    |
| 5xx / network error          | Connection error + Try again           |

---

## For Nurmek — document requirements (T4.1 / T4.2)

- Reference programs by `program.program_id` (`VARCHAR(64)`, primary key of table `program`) — a foreign key from your requirements table, e.g. `program_document_requirement.program_id → program.program_id`.
- The `program` table is created by migration `0003` and changed by `0007`; new migrations go on top of the current head (`uv run alembic heads`).
- Suggested path for the checklist endpoint, so it sits next to the catalogue: `GET /api/programs/{program_id}/checklist?applicant_type=...` — your call.
- Reuse `ErrorResponse` and the 503 handling from `app/api/errors.py` so errors look the same across the API.

---

## Changes to this contract

Any change to paths, parameters or fields is announced to Daniyar, Nurmek and Serdar before it is merged, and `openapi.json` is regenerated.

## Confirmation

| Who     | For            | Confirmed |
| ------- | -------------- | --------- |
| Daniyar | T2.6           | _pending_ |
| Nurmek  | T4.1, T4.2     | confirmed 2026-09-18 — `program_id` is the checklist foreign key |
