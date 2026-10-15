import { LogOut } from "lucide-react"
import { Link, Navigate, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom"
import { ErrorBoundary } from "@/components/common/ErrorBoundary"
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher"
import { Button } from "@/components/ui/button"
import { useStaffT } from "@/staff/i18n"
import { STAFF_NAV } from "@/staff/nav"
import { isNotLoggedIn, useStaffLogout, useStaffMe } from "@/staff/session"

export function StaffLayout() {
  const t = useStaffT()
  const location = useLocation()
  const navigate = useNavigate()
  const me = useStaffMe()
  const logoutMutation = useStaffLogout()

  if (me.isPending) {
    return <p className="p-6 text-sm text-muted-foreground">{t("common.loading")}</p>
  }
  if (me.isError) {
    if (isNotLoggedIn(me.error)) {
      const next = encodeURIComponent(location.pathname + location.search)
      return <Navigate to={`/staff/login?next=${next}`} replace />
    }
    return (
      <div className="p-6 text-sm">
        <p>{t("common.error")}</p>
        <Button variant="outline" size="sm" className="mt-3" onClick={() => me.refetch()}>
          {t("common.retry")}
        </Button>
      </div>
    )
  }

  const user = me.data
  const onLogout = () => logoutMutation.mutate(undefined, { onSettled: () => navigate("/staff/login", { replace: true }) })

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-b border-border/80">
        {/* Phones: logo and controls on the first row, the page links on the second. */}
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-5 gap-y-2 px-4 py-3 sm:h-16 sm:flex-nowrap sm:py-0 sm:px-6">
          <Link to="/staff" className="flex shrink-0 items-center gap-2">
            <img src="/logo.svg" alt="" className="size-6" />
            <span className="text-xl font-semibold tracking-tight">SDU</span>
            <span className="hidden text-[11px] tracking-[0.12em] text-muted-foreground uppercase md:inline">
              {t("staff.title")}
            </span>
          </Link>
          <nav className="order-last flex w-full items-center gap-4 text-sm sm:order-none sm:w-auto sm:flex-1">
            {STAFF_NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground")}
              >
                {t(item.label)}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden text-right leading-tight lg:block">
              <span className="block">{user.name}</span>
              <span className="block text-xs text-muted-foreground">{t(`staff.role.${user.role}`)}</span>
            </span>
            <LanguageSwitcher />
            <Button variant="outline" size="sm" onClick={onLogout} disabled={logoutMutation.isPending}>
              <LogOut />
              <span className="hidden sm:inline">{t("staff.logout")}</span>
              <span className="sr-only sm:hidden">{t("staff.logout")}</span>
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <ErrorBoundary key={location.pathname}>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  )
}
