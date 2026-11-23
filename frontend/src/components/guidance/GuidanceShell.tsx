import type { ReactNode } from "react"
import { Link, NavLink, useLocation } from "react-router-dom"
import { useGuidanceT } from "@/guidance/i18n"
import { GUIDANCE_ROUTES } from "@/guidance/routes"
import { RidgeHorizon } from "@/components/mosaic/RidgeHorizon"
import { cn } from "@/lib/utils"

// Each page sits at its own bearing on the Alatau, east to west in the order an applicant reads them.
const BEARINGS: Record<string, number> = {
  "/admissions": 163,
  "/eligibility": 152,
  "/recommendations": 156,
  "/cost-calculator": 172,
  "/funding": 176,
  "/account/requests": 184,
  "/apply": 148,
  "/deadlines": 160,
  "/application-status": 180,
  "/cost-and-aid": 168,
  "/contact": 188,
  "/search": 158,
}


// Admissions planning pages: a turquoise band with the title and the tools as tile tabs,
// then a reading column. Mode: Read.
// `tools={false}` for the information pages (apply, deadlines, status, contact): no tool tabs,
// and the content uses the full page width like the hub.
export function GuidanceShell({ title, lead, children, tools = true }: { title: string; lead?: string; children: ReactNode; tools?: boolean }) {
  const t = useGuidanceT()
  const { pathname } = useLocation()
  const onHub = pathname === "/admissions"
  const wide = onHub || !tools

  return (
    <div>
      <section className="on-field relative bg-field">
        <div className="mx-auto max-w-[84rem] px-4 pt-8 pb-4 sm:px-6 lg:px-8">
          {onHub ? null : (
            <Link className="text-[0.9375rem] font-semibold text-field-muted underline decoration-field-foreground/40 underline-offset-4 hover:text-field-foreground" to="/admissions">
              {t("hub")}
            </Link>
          )}
          <h1 className={cn("max-w-[20ch] text-[clamp(2.5rem,4.5vw,4rem)] leading-[1.06] font-medium", onHub ? "mt-4" : "mt-6")}>
            {title}
          </h1>
          {lead ? <p className="mt-5 max-w-[60ch] text-lg text-field-muted">{lead}</p> : null}
          {wide ? null : (
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
        <RidgeHorizon bearing={BEARINGS[pathname] ?? 163} />
      </section>
      <div className={cn("mx-auto px-4 pt-16 pb-24 sm:px-6 lg:px-8 lg:pt-20", wide ? "max-w-[84rem]" : "max-w-[84rem] [&>*]:max-w-6xl")}>{children}</div>
    </div>
  )
}
