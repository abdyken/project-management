import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router-dom"
import { listStaffApplications, STAFF_PAGE, type StaffQueueFilter } from "@/api/applications"
import { allProgramsQuery } from "@/api/programs"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { staffErrorKey, useStaffDate, useStaffT, type StaffKey } from "@/staff/i18n"
import { selectClass } from "@/staff/styles"

const FILTERS: StaffQueueFilter[] = ["open", "submitted", "in_review", "needs_changes", "accepted", "rejected", "all"]

function filterLabel(filter: StaffQueueFilter): StaffKey {
  return filter === "open" ? "app.filter.open" : filter === "all" ? "app.filter.all" : `app.status.${filter}`
}

// US33: submitted applications, oldest first.
export function StaffApplicationsPage() {
  const t = useStaffT()
  const date = useStaffDate()
  const { programTitle } = useI18n()
  const [params, setParams] = useSearchParams()
  const status = FILTERS.find((value) => value === params.get("status")) ?? "open"
  const programId = params.get("program") ?? ""
  const offset = Math.max(0, Math.floor(Number(params.get("offset")) || 0))
  const setParam = (values: Record<string, string>) => {
    const next = new URLSearchParams(params)
    for (const [name, value] of Object.entries(values)) {
      if (value) next.set(name, value)
      else next.delete(name)
    }
    setParams(next, { replace: true })
  }
  const programs = useQuery({ ...allProgramsQuery, staleTime: 5 * 60_000 })
  const queue = useQuery({
    queryKey: ["staff", "applications", status, programId, offset],
    queryFn: ({ signal }) => listStaffApplications(status, programId, offset, signal),
    placeholderData: keepPreviousData,
    staleTime: 0,
  })
  const total = queue.data?.total ?? 0
  const pastTheEnd = queue.data !== undefined && queue.data.items.length === 0 && offset > 0 && total > 0

  return (
    <div>
      <h1 className="text-4xl leading-[0.95] font-extrabold">{t("app.title")}</h1>
      <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t("app.lead")}</p>
      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
        <div className="flex items-center gap-2">
          <label htmlFor="applications-filter">{t("app.filter")}</label>
          <select id="applications-filter" className={selectClass} value={status} onChange={(event) => setParam({ status: event.target.value, offset: "" })}>
            {FILTERS.map((value) => (
              <option key={value} value={value}>
                {t(filterLabel(value))}
              </option>
            ))}
          </select>
        </div>
        <div className="flex min-w-0 items-center gap-2">
          <label htmlFor="applications-program">{t("app.program")}</label>
          <select
            id="applications-program"
            className={`${selectClass} max-w-[16rem]`}
            value={programId}
            onChange={(event) => setParam({ program: event.target.value, offset: "" })}
          >
            <option value="">{t("app.program.all")}</option>
            {(programs.data?.programs ?? []).map((program) => (
              <option key={program.program_id} value={program.program_id}>
                {program.program_id} · {programTitle(program)}
              </option>
            ))}
          </select>
        </div>
      </div>
      {queue.isError && (
        <div role="alert" className="mt-6 text-sm text-destructive">
          {t(staffErrorKey(queue.error))}{" "}
          <button type="button" className="underline" onClick={() => void queue.refetch()}>
            {t("common.retry")}
          </button>
        </div>
      )}
      {queue.isPending && <p className="mt-6 text-sm">{t("common.loading")}</p>}
      {pastTheEnd ? (
        <p className="mt-6 text-sm text-muted-foreground">
          {t("app.pageEmpty")}{" "}
          <button type="button" className="underline" onClick={() => setParam({ offset: "" })}>
            {t("app.firstPage")}
          </button>
        </p>
      ) : (
        queue.data && queue.data.items.length === 0 && <p className="mt-6 text-sm text-muted-foreground">{t("app.empty")}</p>
      )}
      {queue.data && queue.data.items.length > 0 && (
        <ul className="mt-6 divide-y divide-border border-y border-border">
          {queue.data.items.map((item) => (
            <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">
                  #{item.id} · {item.program.program_id} · {t(`app.type.${item.applicant_type}`)}
                </p>
                <p className="mt-1 break-words font-medium">{item.full_name ?? item.applicant_email}</p>
                <p className="text-sm text-muted-foreground">{programTitle(item.program)}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {item.submitted_at && <>{t("app.submitted", { date: date(item.submitted_at) })} · </>}
                  {t("app.documents", { count: item.documents })}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={item.status} label={t(`app.status.${item.status}`)} />
                <Link to={`/staff/applications/${item.id}`} className="inline-block py-1 text-sm font-medium underline">
                  {t("app.open")}
                  <span className="sr-only"> #{item.id}</span>
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
      {total > STAFF_PAGE && (
        <div className="mt-4 flex gap-3">
          <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setParam({ offset: String(Math.max(0, offset - STAFF_PAGE)) })}>
            {t("app.previous")}
          </Button>
          <Button variant="outline" size="sm" disabled={offset + STAFF_PAGE >= total} onClick={() => setParam({ offset: String(offset + STAFF_PAGE) })}>
            {t("app.next")}
          </Button>
        </div>
      )}
    </div>
  )
}
