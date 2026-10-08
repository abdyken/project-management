import { apiUrl, errorFromResponse } from "@/api/client"
import { ApiError } from "@/api/errors"
import type { FeedbackRequest, StreamDone, SuggestionsResponse } from "@/api/types"
import { ASSISTANT_TIMEOUT_MS } from "@/lib/constants"

export type StreamHandlers = {
  onChunk: (text: string) => void
  onDone: (done: StreamDone) => void
}

export type StreamOutcome = "done" | "interrupted" | "aborted"

type SseEvent = { event: string; data: string }

function parseSseBlock(block: string): SseEvent | null {
  let event = "message"
  const data: string[] = []
  for (const line of block.split(/\r?\n/)) {
    if (!line || line.startsWith(":")) continue
    if (line.startsWith("event:")) event = line.slice(6).trim()
    else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""))
  }
  if (data.length === 0) return null
  return { event, data: data.join("\n") }
}

export function getSuggestions(sessionId: string, language: string, signal?: AbortSignal) {
  const params = new URLSearchParams({ session_id: sessionId, lang: language })
  return fetch(apiUrl(`/api/assistant/suggestions?${params}`), {
    headers: { Accept: "application/json" },
    signal,
  }).then(async (res) => {
    if (!res.ok) throw await errorFromResponse(res)
    const body = (await res.json()) as SuggestionsResponse
    return body.suggestions
  })
}

export function sendFeedback(body: FeedbackRequest) {
  return fetch(apiUrl("/api/assistant/feedback"), {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(async (res) => {
    if (res.ok) return
    const error = await errorFromResponse(res)
    if (error.code !== "ALREADY_RATED") throw error
  })
}

export async function streamAssistant(
  question: string,
  sessionId: string,
  signal: AbortSignal,
  handlers: StreamHandlers,
): Promise<StreamOutcome> {
  const controller = new AbortController()
  const abortFromCaller = () => controller.abort()
  if (signal.aborted) abortFromCaller()
  else signal.addEventListener("abort", abortFromCaller, { once: true })

  let gotChunk = false
  const timer = window.setTimeout(() => {
    if (!gotChunk) controller.abort()
  }, ASSISTANT_TIMEOUT_MS)

  try {
    const res = await fetch(apiUrl("/api/assistant/ask/stream"), {
      method: "POST",
      headers: { Accept: "text/event-stream", "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: sessionId }),
      signal: controller.signal,
    })

    const contentType = res.headers.get("content-type") ?? ""
    if (!res.ok || !contentType.includes("text/event-stream")) {
      throw await errorFromResponse(res)
    }
    if (!res.body) throw new ApiError(0, "NETWORK", "Network error")

    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader()
    let buffer = ""
    let finished = false

    for (;;) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += value
      let end = buffer.indexOf("\n\n")
      while (end !== -1) {
        const parsed = parseSseBlock(buffer.slice(0, end))
        buffer = buffer.slice(end + 2)
        end = buffer.indexOf("\n\n")
        if (!parsed) continue
        if (parsed.event === "chunk") {
          const text = (JSON.parse(parsed.data) as { text?: string }).text ?? ""
          if (!gotChunk) {
            gotChunk = true
            window.clearTimeout(timer)
          }
          if (text) handlers.onChunk(text)
        } else if (parsed.event === "done") {
          finished = true
          handlers.onDone(JSON.parse(parsed.data) as StreamDone)
        } else if (parsed.event === "error") {
          return "interrupted"
        }
      }
    }

    return finished ? "done" : "interrupted"
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === "AbortError") {
      if (signal.aborted) return "aborted"
      if (!gotChunk) throw new ApiError(0, "TIMEOUT", "Request aborted")
      return "interrupted"
    }
    throw new ApiError(0, "NETWORK", "Network error")
  } finally {
    window.clearTimeout(timer)
    signal.removeEventListener("abort", abortFromCaller)
  }
}
