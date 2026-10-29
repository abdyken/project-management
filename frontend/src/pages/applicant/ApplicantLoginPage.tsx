import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type FormEvent, useState } from "react"
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { loginApplicant, registerApplicant, verifyApplicant } from "@/api/applicant"
import { isApiError } from "@/api/errors"
import { useApplicantT } from "@/applicant/i18n"
import { APPLICANT_KEY, APPLICANT_ME_KEY, useApplicant } from "@/applicant/session"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useI18n } from "@/i18n"

function safeNext(value: string | null) {
  return value && (value === "/account/requests" || /^\/programs(?:\/[^/?#]+)?(?:\?[^#]*)?$/.test(value)) ? value : "/account"
}

export function ApplicantLoginPage({ register = false }: { register?: boolean }) {
  const t = useApplicantT()
  const { language } = useI18n()
  const navigate = useNavigate()
  const location = useLocation()
  const cache = useQueryClient()
  const [params] = useSearchParams()
  const next = safeNext(params.get("next"))
  const me = useApplicant()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const mutation = useMutation({
    mutationFn: async () =>
      register ? await registerApplicant(email, password, language) : await loginApplicant(email, password),
    onSuccess: (result) => {
      setPassword("")
      if ("id" in result) {
        cache.removeQueries({ queryKey: APPLICANT_KEY })
        cache.setQueryData(APPLICANT_ME_KEY, result)
        navigate(next, { replace: true, state: location.state })
      }
    },
    onError: () => setPassword(""),
  })
  if (me.data) return <Navigate to={next} replace state={location.state} />
  const error = mutation.error
  const message = !error
    ? null
    : isApiError(error) && error.code === "INVALID_CREDENTIALS"
      ? t("credentials")
      : isApiError(error) && error.code === "TOO_MANY_ATTEMPTS"
        ? t("tooMany")
        : isApiError(error) && error.code === "ACCOUNTS_UNAVAILABLE"
          ? t("unavailable")
          : t("error")

  function submit(event: FormEvent) {
    event.preventDefault()
    mutation.mutate()
  }

  return (
    <div className="mx-auto max-w-md px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-semibold tracking-tight">{t(register ? "register" : "login")}</h1>
      {register && <p className="mt-3 text-sm text-muted-foreground">{t("signupLead")}</p>}
      {register && mutation.isSuccess ? (
        <p role="status" className="mt-6">
          {t("verifySent")}
        </p>
      ) : (
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block space-y-2 text-sm">
            <span>{t("email")}</span>
            <Input
              type="email"
              autoComplete="username"
              required
              maxLength={254}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="block space-y-2 text-sm">
            <span>{t("password")}</span>
            <Input
              type="password"
              autoComplete={register ? "new-password" : "current-password"}
              required
              minLength={register ? 10 : 1}
              maxLength={200}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {register && <p className="text-xs text-muted-foreground">{t("passwordHint")}</p>}
          {message && (
            <p role="alert" className="text-sm text-destructive">
              {message}
            </p>
          )}
          <Button className="w-full" disabled={mutation.isPending} type="submit">
            {mutation.isPending ? t("working") : t(register ? "register" : "login")}
          </Button>
        </form>
      )}
      <Link
        className="mt-5 inline-block text-sm underline"
        to={`/account/${register ? "login" : "register"}?next=${encodeURIComponent(next)}`}
        state={location.state}
      >
        {t(register ? "login" : "register")}
      </Link>
      <p className="mt-8 text-xs leading-relaxed text-muted-foreground">{t("privacy")}</p>
    </div>
  )
}

export function ApplicantVerifyPage() {
  const t = useApplicantT()
  const cache = useQueryClient()
  const navigate = useNavigate()
  // Fragments are never sent to the server, proxy access logs or referrer headers.
  const [token] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get("token") ?? "")
  const verification = useMutation({
    mutationFn: () => verifyApplicant(token),
    onSuccess: (user) => {
      cache.removeQueries({ queryKey: APPLICANT_KEY })
      cache.setQueryData(APPLICANT_ME_KEY, user)
      navigate("/account", { replace: true })
    },
  })
  return (
    <div className="mx-auto max-w-md space-y-5 px-4 py-12">
      <h1 className="text-3xl font-semibold">{t("verify")}</h1>
      <p>{t("verifyLead")}</p>
      {(!token || verification.isError) && (
        <p role="alert" className="text-sm text-destructive">
          {isApiError(verification.error) && verification.error.code !== "INVALID_VERIFICATION"
            ? t("error")
            : t("invalidLink")}
        </p>
      )}
      <Button disabled={!token || verification.isPending} onClick={() => verification.mutate()}>
        {verification.isPending ? t("working") : t("verify")}
      </Button>
      <Link to="/account/register" className="block text-sm underline">
        {t("register")}
      </Link>
    </div>
  )
}
