import * as Dialog from "@radix-ui/react-dialog"
import { ArrowRight, Menu, X } from "lucide-react"
import { useState } from "react"
import { Link, NavLink } from "react-router-dom"
import { useFeatures } from "@/api/features"
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher"
import { useApplicantT } from "@/applicant/i18n"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { cn } from "@/lib/utils"
import { useChatStore } from "@/store/chat"

const OFFICIAL_APPLICATION_PORTAL = "https://admissions.sdu.edu.kz"

export function SiteHeader() {
  const { t } = useI18n()
  const applicantT = useApplicantT()
  const guidanceT = useGuidanceT()
  const setChatOpen = useChatStore((state) => state.setOpen)
  const features = useFeatures()
  const [menuOpen, setMenuOpen] = useState(false)

  const links = [
    { to: "/programs", label: t("nav.programs") },
    { to: "/admissions", label: guidanceT("hub") },
    { to: "/account", label: applicantT("account") },
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
        className="absolute top-2 left-2 z-50 -translate-y-24 bg-ochre px-4 py-2 font-semibold text-ink focus:translate-y-0"
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
                      "absolute inset-x-4 bottom-0 h-1 origin-left bg-ochre transition-transform duration-300 ease-out",
                      isActive ? "scale-x-100" : "scale-x-0",
                    )}
                  />
                </>
              )}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={() => setChatOpen(true)}
            className="flex items-center px-4 text-[0.9375rem] font-medium whitespace-nowrap text-field-muted transition-colors duration-200 hover:text-field-foreground"
          >
            {t("nav.ask")}
          </button>
        </nav>

        <div className="ml-auto flex items-center gap-2 xl:ml-0 xl:gap-4">
          <LanguageSwitcher tone="field" />
          <div className="hidden sm:block">{apply}</div>
          <Dialog.Root open={menuOpen} onOpenChange={setMenuOpen}>
            <Dialog.Trigger asChild>
              <button
                type="button"
                className="grid size-10 place-items-center border border-field-foreground/50 text-field-foreground transition-colors hover:bg-field-deep xl:hidden"
              >
                <Menu className="size-5" aria-hidden="true" />
                <span className="sr-only">{t("header.menu")}</span>
              </button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/40" />
              <Dialog.Content className="on-field fixed inset-0 z-50 flex flex-col overflow-y-auto bg-field-deep">
                <div className="flex h-16 items-center justify-between px-4 sm:px-6">
                  <img src="/brand/sdu-lockup-white.svg" alt="" className="h-8 w-auto" width={108} height={34} />
                  <Dialog.Close className="grid size-10 place-items-center border border-field-foreground/50 hover:bg-field">
                    <X className="size-5" aria-hidden="true" />
                    <span className="sr-only">{t("header.closeMenu")}</span>
                  </Dialog.Close>
                </div>
                <Dialog.Title className="sr-only">{t("header.menu")}</Dialog.Title>
                <Dialog.Description className="sr-only">{t("header.admissions")}</Dialog.Description>
                <nav aria-label={t("header.menu")} className="flex flex-col px-4 pt-6 sm:px-6">
                  {links.map((link) => (
                    <NavLink
                      key={link.to}
                      to={link.to}
                      onClick={() => setMenuOpen(false)}
                      className={({ isActive }) =>
                        cn(
                          "flex items-center justify-between border-b border-field-foreground/20 py-4 font-heading text-2xl font-medium",
                          isActive ? "text-ochre" : "text-field-foreground",
                        )
                      }
                    >
                      {link.label}
                      <ArrowRight className="size-6" aria-hidden="true" />
                    </NavLink>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false)
                      setChatOpen(true)
                    }}
                    className="flex items-center justify-between border-b border-field-foreground/20 py-4 text-left font-heading text-2xl font-medium"
                  >
                    {t("nav.ask")}
                    <ArrowRight className="size-6" aria-hidden="true" />
                  </button>
                </nav>
                <div className="mt-8 px-4 sm:px-6" onClick={() => setMenuOpen(false)}>
                  {apply}
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
