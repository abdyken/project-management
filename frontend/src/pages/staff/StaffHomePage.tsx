import { Link } from "react-router-dom"
import { useStaffT } from "@/staff/i18n"
import { STAFF_NAV } from "@/staff/nav"
import { useStaffMe } from "@/staff/session"

export function StaffHomePage() {
  const t = useStaffT()
  const { data: user } = useStaffMe()

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold tracking-tight">{t("staff.welcome", { name: user?.name ?? "" })}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{t("staff.welcomeText")}</p>
      <ul className="mt-6 space-y-2 text-sm">
        {STAFF_NAV.map((item) => (
          <li key={item.to}>
            <Link to={item.to} className="underline underline-offset-4">
              {t(item.label)}
            </Link>
          </li>
        ))}
      </ul>
      <Link to="/" className="mt-8 inline-block text-sm text-muted-foreground hover:text-foreground">
        ← {t("staff.backToPortal")}
      </Link>
    </div>
  )
}
