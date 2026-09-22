import { useQuery } from "@tanstack/react-query"
import { useSearchParams } from "react-router-dom"
import { isApiError } from "@/api/errors"
import { listPrograms } from "@/api/programs"
import { ProgramCard } from "@/components/catalog/ProgramCard"
import { ProgramFilters, type FilterValues } from "@/components/catalog/ProgramFilters"
import { Button } from "@/components/ui/button"

function readFilters(params: URLSearchParams): FilterValues & { force: string } {
  return {
    q: params.get("q") ?? "",
    faculty: params.get("faculty") ?? "",
    degree_level: params.get("degree_level") ?? "",
    language: params.get("language") ?? "",
    force: params.get("force") ?? "",
  }
}

export function ProgramsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = readFilters(searchParams)

  const query = useQuery({
    queryKey: ["programs", filters],
    queryFn: () => listPrograms(filters),
    retry: false,
  })

  function updateFilters(next: FilterValues) {
    const params = new URLSearchParams()
    if (next.q) params.set("q", next.q)
    if (next.faculty) params.set("faculty", next.faculty)
    if (next.degree_level) params.set("degree_level", next.degree_level)
    if (next.language) params.set("language", next.language)
    if (filters.force) params.set("force", filters.force)
    setSearchParams(params)
  }

  const unavailable = query.isError && isApiError(query.error) && (query.error.status === 503 || query.error.code === "SERVICE_UNAVAILABLE")

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <p className="text-[11px] tracking-[0.12em] text-muted-foreground uppercase">Catalogue</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">Study programmes</h1>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
        Mock data compiled from public SDU pages. Fees and deadlines should be confirmed with the Admissions
        Office until the official import lands.
      </p>

      <div className="mt-10">
        <ProgramFilters values={filters} onChange={updateFilters} />
      </div>

      <div className="mt-8">
        {query.isLoading ? <p className="text-sm text-muted-foreground">Loading programmes…</p> : null}

        {unavailable ? (
          <div className="border border-border bg-card p-6">
            <p className="text-2xl font-semibold tracking-tight">Connection error</p>
            <p className="mt-2 text-sm text-muted-foreground">
              The catalogue is temporarily unavailable. Your search and filters are still here.
            </p>
            <Button className="mt-5" onClick={() => void query.refetch()}>
              Try again
            </Button>
          </div>
        ) : null}

        {query.data && query.data.total === 0 ? (
          <div className="border border-border bg-card p-6">
            <p className="text-2xl font-semibold tracking-tight">No programs found</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Nothing matches this combination. Clear a filter or try another keyword.
            </p>
          </div>
        ) : null}

        {query.data && query.data.total > 0 ? (
          <>
            <p className="mb-4 text-sm text-muted-foreground">
              {query.data.total} {query.data.total === 1 ? "program" : "programs"} found
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              {query.data.programs.map((program) => (
                <ProgramCard key={program.program_id} program={program} />
              ))}
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
