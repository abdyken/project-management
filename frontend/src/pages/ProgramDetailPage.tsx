import { useQuery } from "@tanstack/react-query"
import { Link, useParams, useSearchParams } from "react-router-dom"
import { isNotFound } from "@/api/errors"
import { getChecklist, getProgram } from "@/api/programs"
import type { ApplicantType } from "@/api/types"
import { DocumentChecklist } from "@/components/catalog/DocumentChecklist"
import { ConnectionError } from "@/components/common/ConnectionError"
import { CompareToggle } from "@/components/compare/CompareToggle"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { useChatStore } from "@/store/chat"

const APPLICANT_TYPES: ApplicantType[] = ["local", "international"]

const labelClass = "text-[11px] tracking-[0.14em] text-muted-foreground uppercase"

export function ProgramDetailPage() {
  const { t, degree, languages, deadline, tuitionKzt, tuitionUsd } = useI18n()
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
    return <p className="mx-auto max-w-5xl px-4 py-16 text-sm text-muted-foreground">{t("detail.loading")}</p>
  }

  if (programQuery.isError) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16">
        {isNotFound(programQuery.error) ? (
          <p className="text-3xl font-semibold tracking-tight">{t("detail.notFound")}</p>
        ) : (
          <ConnectionError
            message={t("detail.loadError")}
            retrying={programQuery.isFetching}
            onRetry={() => void programQuery.refetch()}
          />
        )}
        <Link to="/programs" className="mt-4 inline-block text-sm underline">
          {t("detail.back")}
        </Link>
      </div>
    )
  }

  const program = programQuery.data

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <Link to="/programs" className="text-sm text-muted-foreground hover:text-foreground">
        {t("detail.backToPrograms")}
      </Link>
      <p className={`mt-6 ${labelClass}`}>
        {program.program_id} · {degree(program.degree_level)}
      </p>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{program.title}</h1>
        <CompareToggle programId={program.program_id} title={program.title} />
      </div>

      <dl className="mt-10 grid gap-6 border-y border-border py-8 sm:grid-cols-2">
        <div>
          <dt className={labelClass}>{t("detail.school")}</dt>
          <dd className="mt-1">{program.faculty}</dd>
        </div>
        <div>
          <dt className={labelClass}>{t("detail.language")}</dt>
          <dd className="mt-1">{languages(program.language)}</dd>
        </div>
        <div>
          <dt className={labelClass}>{t("detail.tuition")}</dt>
          <dd className="mt-1">
            {t("detail.localValue", { value: tuitionKzt(program.tuition_per_ects_kzt) })}
            <br />
            {t("detail.internationalValue", { value: tuitionUsd(program.tuition_per_ects_usd) })}
          </dd>
        </div>
        <div>
          <dt className={labelClass}>{t("detail.deadline")}</dt>
          <dd className="mt-1">
            {t("detail.localValue", { value: deadline(program.deadline_local) })}
            <br />
            {t("detail.internationalValue", { value: deadline(program.deadline_international) })}
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
          {t("detail.officialPage")}
        </a>
      ) : null}

      <section className="mt-12" aria-labelledby="documents-heading">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 id="documents-heading" className="text-3xl font-semibold tracking-tight">
              {t("detail.documents")}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">{t("detail.documentsNote")}</p>
          </div>
          <div className="flex gap-2" role="group" aria-label={t("detail.applicantType")}>
            {APPLICANT_TYPES.map((type) => (
              <Button
                key={type}
                size="sm"
                variant={applicant === type ? "default" : "outline"}
                aria-pressed={applicant === type}
                onClick={() => setApplicant(type)}
              >
                {t(`applicant.${type}`)}
              </Button>
            ))}
          </div>
        </div>

        <div className="mt-6">
          {checklistQuery.isPending ? <p className="text-sm text-muted-foreground">{t("detail.loadingChecklist")}</p> : null}
          {checklistQuery.isError ? (
            <ConnectionError
              message={t("detail.checklistError")}
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
            setDraft(t(`detail.askDocuments.${applicant}`, { title: program.title, code: program.program_id }))
            setOpen(true)
          }}
        >
          {t("detail.askInChat")}
        </Button>
      </section>
    </div>
  )
}
