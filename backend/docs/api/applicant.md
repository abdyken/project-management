# Applicant area — Sprint 5 (US23–US26, US7)

All paths below start with `/api/applicant`. JSON errors use the existing `{ "error_code": "…", "message": "…" }` contract. Every response is `Cache-Control: no-store`. Applicant sessions are distinct from staff and chat sessions; no applicant id is accepted from a caller to select an owner.

`APPLICANT_ACCOUNTS_ENABLED=false` returns 503 `ACCOUNTS_UNAVAILABLE`. The local Docker stack enables it; the live deployment defaults off pending the hosting decision. Mutations with an Origin header outside the configured public/CORS origins return 403. Deploy behind the same origin as the frontend.

## Account endpoints

| Method/path | Input | Result |
| --- | --- | --- |
| POST `/register` | `{email, language?: "en"}`; valid e-mail, language `en`/`ru`/`kk`. A `password` field is accepted and ignored (older clients) | 202 generic verification message; SMTP sends a link valid for 24 h; an existing verified account is unchanged |
| POST `/verify` | `{token, password}`: token from the link fragment, 10–200 character password | 200 applicant and new cookie; the password given here becomes the account password; token consumed; invalid/expired/reused token: 422 `INVALID_VERIFICATION` |
| POST `/login` | `{email, password}` | 200 applicant and cookie; unverified/unknown/wrong password: 401 `INVALID_CREDENTIALS` |
| POST `/logout` | none | 204, current session revoked and cookie cleared; idempotent |
| GET `/me` | session cookie | `{id, email, language, reminders_enabled}` |
| PATCH `/me` | `{language, reminders_enabled}` | Updated applicant; reminder opt-in defaults false |
| DELETE `/me` | session cookie | 204; applicant, all sessions, saved programs, progress and delivery history deleted; cookie cleared |

Cookie: `applicant_session`, path `/api/applicant`, HttpOnly, Secure, SameSite Strict; seven-day expiry by default. Only SHA-256 token hashes are stored. Password hashes reuse the existing scrypt implementation. Five failed logins per account, or 30 per client IP, in 15 minutes block further attempts with 429 `TOO_MANY_ATTEMPTS`; registration/resend is limited to five requests per e-mail, or 30 per IP, in 15 minutes. The per-IP limit is higher because a campus or mobile network puts many applicants behind one address. The client IP is the first `X-Forwarded-For` entry (Caddy replaces any client-sent value, nginx appends its own address), as for staff login; without the header the socket address is used. Limiters follow the existing single-process in-memory approach and reset on API restart.

Registration requires SMTP configuration: missing delivery returns 503 `MAIL_UNAVAILABLE`. The pending account and token are committed before the e-mail is sent, so a slow mail server holds no lock or database connection; failing delivery also returns 503, and registering again sends a new link. Registration takes no password: the account gets one on the verification page, so only the inbox owner chooses it and registering someone else's pending e-mail gains nothing. Until then the stored hash matches no password. Registering an unverified account again rotates its token; only the newest link works. The same generic success body is returned for a verified e-mail. Verification links use `/account/verify#token=…` so tokens are not sent in access logs or referrer headers. No passwords, cookie values or verification tokens are returned in account JSON.

## Saved programs and progress

All endpoints below require a verified, unexpired applicant cookie; otherwise 401 `NOT_LOGGED_IN`.

| Method/path | Input | Result |
| --- | --- | --- |
| GET `/programs` | none | `{items: SavedChecklist[]}` for this applicant, including archived saved programs |
| PUT `/programs/{program_id}/{applicant_type}` | none | Idempotent save; active program required; returns checklist |
| GET `/programs/{program_id}/{applicant_type}` | none | Current saved checklist; 404 `SAVED_PROGRAM_NOT_FOUND` if not owned/saved |
| DELETE `/programs/{program_id}/{applicant_type}` | none | 204; removes this saved checklist and its prepared flags; idempotent |
| PUT `/programs/{program_id}/{applicant_type}/documents/{requirement_id}` | `{prepared: boolean}` | Updated checklist; unsaved/wrong program/type/deleted requirement rejected; archived programs read-only |
| GET `/programs/{program_id}/{applicant_type}/pdf?language=en` | language `en`/`ru`/`kk` | `application/pdf` attachment with this applicant's prepared flags |

`applicant_type` is `local` or `international`. A `SavedChecklist` contains `program` (existing ProgramOut), `applicant_type`, `items` (existing document fields plus `id` and `prepared`), `prepared` count, `total`, `warning` and `contact`. Requirements are read from `program_document_requirement`; there is no copied personal document list. Staff replacement keeps the rows (and their progress) of documents whose name (ignoring case and spacing), format, translation and notarisation are unchanged; their deadline and order may change. A removed or renamed document, or one that now needs another format, translation or notarisation, gets a new row and its progress is cleared. Newly created requirements start unprepared. An unpublished list has zero items plus an explicit warning and contact, not a completion claim. Missing/archived programs cannot be saved; existing archived saves remain inspectable but get no reminders.

Public export: `GET /api/programs/{program_id}/checklist/pdf?applicant_type=local&language=en` requires no account and includes no personal progress. Both PDF routes use the same current snapshot and renderer, preserve official document text and include deadline, source and admissions contact. Unknown values remain explicit. Invalid program: 404; invalid language/type: 422.

## Reminder delivery

The hourly worker (also `python scripts/send_reminders.py`) checks Asia/Almaty dates. Verified, opted-in accounts with active saved programs receive reminders at 7 days, 1 day and on the program's published applicant-type deadline. A milestone missed on its day (outage, daily limit) is still sent on the following days until the next milestone replaces it; nothing is sent after the deadline. One e-mail per applicant per run that lists every saved checklist due that day, each with the applicant type, the current unprepared documents (or an explicit unpublished-list warning), and a link to account preferences. One SMTP connection serves the run; a login, quota or connection error, or a temporary (4xx) refusal, stops the run and leaves the rest pending; a permanent (5xx) recipient refusal skips only that applicant. A connection is never reused after an error. `REMINDER_DAILY_LIMIT` (default 300) caps reminder e-mails per rolling 24 hours, as Gmail counts, leaving room in its roughly 500-per-day allowance for verification and reply e-mails; the closest deadlines go first and reminders over the cap are caught up on later runs. A failure for one applicant (for example a checklist removed during the run) skips only that applicant, and reminders and reply notifications run independently. SMTP errors are logged with their class and code, never the recipient. A durable key `(applicant, program, type, deadline, milestone)` and row lock prevent repeated successful sends and overlapping deliveries. SMTP failure leaves the milestone retryable. SMTP acceptance and database commit are separate: a crash between them may cause a duplicate retry.
