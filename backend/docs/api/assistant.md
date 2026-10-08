# FAQ assistant API (US3 / T3.5, contract v2: US10 / T10.4)

## `POST /api/assistant/ask`

```json
{ "question": "When is the application deadline?", "session_id": "3f0c…" }
```

| Field        | Rules                                                  |
| ------------ | ------------------------------------------------------ |
| `question`   | Required, 1–500 characters after trimming whitespace   |
| `session_id` | Required, 1–100 characters; the chat's session id      |

### Answer — 200

```json
{
  "answer": "Text of the matching official FAQ item",
  "sources": [
    { "faq_id": "faq-004", "question": "What are the steps of the admission process for international applicants?", "link": "https://sdu.edu.kz/en/…" }
  ],
  "answer_id": "42",
  "source_link": "https://sdu.edu.kz/en/…",
  "faq_id": "faq-004",
  "similarity_score": 0.83
}
```

| Field | Type | Notes |
| ----- | ---- | ----- |
| `answer` | string | The answer text. Document lists are one line per document, separated by `\n`. |
| `sources` | `[{faq_id, question, link}]` | Official sources of the answer, in the order they are used; `[]` when there is none (fallback, document checklist, "which program?" questions). A FAQ source has all three fields. A catalogue answer (US12) cites the official page of every program it uses: `faq_id` and `question` are `null`, `link` is the page. Once answers are generated (US10), one answer can cite several FAQ items. |
| `answer_id` | string | Id of the stored answer, the same as in the stream's `done` event. Use it to rate the answer (`POST /api/assistant/feedback`). |
| `source_link`, `faq_id`, `similarity_score` | as in contract v1 | **Deprecated, kept for Sprint 2 only.** `source_link` and `faq_id` are the first source. Read `sources` instead; they are removed in Sprint 3. |

`answer` is always one of:

| Case | `answer` | `source_link` / `faq_id` | `similarity_score` |
| ---- | -------- | ------------------------ | ------------------ |
| FAQ match (score ≥ `SIMILARITY_THRESHOLD`), model answer passes the grounding check (US10) | Gemini's answer in its own words, from the cited FAQ items only; a combined question gets one answer | first cited item; `sources` lists every cited item | best item's cosine similarity |
| FAQ match, but no model answer: no `GEMINI_API_KEY`, every free model at its limit, API error, model timeout, or the answer fails the grounding check | The best FAQ item's answer, verbatim (Sprint 1) | set | cosine similarity |
| Catalogue question (US12): fee, deadline, language or faculty of a program, a comparison, or a program list | Values from the catalogue, see *Catalogue answers* below | `source_link` is the first program page, `faq_id` `null` | `null` |
| No FAQ match (T3.4) | `I could not find this information in the official FAQ. Please contact the admissions office: <contact>` | `null` | best score, or `null` when the FAQ is empty |
| Document question (T3.6), one program, applicant type given | `Required documents for <Program> (<degree>, <code>), <local\|international> applicant:` and one line per document | `null` | `null` |
| Document question, applicant type not given | Asks the applicant to say "local" or "international" | `null` | `null` |
| Document question matching several programs (e.g. the bachelor and master Information Systems) | Lists the programs with degree and code and asks for the code | `null` | `null` |
| Document question, no requirements stored (T4.3) | `The document list for this program is not published yet, please contact the admissions office. <contact>` | `null` | `null` |

Unanswered questions and programs without requirements are recorded in the `admissions_followup` table for the admissions office.

A document question contains "document", "paperwork", "checklist", "документ" or "құжат" and names a program by its code (`6B06102`), its full title, or at least two thirds of the words of a title with three or more words. A degree word (bachelor, master, PhD, магистр…) narrows the match to that degree. The applicant type is read from "local", "Kazakhstani", "citizen(s) of Kazakhstan", "местный" (local) or "international", "foreign", "abroad", "иностранец", "шетел" (international); words that are part of the program title ("International Relations") do not count.

**Catalogue answers (US12).** A question that names a program (code, title or most of a long title) and asks for its fee ("tuition", "cost", "ECTS", "стоимость"…), application deadline ("deadline", "until when", "срок", "мерзім"…), language of instruction or faculty is answered from the catalogue. So is "compare X and Y" (fee, language, both deadlines and faculty, one line per value with each program side by side; up to 3 programs), a question with two or more program codes, and a program list ("Which master programs are taught in English?", filtered by degree, language and faculty). A program named with no topic and no FAQ match gets its catalogue summary. A value that is empty in the catalogue is answered as "not published yet" (fees: "The catalogue does not publish a tuition fee for …") with the Admissions Office contact, never with a number, and that program page is not cited. A title shared by several programs (Information Systems) gets the "which program?" answer.

