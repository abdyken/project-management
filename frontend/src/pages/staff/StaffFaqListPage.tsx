import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useDeferredValue } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { type FaqStatus, listFaq } from "@/api/staff"
import { StatusBadge } from "@/components/staff/StatusBadge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useStaffT } from "@/staff/i18n"
import { selectClass } from "@/staff/styles"

const STATUSES: FaqStatus[] = ["published", "draft", "retired"]

export function StaffFaqListPage() {
  const t = useStaffT()
  const [params, setParams] = useSearchParams()
  const q = params.get("q") ?? ""
  const status = (params.get("status") as FaqStatus | null) ?? undefined
  const category = params.get("category") ?? undefined
  const deferredQ = useDeferredValue(q)

  const setParam = (name: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    setParams(next, { replace: true })
  }

  const faq = useQuery({
    queryKey: ["staff", "faq", "list", deferredQ, status, category],
    queryFn: ({ signal }) => listFaq({ q: deferredQ.trim() || undefined, status, category }, signal),
    placeholderData: keepPreviousData,
  })

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t("faq.title")}</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t("faq.lead")}</p>
        </div>
        <Button asChild>
          <Link to="/staff/faq/new">
            <Plus />
            {t("faq.new")}
          </Link>
        </Button>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Input
          type="search"
          aria-label={t("faq.search")}
          placeholder={t("faq.search")}
          value={q}
          onChange={(event) => setParam("q", event.target.value)}
          className="max-w-xs"
        />
        <select aria-label={t("faq.col.status")} className={selectClass} value={status ?? ""} onChange={(event) => setParam("status", event.target.value)}>
          <option value="">{t("faq.allStatuses")}</option>
          {STATUSES.map((value) => (
            <option key={value} value={value}>
              {t(`status.${value}`)}
            </option>
          ))}
        </select>
        <select aria-label={t("faq.col.category")} className={selectClass} value={category ?? ""} onChange={(event) => setParam("category", event.target.value)}>
          <option value="">{t("faq.allCategories")}</option>
          {faq.data?.categories.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </div>

      {faq.isPending ? (
        <p className="mt-6 text-sm text-muted-foreground">{t("common.loading")}</p>
      ) : faq.isError ? (
        <div className="mt-6 text-sm">
          <p>{t("common.error")}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => faq.refetch()}>
            {t("common.retry")}
          </Button>
        </div>
      ) : (
        <>
          <p className="mt-4 text-xs text-muted-foreground">{t("faq.count", { count: faq.data.items.length })}</p>
          {faq.data.items.length === 0 ? (
            <p className="mt-6 text-sm text-muted-foreground">{t("faq.empty")}</p>
          ) : (
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="py-2 pr-3 font-normal">{t("faq.col.id")}</th>
                    <th className="py-2 pr-3 font-normal">{t("faq.col.question")}</th>
                    <th className="py-2 pr-3 font-normal">{t("faq.col.category")}</th>
                    <th className="py-2 pr-3 font-normal">{t("faq.col.languages")}</th>
                    <th className="py-2 pr-3 font-normal">{t("faq.col.status")}</th>
                    <th className="py-2 font-normal">{t("faq.col.updated")}</th>
                  </tr>
                </thead>
                <tbody>
                  {faq.data.items.map((item) => (
                    <tr key={item.faq_id} className="border-b border-border/60 align-top">
                      <td className="py-2 pr-3 whitespace-nowrap text-muted-foreground">{item.faq_id}</td>
                      <td className="py-2 pr-3">
                        <Link to={`/staff/faq/${item.faq_id}`} className="hover:underline">
                          {item.question}
                        </Link>
                      </td>
                      <td className="py-2 pr-3 text-muted-foreground">{item.category}</td>
                      <td className="py-2 pr-3 whitespace-nowrap uppercase text-xs">{item.languages.join(" · ")}</td>
                      <td className="py-2 pr-3">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="py-2 whitespace-nowrap text-xs text-muted-foreground">
                        {item.last_update}
                        {item.updated_by ? <span className="block">{item.updated_by}</span> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
