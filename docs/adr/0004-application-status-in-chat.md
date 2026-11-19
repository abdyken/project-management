# ADR 0004: Application status in the chat

**Date:** 19.11.2026. **Status:** accepted.

## Context
US6: "what is the status of my application?" in the chat. The chat endpoint
`/api/assistant` is public, and the applicant session cookie is scoped to
`/api/applicant`, so the chat does not know who is asking.

## Decision
The assistant recognises status questions (EN/RU/KK) and answers them without the model
and without personal data, marking the answer `intent: "application_status"`. When the
widget sees that intent and the visitor is logged in, it calls
`GET /api/applicant/applications/status`, which builds the stage and next step from the
database in the applicant's language, and shows it as a second message.

## Alternatives considered
- **Widen the cookie path to `/api`**: every public request would carry the session.
- **Let the model answer from the database**: personal data in the prompt, and no
  guarantee the stage is stated correctly.

## Consequences
The cookie scope and the "no personal data to the model" rule stay intact. Anonymous
visitors get a short answer with a link to log in.
