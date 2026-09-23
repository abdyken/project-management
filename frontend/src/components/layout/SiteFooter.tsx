import { ADMISSIONS_CONTACT } from "@/lib/constants"

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border/80">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-10 text-sm text-muted-foreground sm:flex-row sm:justify-between sm:px-6">
        <div>
          <p className="text-base font-semibold text-foreground">{ADMISSIONS_CONTACT.name}</p>
          <p className="mt-2 max-w-xs">{ADMISSIONS_CONTACT.address}</p>
          <p className="mt-1">{ADMISSIONS_CONTACT.phone}</p>
        </div>
        <div className="space-y-2">
          <a className="block hover:text-foreground" href={ADMISSIONS_CONTACT.website} target="_blank" rel="noreferrer">
            Official admissions
          </a>
          <a className="block hover:text-foreground" href="https://admissions.sdu.edu.kz" target="_blank" rel="noreferrer">
            Application portal
          </a>
        </div>
      </div>
    </footer>
  )
}
