import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, ArrowRight, ExternalLink, MessageCircleQuestion } from "lucide-react"
import type { ReactNode } from "react"
import { Link, useParams, useSearchParams } from "react-router-dom"
import { isNotFound } from "@/api/errors"
import { getGuidance } from "@/api/guidance"
import { allProgramsQuery, getChecklist, getProgram } from "@/api/programs"
import type { ApplicantType, Program } from "@/api/types"
import { ChecklistPdfButton } from "@/components/catalog/ChecklistPdfButton"
import { DocumentChecklist } from "@/components/catalog/DocumentChecklist"
import { SaveChecklistButton } from "@/components/catalog/SaveChecklistButton"
import { ApplyAction } from "@/components/common/ApplyAction"
import { ConnectionError } from "@/components/common/ConnectionError"
import { CompareToggle } from "@/components/compare/CompareToggle"
import { ConditionText, EvidenceView } from "@/components/guidance/rules"
import { PageShell } from "@/components/layout/PageShell"
import { signatureSteps } from "@/components/mosaic/pattern"
import { Tesserae } from "@/components/mosaic/Tesserae"
import { Button } from "@/components/ui/button"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { programImage } from "@/lib/programImages"
import { cn } from "@/lib/utils"
import { useChatStore } from "@/store/chat"

const APPLICANT_TYPES: ApplicantType[] = ["local", "international"]
const PHOTO_STEPS = signatureSteps(80, 2, "deep", "field", 7)

