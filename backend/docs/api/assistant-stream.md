# Streaming answers — `POST /api/assistant/ask/stream` (US14)

Owner: Dinmukhamed (backend). For: Daniyar (streaming in the widget, US14), Nurmek (`answer_id` for feedback, US13), Serdar (model token stream, US10).

Same request, same answer, same fallbacks and same time budget as `POST /api/assistant/ask` (see [assistant.md](assistant.md)); only the delivery differs: the answer text arrives in pieces as [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events).

## Request

```http
POST /api/assistant/ask/stream
Content-Type: application/json

{ "question": "Which documents do I need for 6B06102 as a local applicant?", "session_id": "<uuid>" }
```

`session_id` also scopes the conversation context (US11): follow-ups such as *"and as an international applicant?"* are understood from the last 6 turns of the same session only. A new `session_id` (the widget's *New conversation*) starts with no context.

## Errors before the stream starts — normal JSON, same as `/ask`

| Status | `error_code` | When |
| ------ | ------------ | ---- |
| 422 | `INVALID_REQUEST` | Empty or too long question, missing `session_id` |
| 503 | `DATABASE_UNAVAILABLE` | Database unreachable (`Retry-After` header) |
| 504 | `ASSISTANT_TIMEOUT` | No answer within the time budget (`ASSISTANT_TIMEOUT_SECONDS`) |

Check `response.ok` and the `Content-Type` before reading the body as a stream.

## 200 — `Content-Type: text/event-stream`

```text
event: chunk
data: {"text": "Required documents for "}

event: chunk
data: {"text": "Computer Science (bachelor, "}

...

event: done
data: {"answer_id": "42", "sources": []}
```

For an FAQ answer `done` carries the source:

```text
event: done
data: {"answer_id": "43", "sources": [{"faq_id": "faq-003", "question": "How do I apply online for a bachelor's programme?", "link": "https://sdu.edu.kz/...", "title": "How do I apply online for a bachelor's programme?"}]}
```

| Event | Data | Meaning |
| ----- | ---- | ------- |
| `chunk` | `{"text": string}` | Next piece of the answer. Append in order; all `text` values joined are exactly the `/ask` `answer` (including newlines of document lists). |
| `done` | see below | Always the last event of a complete answer. |
| `error` | `{"error_code", "message"}` | Reserved: the answer broke off after streaming started (model answers, US10). The pieces shown so far are incomplete — mark the message as interrupted and offer resend. Not sent by the current answer service. |

`done` data:

| Field | Type | Notes |
| ----- | ---- | ----- |
| `answer_id` | string | Id of the stored answer. Use it to rate the answer (US13 feedback). |
| `sources` | `[{faq_id, question, link, title}]` | Same as `sources` in the `/ask` response (contract v3, [assistant.md](assistant.md)). `[]` when the answer has no source (checklist answers, fallbacks). |

A stream that ends without `done` was interrupted (network, closed tab): treat it like `error`.

## Timing

- The first `chunk` arrives as soon as the answer is ready: under 1 s without a model, about 6–8 s for a model answer (US10), never later than `ASSISTANT_TIMEOUT_SECONDS` (15 s). The widget's timeout counts to the first chunk and must be at least 15 s.
- Chunks are paced by `STREAM_CHUNK_DELAY_SECONDS` (default 0.02 s, 0 = no pause) and a long answer always finishes within 2 s. Model answers (US10) are streamed the same way, not token by token: the grounding check needs the whole answer before any of it is shown, so an invented number is never on screen.
- The response sends `X-Accel-Buffering: no` and `Cache-Control: no-cache`, so nginx (the `web` container) passes chunks through instead of buffering the whole answer.

## Reading it in the browser

`EventSource` only supports GET, so use `fetch` and read the body:

```ts
const res = await fetch(`${BASE_URL}/api/assistant/ask/stream`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question, session_id }),
  signal, // AbortController: abort when the widget closes
})
if (!res.ok || !res.headers.get("content-type")?.startsWith("text/event-stream")) {
  // JSON error body: { error_code, message }
}
const reader = res.body!.pipeThrough(new TextDecoderStream()).getReader()
let buffer = ""
for (;;) {
  const { value, done } = await reader.read()
  if (done) break
  buffer += value
  let end
  while ((end = buffer.indexOf("\n\n")) !== -1) {
    const block = buffer.slice(0, end)
    buffer = buffer.slice(end + 2)
    const event = /^event: (.*)$/m.exec(block)?.[1]
    const data = JSON.parse(/^data: (.*)$/m.exec(block)?.[1] ?? "{}")
    // event === "chunk" -> append data.text; "done" -> sources + answer_id; "error" -> interrupted
  }
}
```
