# FAQ assistant API (US3 / T3.5)

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
  "source_link": "https://sdu.edu.kz/en/…",
  "faq_id": "faq-004",
  "similarity_score": 0.83
}
```

`answer` is always one of:

| Case | `answer` | `source_link` / `faq_id` | `similarity_score` |
| ---- | -------- | ------------------------ | ------------------ |
| FAQ match (score ≥ `SIMILARITY_THRESHOLD`) | The FAQ item's answer, verbatim | set | cosine similarity |
| No FAQ match (T3.4) | `I could not find this information in the official FAQ. Please contact the admissions office: <contact>` | `null` | best score, or `null` when the FAQ is empty |
| Document question (T3.6), applicant type given | `Required documents for <Program> (<local\|international> applicant):` and one line per document | `null` | `null` |
| Document question, applicant type not given | Asks the applicant to say "local" or "international" | `null` | `null` |
| Document question, no requirements stored (T4.3) | `The document list for this program is not published yet, please contact the admissions office. <contact>` | `null` | `null` |

Unanswered questions and programs without requirements are recorded in the `admissions_followup` table for the admissions office.

A document question is recognised by words like "documents", "checklist", "документы" plus a program title (or part of it, e.g. "law") or program code. The applicant type is read from words like "local", "citizen", "international", "foreign", "иностранец".

### Errors

Same shape as the rest of the API: `{ "error_code": "...", "message": "..." }`.

| Status | `error_code`           | When                                          |
| ------ | ---------------------- | --------------------------------------------- |
| 422    | `INVALID_REQUEST`      | Empty/too long question or missing session id |
| 503    | `DATABASE_UNAVAILABLE` | Database unreachable                          |
| 504    | `ASSISTANT_TIMEOUT`    | No answer within `ASSISTANT_TIMEOUT_SECONDS` (default 4 s) |

Latency budget: 5 s end to end. The chat widget gives up after 10 s (T2.4).
