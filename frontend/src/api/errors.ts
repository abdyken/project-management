import type { MessageKey } from "@/i18n/messages"

export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.code = code
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

export function isNotFound(error: unknown) {
  return isApiError(error) && error.status === 404
}

export function isInvalidRequest(error: unknown) {
  return isApiError(error) && error.status === 422
}

export function chatErrorKey(error: unknown): MessageKey {
  if (!isApiError(error)) return "chat.error.generic"
  if (error.code === "TIMEOUT" || error.code === "ASSISTANT_TIMEOUT") return "chat.error.timeout"
  if (error.code === "NETWORK") return "chat.error.network"
  if (error.code === "INVALID_REQUEST") return "chat.error.invalid"
  return "chat.error.unavailable"
}
