import type { ReactNode } from "react"
import { Link, NavLink, useLocation } from "react-router-dom"
import { mosaicRow } from "@/components/mosaic/pattern"
import { Tesserae } from "@/components/mosaic/Tesserae"
import { useGuidanceT } from "@/guidance/i18n"
import { GUIDANCE_ROUTES } from "@/guidance/routes"
import { cn } from "@/lib/utils"

const BAND_EDGE = [mosaicRow(140, 70, 0.5, ["deep", "field", "glacier", "ochre", "deep"])]

// Admissions planning pages: a turquoise band with the title and the tools as tile tabs,
// then a reading column. Mode: Read.
export function GuidanceShell({ title, lead, children }: { title: string; lead?: string; children: ReactNode }) {
  const t = useGuidanceT()
  const { pathname } = useLocation()
  const onHub = pathname === "/admissions"

  return (
    <div>
      <section className="on-field relative bg-field">
        <div className="mx-auto max-w-[84rem] px-4 pt-8 pb-10 sm:px-6 lg:px-8">
          {onHub ? null : (
            <Link className="text-[0.9375rem] font-semibold text-field-muted underline decoration-field-foreground/40 underline-offset-4 hover:text-field-foreground" to="/admissions">
              {t("hub")}
            </Link>
          )}
          <h1 className={cn("max-w-[20ch] text-[clamp(2.5rem,6vw,5rem)] leading-[0.88] font-extrabold uppercase", onHub ? "mt-4" : "mt-6")}>
            {title}
          </h1>
          {lead ? <p className="mt-5 max-w-[60ch] text-lg text-field-muted">{lead}</p> : null}
          {onHub ? null : (
          <nav aria-label={t("hub")} className="mt-10 flex flex-wrap gap-1.5">
            {GUIDANCE_ROUTES.map(([key, to]) => (
              <NavLink
                key={key}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "inline-flex min-h-11 items-center px-4 text-[0.9375rem] font-semibold transition-colors duration-200",
                    isActive ? "bg-field-foreground text-field" : "bg-field-deep text-field-foreground hover:bg-ink",
                  )
                }
              >
                {t(key)}
              </NavLink>
            ))}
          </nav>
          )}
        </div>
        <div className="absolute inset-x-0 top-full overflow-hidden">
          <Tesserae size={24} rows={BAND_EDGE} />
        </div>
      </section>
      <div className={cn("mx-auto px-4 pt-16 pb-24 sm:px-6 lg:px-8 lg:pt-20", onHub ? "max-w-[84rem]" : "max-w-6xl")}>{children}</div>
    </div>
  )
}
