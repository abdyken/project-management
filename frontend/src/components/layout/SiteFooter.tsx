import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import { signatureSteps } from "@/components/mosaic/pattern"
import { Tesserae } from "@/components/mosaic/Tesserae"
import { useApplicantT } from "@/applicant/i18n"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { ADMISSIONS_PHONE, ADMISSIONS_WEBSITE } from "@/lib/constants"

// Signature 2 of 2: the footer rises into the page with the same stepped mosaic edge.
const FOOTER_SIGNATURE = signatureSteps(240, 3, "field", "deep", 2026)

export function SiteFooter() {
  const { t, language } = useI18n()
  const applicantT = useApplicantT()
  const guidanceT = useGuidanceT()
  const email = t("footer.email")

  return (
    <footer className="on-field relative mt-auto bg-field-deep">
      <div className="absolute inset-x-0 bottom-full overflow-hidden">
        <Tesserae size={16} rows={FOOTER_SIGNATURE} />
      </div>
      <div className="mx-auto grid max-w-[84rem] gap-x-8 gap-y-10 px-4 pt-12 pb-10 sm:grid-cols-2 sm:px-6 lg:grid-cols-[1.3fr_1fr_1fr_1.2fr] lg:px-8">
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

        <FooterColumn title={t("footer.applyTitle")}>
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
          <FooterLink href={ADMISSIONS_WEBSITE[language]}>{t("footer.officialAdmissions")}</FooterLink>
        </FooterColumn>
      </div>
      <div className="border-t border-field-foreground/15">
        <p className="mx-auto max-w-[84rem] px-4 pt-5 pb-24 text-sm text-field-muted sm:px-6 sm:pb-6 lg:px-8">
          {t("footer.credit")}
        </p>
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
