import { ApiError } from "@/api/errors"
import { mockRequest } from "@/mocks/handlers"

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== "false"
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "")

type RequestOptions = RequestInit & {
  query?: Record<string, string | undefined>
  timeoutMs?: number
}

function withQuery(path: string, query?: Record<string, string | undefined>) {
  if (!query) return path
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value) params.set(key, value)
  }
  const encoded = params.toString()
  return encoded ? `${path}?${encoded}` : path
}

function mergeSignals(timeoutMs?: number, external?: AbortSignal) {
  const controller = new AbortController()

  const abort = () => controller.abort()
  const timer = timeoutMs ? window.setTimeout(abort, timeoutMs) : undefined

  if (external?.aborted) abort()
  else external?.addEventListener("abort", abort, { once: true })

  return {
    signal: controller.signal,
    cleanup: () => {
      if (timer) window.clearTimeout(timer)
    },
  }
}

async function parseError(res: Response) {
  const body = (await res.json().catch(() => ({}))) as { error_code?: string; message?: string }
  throw new ApiError(
    res.status,
    body.error_code ?? (res.status === 503 ? "SERVICE_UNAVAILABLE" : "HTTP_ERROR"),
    body.message ?? res.statusText,
  )
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { query, timeoutMs, headers, ...init } = options
  const url = withQuery(path, query)
  const { signal, cleanup } = mergeSignals(timeoutMs, init.signal ?? undefined)

  try {
    if (USE_MOCKS) {
      try {
        return await mockRequest<T>(url, { ...init, signal })
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          throw new ApiError(0, "TIMEOUT", "Request aborted")
        }
        throw error
      }
    }

    const res = await fetch(`${BASE_URL}${url}`, {
      ...init,
      signal,
      headers: {
        Accept: "application/json",
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
    })

    if (!res.ok) {
      await parseError(res)
    }

    return (await res.json()) as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(0, "TIMEOUT", "Request aborted")
    }
    throw new ApiError(0, "NETWORK", "Network error")
  } finally {
    cleanup()
  }
}

export const useMocks = USE_MOCKS
