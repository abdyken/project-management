# Program catalogue API (US1) — contract

Owner: Dinmukhamed (backend). Task T1.5.
For: Daniyar (catalogue and program pages, T2.6), Nurmek (document checklist, T4.1–T4.2), Serdar (assistant program lookup, T3.6).

**Status:** published 2026-09-18 — waiting for confirmation from Daniyar and Nurmek (see the end of this file).

- Base URL, local: `http://localhost:8000` (run `docker compose up` in `backend/`)
- Base URL, dev environment: _set when T0.5 is deployed_
- Interactive docs: `<base URL>/docs` (Swagger UI)
- Machine-readable description: [`openapi.json`](openapi.json) — regenerate with `uv run python scripts/export_openapi.py`
- All responses are JSON. CORS allows the origins in `CORS_ORIGINS` (default `http://localhost:5173`, `http://localhost:3000`) — tell backend the deployed front-end URL.

---

## Program object

Every endpoint below returns programs in this shape.

| Field                  | Type                                    | Always set | Notes                                                                     |
| ---------------------- | --------------------------------------- | ---------- | ------------------------------------------------------------------------- |
| `program_id`           | string (max 64)                         | yes        | Stable text id from the source data, e.g. `"prog-cs-bsc"`. Use it in URLs. |
| `title`                | string                                  | yes        | e.g. `"Computer Science"`                                                  |
| `faculty`              | string                                  | yes        | e.g. `"Faculty of Engineering"`                                            |
| `degree_level`         | `"bachelor"` \| `"master"` \| `"phd"`   | yes        | Lower-case code — the front-end chooses the display label                 |
| `language`             | string                                  | yes        | Language of instruction as written in the source, e.g. `"English"`        |
| `tuition_fee`          | number \| `null`                        | no         | KZT per academic year. `null` = unknown in the official data              |
| `application_deadline` | string `YYYY-MM-DD` \| `null`           | no         | `null` = unknown in the official data                                     |
| `is_active`            | boolean                                 | yes        | Always `true` in responses — inactive programs are never returned         |

Show `null` as "not specified" (or similar) — never as `0` or an empty date.

```json
{
  "program_id": "prog-cs-bsc",
  "title": "Computer Science",
  "faculty": "Faculty of Engineering",
  "degree_level": "bachelor",
  "language": "English",
  "tuition_fee": 2500000.0,
  "application_deadline": "2026-08-01",
  "is_active": true
}
```

---

## `GET /api/programs` — search and filter

All parameters are optional and combine with **AND**. Blank values (`?q=`) are ignored.

| Parameter      | Matching                                                                   | Example                          |
| -------------- | -------------------------------------------------------------------------- | -------------------------------- |
| `q`            | Case-insensitive substring of the **title, the faculty or the `program_id`** (max 100 chars) | `q=computer`, `q=6B061` |
| `faculty`      | Case-insensitive **exact** faculty name                                    | `faculty=Faculty of Engineering` |
| `degree_level` | `bachelor`, `master` or `phd` — anything else returns 422                  | `degree_level=master`            |
| `language`     | Case-insensitive **exact** language                                        | `language=English`               |

Results: only active programs, ordered by title. No pagination — the whole result is returned (10–15 programs in iteration 1).

### 200 OK

`total` is **always** present and equals the number of items in `programs`.

```json
{
  "total": 2,
  "programs": [
    { "program_id": "prog-arch-bsc", "title": "Architecture", "...": "..." },
    { "program_id": "prog-cs-bsc", "title": "Computer Science", "...": "..." }
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
GET /api/programs?faculty=Faculty%20of%20Engineering&degree_level=bachelor
GET /api/programs?q=science&degree_level=master&language=English
```

### Filter options for the dropdowns

There is no separate endpoint for the list of faculties / languages. Call `GET /api/programs` once without filters and take the distinct `faculty`, `degree_level` and `language` values from the result. With the iteration-1 catalogue size this is one small request. (If this becomes a problem, ask backend for a `/api/programs/filters` endpoint.)

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
- The `program` table is created by migration `0003`; add your migration on top (`down_revision = "0003"`, check with `uv run alembic heads`).
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
