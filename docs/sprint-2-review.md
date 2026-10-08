# Sprint 2 — review, acceptance and retro

**Sprint:** 26.09 – 02.10.2026. **Record written:** 08.10.2026 (the review on 02.10 ran without merged code, so the outcome below replaces it).

## Sprint goal

> The chat assistant answers in its own words from official sources (Gemini Flash, free tier), remembers the conversation, answers program facts from the catalogue, streams answers with suggested questions and collects ratings — all running on the deployed dev environment.

**Result:** everything except the last part is built and checked locally. Nothing of Sprint 2 runs on dev yet, so under the Definition of Done no story is accepted.

## Stories (PO.2)

| Story | Built | Local QA | Dev QA | Status |
| --- | --- | --- | --- | --- |
| US10 Grounded AI Answers | Gemini model chain, grounded answers, grounding check, contract v2, evaluation set v2 (PR #11) | Model run by Serdar on 02.10: 38/40, 0 invented facts; without a model 35/40 | Open: needs `GEMINI_API_KEY` in Render | Done, not accepted |
| US11 Follow-up Questions in Context | Turn storage, follow-ups, new conversation, FAQ-topic follow-ups, daily purge | `US11-QA.md` — PASS | Open | Done, not accepted |
| US12 Catalogue Facts in the Chat | Catalogue tools, fee/deadline/language/faculty answers, comparison, program lists, "not published yet" | `US12-QA.md` — 36/36 catalogue checks, US12QATest PASS | Open | Done, not accepted |
| US13 Answer Feedback | Feedback endpoint (now bound to the session), rating buttons, export | `US13-QA.md` — PASS | Open | Done, not accepted |
| US14 Streaming Answers and Suggested Questions | SSE endpoint, streaming widget, sources, suggestions | `US14-QA.md` — 78/78 in Chromium and Firefox | Open | Done, not accepted |

**Accepted:** none. **Carried over to Sprint 3:** the dev run of US10–US14 (one task, see below). No development work is carried over.

**Decisions recorded (Product Owner):**

- US12: the catalogue tools run in the answer service and their records go to the model in one call, instead of a model-driven tool loop. A loop needs a second free-tier call (about 6 s each) and does not fit the 15 s answer budget.
- US14: answers are streamed after the grounding check, not token by token, because the check needs the whole answer. "First words within 2 s" holds for answers without a model (checklists, catalogue, fallback); a model answer starts after the model call (1–6 s). Accepted as a known deviation; revisit if a paid or faster model is ever used.
- US13: the feedback request now carries `session_id`; an answer can only be rated from its own chat session (review finding).

## Carry-over and new inputs for Sprint 3

| Item | Owner | Why it is open |
| --- | --- | --- |
| Merge PR #11 → US12 → wrap-up after review; deploy to dev; set `GEMINI_API_KEY` in Render; run US10–US14 QATests on dev | Daniyar (SM) with the repository owner | Needs the hosting accounts |
| SM.3 branch protection on `main` | Daniyar with the repository owner | GitHub settings, not code |
| SM.4 contract confirmations (programs, assistant v2) | Daniyar, Serdar | Needs the people to confirm |
| PO.3 request to the admissions office | Askhat | Draft below; must be sent by the Product Owner |

## PO.3 — request to the admissions office (draft)

> Subject: SDU admissions portal — official texts for Sprint 3
>
> Dear Admissions Office,
>
> for the next version of the admissions portal and its assistant we would like to ask for:
>
> 1. The official Kazakh and Russian texts of the FAQ items you approved in September (35 items).
> 2. The official titles of all study programs in Kazakh, Russian and English.
> 3. The full list of 2026–2027 programs (bachelor, master, PhD) with faculty, language of instruction, tuition per ECTS credit, application deadlines and the required documents for local and international applicants.
> 4. Answers to the questions applicants asked the assistant that it could not answer (list attached from the portal's follow-up log).
>
> Until we receive them, the portal uses the texts published on sdu.edu.kz, marked as pending your review.
>
> Kind regards, Askhat (Product Owner)

## Retro (SM.5)

| Went well | Went badly | Action for Sprint 3 |
| --- | --- | --- |
| The model chain and grounding check gave 0 invented facts in every run | No Sprint 2 code was merged by the review day; branches were stacked and reviewed late | Merge each story's PR as soon as its tests pass; no stacked branches older than 2 days |
| Contract v2 let the widget and the API move in parallel once it existed | Contract v2 came on day 4 instead of day 2 | Contract changes first in the sprint, confirmed in the doc |
| Scripted widget QA (`frontend/e2e/widget-qa.mjs`) covers both browsers and three widths in minutes | Dev deploy was not part of the sprint flow, so no story could be accepted | Deploy to dev after every merge; acceptance runs on dev before the review |
