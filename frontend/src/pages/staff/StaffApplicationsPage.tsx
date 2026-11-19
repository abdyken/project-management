import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router-dom"
import { listStaffApplications, type StaffQueueFilter } from "@/api/applications"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { staffErrorKey, useStaffT, type StaffKey } from "@/staff/i18n"
import { selectClass } from "@/staff/styles"

const FILTERS: StaffQueueFilter[] = ["open", "submitted", "in_review", "needs_changes", "accepted", "rejected", "all"]
const PAGE = 30

function filterLabel(filter: StaffQueueFilter): StaffKey {
  return filter === "open" ? "app.filter.open" : filter === "all" ? "app.filter.all" : `app.status.${filter}`
}

// US33: submitted applications, oldest first.
export function StaffApplicationsPage() {
  const t = useStaffT()
  const { programTitle } = useI18n()
  const [params, setParams] = useSearchParams()
  const status = FILTERS.find((value) => value === params.get("status")) ?? "open"
  const offset = Math.max(0, Number(params.get("offset")) || 0)
  const setParam = (values: Record<string, string>) => {
    const next = new URLSearchParams(params)
    for (const [name, value] of Object.entries(values)) next.set(name, value)
    setParams(next, { replace: true })
  }
  const queue = useQuery({
    queryKey: ["staff", "applications", status, offset],
    queryFn: ({ signal }) => listStaffApplications(status, offset, signal),
    placeholderData: keepPreviousData,
    staleTime: 0,
  })
  const total = queue.data?.total ?? 0

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">{t("app.title")}</h1>
      <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t("app.lead")}</p>
      <div className="mt-6 flex items-center gap-2 text-sm">
        <label htmlFor="applications-filter">{t("app.filter")}</label>
        <select
          id="applications-filter"
          className={selectClass}
          value={status}
          onChange={(event) => setParam({ status: event.target.value, offset: "0" })}
        >
          {FILTERS.map((value) => (
            <option key={value} value={value}>
              {t(filterLabel(value))}
            </option>
          ))}
        </select>
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
      {queue.data && queue.data.items.length === 0 && <p className="mt-6 text-sm text-muted-foreground">{t("app.empty")}</p>}
      {queue.data && queue.data.items.length > 0 && (
        <ul className="mt-6 divide-y divide-border border-y border-border">
          {queue.data.items.map((item) => (
            <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">
                  #{item.id} · {item.program.program_id} · {t(`app.type.${item.applicant_type}`)}
                </p>
                <p className="mt-1 font-medium">{item.full_name ?? item.applicant_email}</p>
                <p className="text-sm text-muted-foreground">{programTitle(item.program)}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {item.submitted_at && t("app.submitted", { date: item.submitted_at.slice(0, 10) })} ·{" "}
                  {t("app.documents", { count: item.documents })}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={item.status} label={t(`app.status.${item.status}`)} />
                <Link to={`/staff/applications/${item.id}`} className="text-sm font-medium underline">
                  {t("app.open")}
                  <span className="sr-only"> #{item.id}</span>
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
      {total > PAGE && (
        <div className="mt-4 flex gap-3">
          <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setParam({ offset: String(Math.max(0, offset - PAGE)) })}>
            {t("app.previous")}
          </Button>
          <Button variant="outline" size="sm" disabled={offset + PAGE >= total} onClick={() => setParam({ offset: String(offset + PAGE) })}>
            {t("app.next")}
          </Button>
        </div>
      )}
    </div>
  )
}
