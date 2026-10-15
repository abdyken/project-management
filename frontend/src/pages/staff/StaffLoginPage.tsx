import { type FormEvent, useState } from "react"
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom"
import { isApiError } from "@/api/errors"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useStaffT } from "@/staff/i18n"
import { useStaffLogin, useStaffMe } from "@/staff/session"

function safeNext(value: string | null) {
  // Only staff paths, so the login cannot redirect to another site.
  return value && value.startsWith("/staff") && !value.startsWith("//") ? value : "/staff"
}

export function StaffLoginPage() {
  const t = useStaffT()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get("next"))
  const me = useStaffMe()
  const loginMutation = useStaffLogin()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  if (me.data) return <Navigate to={next} replace />

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    loginMutation.mutate(
      { email, password },
      {
        onSuccess: () => navigate(next, { replace: true }),
        onError: () => setPassword(""),
      },
    )
  }

  const error = loginMutation.error
  const errorText = !error
    ? null
    : isApiError(error) && error.code === "INVALID_CREDENTIALS"
      ? t("login.error.credentials")
      : isApiError(error) && error.code === "TOO_MANY_ATTEMPTS"
        ? t("login.error.tooMany")
        : t("login.error.generic")

  return (
    <div className="flex min-h-dvh items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-8 flex items-center gap-2">
          <img src="/logo.svg" alt="" className="size-6" />
          <span className="text-xl font-semibold tracking-tight">SDU</span>
          <span className="text-[11px] tracking-[0.12em] text-muted-foreground uppercase">{t("staff.title")}</span>
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">{t("login.title")}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{t("login.lead")}</p>
        <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
          <label className="block space-y-1.5 text-sm">
            <span>{t("login.email")}</span>
            <Input
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="block space-y-1.5 text-sm">
            <span>{t("login.password")}</span>
            <Input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {errorText && (
            <p role="alert" className="text-sm text-destructive">
              {errorText}
            </p>
          )}
          <Button type="submit" className="w-full" disabled={loginMutation.isPending || !email || !password}>
            {loginMutation.isPending ? t("login.submitting") : t("login.submit")}
          </Button>
        </form>
      </div>
    </div>
  )
}