export function ProgramDetailPage() {
  const guidanceT = useGuidanceT()
  const { t, language, degree, languages, deadlineWithStatus, schoolName, schoolLang, tuitionKzt, tuitionUsd, programTitle } = useI18n()
  const { id = "" } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const applicant: ApplicantType = searchParams.get("applicant") === "international" ? "international" : "local"
  const setOpen = useChatStore((state) => state.setOpen)
  const setDraft = useChatStore((state) => state.setDraft)
  const backLabel = t("detail.backToPrograms").replace(/^←\s*/, "")

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
    return (
      <PageShell>
        <p className="text-muted-foreground">{t("detail.loading")}</p>
      </PageShell>
    )
  }

  if (programQuery.isError) {
    return (
      <PageShell>
        {isNotFound(programQuery.error) ? (
          <h1 className="text-[clamp(2.25rem,4vw,3.5rem)] leading-[1.08] font-medium">{t("detail.notFound")}</h1>
        ) : (
          <ConnectionError message={t("detail.loadError")} retrying={programQuery.isFetching} onRetry={() => void programQuery.refetch()} />
        )}
        <Button asChild variant="link" className="mt-6 text-base">
          <Link to="/programs">{t("detail.back")}</Link>
        </Button>
      </PageShell>
    )
  }

  const program = programQuery.data
  const title = programTitle(program)
  const photo = programImage(program.program_id)

  function askInChat() {
    setDraft(t(`detail.askDocuments.${applicant}`, { title, code: program.program_id }))
    setOpen(true)
  }

  return (
    <div>
      <section className="on-field relative bg-field">
        <div className="mx-auto max-w-[84rem] px-4 pt-8 pb-16 sm:px-6 lg:px-8 lg:pb-20">
          <nav aria-label={t("detail.breadcrumb")}>
            <ol className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[0.9375rem] font-semibold text-field-muted">
              <li>
                <Link to="/programs" className="inline-flex items-center gap-2 hover:text-field-foreground">
                  <ArrowLeft className="size-4" aria-hidden="true" />
                  {backLabel}
                </Link>
              </li>
              <li aria-hidden="true">/</li>
              <li>
                <Link to={`/programs?degree_level=${program.degree_level}`} className="hover:text-field-foreground">
                  {degree(program.degree_level)}
                </Link>
              </li>
              <li aria-hidden="true" className="hidden sm:block">/</li>
              <li aria-current="page" className="hidden max-w-[32ch] truncate text-field-foreground sm:block">
                {title}
              </li>
            </ol>
          </nav>
          <div className={cn("mt-8 grid grid-cols-1 gap-8", photo && "lg:grid-cols-[minmax(0,1fr)_minmax(0,0.95fr)] lg:items-center lg:gap-14")}>
            <div className="min-w-0">
              <h1 className="max-w-[18ch] text-[clamp(2.5rem,4.5vw,4rem)] leading-[1.06] font-medium">{title}</h1>
              <p className="tabular mt-4 text-lg text-field-muted">
                {degree(program.degree_level)} · {program.program_id}
              </p>
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <ApplyAction label={t("detail.apply")} />
                <CompareToggle programId={program.program_id} title={title} tone="field" className="h-12 px-5" />
              </div>
            </div>
            {photo ? (
              <figure className="m-0 min-w-0">
                <div className="relative overflow-hidden">
                  <img
                    src={photo.src}
                    srcSet={photo.srcSet}
                    sizes="(min-width: 1024px) 45vw, 100vw"
                    alt=""
                    width={1920}
                    height={1200}
                    fetchPriority="high"
                    className="hero-settle block aspect-[16/10] w-full object-cover"
                  />
                  {/* The band rises into the photo with the stepped mosaic edge (signature 1 of 2). */}
                  <div className="absolute inset-x-0 bottom-0 overflow-hidden">
                    <Tesserae size={16} rows={PHOTO_STEPS} />
                  </div>
                </div>
                {photo.credit ? <figcaption className="mt-2 text-xs text-field-muted">{t("detail.photoCredit", { name: photo.credit })}</figcaption> : null}
              </figure>
            ) : null}
          </div>

          <dl className="mt-10 grid gap-1.5 sm:grid-cols-2 lg:grid-cols-4">
            <Fact label={t("detail.school")}>
              <span lang={schoolLang(program.faculty)}>{schoolName(program.faculty)}</span>
            </Fact>
            <Fact label={t("detail.language")}>{languages(program.language)}</Fact>
            <Fact label={t("detail.tuition")} published={program.tuition_per_ects_kzt !== null}>
              {t("detail.localValue", { value: tuitionKzt(program.tuition_per_ects_kzt) })}
              <br />
              {t("detail.internationalValue", { value: tuitionUsd(program.tuition_per_ects_usd) })}
            </Fact>
            <Fact label={t("detail.deadline")} published={Boolean(program.deadline_local || program.deadline_international)}>
              {program.deadline_local || program.deadline_international ? (
                <>
                  {t("detail.localValue", { value: deadlineWithStatus(program.deadline_local) })}
                  <br />
                  {t("detail.internationalValue", { value: deadlineWithStatus(program.deadline_international) })}
                </>
              ) : (
                t("format.notPublishedYet")
              )}
            </Fact>
          </dl>
          <nav aria-label={t("detail.jump")} className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-[0.9375rem] font-semibold">
            {[
              ["#documents-heading", t("detail.documents")],
              ["#requirements-heading", t("detail.requirements")],
              ["#next-steps", t("detail.nextSteps")],
              ["#related-heading", t("detail.related")],
            ].map(([href, label]) => (
              <a key={href} href={href} className="text-field-muted underline decoration-field-foreground/30 underline-offset-4 hover:text-field-foreground hover:decoration-field-foreground">
                {label}
              </a>
            ))}
          </nav>
        </div>
      </section>

      <div className="mx-auto grid max-w-[84rem] gap-12 px-4 pt-16 pb-24 sm:px-6 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-16 lg:px-8 lg:pt-20">
        <div className="min-w-0">
        <section aria-labelledby="documents-heading">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="documents-heading" className="scroll-mt-6 text-[clamp(1.875rem,3vw,2.75rem)] leading-[1.1] font-medium">
                {t("detail.documents")}
              </h2>
              <p className="mt-3 text-muted-foreground">{t("detail.documentsNote")}</p>
            </div>
            <div className="flex" role="group" aria-label={t("detail.applicantType")}>
              {APPLICANT_TYPES.map((type) => (
                <Button
                  key={type}
                  size="sm"
                  variant={applicant === type ? "default" : "outline"}
                  aria-pressed={applicant === type}
                  onClick={() => setApplicant(type)}
                  className="h-11 px-4 [&+&]:-ml-0.5"
                >
                  {t(`applicant.${type}`)}
                </Button>
              ))}
            </div>
          </div>

          <div className="mt-8">
            {checklistQuery.isPending ? <p className="text-muted-foreground">{t("detail.loadingChecklist")}</p> : null}
            {checklistQuery.isError ? (
              <ConnectionError message={t("detail.checklistError")} retrying={checklistQuery.isFetching} onRetry={() => void checklistQuery.refetch()} />
            ) : null}
            {checklistQuery.data ? <DocumentChecklist checklist={checklistQuery.data} /> : null}
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <SaveChecklistButton key={`${id}:${applicant}`} programId={id} applicantType={applicant} />
            <ChecklistPdfButton path={`/api/programs/${encodeURIComponent(id)}/checklist/pdf?applicant_type=${applicant}&language=${language}`} />
          </div>
        </section>
          <RequirementsSection programId={program.program_id} applicant={applicant} />
          <RelatedPrograms program={program} />
        </div>

        <aside aria-labelledby="next-steps" className="lg:sticky lg:top-6 lg:self-start">
          <div className="bg-card p-6">
            <h2 id="next-steps" className="text-2xl leading-[1.15] font-medium">
              {t("detail.nextSteps")}
            </h2>
            <ul className="mt-5 border-t-2 border-ink">
              <StepLink to={`/eligibility?program=${encodeURIComponent(id)}`}>{guidanceT("eligibility")}</StepLink>
              <StepLink to={`/cost-calculator?program=${encodeURIComponent(id)}`}>{guidanceT("cost")}</StepLink>
              <StepLink to="/funding">{guidanceT("funding")}</StepLink>
              {program.source_url ? (
                <li className="border-b border-border">
                  <a
                    href={program.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-between gap-4 py-3.5 font-semibold transition-colors hover:text-primary"
                  >
                    {t("detail.officialPage")}
                    <ExternalLink className="size-4 shrink-0" aria-hidden="true" />
                  </a>
                </li>
              ) : null}
            </ul>
            <Button className="mt-6 w-full justify-between" onClick={askInChat}>
              {t("detail.askInChat")}
              <MessageCircleQuestion aria-hidden="true" />
            </Button>
          </div>
        </aside>
      </div>
    </div>
  )
}

