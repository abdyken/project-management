import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react"
import { type FormEvent, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { isApiError, isNotFound } from "@/api/errors"
import {
  type ApplicantType,
  createStaffProgram,
  getStaffProgram,
  replaceStaffDocuments,
  type StaffDocument,
  type StaffProgram,
  type StaffProgramFields,
  updateStaffProgram,
} from "@/api/staff"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { type StaffKey, useStaffT } from "@/staff/i18n"
import { selectClass } from "@/staff/styles"

type Facts = Record<
  | "program_id"
  | "title"
  | "title_ru"
  | "title_kk"
  | "faculty"
  | "language"
  | "tuition_per_ects_kzt"
  | "tuition_per_ects_usd"
  | "deadline_local"
  | "deadline_international"
  | "source_url",
  string
> & { degree_level: StaffProgramFields["degree_level"]; is_active: boolean }

const EMPTY_FACTS: Facts = {
  program_id: "",
  title: "",
  title_ru: "",
  title_kk: "",
  faculty: "",
  degree_level: "bachelor",
  language: "",
  tuition_per_ects_kzt: "",
  tuition_per_ects_usd: "",
  deadline_local: "",
  deadline_international: "",
  source_url: "",
  is_active: true,
}

const APPLICANT_TYPES: ApplicantType[] = ["local", "international"]
const NEW_DOCUMENT: StaffDocument = { name: "", format: "copy", translation: false, notarisation: false, deadline: "" }

function toFacts(program: StaffProgram): Facts {
  const text = (value: string | number | null) => (value === null ? "" : String(value))
  return {
    program_id: program.program_id,
    title: program.title,
    title_ru: text(program.title_ru),
    title_kk: text(program.title_kk),
    faculty: program.faculty,
    degree_level: program.degree_level,
    language: text(program.language),
    tuition_per_ects_kzt: text(program.tuition_per_ects_kzt),
    tuition_per_ects_usd: text(program.tuition_per_ects_usd),
    deadline_local: text(program.deadline_local),
    deadline_international: text(program.deadline_international),
    source_url: text(program.source_url),
    is_active: program.is_active,
  }
}

function toFields(facts: Facts): StaffProgramFields {
  const nullable = (value: string) => value.trim() || null
  const amount = (value: string) => (value.trim() === "" ? null : Number(value))
  return {
    title: facts.title.trim(),
    title_ru: nullable(facts.title_ru),
    title_kk: nullable(facts.title_kk),
    faculty: facts.faculty.trim(),
    degree_level: facts.degree_level,
    language: nullable(facts.language),
    tuition_per_ects_kzt: amount(facts.tuition_per_ects_kzt),
    tuition_per_ects_usd: amount(facts.tuition_per_ects_usd),
    deadline_local: nullable(facts.deadline_local),
    deadline_international: nullable(facts.deadline_international),
    source_url: nullable(facts.source_url),
    is_active: facts.is_active,
  }
}

function errorText(error: unknown) {
  return isApiError(error) ? error.message : String(error)
}

function DocumentsEditor({ program, applicantType }: { program: StaffProgram; applicantType: ApplicantType }) {
  const t = useStaffT()
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState<StaffDocument[] | null>(null)
  const [saved, setSaved] = useState(false)
  const documents = draft ?? program.documents[applicantType]

  const save = useMutation({
    mutationFn: () => replaceStaffDocuments(program.program_id, applicantType, documents.map((doc) => ({ ...doc, name: doc.name.trim(), deadline: doc.deadline.trim() }))),
    onSuccess: (updated) => {
      queryClient.setQueryData(["staff", "programs", "item", program.program_id], updated)
      queryClient.invalidateQueries({ queryKey: ["staff", "programs", "list"] })
      setDraft(null)
      setSaved(true)
    },
  })

  const change = (next: StaffDocument[]) => {
    setDraft(next)
    setSaved(false)
  }
  const patch = (index: number, value: Partial<StaffDocument>) => change(documents.map((doc, i) => (i === index ? { ...doc, ...value } : doc)))
  const move = (index: number, by: number) => {
    const next = [...documents]
    ;[next[index], next[index + by]] = [next[index + by], next[index]]
    change(next)
  }
  const valid = documents.every((doc) => doc.name.trim() && doc.deadline.trim())
  const title = t(`prog.documents.${applicantType}` as StaffKey)

  return (
    <section aria-label={title} className="mt-8">
      <h2 className="text-lg font-medium">{title}</h2>
      {documents.length === 0 && <p className="mt-2 text-sm text-muted-foreground">{t("prog.noDocuments")}</p>}
      <ol className="mt-3 space-y-3">
        {documents.map((doc, index) => (
          <li key={index} className="rounded-md border border-border bg-card p-3">
            <div className="grid gap-3 md:grid-cols-[2fr_1fr]">
              <label className="block space-y-1 text-sm">
                <span>
                  {index + 1}. {t("prog.doc.name")}
                </span>
                <Input value={doc.name} onChange={(event) => patch(index, { name: event.target.value })} />
              </label>
              <label className="block space-y-1 text-sm">
                <span>{t("prog.doc.deadline")}</span>
                <Input value={doc.deadline} onChange={(event) => patch(index, { deadline: event.target.value })} />
              </label>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-4 text-sm">
              <label className="flex items-center gap-2">
                {t("prog.doc.format")}
                <select
                  className={`${selectClass} h-8`}
                  value={doc.format}
                  onChange={(event) => patch(index, { format: event.target.value as StaffDocument["format"] })}
                >
                  <option value="copy">{t("prog.doc.copy")}</option>
                  <option value="original">{t("prog.doc.original")}</option>
                </select>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={doc.translation} onChange={(event) => patch(index, { translation: event.target.checked })} />
                {t("prog.doc.translation")}
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={doc.notarisation} onChange={(event) => patch(index, { notarisation: event.target.checked })} />
                {t("prog.doc.notarisation")}
              </label>
              <span className="ml-auto flex gap-1">
                <Button type="button" variant="ghost" size="icon" aria-label={t("prog.doc.up")} disabled={index === 0} onClick={() => move(index, -1)}>
                  <ArrowUp />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={t("prog.doc.down")}
                  disabled={index === documents.length - 1}
                  onClick={() => move(index, 1)}
                >
                  <ArrowDown />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={`${t("prog.doc.remove")}: ${doc.name || index + 1}`}
                  onClick={() => change(documents.filter((_, i) => i !== index))}
                >
                  <Trash2 />
                </Button>
              </span>
            </div>
          </li>
        ))}
      </ol>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Button type="button" variant="outline" onClick={() => change([...documents, { ...NEW_DOCUMENT }])}>
          <Plus />
          {t("prog.doc.add")}
        </Button>
        <Button type="button" disabled={draft === null || !valid || save.isPending} onClick={() => save.mutate()}>
          {save.isPending ? t("edit.saving") : t("prog.saveDocuments")}
        </Button>
        {save.error && (
          <p role="alert" className="text-sm text-destructive">
            {t("edit.error", { message: errorText(save.error) })}
          </p>
        )}
        {saved && draft === null && <p role="status" className="text-sm">{t("edit.saved")}</p>}
      </div>
    </section>
  )
}

export function StaffProgramEditPage() {
  const t = useStaffT()
  const { programId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isNew = !programId
  const [draft, setDraft] = useState<Facts | null>(null)
  const [saved, setSaved] = useState(false)

  const program = useQuery({
    queryKey: ["staff", "programs", "item", programId],
    queryFn: ({ signal }) => getStaffProgram(programId!, signal),
    enabled: !isNew,
  })

  const save = useMutation({
    mutationFn: (facts: Facts) =>
      isNew ? createStaffProgram({ ...toFields(facts), program_id: facts.program_id.trim() }) : updateStaffProgram(programId!, toFields(facts)),
    onSuccess: (updated) => {
      queryClient.setQueryData(["staff", "programs", "item", updated.program_id], updated)
      queryClient.invalidateQueries({ queryKey: ["staff", "programs", "list"] })
      setDraft(null)
      setSaved(true)
      if (isNew) navigate(`/staff/programs/${updated.program_id}`, { replace: true })
    },
  })

  if (!isNew && program.isPending) return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
  if (!isNew && program.isError) {
    return (
      <div className="text-sm">
        <p>{isNotFound(program.error) ? t("prog.notFound") : t("common.error")}</p>
        <Link to="/staff/programs" className="mt-3 inline-block underline">
          {t("prog.back")}
        </Link>
      </div>
    )
  }

  const facts = draft ?? (program.data ? toFacts(program.data) : EMPTY_FACTS)
  const update = (patch: Partial<Facts>) => {
    setDraft({ ...facts, ...patch })
    setSaved(false)
  }
  const canSave =
    facts.title.trim() !== "" && facts.faculty.trim() !== "" && (!isNew || /^[0-9A-Z]{2,}$/.test(facts.program_id.trim())) && !save.isPending

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (canSave) save.mutate(facts)
  }

  const text = (name: keyof Facts, label: StaffKey, props: Record<string, unknown> = {}) => (
    <label className="block space-y-1.5 text-sm">
      <span>{t(label)}</span>
      <Input value={facts[name] as string} onChange={(event) => update({ [name]: event.target.value })} {...props} />
    </label>
  )

  return (
    <div className="max-w-4xl">
      <Link to="/staff/programs" className="text-sm text-muted-foreground hover:text-foreground">
        {t("prog.back")}
      </Link>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight">
        {isNew ? t("prog.newTitle") : `${program.data!.program_id} · ${program.data!.title}`}
      </h1>
      {program.data?.updated_by && (
        <p className="mt-1 text-xs text-muted-foreground">
          {t("edit.updatedBy", { date: program.data.updated_at!.slice(0, 10), name: program.data.updated_by })}
        </p>
      )}

      <form onSubmit={onSubmit} aria-label={t("prog.facts")} className="mt-6">
        <p className="text-sm text-muted-foreground">{t("prog.emptyHint")}</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {isNew && (
            <label className="block space-y-1.5 text-sm">
              <span>{t("prog.code")}</span>
              <Input value={facts.program_id} onChange={(event) => update({ program_id: event.target.value.toUpperCase() })} />
              <span className="block text-xs text-muted-foreground">{t("prog.codeHint")}</span>
            </label>
          )}
          {text("title", "prog.title")}
          {text("title_ru", "prog.titleRu")}
          {text("title_kk", "prog.titleKk")}
          {text("faculty", "prog.faculty")}
          <label className="block space-y-1.5 text-sm">
            <span>{t("prog.degree")}</span>
            <select
              className={`${selectClass} w-full`}
              value={facts.degree_level}
              onChange={(event) => update({ degree_level: event.target.value as Facts["degree_level"] })}
            >
              {(["bachelor", "master", "phd"] as const).map((value) => (
                <option key={value} value={value}>
                  {t(`edit.degree.${value}`)}
                </option>
              ))}
            </select>
          </label>
          {text("language", "prog.language")}
          {text("tuition_per_ects_kzt", "prog.feeKzt", { type: "number", min: 0, inputMode: "numeric" })}
          {text("tuition_per_ects_usd", "prog.feeUsd", { type: "number", min: 0, inputMode: "numeric" })}
          {text("deadline_local", "prog.deadlineLocal", { type: "date" })}
          {text("deadline_international", "prog.deadlineInternational", { type: "date" })}
          {text("source_url", "prog.sourceUrl", { type: "url" })}
        </div>
        <label className="mt-4 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={facts.is_active} onChange={(event) => update({ is_active: event.target.checked })} />
          {t("prog.active")}
        </label>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={!canSave || (!isNew && draft === null)}>
            {save.isPending ? t("edit.saving") : isNew ? t("prog.create") : t("prog.saveFacts")}
          </Button>
          {save.error && (
            <p role="alert" className="text-sm text-destructive">
              {t("edit.error", { message: errorText(save.error) })}
            </p>
          )}
          {saved && draft === null && <p role="status" className="text-sm">{t("edit.saved")}</p>}
        </div>
      </form>

      {program.data && APPLICANT_TYPES.map((type) => <DocumentsEditor key={type} program={program.data} applicantType={type} />)}
    </div>
  )
}
