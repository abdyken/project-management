import { Link, NavLink } from "react-router-dom"
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher"
import { useI18n } from "@/i18n"
import { useChatStore } from "@/store/chat"

export function SiteHeader() {
  const { t } = useI18n()
  const setOpen = useChatStore((state) => state.setOpen)
  const links = [
    { to: "/", label: t("nav.overview") },
    { to: "/programs", label: t("nav.programs") },
  ]

  return (
    <header className="border-b border-border/80">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-3 px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2">
          <img src="/logo.svg" alt="" className="size-6" />
          <span className="text-xl font-semibold tracking-tight">SDU</span>
          <span className="hidden text-[11px] tracking-[0.12em] text-muted-foreground uppercase md:inline">
            {t("header.admissions")}
          </span>
        </Link>
        <nav className="flex items-center gap-3 text-sm sm:gap-5">
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
