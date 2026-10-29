import { Link, NavLink } from "react-router-dom"
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher"
import { useApplicantT } from "@/applicant/i18n"
import { useI18n } from "@/i18n"
import { useChatStore } from "@/store/chat"
import { useGuidanceT } from "@/guidance/i18n"

export function SiteHeader() {
  const { t } = useI18n()
  const applicantT = useApplicantT()
  const guidanceT = useGuidanceT()
  const setOpen = useChatStore((state) => state.setOpen)
  const links = [
    { to: "/", label: t("nav.overview") },
    { to: "/programs", label: t("nav.programs") },
    { to: "/admissions", label: guidanceT("hub") },
    { to: "/account", label: applicantT("account") },
  ]

  return (
    <header className="border-b border-border/80">
      <div className="mx-auto flex min-h-16 max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link to="/" className="flex shrink-0 items-center gap-2">
          <img src="/logo.svg" alt="" className="size-6" />
          <span className="text-xl font-semibold tracking-tight">SDU</span>
          <span className="hidden text-[11px] tracking-[0.12em] text-muted-foreground uppercase md:inline">
            {t("header.admissions")}
          </span>
        </Link>
        <nav className="flex min-w-0 flex-wrap items-center justify-end gap-x-3 gap-y-2 text-sm sm:gap-x-5">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                [
                  isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground",
                  link.to === "/" ? "hidden sm:inline" : "",
                ].join(" ")
              }
            >
              {link.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="hidden text-muted-foreground hover:text-foreground sm:inline"
          >
            {t("nav.ask")}
          </button>
          <LanguageSwitcher />
        </nav>
      </div>
    </header>
  )
}
