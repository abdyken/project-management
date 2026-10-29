# Private admissions requests - US30

These are individual applicant questions and office replies, separate from the
anonymous grouped US22 inbox. Questions never become public FAQ automatically.

| Method/path (prefix `/api`) | Input / result |
| --- | --- |
| POST `/applicant/requests` | `{question, client_key, language?:"en"}` → 201 request |
| GET `/applicant/requests?offset=0&limit=30` | `{items,total}` for the verified owner |
| GET `/applicant/requests/{id}` | One owned request; another owner's id returns 404 |
| GET `/staff/requests?status=new&offset=0&limit=30` | Staff queue; status new/answered/all |
| GET `/staff/requests/{id}` | One request, staff session required |
| POST `/staff/requests/{id}/answer` | `{answer}` → answered request |

Question: trimmed 1-2000 characters; answer: trimmed 1-6000. Language en/ru/kk.
Client key: 16-64 URL-safe alphanumeric/underscore/hyphen characters, generated once
per new question. A retry with the same key/body returns the existing row; reusing
it for another question/language is 409 `REQUEST_KEY_REUSED`. Five new questions
per applicant per hour; further submissions return 429 `TOO_MANY_REQUESTS`.
Submission serializes on the applicant row, so concurrent retries are deduplicated.

Responses contain id, question, language, answer, created/answered timestamps and
notification timestamp. They never include e-mail, session ids or token values.
Applicant routes reuse the enabled flag, Secure HttpOnly cookie on `/api/applicant`,
origin checks and verified-owner dependency. Staff routes use `/api/staff` cookies;
the answer mutation also checks the configured origin and enabled flag. Both sets
of private responses are `Cache-Control: no-store`. UI caches clear with existing
applicant/staff logout flows. Chat transfers the draft through navigation state,
not a URL query or request log; login preserves that draft and return path.

An answer commits before notification and is immediately visible in the account.
Repeated identical answer submissions are idempotent; a different second answer
returns 409 `ALREADY_ANSWERED`. E-mail notifications contain only a link to the
account, not the private question/answer. The hourly API worker retries unsent
notifications with row locks, as does `python scripts/send_request_notifications.py`.
An SMTP failure keeps the answer and pending delivery. Successful delivery is
recorded; ordinary SMTP still has a possible duplicate on a crash between external
acceptance and database commit. Request-reply notifications are transactional and
independent of optional deadline-reminder consent.

Account deletion cascades to questions, answers and delivery state. Staff deletion
only clears editor references. Missing/foreign request: 404 `REQUEST_NOT_FOUND`;
invalid input: 422; no session: 401; disabled accounts: 503 `ACCOUNTS_UNAVAILABLE`.
No document attachments, guest e-mail workflow, live chat or application status
processing are added by this story.
