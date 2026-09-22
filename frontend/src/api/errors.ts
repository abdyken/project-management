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

const ASSISTANT_TIMEOUT =
  "The assistant is not responding, please try again or contact the admissions office"

export function toReadableError(error: unknown): string {
  if (isApiError(error)) {
    if (error.code === "TIMEOUT" || error.code === "ASSISTANT_TIMEOUT" || error.status === 504) {
      return ASSISTANT_TIMEOUT
    }
    if (error.code === "ASSISTANT_UNAVAILABLE") {
      return "The assistant is temporarily unavailable. Please try again or contact the admissions office."
    }
    if (error.code === "EMPTY_QUESTION") {
      return "Write a question before sending."
    }
    if (error.code === "QUESTION_TOO_LONG") {
      return "That question is too long. Shorten it and try again."
    }
    if (error.status === 503 || error.code === "SERVICE_UNAVAILABLE" || error.code === "DATABASE_UNAVAILABLE") {
      return "The catalogue is temporarily unavailable. Please try again."
    }
    if (error.status >= 500) {
      return "The service is unavailable right now. Please try again or contact the admissions office."
    }
    if (error.status >= 400) {
      return error.message || "The request could not be processed. Please rephrase and try again."
    }
    return error.message
  }
  return "Something went wrong. Please try again or contact the admissions office."
}
