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

export function toReadableError(error: unknown): string {
  if (isApiError(error)) {
    if (error.code === "TIMEOUT") {
      return "The assistant is not responding, please try again or contact the admissions office"
    }
    if (error.status === 503 || error.code === "SERVICE_UNAVAILABLE") {
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
