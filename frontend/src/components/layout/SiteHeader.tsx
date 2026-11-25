import * as Dialog from "@radix-ui/react-dialog"
import { ArrowRight, Menu, Search, X } from "lucide-react"
import { useState } from "react"
import { Link, NavLink } from "react-router-dom"
import { useFeatures } from "@/api/features"
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher"
import { useApplicantT } from "@/applicant/i18n"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { useInfoT } from "@/info/i18n"
import { cn } from "@/lib/utils"
import { useChatStore } from "@/store/chat"

const OFFICIAL_APPLICATION_PORTAL = "https://admissions.sdu.edu.kz"

export function SiteHeader() {
  const { t } = useI18n()
  const applicantT = useApplicantT()
  const guidanceT = useGuidanceT()
  const infoT = useInfoT()
  const setChatOpen = useChatStore((state) => state.setOpen)
  const features = useFeatures()
  const [menuOpen, setMenuOpen] = useState(false)

  const links = [
    { to: "/programs", label: t("nav.programs") },
    { to: "/admissions", label: guidanceT("hub") },
    { to: "/account", label: applicantT("account") },
  ]
  // Purdue's pattern: one calm row, and a Menu panel that groups everything else.
  const groups = [
    {
      title: infoT("hub.applyTitle"),
      links: [
        { to: "/apply", label: infoT("apply.title") },
        { to: "/deadlines", label: infoT("deadlines.title") },
        { to: "/application-status", label: infoT("status.title") },
        { to: "/cost-and-aid", label: infoT("costaid.title") },
        { to: "/contact", label: infoT("contact.title") },
      ],
    },
    {
      title: guidanceT("hub"),
      links: [
        { to: "/eligibility", label: guidanceT("eligibility") },
        { to: "/recommendations", label: guidanceT("recommendations") },
        { to: "/cost-calculator", label: guidanceT("cost") },
        { to: "/funding", label: guidanceT("funding") },
        { to: "/compare", label: t("footer.compare") },
        { to: "/account/requests", label: guidanceT("requests") },
      ],
    },
    {
      title: infoT("footer.infoFor"),
      links: [
        { to: "/apply#bachelor-local", label: infoT("footer.schoolLeavers") },
        { to: "/apply#bachelor-international", label: infoT("footer.international") },
        { to: "/apply#master", label: infoT("footer.masters") },
        { to: "/apply#phd", label: infoT("footer.phd") },
        { to: "/cost-and-aid", label: infoT("footer.parents") },
      ],
    },
  ]
  const applyInPortal = features.data?.applications === true

  const apply = applyInPortal ? (
    <Link to="/account/applications" className={applyClass}>
      {t("header.apply")}
      <ArrowRight aria-hidden="true" />
    </Link>
  ) : (
    <a href={OFFICIAL_APPLICATION_PORTAL} target="_blank" rel="noreferrer" className={applyClass}>
      {t("header.apply")}
      <ArrowRight aria-hidden="true" />
    </a>
  )

  return (
    <header className="on-field relative z-30 bg-field">
      <a
        href="#main"
        className="absolute top-2 left-2 z-50 -translate-y-24 bg-white px-4 py-2 font-semibold text-ink focus:translate-y-0"
      >
        {t("header.skip")}
      </a>
      <div className="mx-auto flex h-16 max-w-[84rem] items-center gap-3 px-4 sm:px-6 lg:h-[4.5rem] lg:gap-6 lg:px-8">
        <Link to="/" aria-label={t("header.home")} className="flex shrink-0 items-center gap-3">
          <img src="/brand/sdu-lockup-white.svg" alt="" className="h-8 w-auto lg:h-10" width={108} height={34} />
          <span aria-hidden="true" className="hidden h-7 w-px bg-field-foreground/40 sm:block" />
          <span className="label hidden text-[0.9375rem] sm:block">
            {t("header.admissions")}
          </span>
        </Link>

        <nav aria-label={t("header.menu")} className="ml-auto hidden items-stretch self-stretch xl:flex">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                cn(
                  "relative flex items-center px-4 text-[0.9375rem] font-medium whitespace-nowrap transition-colors duration-200",
                  isActive ? "text-field-foreground" : "text-field-muted hover:text-field-foreground",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {link.label}
                  <span
                    aria-hidden="true"
                    className={cn(
                      "absolute inset-x-4 bottom-0 h-0.5 origin-left bg-field-foreground transition-transform duration-300 ease-out",
                      isActive ? "scale-x-100" : "scale-x-0",
                    )}
                  />
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2 xl:ml-0 xl:gap-4">
          <Link
            to="/search"
            className="hidden size-10 place-items-center text-field-muted transition-colors hover:text-field-foreground sm:grid"
          >
            <Search className="size-5" aria-hidden="true" />
            <span className="sr-only">{infoT("quick.search")}</span>
          </Link>
          <LanguageSwitcher tone="field" />
          <div className="hidden sm:block">{apply}</div>
          <Dialog.Root open={menuOpen} onOpenChange={setMenuOpen}>
            <Dialog.Trigger asChild>
              <button
                type="button"
                className="inline-flex h-10 items-center gap-2 border border-field-foreground/50 px-2.5 text-[0.9375rem] font-semibold text-field-foreground transition-colors hover:bg-field-deep 2xl:px-3.5"
              >
                <Menu className="size-5" aria-hidden="true" />
                <span className="sr-only lg:not-sr-only xl:sr-only 2xl:not-sr-only">{t("header.menu")}</span>
              </button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/40" />
              <Dialog.Content className="menu-sheet on-field fixed inset-0 z-50 flex flex-col overflow-y-auto bg-field-deep">
                <div className="mx-auto flex h-16 w-full max-w-[84rem] items-center justify-between px-4 sm:px-6 lg:h-[4.5rem] lg:px-8">
                  <img src="/brand/sdu-lockup-white.svg" alt="" className="h-8 w-auto lg:h-10" width={108} height={34} />
                  <Dialog.Close className="inline-flex h-10 items-center gap-2 border border-field-foreground/50 px-2.5 text-[0.9375rem] font-semibold hover:bg-field lg:px-3.5">
                    <X className="size-5" aria-hidden="true" />
                    <span className="sr-only lg:not-sr-only">{t("header.closeMenu")}</span>
                  </Dialog.Close>
                </div>
                <Dialog.Title className="sr-only">{t("header.menu")}</Dialog.Title>
                <Dialog.Description className="sr-only">{t("header.admissions")}</Dialog.Description>
                <div className="mx-auto w-full max-w-[84rem] px-4 pt-6 pb-12 sm:px-6 lg:px-8 lg:pt-10">
                  <nav aria-label={t("header.menu")} className="grid grid-cols-1 gap-x-10 lg:grid-cols-3">
                    {links.map((link) => (
                      <NavLink
                        key={link.to}
                        to={link.to}
                        onClick={() => setMenuOpen(false)}
                        className={({ isActive }) =>
                          cn(
                            "flex items-center justify-between border-b border-field-foreground/20 py-4 font-heading text-2xl font-medium lg:text-3xl",
                            isActive ? "text-field-foreground underline decoration-2 underline-offset-8" : "text-field-muted hover:text-field-foreground",
                          )
                        }
                      >
                        {link.label}
                        <ArrowRight className="size-6" aria-hidden="true" />
                      </NavLink>
                    ))}
                  </nav>
                  <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-4">
                    <div onClick={() => setMenuOpen(false)}>{apply}</div>
                    <Link to="/search" onClick={() => setMenuOpen(false)} className="inline-flex items-center gap-2 font-semibold text-field-foreground underline decoration-field-foreground/40 underline-offset-4">
                      <Search className="size-4" aria-hidden="true" />
                      {infoT("quick.search")}
                    </Link>
                    <button
                      type="button"
                      onClick={() => {
                        setMenuOpen(false)
                        setChatOpen(true)
                      }}
                      className="font-semibold text-field-foreground underline decoration-field-foreground/40 underline-offset-4"
                    >
                      {t("nav.ask")}
                    </button>
                  </div>
                  <div className="mt-12 grid grid-cols-1 gap-x-10 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
                    {groups.map((group) => (
                      <nav key={group.title} aria-label={group.title}>
                        <h2 className="label text-field-muted">{group.title}</h2>
                        <ul className="mt-3 border-t border-field-foreground/30">
                          {group.links.map((link) => (
                            <li key={link.to + link.label}>
                              <Link
                                to={link.to}
                                onClick={() => setMenuOpen(false)}
                                className="block border-b border-field-foreground/15 py-3 text-field-foreground transition-colors hover:bg-field/60"
                              >
                                {link.label}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </nav>
                    ))}
                  </div>
                </div>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </div>
      </div>
    </header>
  )
}

const applyClass =
  "group/button inline-flex h-11 items-center gap-2 whitespace-nowrap bg-ochre px-5 font-display text-[0.9375rem] font-semibold tracking-[0.06em] text-ink uppercase transition-colors duration-200 hover:bg-ochre-hover [&_svg]:size-4 [&_svg]:transition-transform [&_svg]:duration-200 hover:[&_svg]:translate-x-[3px]"
