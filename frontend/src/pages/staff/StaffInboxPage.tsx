import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router-dom"
import { dismissInboxGroup, type InboxStatus, listInbox } from "@/api/staff"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useStaffT } from "@/staff/i18n"
import { selectClass } from "@/staff/styles"

const STATUSES: InboxStatus[] = ["new", "answered", "dismissed"]
const PERIODS = [7, 30, 90]

function shortDate(value: string) {
  return value.slice(0, 10)
}

export function StaffInboxPage() {
  const t = useStaffT()
  const queryClient = useQueryClient()
  const [params, setParams] = useSearchParams()
  const status = (STATUSES.find((value) => value === params.get("status")) ?? "new") as InboxStatus
  const days = PERIODS.find((value) => String(value) === params.get("days")) ?? 30

  const setParam = (name: string, value: string) => {
    const next = new URLSearchParams(params)
    next.set(name, value)
    setParams(next, { replace: true })
  }

  const inbox = useQuery({
    queryKey: ["staff", "inbox", status, days],
    queryFn: ({ signal }) => listInbox({ status, days }, signal),
    placeholderData: keepPreviousData,
  })

  const dismiss = useMutation({
    mutationFn: dismissInboxGroup,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["staff", "inbox"] }),
  })

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">{t("inbox.title")}</h1>
      <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t("inbox.lead")}</p>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <div role="tablist" className="flex border border-border text-sm">
          {STATUSES.map((value) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={status === value}
              onClick={() => setParam("status", value)}
              className={cn("px-3 py-1.5", status === value ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}
            >
              {t(`inbox.status.${value}`)}
            </button>
          ))}
        </div>
        <select aria-label={t("inbox.period")} className={selectClass} value={days} onChange={(event) => setParam("days", event.target.value)}>
          {PERIODS.map((value) => (
            <option key={value} value={value}>
              {t("inbox.days", { days: value })}
            </option>
          ))}
        </select>
      </div>

      {inbox.isPending ? (
        <p className="mt-6 text-sm text-muted-foreground">{t("common.loading")}</p>
      ) : inbox.isError ? (
        <div className="mt-6 text-sm">
          <p>{t("common.error")}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => inbox.refetch()}>
            {t("common.retry")}
          </Button>
        </div>
      ) : inbox.data.items.length === 0 ? (
        <p className="mt-6 text-sm text-muted-foreground">{t("inbox.empty")}</p>
      ) : (
        <>
          <p className="mt-4 text-xs text-muted-foreground">
            {t("inbox.summary", { groups: inbox.data.items.length, asks: inbox.data.total_asks })}
          </p>
          <ul className="mt-2 divide-y divide-border/60 border-y border-border/60">
            {inbox.data.items.map((group) => (
              <li key={group.key} className="flex flex-wrap items-start justify-between gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm break-words" lang={group.language}>
                    {group.question}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {t("inbox.asked", { count: group.count })} · {t("inbox.lastAsked", { date: shortDate(group.last_asked) })} ·{" "}
                    <span className="uppercase">{group.language}</span>
                    {group.faq_id && (
                      <>
                        {" · "}
                        <Link to={`/staff/faq/${group.faq_id}`} className="underline">
                          {t("inbox.answeredBy", { faq: group.faq_id })}
                        </Link>
                      </>
                    )}
                  </p>
                </div>
                {status === "new" && (
                  <div className="flex gap-2">
                    <Button asChild size="sm">
                      <Link to={`/staff/faq/new?${new URLSearchParams({ question: group.question, inbox: group.key })}`}>
                        {t("inbox.answer")}
                      </Link>
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={dismiss.isPending}
                      onClick={() => dismiss.mutate(group.key)}
                    >
                      {t("inbox.dismiss")}
                    </Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
