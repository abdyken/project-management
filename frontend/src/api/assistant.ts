import { request } from "@/api/client"
import type { AssistantResponse } from "@/api/types"
import { ASSISTANT_TIMEOUT_MS } from "@/lib/constants"

export function askAssistant(question: string, sessionId: string, signal?: AbortSignal) {
  return request<AssistantResponse>("/api/assistant/ask", {
    method: "POST",
    body: JSON.stringify({ question, session_id: sessionId }),
    timeoutMs: ASSISTANT_TIMEOUT_MS,
    signal,
  })
}
