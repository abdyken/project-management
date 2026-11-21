import type { ReactNode } from "react"
import { Link, useLocation } from "react-router-dom"
import { signatureSteps } from "@/components/mosaic/pattern"
import { Tesserae } from "@/components/mosaic/Tesserae"
import { useApplicantT } from "@/applicant/i18n"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { useInfoT } from "@/info/i18n"
import { ADMISSIONS_PHONE } from "@/lib/constants"

// Signature 2 of 2: the footer rises into the page with the same stepped mosaic edge.
const FOOTER_SIGNATURE = signatureSteps(240, 3, "field", "deep", 2026)

export function SiteFooter() {
  const { t } = useI18n()
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
      {/* Purdue's pattern: contact details under the logo, then three short columns of plain links. */}
      <div className="mx-auto grid max-w-[84rem] gap-x-8 gap-y-10 px-4 pt-12 pb-28 sm:grid-cols-3 sm:px-6 sm:pb-12 lg:grid-cols-[1.5fr_1fr_1fr_1fr] lg:px-8">
        <div className="sm:col-span-3 lg:col-span-1">
          <img src="/brand/sdu-lockup-white.svg" alt="SDU University" className="h-11 w-auto" width={150} height={47} />
          <p className="mt-6 max-w-[16ch] font-heading text-3xl leading-[1.12] font-normal">
            {t("footer.tagline")}
          </p>
          <address className="mt-8 space-y-1.5 text-[0.9375rem] not-italic text-field-muted">
            <span className="block font-semibold text-field-foreground">{t("contact.name")}</span>
            <span className="block max-w-[34ch]">{t("contact.address")}</span>
            <a href={`tel:${ADMISSIONS_PHONE.replace(/\s/g, "")}`} className={`${LINK} tabular block w-fit`}>
              {ADMISSIONS_PHONE}
            </a>
            <a href={`mailto:${email}`} className={`${LINK} block w-fit`}>
              {email}
            </a>
          </address>
        </div>

        <FooterColumn title={t("footer.explore")}>
          <FooterLink to="/programs">{t("nav.programs")}</FooterLink>
          <FooterLink to="/compare">{t("footer.compare")}</FooterLink>
          <FooterLink to="/cost-calculator">{guidanceT("cost")}</FooterLink>
          <FooterLink to="/funding">{guidanceT("funding")}</FooterLink>
        </FooterColumn>

        <FooterColumn title={t("footer.applyTitle")}>
          <FooterLink to="/apply">{infoT("apply.title")}</FooterLink>
          <FooterLink to="/deadlines">{infoT("deadlines.title")}</FooterLink>
          <FooterLink to="/application-status">{infoT("status.title")}</FooterLink>
          <FooterLink to="/account">{applicantT("account")}</FooterLink>
        </FooterColumn>

        <FooterColumn title={infoT("footer.infoFor")}>
          <FooterLink to="/apply#bachelor-local">{infoT("footer.schoolLeavers")}</FooterLink>
          <FooterLink to="/apply#bachelor-international">{infoT("footer.international")}</FooterLink>
          <FooterLink to="/apply#master">{infoT("footer.masters")}</FooterLink>
          <FooterLink to="/apply#phd">{infoT("footer.phd")}</FooterLink>
        </FooterColumn>
      </div>
    </footer>
  )
}

function FooterColumn({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h2 className="label text-field-muted">{title}</h2>
      <ul className="mt-4 space-y-3 text-[0.9375rem]">{children}</ul>
    </div>
  )
}

// Plain links: no underline at rest, one on hover and keyboard focus.
const LINK =
  "text-field-foreground underline-offset-4 transition-colors hover:underline focus-visible:underline decoration-field-foreground/60"

function FooterLink({ children, to }: { children: ReactNode; to: string }) {
  return (
    <li>
      <Link to={to} className={LINK}>
        {children}
      </Link>
    </li>
  )
}