function Fact({ label, children, published = true }: { label: string; children: ReactNode; published?: boolean }) {
  return (
    <div className={cn("p-5", published ? "bg-field-deep" : "bg-field-deep/50")}>
      <dt className="text-sm font-semibold text-field-muted">{label}</dt>
      <dd className="tabular mt-2 text-lg leading-snug font-semibold">{children}</dd>
    </div>
  )
}

function StepLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <li className="border-b border-border">
      <Link to={to} className="group flex items-center justify-between gap-4 py-3.5 font-semibold transition-colors hover:text-primary">
        {children}
        <ArrowRight className="size-4 shrink-0 transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
      </Link>
    </li>
  )
}

// Published entry requirements for the chosen applicant type, each with its source; the same
// rules the eligibility check evaluates. Hidden while loading or when the service is down.
function RequirementsSection({ programId, applicant }: { programId: string; applicant: ApplicantType }) {
  const { t } = useI18n()
  const guidanceT = useGuidanceT()
  const guidance = useQuery({
    queryKey: ["guidance", programId],
    queryFn: ({ signal }) => getGuidance(programId, false, signal),
  })
  if (!guidance.data) return null
  // Only confirmed rules are shown to applicants; rules still under review stay out of sight.
  const rules = guidance.data.rules.filter(
    (rule) => rule.evidence.status === "confirmed" && (!rule.applicant_type || rule.applicant_type === applicant),
  )

  return (
    <section aria-labelledby="requirements-heading" className="mt-20">
      <h2 id="requirements-heading" className="scroll-mt-6 text-[clamp(1.875rem,3vw,2.75rem)] leading-[1.1] font-medium">
        {t("detail.requirements")}
      </h2>
      <p className="mt-3 text-muted-foreground">{t("detail.requirementsNote")}</p>
      {rules.length ? (
        <ul className="mt-8 border-t-2 border-ink">
          {rules.map((rule, index) => {
            const scope = [rule.education_route, rule.track, rule.admission_basis].flatMap((value) => (value ? [value] : []))
            return (
              <li key={`${rule.key}-${index}`} className="border-b border-border py-5">
                <h3 className="font-semibold">{guidanceT.code(rule.key)}</h3>
                {scope.length ? <p className="mt-1 text-sm text-muted-foreground">{scope.map((value) => guidanceT.code(value)).join(" · ")}</p> : null}
                <div className="mt-2 space-y-1 text-[0.9375rem]">
                  {rule.alternatives.map((group, groupIndex) => (
                    <p key={groupIndex}>
                      {groupIndex > 0 ? <strong className="label mr-1">{guidanceT("or")}</strong> : null}
                      {group.map((condition, conditionIndex) => (
                        <span key={conditionIndex}>
                          {conditionIndex > 0 ? ` ${guidanceT("and").toLocaleLowerCase()} ` : null}
                          <ConditionText condition={condition} />
                        </span>
                      ))}
                    </p>
                  ))}
                </div>
                <EvidenceView evidence={rule.evidence} />
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="mt-6 text-muted-foreground">{t("detail.requirementsNone")}</p>
      )}
      <Button asChild variant="outline" className="mt-6">
        <Link to={`/eligibility?program=${encodeURIComponent(programId)}`}>
          {t("detail.checkEligibility")}
          <ArrowRight aria-hidden="true" />
        </Link>
      </Button>
    </section>
  )
}

// Up to three programs of the same school: the same title at other degrees first, then the same degree.
function RelatedPrograms({ program }: { program: Program }) {
  const { t, degree, programTitle } = useI18n()
  const catalogue = useQuery(allProgramsQuery)
  const others = (catalogue.data?.programs ?? []).filter((item) => item.faculty === program.faculty && item.program_id !== program.program_id)
  const sameTitle = others.filter((item) => item.title.toLowerCase() === program.title.toLowerCase())
  const sameLevel = others.filter((item) => item.degree_level === program.degree_level && !sameTitle.includes(item))
  const picks = [...sameTitle, ...sameLevel].slice(0, 3)
  if (!picks.length) return null

  return (
    <section aria-labelledby="related-heading" className="mt-20">
      <h2 id="related-heading" className="scroll-mt-6 text-[clamp(1.875rem,3vw,2.75rem)] leading-[1.1] font-medium">
        {t("detail.related")}
      </h2>
      <ul className="mt-8 border-t-2 border-ink">
        {picks.map((item) => (
          <li key={item.program_id} className="border-b border-border">
            <Link
              to={`/programs/${item.program_id}`}
              className="group grid grid-cols-[minmax(0,1fr)_1.25rem] items-center gap-4 py-5 transition-colors hover:bg-secondary/60 sm:-mx-2 sm:px-2"
            >
              <span className="min-w-0">
                <span className="block font-heading text-xl font-medium group-hover:text-primary">{programTitle(item)}</span>
                <span className="tabular mt-1 block text-sm text-muted-foreground">
                  {degree(item.degree_level)} · {item.program_id}
                </span>
              </span>
              <ArrowRight className="size-5 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
