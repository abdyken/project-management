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

export const ASSISTANT_TIMEOUT_MESSAGE =
  "The assistant is not responding, please try again or contact the admissions office"

export function chatErrorMessage(error: unknown): string {
  if (!isApiError(error)) {
    return "Something went wrong. Please try again or contact the admissions office."
  }
  if (error.code === "TIMEOUT" || error.code === "ASSISTANT_TIMEOUT") {
    return ASSISTANT_TIMEOUT_MESSAGE
  }
  if (error.code === "NETWORK") {
    return "Could not reach the assistant. Check your connection and try again."
  }
  if (error.code === "INVALID_REQUEST") {
    return "This question can't be sent. Keep it under 500 characters and try again."
  }
  return "The assistant is unavailable right now. Please try again or contact the admissions office."
}
