import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { useSearchParams } from "react-router-dom"
import { allProgramsQuery, filterOptions, listPrograms } from "@/api/programs"
import { ProgramCard } from "@/components/catalog/ProgramCard"
import { ProgramFilters, type FilterValues } from "@/components/catalog/ProgramFilters"
import { ConnectionError } from "@/components/common/ConnectionError"

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
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = readFilters(searchParams)

  const optionsQuery = useQuery({ ...allProgramsQuery, select: (data) => filterOptions(data.programs) })
  const query = useQuery({
    queryKey: ["programs", filters],
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
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <p className="text-[11px] tracking-[0.12em] text-muted-foreground uppercase">Catalogue</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">Study programs</h1>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
        Fees and deadlines come from the admissions catalogue. Confirm them with the Admissions Office before
        you apply.
      </p>

      <div className="mt-10">
        <ProgramFilters values={filters} options={optionsQuery.data ?? NO_OPTIONS} onChange={updateFilters} />
      </div>

      <div className="mt-8" aria-busy={query.isFetching}>
        {query.isPending ? <p className="text-sm text-muted-foreground">Loading programs…</p> : null}

        {query.isError ? (
          <ConnectionError
            message="The catalogue is temporarily unavailable. Your search and filters are still here."
            retrying={query.isFetching}
            onRetry={retry}
          />
        ) : null}

        {data && data.total === 0 ? (
          <div role="status" className="border border-border bg-card p-6">
            <p className="text-2xl font-semibold tracking-tight">No programs found</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Nothing matches this combination. Clear a filter or try another keyword.
            </p>
          </div>
        ) : null}

        {data && data.total > 0 ? (
          <div className={query.isPlaceholderData ? "opacity-60 transition-opacity" : "transition-opacity"}>
            <p role="status" className="mb-4 text-sm text-muted-foreground">
              {data.total} {data.total === 1 ? "program" : "programs"} found
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              {data.programs.map((program) => (
                <ProgramCard key={program.program_id} program={program} />
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
