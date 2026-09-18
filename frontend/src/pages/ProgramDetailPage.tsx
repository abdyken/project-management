import { useQuery } from "@tanstack/react-query"
import { Link, useParams, useSearchParams } from "react-router-dom"
import { getChecklist, getProgram } from "@/api/programs"
import type { ApplicantType } from "@/api/types"
import { DocumentChecklist } from "@/components/catalog/DocumentChecklist"
import { Button } from "@/components/ui/button"
import { DEGREE_LABELS, LANGUAGE_LABELS } from "@/lib/constants"
import { useChatStore } from "@/store/chat"

export function ProgramDetailPage() {
  const { id = "" } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const applicant = (searchParams.get("applicant") === "international" ? "international" : "local") as ApplicantType
  const setOpen = useChatStore((state) => state.setOpen)
  const setDraft = useChatStore((state) => state.setDraft)

  const programQuery = useQuery({
    queryKey: ["program", id],
    queryFn: () => getProgram(id),
    enabled: Boolean(id),
    retry: false,
  })

  const checklistQuery = useQuery({
    queryKey: ["checklist", id, applicant],
    queryFn: () => getChecklist(id, applicant),
    enabled: Boolean(id) && programQuery.isSuccess,
    retry: false,
  })

  function setApplicant(next: ApplicantType) {
    const params = new URLSearchParams(searchParams)
    params.set("applicant", next)
    setSearchParams(params, { replace: true })
  }

  if (programQuery.isLoading) {
    return <p className="mx-auto max-w-5xl px-4 py-16 text-sm text-muted-foreground">Loading programme…</p>
  }

  if (programQuery.isError || !programQuery.data) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16">
        <p className="font-serif text-3xl">Programme not found</p>
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
        ← Programmes
      </Link>
      <p className="mt-6 text-[11px] tracking-[0.12em] text-muted-foreground uppercase">
        {program.program_id} · {DEGREE_LABELS[program.degree_level]}
      </p>
      <h1 className="mt-3 font-serif text-4xl sm:text-5xl">{program.title}</h1>

      <dl className="mt-10 grid gap-6 border-y border-border py-8 sm:grid-cols-2">
        <div>
          <dt className="text-[11px] tracking-[0.14em] text-muted-foreground uppercase">School</dt>
          <dd className="mt-1">{program.faculty}</dd>
        </div>
        <div>
          <dt className="text-[11px] tracking-[0.14em] text-muted-foreground uppercase">Language</dt>
          <dd className="mt-1">{LANGUAGE_LABELS[program.language]}</dd>
        </div>
        <div>
          <dt className="text-[11px] tracking-[0.14em] text-muted-foreground uppercase">Tuition</dt>
          <dd className="mt-1">{program.tuition_fee}</dd>
        </div>
        <div>
          <dt className="text-[11px] tracking-[0.14em] text-muted-foreground uppercase">Application deadline</dt>
          <dd className="mt-1">{program.application_deadline}</dd>
        </div>
      </dl>

      <section className="mt-12">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="font-serif text-3xl">Required documents</h2>
            <p className="mt-2 text-sm text-muted-foreground">Same list the assistant uses for this programme.</p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant={applicant === "local" ? "default" : "outline"} onClick={() => setApplicant("local")}>
              Local
            </Button>
            <Button
              size="sm"
              variant={applicant === "international" ? "default" : "outline"}
              onClick={() => setApplicant("international")}
            >
              International
            </Button>
          </div>
        </div>

        <div className="mt-6">
          {checklistQuery.isLoading ? <p className="text-sm text-muted-foreground">Loading checklist…</p> : null}
          {checklistQuery.data ? <DocumentChecklist checklist={checklistQuery.data} /> : null}
        </div>

        <Button
          className="mt-8"
          variant="outline"
          onClick={() => {
            setDraft(`Which documents do I need for ${program.title}?`)
            setOpen(true)
          }}
        >
          Ask in chat
        </Button>
      </section>
    </div>
  )
}
