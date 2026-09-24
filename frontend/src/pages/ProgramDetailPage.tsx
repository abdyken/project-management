import { useQuery } from "@tanstack/react-query"
import { Link, useParams, useSearchParams } from "react-router-dom"
import { isNotFound } from "@/api/errors"
import { getChecklist, getProgram } from "@/api/programs"
import type { ApplicantType } from "@/api/types"
import { DocumentChecklist } from "@/components/catalog/DocumentChecklist"
import { ConnectionError } from "@/components/common/ConnectionError"
import { Button } from "@/components/ui/button"
import { DEGREE_LABELS } from "@/lib/constants"
import { formatDeadline, formatTuitionInternational, formatTuitionLocal } from "@/lib/utils"
import { useChatStore } from "@/store/chat"

const APPLICANT_TYPES: { value: ApplicantType; label: string }[] = [
  { value: "local", label: "Local" },
  { value: "international", label: "International" },
]

const labelClass = "text-[11px] tracking-[0.14em] text-muted-foreground uppercase"

export function ProgramDetailPage() {
  const { id = "" } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const applicant: ApplicantType = searchParams.get("applicant") === "international" ? "international" : "local"
  const setOpen = useChatStore((state) => state.setOpen)
  const setDraft = useChatStore((state) => state.setDraft)

  const programQuery = useQuery({
    queryKey: ["program", id],
    queryFn: () => getProgram(id),
    enabled: Boolean(id),
  })

  const checklistQuery = useQuery({
    queryKey: ["checklist", id, applicant],
    queryFn: () => getChecklist(id, applicant),
    enabled: programQuery.isSuccess,
  })

  function setApplicant(next: ApplicantType) {
    const params = new URLSearchParams(searchParams)
    params.set("applicant", next)
    setSearchParams(params, { replace: true })
  }

  if (programQuery.isPending) {
    return <p className="mx-auto max-w-5xl px-4 py-16 text-sm text-muted-foreground">Loading program…</p>
  }

  if (programQuery.isError) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16">
        {isNotFound(programQuery.error) ? (
          <p className="text-3xl font-semibold tracking-tight">Program not found</p>
        ) : (
          <ConnectionError
            message="The program could not be loaded."
            retrying={programQuery.isFetching}
            onRetry={() => void programQuery.refetch()}
          />
        )}
        <Link to="/programs" className="mt-4 inline-block text-sm underline">
          Back to the catalogue
        </Link>
      </div>
    )
  }

  const program = programQuery.data

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <Link to="/programs" className="text-sm text-muted-foreground hover:text-foreground">
        ← Programs
      </Link>
      <p className={`mt-6 ${labelClass}`}>
        {program.program_id} · {DEGREE_LABELS[program.degree_level]}
      </p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">{program.title}</h1>

      <dl className="mt-10 grid gap-6 border-y border-border py-8 sm:grid-cols-2">
        <div>
          <dt className={labelClass}>School</dt>
          <dd className="mt-1">{program.faculty}</dd>
        </div>
        <div>
          <dt className={labelClass}>Language</dt>
          <dd className="mt-1">{program.language}</dd>
        </div>
        <div>
          <dt className={labelClass}>Tuition, program courses</dt>
          <dd className="mt-1">
            Local: {formatTuitionLocal(program.tuition_per_ects_kzt)}
            <br />
            International: {formatTuitionInternational(program.tuition_per_ects_usd)}
          </dd>
        </div>
        <div>
          <dt className={labelClass}>Application deadline</dt>
          <dd className="mt-1">
            Local: {formatDeadline(program.deadline_local)}
            <br />
            International: {formatDeadline(program.deadline_international)}
          </dd>
        </div>
      </dl>
      {program.source_url ? (
        <a
          href={program.source_url}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-block text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          Official program page
        </a>
      ) : null}

      <section className="mt-12" aria-labelledby="documents-heading">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 id="documents-heading" className="text-3xl font-semibold tracking-tight">
              Required documents
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">Same list the assistant uses for this program.</p>
          </div>
          <div className="flex gap-2" role="group" aria-label="Applicant type">
            {APPLICANT_TYPES.map((type) => (
              <Button
                key={type.value}
                size="sm"
                variant={applicant === type.value ? "default" : "outline"}
                aria-pressed={applicant === type.value}
                onClick={() => setApplicant(type.value)}
              >
                {type.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="mt-6">
          {checklistQuery.isPending ? <p className="text-sm text-muted-foreground">Loading checklist…</p> : null}
          {checklistQuery.isError ? (
            <ConnectionError
              message="The document checklist could not be loaded."
              retrying={checklistQuery.isFetching}
              onRetry={() => void checklistQuery.refetch()}
            />
          ) : null}
          {checklistQuery.data ? <DocumentChecklist checklist={checklistQuery.data} /> : null}
        </div>

        <Button
          className="mt-8"
          variant="outline"
          onClick={() => {
            setDraft(
              `Which documents do I need for ${program.title} (${program.program_id}) as ${applicant === "local" ? "a local" : "an international"} applicant?`,
            )
            setOpen(true)
          }}
        >
          Ask in chat
        </Button>
      </section>
    </div>
  )
}
