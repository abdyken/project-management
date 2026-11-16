import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import { useGuidanceT } from "@/guidance/i18n"
import { GUIDANCE_ROUTES } from "@/guidance/routes"

export function GuidanceShell({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  const t = useGuidanceT()
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <Link className="text-sm underline" to="/admissions">
        {t("hub")}
      </Link>
      <h1 className="mt-4 text-3xl font-semibold tracking-tight">{title}</h1>
      <nav
        aria-label={t("hub")}
        className="my-6 flex flex-wrap gap-x-5 gap-y-2 text-sm"
      >
        {GUIDANCE_ROUTES.map(([key, to]) => (
          <Link className="underline underline-offset-4" key={key} to={to}>
            {t(key)}
          </Link>
        ))}
      </nav>
      {children}
    </div>
  )
}

