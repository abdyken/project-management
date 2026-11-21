import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { getSavedPrograms, type SavedChecklist } from "@/api/applicant"
import { applicationsKey, listApplications, startApplication, type ApplicationSummary } from "@/api/applications"
import { isApiError } from "@/api/errors"
import { SAVED_PROGRAMS_KEY, useApplicant } from "@/applicant/session"
import { applicationsErrorKey, useApplicationsT } from "@/applications/i18n"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { ConnectionError } from "@/components/common/ConnectionError"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { useInfoT } from "@/info/i18n"

function ApplicationCard({ item }: { item: ApplicationSummary }) {
  const t = useApplicationsT()
  const { programTitle, deadline } = useI18n()
  return (
    <li className="border-2 border-border bg-card p-6">
      <p className="text-xs text-muted-foreground">
        {item.program.program_id} · {t(item.applicant_type)}
      </p>
      <h2 className="mt-2 text-xl font-medium">{programTitle(item.program)}</h2>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <StatusBadge status={item.status} />
        <span className="text-muted-foreground">{t("updated", { date: deadline(item.updated_at.slice(0, 10)) })}</span>
        <span className="text-muted-foreground">{t("documentsCount", { count: item.documents })}</span>
      </div>
      <p className="mt-3 text-sm">{t(`help.${item.status}`)}</p>
      <Link
        to={`/account/applications/${item.id}`}
        className="mt-3 inline-block py-1 text-sm font-medium underline"
        aria-label={`${t("open")}: ${programTitle(item.program)}`}
      >
        {t("open")}
      </Link>
    </li>
  )
}

function StartFromSaved({ saved, live }: { saved: SavedChecklist[]; live: ApplicationSummary[] }) {
  const t = useApplicationsT()
  const { programTitle, language } = useI18n()
  const cache = useQueryClient()
  const navigate = useNavigate()
  const start = useMutation({
    mutationFn: (checklist: SavedChecklist) =>
      startApplication(checklist.program.program_id, checklist.applicant_type, language),
    onSuccess: (application) => {
      cache.setQueryData([...applicationsKey, application.id], application)
      void cache.invalidateQueries({ queryKey: applicationsKey, exact: true })
      navigate(`/account/applications/${application.id}`)
    },
    onError: (error) => {
      // Started in another tab: refresh the list so the existing application shows up above.
      if (isApiError(error) && error.code === "APPLICATION_EXISTS") void cache.invalidateQueries({ queryKey: applicationsKey, exact: true })
    },
  })
  const startable = saved.filter(
    (checklist) =>
      checklist.program.is_active &&
      !live.some(
        (item) =>
          item.program.program_id === checklist.program.program_id &&
          item.applicant_type === checklist.applicant_type &&
          item.status !== "rejected",
      ),
  )
  return (
    <section aria-labelledby="start-title" className="mt-10">
      <h2 id="start-title" className="text-2xl font-medium">
        {t("startTitle")}
      </h2>
      <p className="mt-2 text-sm text-muted-foreground">{t("startLead")}</p>
      {startable.length === 0 ? (
        <p className="mt-4 text-sm">
          {t("noSaved")}{" "}
          <Link to="/programs" className="underline">
            {t("browse")}
          </Link>
        </p>
      ) : (
        <ul className="mt-4 space-y-3">
          {startable.map((checklist) => (
            <li
              key={`${checklist.program.program_id}:${checklist.applicant_type}`}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border p-4"
            >
              <span>
                <span className="block font-medium">{programTitle(checklist.program)}</span>
                <span className="text-xs text-muted-foreground">
                  {checklist.program.program_id} · {t(checklist.applicant_type)}
                </span>
              </span>
              <Button disabled={start.isPending} onClick={() => start.mutate(checklist)}>
                {start.isPending && start.variables === checklist ? t("working") : t("start")}
              </Button>
            </li>
          ))}
        </ul>
      )}
      {start.isError && (
        <p role="alert" className="mt-3 text-sm text-destructive">
          {t(isApiError(start.error) ? applicationsErrorKey(start.error.code, start.error.status) : "error")}
        </p>
      )}
    </section>
  )
}

export function ApplicationsPage() {
  const t = useApplicationsT()
  const infoT = useInfoT()
  const me = useApplicant()
  const applications = useQuery({
    queryKey: applicationsKey,
    queryFn: ({ signal }) => listApplications(signal),
    enabled: Boolean(me.data),
    staleTime: 0,
    refetchOnWindowFocus: true,
  })
  const saved = useQuery({
    queryKey: SAVED_PROGRAMS_KEY,
    queryFn: ({ signal }) => getSavedPrograms(signal),
    enabled: Boolean(me.data),
    staleTime: 0,
  })

  if (me.isPending) return <p className="mx-auto max-w-3xl px-4 pt-12 pb-20 sm:px-6 sm:pt-16 sm:pb-24">{t("working")}</p>
  if (isApiError(me.error) && me.error.status === 401) return <Navigate to="/account/login" replace />
  const error = me.error ?? applications.error
  if (!me.data || applications.isError) {
    return (
      <div className="mx-auto max-w-3xl px-4 pt-12 pb-20 sm:px-6 sm:pt-16 sm:pb-24">
        <ConnectionError
          message={t(isApiError(error) ? applicationsErrorKey(error.code, error.status) : "error")}
          onRetry={() => void (me.data ? applications.refetch() : me.refetch())}
          retrying={me.isFetching || applications.isFetching}
        />
      </div>
    )
  }

  const items = applications.data?.items ?? []
  return (
    <div className="mx-auto max-w-3xl px-4 pt-12 pb-20 sm:px-6 sm:pt-16 sm:pb-24">
      <Link to="/account" className="text-sm underline">
        ← {me.data.email}
      </Link>
      <h1 className="mt-4 text-[clamp(2.25rem,4vw,3.5rem)] leading-[1.08] font-medium">{t("title")}</h1>
      <p className="mt-3 text-muted-foreground">{t("lead")}</p>
      <Link to="/application-status" className="mt-3 inline-block text-sm font-semibold text-primary underline decoration-primary/30 underline-offset-4 hover:decoration-primary">
        {infoT("status.lead")}
      </Link>
      {applications.isPending ? (
        <p className="mt-8">{t("working")}</p>
      ) : items.length === 0 ? (
        <p className="mt-8 text-sm text-muted-foreground">{t("empty")}</p>
      ) : (
        <ul className="mt-8 space-y-4">
          {items.map((item) => (
            <ApplicationCard key={item.id} item={item} />
          ))}
        </ul>
      )}
      {saved.data && <StartFromSaved saved={saved.data.items} live={items} />}
    </div>
  )
}
