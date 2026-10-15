# Staff API (US19) — contract

Owner: Serdar (Sprint 4 is done by one developer). Task 19.0.
For: the staff pages of the frontend (login, FAQ editor US20, inbox US22, dashboard US9).

**Status:** published 2026-10-15.

- Base URL, local: `http://localhost:8080/api/staff` through the web container (`docker compose up --build`), or `http://localhost:8000/api/staff` directly
- Base URL, live site: `https://193-123-95-102.sslip.io/api/staff`
- Machine-readable description: [`openapi.json`](openapi.json) — regenerate with `uv run python scripts/export_openapi.py`
- Errors use the same `{ "error_code", "message" }` body as every other endpoint.

---

## Accounts

There is no sign-up page. Accounts are managed on the server with
`scripts/create_staff_user.py` (`add`, `reset-password`, `deactivate`, `activate`, `list`).
The password is typed interactively or read from stdin, never passed as an argument.

| Role      | Can use                                                    |
| --------- | ---------------------------------------------------------- |
| `officer` | Every staff page: FAQ editor, inbox, dashboard             |
| `admin`   | Everything an officer can, plus `GET /api/staff/users`     |

Passwords need at least 10 characters and are stored as salted scrypt hashes.
Resetting a password or deactivating an account logs out all its sessions.

## Session

`POST /login` sets the cookie `staff_session`:

| Attribute  | Value          | Why |
| ---------- | -------------- | --- |
| `HttpOnly` | yes            | Page scripts cannot read the token |
| `Secure`   | yes            | Sent over HTTPS only (browsers also send it to `http://localhost`) |
| `SameSite` | `Strict`       | Not sent with requests started by other sites |
| `Path`     | `/api/staff`   | Never sent with public catalogue or chat requests |
| `Max-Age`  | 28800 (8 hours) | `STAFF_SESSION_HOURS`; the session also ends at logout |

The frontend calls the staff API on the same origin (nginx proxies `/api/`), so no CORS
setting is needed. Every request after login only has to send the cookie (`fetch` sends it
by default for same-origin requests).

Only the SHA-256 of the token is stored in `staff_session`.

## Endpoints

### `POST /api/staff/login`

```json
{ "email": "officer@sdu.edu.kz", "password": "••••••••••" }
```

`200` — the user, and the cookie is set:

```json
{ "id": 3, "email": "officer@sdu.edu.kz", "name": "Aigerim", "role": "officer" }
```

The e-mail is case-insensitive.

| Status | `error_code`          | When |
| ------ | --------------------- | ---- |
| 401    | `INVALID_CREDENTIALS` | Unknown e-mail, wrong password or deactivated account — one message for all three |
| 429    | `TOO_MANY_ATTEMPTS`   | 5 failed logins in 15 minutes for this e-mail or from this IP address; the right password is refused too until the window passes |
| 422    | `INVALID_REQUEST`     | Missing field |

### `POST /api/staff/logout`

`204`, the session is deleted and the cookie cleared. Works without a session too.

### `GET /api/staff/me`

`200` — the same user object as the login. `401 NOT_LOGGED_IN` without a valid session:
the frontend uses this call to decide whether to show the login page.

### `GET /api/staff/users` (admin)

```json
{
  "items": [
    { "id": 3, "email": "officer@sdu.edu.kz", "name": "Aigerim", "role": "officer",
      "active": true, "last_login_at": "2026-10-16T09:12:00Z" }
  ]
}
```

`403 FORBIDDEN` for an officer.

## Every staff endpoint

Every endpoint under `/api/staff` except `login` and `logout` uses the `require_staff`
dependency and answers `401 NOT_LOGGED_IN` without a valid session; each one has a test
for that (Definition of Done, Sprint 4).

---

## FAQ management (US20)

Since Sprint 4 the `faq_item` table is the source of truth for the FAQ. Migration 0015
loaded it once from `app/data/faq.json`; the API start indexes the **published** items.
Draft and retired items are never used by the assistant or suggested in the chat.

### FAQ item

| Field | Type | Notes |
| ----- | ---- | ----- |
| `faq_id` | string | `faq-NNN`, given by the server on create |
| `status` | `"draft"` \| `"published"` \| `"retired"` | New items are drafts |
| `category` | string | Lower-case Latin letters and `-`, e.g. `dormitory` |
| `question`, `answer` | string | English, required |
| `source_link` | string | Official page, must start with `https://` |
| `evidence` | string \| `null` | Quote from the page, for the office review only |
| `question_ru`, `answer_ru`, `source_link_ru`, `evidence_ru` | string \| `null` | Russian version: question, answer and link all set, or all `null` |
| `question_kk`, `answer_kk`, `source_link_kk`, `evidence_kk` | string \| `null` | Kazakh version, same rule |
| `degrees` | `("bachelor" \| "master" \| "phd")[]` | Empty = every level |
| `applicant_types` | `("local" \| "international")[]` | Empty = everyone |
| `last_update` | `YYYY-MM-DD` | Set by the server on every change |
| `updated_at`, `updated_by` | datetime, string \| `null` | Who changed it last (staff name); `null` for items from `faq.json` |

