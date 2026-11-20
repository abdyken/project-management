import { isApiError } from "@/api/errors"
import { cloneElement, isValidElement, useId, type ReactNode } from "react"
import { useGuidanceT } from "@/guidance/i18n"

export const fieldClass =
  "h-11 w-full min-w-0 rounded-none border-2 border-input bg-card px-3 text-base outline-none transition-colors hover:border-ink focus-visible:border-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
export function Field({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  const generatedId = useId()
  const control = isValidElement<{ id?: string }>(children) ? children : null
  const id = control?.props.id ?? generatedId
  return (
    <div className="block min-w-0 space-y-1.5">
      <label htmlFor={id} className="block text-[0.9375rem] font-semibold"><span>{label}</span></label>
      {control ? cloneElement(control, { id }) : children}
    </div>
  )
}
export function ErrorMessage({ error }: { error: unknown }) {
  const t = useGuidanceT()
  return error ? (
    <p role="alert" className="mt-4 text-sm text-destructive">
      {t(isApiError(error) && error.status === 429 ? "tooMany" : "error")}
    </p>
  ) : null
}
