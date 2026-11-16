import { cloneElement, isValidElement, useId, type ReactNode } from "react"
import { useGuidanceT } from "@/guidance/i18n"

export const fieldClass =
  "w-full min-w-0 rounded-md border border-border bg-background px-3 py-2 text-base sm:text-sm"
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
    <div className="block min-w-0 space-y-1 text-sm">
      <label htmlFor={id} className="block"><span>{label}</span></label>
      {control ? cloneElement(control, { id }) : children}
    </div>
  )
}
export function ErrorMessage({ error }: { error: unknown }) {
  const t = useGuidanceT()
  return error ? (
    <p role="alert" className="mt-4 text-sm text-destructive">
      {t("error")}
    </p>
  ) : null
}