### Endpoints

| Method and path | Body | Answer |
| --------------- | ---- | ------ |
| `GET /api/staff/faq?q=&status=&category=` | — | `{ items: [{faq_id, status, category, question, languages, last_update, updated_at, updated_by}], categories }` |
| `GET /api/staff/faq/{faq_id}` | — | the item, `404 FAQ_NOT_FOUND` |
| `POST /api/staff/faq` | item fields (no id, status or dates) | `201`, the new draft |
| `PUT /api/staff/faq/{faq_id}` | item fields | the item; a published item is re-indexed at once |
| `POST /api/staff/faq/{faq_id}/publish` | — | the item, now used by the assistant |
| `POST /api/staff/faq/{faq_id}/unpublish` | — | back to draft, no longer used |
| `POST /api/staff/faq/{faq_id}/retire` | — | retired, no longer used, kept in the list |

An invalid body (e.g. an `http://` link or a Russian question without an answer) gets
`422 INVALID_REQUEST` with the field in the message.

---

## Unanswered question inbox (US22)

Questions the assistant could not answer (`admissions_followup`, kind `unanswered_question`),
grouped like `scripts/export_unanswered.py`: questions that differ only in case, spacing or
punctuation are one group. E-mail addresses and phone numbers are redacted; session ids are
never returned.

| Method and path | Body | Answer |
| --------------- | ---- | ------ |
| `GET /api/staff/inbox?status=new&days=30` | — | `{ items: [{key, question, count, language, best_score, first_asked, last_asked, faq_id}], total_asks }`, most asked first; `status` `new` \| `answered` \| `dismissed`, `days` 1–90 |
| `POST /api/staff/inbox/dismiss` | `{ key }` | `{ key, status: "dismissed", updated }`; `404 GROUP_NOT_FOUND` when the group has no new question |
| `POST /api/staff/inbox/answer` | `{ key, faq_id }` | `{ key, status: "answered", updated }`; `409 FAQ_NOT_PUBLISHED` unless the item is published |

`key` is the normalized question from the list. Dismissing or answering a group handles
every new question of it; a later ask of the same question starts a new group.

The staff editor calls `answer` after publishing an item created with "Answer" in the inbox.

---

## Admissions dashboard (US9)

`GET /api/staff/analytics?days=7` — `days` 1–30 (chat turns are deleted after 30 days).
Days are counted in Kazakhstan time (UTC+5), today included.

```json
{
  "days": 7, "since": "2026-10-10",
  "questions": 80, "sessions": 79, "unanswered": 12,
  "per_day": [{ "date": "2026-10-16", "questions": 80, "unanswered": 12 }],
  "top_questions": [{ "question": "How much does the dormitory cost?", "count": 5 }],
  "top_sources": [{ "faq_id": "faq-022", "question": "How much does the dormitory cost?", "count": 8 }],
  "languages": { "en": 63, "ru": 8, "kk": 9 },
  "ratings": { "up": 3, "down": 1 },
  "down_reasons": { "outdated": 1 }
}
```

`questions` counts applicant messages, `unanswered` the questions logged without an answer.
Question texts are redacted; no session ids are returned.

---

## Catalogue and checklist management (US21)

Since Sprint 4 the `program` and `program_document_requirement` tables are the source of
truth. The API start runs `scripts/import_catalogue.py --if-empty`, which only fills an
empty catalogue; the public catalogue, the checklist and the assistant read the tables
directly, so an edit is visible at once. `null` means "not published" and is shown that way.

| Method and path | Body | Answer |
| --------------- | ---- | ------ |
| `GET /api/staff/programs?q=&degree_level=&active=` | — | `{ items: [{program_id, title, degree_level, faculty, is_active, documents_local, documents_international, updated_at, updated_by}] }`, archived programs included |
| `GET /api/staff/programs/{program_id}` | — | the program with `documents: {local: [...], international: [...]}`; `404 PROGRAM_NOT_FOUND` |
| `POST /api/staff/programs` | `program_id` (`[0-9A-Z]+`) and the fields below | `201`; `409 PROGRAM_EXISTS` |
| `PUT /api/staff/programs/{program_id}` | `title`, `title_ru`, `title_kk`, `faculty`, `degree_level`, `language`, `tuition_per_ects_kzt`, `tuition_per_ects_usd` (≥ 0), `deadline_local`, `deadline_international` (`YYYY-MM-DD`), `source_url` (`https://`), `is_active` | the program; `is_active: false` archives it (it leaves the catalogue, the comparison and the assistant) |
| `PUT /api/staff/programs/{program_id}/documents/{local\|international}` | `{ documents: [{name, format: "original"\|"copy", translation, notarisation, deadline}] }` | the program; the list replaces the old one in this order; an empty list = no official list (the checklist shows the missing-data warning) |

Programs that shared one official list in `catalogue.json` (`documents_from`) have their
own copy in the database: editing one program's list does not change the others.
