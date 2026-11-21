import type { ReactNode } from "react"
import { Link, useLocation } from "react-router-dom"
import { signatureSteps } from "@/components/mosaic/pattern"
import { Tesserae } from "@/components/mosaic/Tesserae"
import { useApplicantT } from "@/applicant/i18n"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { useInfoT } from "@/info/i18n"
import { ADMISSIONS_PHONE, ADMISSIONS_WEBSITE } from "@/lib/constants"

// Signature 2 of 2: the footer rises into the page with the same stepped mosaic edge.
const FOOTER_SIGNATURE = signatureSteps(240, 3, "field", "deep", 2026)

export function SiteFooter() {
  const { t, language } = useI18n()
  const applicantT = useApplicantT()
  const guidanceT = useGuidanceT()
  const infoT = useInfoT()
  const email = t("footer.email")
  const { pathname } = useLocation()

  // Below 640px the bottom padding clears the fixed Apply/Ask bar.
  return (
    <footer className="on-field relative mt-auto bg-field-deep">
      <div className="absolute inset-x-0 bottom-full overflow-hidden">
        <Tesserae size={16} rows={FOOTER_SIGNATURE} still={pathname !== "/"} />
      </div>
      <div className="mx-auto grid max-w-[84rem] gap-x-8 gap-y-10 px-4 pt-12 pb-28 sm:grid-cols-2 sm:pb-10 sm:px-6 lg:grid-cols-[1.2fr_1fr_1fr_1fr_1.2fr] lg:px-8">
        <div>
          <img src="/brand/sdu-lockup-white.svg" alt="SDU University" className="h-11 w-auto" width={150} height={47} />
          <p className="mt-6 max-w-[16ch] font-heading text-3xl leading-[1.12] font-normal">
            {t("footer.tagline")}
          </p>
        </div>

        <FooterColumn title={t("footer.explore")}>
          <FooterLink to="/programs">{t("nav.programs")}</FooterLink>
          <FooterLink to="/compare">{t("footer.compare")}</FooterLink>
          <FooterLink to="/admissions">{guidanceT("hub")}</FooterLink>
          <FooterLink to="/cost-calculator">{guidanceT("cost")}</FooterLink>
          <FooterLink to="/funding">{guidanceT("funding")}</FooterLink>
        </FooterColumn>

        <FooterColumn title={infoT("footer.infoFor")}>
          <FooterLink to="/apply#bachelor-local">{infoT("footer.schoolLeavers")}</FooterLink>
          <FooterLink to="/apply#bachelor-international">{infoT("footer.international")}</FooterLink>
          <FooterLink to="/apply#master">{infoT("footer.masters")}</FooterLink>
          <FooterLink to="/apply#phd">{infoT("footer.phd")}</FooterLink>
          <FooterLink to="/cost-and-aid">{infoT("footer.parents")}</FooterLink>
        </FooterColumn>

        <FooterColumn title={t("footer.applyTitle")}>
          <FooterLink to="/apply">{infoT("apply.title")}</FooterLink>
          <FooterLink to="/deadlines">{infoT("deadlines.title")}</FooterLink>
          <FooterLink to="/application-status">{infoT("status.title")}</FooterLink>
          <FooterLink to="/account">{applicantT("account")}</FooterLink>
          <FooterLink to="/account/requests">{guidanceT("requests")}</FooterLink>
          <FooterLink href="https://admissions.sdu.edu.kz">{t("footer.applicationPortal")}</FooterLink>
        </FooterColumn>

        <FooterColumn title={t("footer.contactTitle")}>
          <li className="font-semibold text-field-foreground">{t("contact.name")}</li>
          <li className="max-w-[30ch] text-field-muted">{t("contact.address")}</li>
          <FooterLink href={`tel:${ADMISSIONS_PHONE.replace(/\s/g, "")}`} tabular>
            {ADMISSIONS_PHONE}
          </FooterLink>
          <FooterLink href={`mailto:${email}`}>{email}</FooterLink>
          <FooterLink to="/contact">{infoT("contact.title")}</FooterLink>
          <FooterLink href={ADMISSIONS_WEBSITE[language]}>{t("footer.officialAdmissions")}</FooterLink>
        </FooterColumn>
      </div>
    </footer>
  )
}

function FooterColumn({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h2 className="label text-field-muted">{title}</h2>
      <ul className="mt-4 space-y-2.5 text-[0.9375rem]">{children}</ul>
    </div>
  )
}

type FooterLinkProps = { children: ReactNode; tabular?: boolean } & ({ to: string; href?: never } | { href: string; to?: never })

function FooterLink({ children, to, href, tabular }: FooterLinkProps) {
  const className = `text-field-foreground underline decoration-field-foreground/30 decoration-1 underline-offset-4 transition-colors hover:decoration-field-foreground hover:decoration-2${tabular ? " tabular" : ""}`
  return (
    <li>
      {to ? (
        <Link to={to} className={className}>
          {children}
        </Link>
      ) : (
        <a
          href={href}
          className={className}
          {...(href?.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {})}
        >
          {children}
        </a>
      )}
    </li>
  )
}
