import { useEffect } from "react"
import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { useLocation, useSearchParams } from "react-router-dom"
import { isInvalidRequest } from "@/api/errors"
import { allProgramsQuery, filterOptions, listPrograms } from "@/api/programs"
import { ProgramCard } from "@/components/catalog/ProgramCard"
import { ActiveFilters, FilterPanel, ProgramSearch, type FilterValues } from "@/components/catalog/ProgramFilters"
import { ConnectionError } from "@/components/common/ConnectionError"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"

const NO_OPTIONS = { faculties: [], degreeLevels: [], languages: [] }

function readFilters(params: URLSearchParams): FilterValues {
  return {
    q: params.get("q") ?? "",
    faculty: params.get("faculty") ?? "",
    degree_level: params.get("degree_level") ?? "",
    language: params.get("language") ?? "",
  }
}

export function ProgramsPage() {
  const { t, tn } = useI18n()
  const { hash } = useLocation()
  // The header search button opens /programs#search: put the cursor in the search box.
  useEffect(() => {
    if (hash === "#search") document.getElementById("q")?.focus()
  }, [hash])
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = readFilters(searchParams)

  const hasFilters = Object.values(filters).some(Boolean)
  const optionsQuery = useQuery({ ...allProgramsQuery, select: (data) => filterOptions(data.programs) })
  const query = useQuery({
    queryKey: hasFilters ? ["programs", filters] : allProgramsQuery.queryKey,
    queryFn: () => listPrograms(filters),
    placeholderData: keepPreviousData,
  })

  function updateFilters(next: FilterValues) {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(next)) {
      if (value) params.set(key, value)
    }
    setSearchParams(params)
  }

  function retry() {
    void query.refetch()
    if (optionsQuery.isError) void optionsQuery.refetch()
  }

  const data = query.isError ? undefined : query.data

  return (
    <div>
      <section className="on-field relative bg-field">
        <div className="mx-auto max-w-[84rem] px-4 pt-12 pb-16 sm:px-6 lg:px-8 lg:pt-16 lg:pb-20">
          <h1 className="text-[clamp(2.5rem,4.5vw,4rem)] leading-[1.06] font-medium">{t("programs.title")}</h1>
          <p className="mt-5 max-w-[60ch] text-lg text-field-muted">{t("programs.lead")}</p>
          <div className="mt-8">
            <ProgramSearch key={filters.q} values={filters} onChange={updateFilters} />
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-[84rem] gap-10 px-4 pt-16 pb-24 sm:px-6 grid-cols-1 lg:grid-cols-[17rem_minmax(0,1fr)] lg:gap-12 lg:px-8 lg:pt-20">
        <aside aria-label={t("filters.title")} className="lg:sticky lg:top-6 lg:self-start">
          <FilterPanel values={filters} options={optionsQuery.data ?? NO_OPTIONS} onChange={updateFilters} />
          {optionsQuery.isError && !query.isError ? (
            <div role="alert" className="mt-4 space-y-3 text-sm text-muted-foreground">
              <p>{t("filters.optionsError")}</p>
              <Button variant="outline" size="sm" onClick={() => void optionsQuery.refetch()} disabled={optionsQuery.isFetching}>
                {optionsQuery.isFetching ? t("error.tryingAgain") : t("error.tryAgain")}
              </Button>
            </div>
          ) : null}
        </aside>

        <div aria-busy={query.isFetching} className="min-w-0">
          {query.isPending ? <p className="text-muted-foreground">{t("programs.loading")}</p> : null}

          {query.isError && isInvalidRequest(query.error) ? (
            <div role="alert" className="border-2 border-ink bg-card p-6">
              <p className="font-heading text-2xl font-medium">{t("programs.invalidTitle")}</p>
              <p className="mt-2 text-muted-foreground">{t("programs.invalidText")}</p>
              <Button className="mt-5" onClick={() => setSearchParams(new URLSearchParams())}>
                {t("programs.clearSearch")}
              </Button>
            </div>
          ) : null}

          {query.isError && !isInvalidRequest(query.error) ? (
            <ConnectionError message={t("programs.unavailable")} retrying={query.isFetching} onRetry={retry} />
          ) : null}

          {data ? (
            <div className="mb-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-b-2 border-ink pb-4">
              <p role="status" className="tabular font-heading text-2xl font-medium">
                {tn("programs.found", data.total)}
              </p>
              <ActiveFilters values={filters} onChange={updateFilters} />
            </div>
          ) : null}

          {data && data.total === 0 ? (
            <div className="border border-border bg-card p-8">
              <p className="font-heading text-2xl font-medium">{t("programs.noneTitle")}</p>
              <p className="mt-2 max-w-[52ch] text-muted-foreground">{t("programs.noneText")}</p>
            </div>
          ) : null}

          {data && data.total > 0 ? (
            <div className={query.isPlaceholderData ? "opacity-60 transition-opacity" : "transition-opacity"}>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                {data.programs.map((program) => (
                  <ProgramCard key={program.program_id} program={program} />
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