The catalogue tools `search_programs(query, degree_level, language, faculty)` and `get_program(program_id)` (`app/assistant/catalogue_tools.py`) read the catalogue service. With a model, the records they return, the FAQ items above the threshold and the office contact are sent in one call; the model must cite every `program_id` and `faq_id` it uses, and every number in its answer must be in the cited records or items (or in the contact, for an unpublished value), so a computed total or an invented date is rejected. The tools run in the answer service, not in a model tool-call loop: a loop needs a second free-tier call (about 6 s each), which does not fit the 15 s budget. Without a model, or when its answer is rejected, the catalogue answer above is built from the same records.

**Grounded answers (US10).** The model gets the best FAQ item and the other items of the top `GROUNDING_TOP_K` (default 5) that are above the threshold and written for the applicant's audience, and the rule: answer only from these items, cite every `faq_id` used, otherwise answer nothing. Its answer is used only when it cites at least one given item, cites nothing that was not given, and every number in it (dates, fees, scores) is found in the cited items or in the question; anything else gets the verbatim answer. Questions below the threshold and document checklists never reach the model. Free Gemini models are tried in `GEMINI_MODELS` order: a model at its free limit (429) or overloaded (503) is replaced by the next one; any other error or a timeout (`GEMINI_TIMEOUT_SECONDS`, default 10 s, the API minimum) ends in the verbatim answer. Every call logs model, tokens and latency.

Each FAQ item has an audience (`degrees`, `applicant_types` in `faq.json`; empty means everyone). When the question names a degree or applicant type, the best FAQ match must be written for it. Otherwise the assistant uses the best match from the same category that is, or answers with the fallback. The answer is used only when its cosine similarity is at least `SIMILARITY_THRESHOLD` (default 0.5).

### Errors

Same shape as the rest of the API: `{ "error_code": "...", "message": "..." }`.

| Status | `error_code`           | When                                          |
| ------ | ---------------------- | --------------------------------------------- |
| 422    | `INVALID_REQUEST`      | Empty/too long question or missing session id |
| 503    | `DATABASE_UNAVAILABLE` | Database unreachable                          |
| 504    | `ASSISTANT_TIMEOUT`    | No answer within `ASSISTANT_TIMEOUT_SECONDS` (default 15 s, above the 10 s model timeout so a slow model ends in the verbatim answer, not in 504) |

Latency: answers without a model (fallback, checklists, tuition, no key) take well under 1 s. A model answer takes about 6–8 s on the Gemini free tier (measured 2026-10-02: Flash-Lite ~6 s; the other free models were often overloaded), 15 s at most. **The chat widget must wait at least 15 s** for the first streamed chunk (`POST /api/assistant/ask/stream`, see [assistant-stream.md](assistant-stream.md)).

## `GET /api/assistant/suggestions`

Suggested questions for the chat widget (US14). Four starters when the session has no turns yet, and up to three follow-ups once it does. Each suggestion is an official FAQ question: sending it to `/ask` or `/ask/stream` returns that item and its source.

```
GET /api/assistant/suggestions?session_id=3f0c…
```

| Field | Rules |
| ----- | ----- |
| `session_id` | Required, 1–100 characters; the chat's session id |

### 200

```json
{
  "suggestions": [
    "What are the application deadlines for international applicants?",
    "Is the UNT required for admission to bachelor's programmes?",
    "What English level do I need for bachelor's admission?",
    "What documents do I need for tuition-based (paid) bachelor's enrollment?"
  ]
}
```

A session that already has a user turn gets at most three questions, and never one the applicant already asked in that session. A new `session_id` (the widget's *New conversation*) gets the four starters again.

## `POST /api/assistant/feedback` (US13)

Rate a stored assistant answer once. The `answer_id` comes from the `/ask` response or the `done` event of `/ask/stream`.

```json
{ "answer_id": "42", "rating": "down", "reason": "outdated" }
```

| Field | Rules |
| ----- | ----- |
| `answer_id` | Required positive decimal id of a stored assistant turn |
| `rating` | Required: `up` or `down` |
| `reason` | Optional for `down`: `outdated`, `incorrect`, `incomplete`, `unclear`, `wrong`, `other`; omit for `up` |

**201:** `{"answer_id":"42","rating":"down","reason":"outdated"}`. The server stores the rating with the anonymous session id, preceding question, answer, and answer sources. A database unique constraint allows only one rating per answer. Feedback is deleted when its chat answer is purged after 30 days.

**Errors:** `404 ANSWER_NOT_FOUND` for an unknown id or a user turn; `409 ALREADY_RATED` for a second rating; `422 INVALID_REQUEST` for invalid fields; `503 DATABASE_UNAVAILABLE` as for the other assistant endpoints.

The Product Owner can export negative ratings with `uv run python scripts/export_negative_feedback.py --days 7 --output feedback.csv` from `backend/`. The CSV contains timestamp, question, answer, sources and reason, but no session id or answer id. Email addresses and phone numbers in free text are redacted. Review the CSV before sharing because free text may contain other personal details.

### Errors

Same shape as `/ask`: `422 INVALID_REQUEST` when `session_id` is missing or too long, `503 DATABASE_UNAVAILABLE` when the database is unreachable.
