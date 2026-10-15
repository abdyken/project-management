import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useDeferredValue } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { listStaffPrograms } from "@/api/staff"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useStaffT } from "@/staff/i18n"
import { selectClass } from "@/staff/styles"

const DEGREES = ["bachelor", "master", "phd"] as const

export function StaffProgramsPage() {
  const t = useStaffT()
  const [params, setParams] = useSearchParams()
  const q = params.get("q") ?? ""
  const degree = params.get("degree_level") ?? ""
  const active = params.get("active") ?? ""
  const deferredQ = useDeferredValue(q)

  const setParam = (name: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    setParams(next, { replace: true })
  }

  const programs = useQuery({
    queryKey: ["staff", "programs", "list", deferredQ, degree, active],
    queryFn: ({ signal }) =>
      listStaffPrograms(
        { q: deferredQ.trim() || undefined, degree_level: degree || undefined, active: active || undefined },
        signal,
      ),
    placeholderData: keepPreviousData,
  })

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t("cat.title")}</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t("cat.lead")}</p>
        </div>
        <Button asChild>
          <Link to="/staff/programs/new">
            <Plus />
            {t("cat.new")}
          </Link>
        </Button>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Input
          type="search"
          aria-label={t("cat.search")}
          placeholder={t("cat.search")}
          value={q}
          onChange={(event) => setParam("q", event.target.value)}
          className="max-w-xs"
        />
        <select aria-label={t("cat.col.degree")} className={selectClass} value={degree} onChange={(event) => setParam("degree_level", event.target.value)}>
          <option value="">{t("cat.allDegrees")}</option>
          {DEGREES.map((value) => (
            <option key={value} value={value}>
              {t(`edit.degree.${value}`)}
            </option>
          ))}
        </select>
        <select aria-label={t("prog.active")} className={selectClass} value={active} onChange={(event) => setParam("active", event.target.value)}>
          <option value="">{t("cat.allStates")}</option>
          <option value="true">{t("cat.activeOnly")}</option>
          <option value="false">{t("cat.archivedOnly")}</option>
        </select>
      </div>

      {programs.isPending ? (
        <p className="mt-6 text-sm text-muted-foreground">{t("common.loading")}</p>
      ) : programs.isError ? (
        <div className="mt-6 text-sm">
          <p>{t("common.error")}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => programs.refetch()}>
            {t("common.retry")}
          </Button>
        </div>
      ) : (
        <>
          <p className="mt-4 text-xs text-muted-foreground">{t("cat.count", { count: programs.data.items.length })}</p>
          {programs.data.items.length === 0 ? (
            <p className="mt-6 text-sm text-muted-foreground">{t("cat.empty")}</p>
          ) : (
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="py-2 pr-3 font-normal">{t("cat.col.code")}</th>
                    <th className="py-2 pr-3 font-normal">{t("cat.col.title")}</th>
                    <th className="py-2 pr-3 font-normal">{t("cat.col.degree")}</th>
                    <th className="py-2 pr-3 font-normal">{t("cat.col.documents")}</th>
                    <th className="py-2 font-normal">{t("faq.col.updated")}</th>
                  </tr>
                </thead>
                <tbody>
                  {programs.data.items.map((program) => (
                    <tr key={program.program_id} className="border-b border-border/60 align-top">
                      <td className="py-2 pr-3 whitespace-nowrap text-muted-foreground">{program.program_id}</td>
                      <td className="py-2 pr-3">
                        <Link to={`/staff/programs/${program.program_id}`} className="hover:underline">
                          {program.title}
                        </Link>
                        {!program.is_active && (
                          <span className="ml-2 rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">{t("cat.archived")}</span>
                        )}
                        <span className="block text-xs text-muted-foreground">{program.faculty}</span>
                      </td>
                      <td className="py-2 pr-3 whitespace-nowrap">{t(`edit.degree.${program.degree_level as (typeof DEGREES)[number]}`)}</td>
                      <td className="py-2 pr-3 whitespace-nowrap tabular-nums">
                        {program.documents_local} / {program.documents_international}
                      </td>
                      <td className="py-2 whitespace-nowrap text-xs text-muted-foreground">
                        {program.updated_at ? program.updated_at.slice(0, 10) : "—"}
                        {program.updated_by ? <span className="block">{program.updated_by}</span> : null}
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
