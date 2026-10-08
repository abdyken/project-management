type AbortReason = "close" | "new"

let controller: AbortController | null = null
let epoch = 0
let reason: AbortReason | null = null

export function nextRequest() {
  controller?.abort()
  epoch += 1
  reason = null
  controller = new AbortController()
  return { signal: controller.signal, token: epoch }
}

export function abortRequest(why: AbortReason) {
  reason = why
  if (why === "new") epoch += 1
  controller?.abort()
  controller = null
}

export function finishRequest(token: number) {
  if (token === epoch) controller = null
}

export function isCurrent(token: number) {
  return token === epoch
}

export function abortReason() {
  return reason
}
