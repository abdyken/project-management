import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent, type ReactNode, type RefObject } from "react"
import { Link, Navigate, useNavigate, useParams } from "react-router-dom"
import {
  ACCEPTED_FILES,
  applicationsKey,
  deleteDocument,
  deleteDraft,
  documentUrl,
  EDUCATION_LEVELS,
  getApplication,
  MAX_FILE_BYTES,
  saveApplication,
  submitApplication,
  uploadDocument,
  type Application,
  type ApplicationDocument,
  type ApplicationFields,
} from "@/api/applications"
import { isApiError } from "@/api/errors"
import { SAVED_PROGRAMS_KEY, useApplicant } from "@/applicant/session"
import { applicationsErrorKey, useApplicationsT } from "@/applications/i18n"
import { ArrowLeft } from "lucide-react"
import { ApplicationStepper } from "@/components/applications/ApplicationStepper"
import { ConnectionError } from "@/components/common/ConnectionError"
import { fieldClass } from "@/components/guidance/fields"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { requirementNotes } from "@/lib/checklist"
import { fileSize } from "@/lib/files"

type T = ReturnType<typeof useApplicationsT>
const FIELD_IDS = {
  full_name: "application-full-name",
  date_of_birth: "application-birth",
  citizenship: "application-citizenship",
  phone: "application-phone",
  education_level: "application-education",
  graduation_year: "application-graduation",
  exam_total: "application-exam",
} as const
type FieldKey = keyof typeof FIELD_IDS
const isField = (name: string): name is FieldKey => name in FIELD_IDS
// Valid under the `v` flag browsers use for `pattern`: brackets and the dash are escaped.
const PHONE_PATTERN = "\\+?[0-9 \\(\\)\\-]{6,30}"
const today = () => new Date().toISOString().slice(0, 10)

function errorText(t: T, error: unknown) {
  return t(isApiError(error) ? applicationsErrorKey(error.code, error.status) : "error")
}

// The API's INVALID_REQUEST message starts with the field: "phone: String should match pattern".
function invalidField(error: unknown): FieldKey | null {
  if (!isApiError(error) || error.code !== "INVALID_REQUEST") return null
  const field = error.message.split(":")[0].trim()
  return isField(field) ? field : null
}

function missingLabel(t: T, name: string) {
  if (isField(name)) return t(name)
  if (name === "consent" || name === "documents") return t(`missing.${name}`)
  return name
}

function fieldsOf(application: Application): ApplicationFields {
  const { full_name, date_of_birth, citizenship, phone, education_level, graduation_year, exam_total, consent } =
    application
  return { full_name, date_of_birth, citizenship, phone, education_level, graduation_year, exam_total, consent }
}

function Row({ id, label, hint, error, wide, children }: { id: string; label: string; hint?: string; error?: string; wide?: boolean; children: ReactNode }) {
  return (
    <div className={wide ? "space-y-1 text-sm sm:col-span-2" : "space-y-1 text-sm"}>
      <label htmlFor={id} className="block">
        {label}
      </label>
      {children}
      {hint && (
        <p id={`${id}-hint`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}

function DocumentRow({ application, document, onRemoved }: { application: Application; document: ApplicationDocument; onRemoved: () => void }) {
  const t = useApplicationsT()
  const { language } = useI18n()
  const cache = useQueryClient()
  const remove = useMutation({
    mutationFn: () => deleteDocument(application.id, document.id),
    onSuccess: async () => {
      await cache.invalidateQueries({ queryKey: [...applicationsKey, application.id] })
      onRemoved()
    },
  })
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      <span className="min-w-0 break-all">{document.original_name}</span>
      <span className="text-xs text-muted-foreground">{fileSize(document.size_bytes, language)}</span>
      <a
        className="inline-block py-1 underline"
        href={documentUrl(application.id, document.id)}
        download={document.original_name}
        aria-label={`${t("download")}: ${document.original_name}`}
      >
        {t("download")}
      </a>
      {application.editable && (
        <button
          type="button"
          className="py-1 underline"
          disabled={remove.isPending}
          aria-label={`${t("remove")}: ${document.original_name}`}
          onClick={() => remove.mutate()}
        >
          {t("remove")}
        </button>
      )}
      {remove.isError && (
        <span role="alert" className="text-destructive">
          {errorText(t, remove.error)}
        </span>
      )}
    </li>
  )
}

function UploadButton({ application, requirementId, label }: { application: Application; requirementId: number | null; label: string }) {
  const t = useApplicationsT()
  const cache = useQueryClient()
  const input = useRef<HTMLInputElement>(null)
  const button = useRef<HTMLButtonElement>(null)
  const [tooLarge, setTooLarge] = useState(false)
  const [done, setDone] = useState("")
  const upload = useMutation({
    mutationFn: (file: File) => uploadDocument(application.id, file, requirementId),
    onSuccess: async (document) => {
      setDone(t("uploadedFile", { name: document.original_name }))
      await cache.invalidateQueries({ queryKey: [...applicationsKey, application.id] })
      void cache.invalidateQueries({ queryKey: SAVED_PROGRAMS_KEY })
      button.current?.focus()
    },
    onError: () => button.current?.focus(),
  })
  function choose(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return
    setDone("")
    setTooLarge(file.size > MAX_FILE_BYTES)
    if (file.size <= MAX_FILE_BYTES) upload.mutate(file)
    else button.current?.focus()
  }
  return (
    <div className="mt-2">
      {/* The visible button opens the picker; the input itself stays out of the Tab order. */}
      <input ref={input} type="file" accept={ACCEPTED_FILES} className="sr-only" tabIndex={-1} aria-hidden="true" onChange={choose} />
      <Button
        ref={button}
        type="button"
        variant="outline"
        size="sm"
        disabled={upload.isPending}
        aria-label={`${t("chooseFile")}: ${label}`}
        onClick={() => input.current?.click()}
      >
        {upload.isPending ? t("uploading") : t("chooseFile")}
      </Button>
      <p role="status" className="sr-only">
        {done}
      </p>
      {(tooLarge || upload.isError) && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {tooLarge ? t("fileTooLarge") : errorText(t, upload.error)}
        </p>
      )}
    </div>
  )
}

function Documents({ application }: { application: Application }) {
  const t = useApplicationsT()
  const { t: portalT, language } = useI18n()
  const heading = useRef<HTMLHeadingElement>(null)
  const requirementIds = new Set(application.requirements.map((item) => item.id))
  const other = application.documents.filter((document) => document.requirement_id === null || !requirementIds.has(document.requirement_id))
  const focusHeading = () => heading.current?.focus()
  return (
    <section aria-labelledby="documents-title" className="mt-10">
      <h2 id="documents-title" ref={heading} tabIndex={-1} className="text-2xl font-medium outline-none">
        {t("documentsTitle")}
      </h2>
      <p className="mt-2 text-sm text-muted-foreground">{t("documentsLead")}</p>
      <p className="mt-1 text-xs text-muted-foreground">
        {t("used", { used: fileSize(application.bytes_used, language), limit: fileSize(application.bytes_limit, language) })}
      </p>
      <ul className="mt-5 space-y-4">
        {application.requirements.map((requirement) => {
          const uploaded = application.documents.filter((document) => document.requirement_id === requirement.id)
          return (
            <li key={requirement.id} className="rounded-lg border border-border p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-medium">{requirement.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {requirementNotes(requirement, portalT)} · {requirement.deadline}
                  </p>
                </div>
                <span className="text-xs">{t(uploaded.length ? "uploaded" : "notUploaded")}</span>
              </div>
              {uploaded.length > 0 && (
                <ul className="mt-3 space-y-1">
                  {uploaded.map((document) => (
                    <DocumentRow key={document.id} application={application} document={document} onRemoved={focusHeading} />
                  ))}
                </ul>
              )}
              {application.editable && <UploadButton application={application} requirementId={requirement.id} label={requirement.name} />}
            </li>
          )
        })}
        <li className="rounded-lg border border-border p-4">
          <p className="font-medium">{t("otherDocument")}</p>
          {other.length > 0 && (
            <ul className="mt-3 space-y-1">
              {other.map((document) => (
                <DocumentRow key={document.id} application={application} document={document} onRemoved={focusHeading} />
              ))}
            </ul>
          )}
          {application.editable && <UploadButton application={application} requirementId={null} label={t("otherDocument")} />}
        </li>
      </ul>
    </section>
  )
}

function Form({ application, statusBox }: { application: Application; statusBox: RefObject<HTMLDivElement | null> }) {
  const t = useApplicationsT()
  const { language } = useI18n()
  const cache = useQueryClient()
  const navigate = useNavigate()
  const formRef = useRef<HTMLFormElement>(null)
  const deleteButton = useRef<HTMLButtonElement>(null)
  const confirmText = useRef<HTMLParagraphElement>(null)
  const [fields, setFields] = useState<ApplicationFields>(() => fieldsOf(application))
  const [dirty, setDirty] = useState(false)
  const [badField, setBadField] = useState<FieldKey | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const key = [...applicationsKey, application.id]

  // Warn before the tab is closed or reloaded with unsaved changes.
  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener("beforeunload", warn)
    return () => window.removeEventListener("beforeunload", warn)
  }, [dirty])
  useEffect(() => {
    if (confirmDelete) confirmText.current?.focus()
  }, [confirmDelete])

  const update = (patch: Partial<ApplicationFields>) => {
    setFields((current) => ({ ...current, ...patch }))
    setDirty(true)
    setBadField(null)
  }
  const text = (name: "full_name" | "date_of_birth" | "citizenship" | "phone") => (event: ChangeEvent<HTMLInputElement>) =>
    update({ [name]: event.target.value || null })
  const number = (name: "graduation_year" | "exam_total") => (event: ChangeEvent<HTMLInputElement>) =>
    update({ [name]: event.target.value === "" ? null : Number(event.target.value) })
  const showInvalid = (error: unknown) => {
    const field = invalidField(error)
    setBadField(field)
    if (field) window.setTimeout(() => document.getElementById(FIELD_IDS[field])?.focus())
  }
  const persist = async () => {
    const saved = await saveApplication(application.id, fields, language)
    cache.setQueryData(key, saved)
    setDirty(false)
    return saved
  }
  const save = useMutation({ mutationFn: persist, onError: showInvalid })
  const submit = useMutation({
    // Unsaved edits are saved first; the cache then holds what the server has.
    mutationFn: async () => {
      if (dirty && (await persist()).missing.length) return null
      return submitApplication(application.id)
    },
    onSuccess: (submitted) => {
      if (!submitted) return
      cache.setQueryData(key, submitted)
      void cache.invalidateQueries({ queryKey: applicationsKey, exact: true })
      window.setTimeout(() => statusBox.current?.focus())
    },
    onError: showInvalid,
  })
  const remove = useMutation({
    mutationFn: () => deleteDraft(application.id),
    onSuccess: () => {
      cache.removeQueries({ queryKey: key })
      void cache.invalidateQueries({ queryKey: applicationsKey, exact: true })
      navigate("/account/applications", { replace: true })
    },
  })

  const locked = !application.editable
  const busy = save.isPending || submit.isPending
  const missing = dirty ? [] : application.missing
  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (formRef.current?.reportValidity()) save.mutate()
  }
  function onFinalSubmit() {
    if (formRef.current?.reportValidity()) submit.mutate()
  }
  const errorFor = (name: FieldKey) => (badField === name ? t("invalidField") : undefined)
  const described = (name: FieldKey, hint = false) =>
    [hint && `${FIELD_IDS[name]}-hint`, badField === name && `${FIELD_IDS[name]}-error`].filter(Boolean).join(" ") || undefined
  const field = (name: FieldKey, hint = false) => ({
    id: FIELD_IDS[name],
    "aria-invalid": badField === name || undefined,
    "aria-describedby": described(name, hint),
  })

  return (
    <>
      <form ref={formRef} onSubmit={onSubmit} className="mt-10" aria-labelledby="form-title">
        <h2 id="form-title" className="text-2xl font-medium">
          {t("formTitle")}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">{t("noIdentityNumbers")}</p>
        <fieldset disabled={locked || busy} className="mt-5 grid gap-4 sm:grid-cols-2">
          {/* Explicit labels: a label wrapped around a select would also read out its options. */}
          <Row id={FIELD_IDS.full_name} label={t("full_name")} error={errorFor("full_name")} wide>
            <input {...field("full_name")} className={fieldClass} autoComplete="name" maxLength={200} value={fields.full_name ?? ""} onChange={text("full_name")} />
          </Row>
          <Row id={FIELD_IDS.date_of_birth} label={t("date_of_birth")} error={errorFor("date_of_birth")}>
            <input {...field("date_of_birth")} className={fieldClass} type="date" autoComplete="bday" min="1900-01-01" max={today()} value={fields.date_of_birth ?? ""} onChange={text("date_of_birth")} />
          </Row>
          <Row id={FIELD_IDS.citizenship} label={t("citizenship")} error={errorFor("citizenship")}>
            <input {...field("citizenship")} className={fieldClass} autoComplete="country-name" maxLength={100} value={fields.citizenship ?? ""} onChange={text("citizenship")} />
          </Row>
          <Row id={FIELD_IDS.phone} label={t("phone")} hint={t("phoneHint")} error={errorFor("phone")}>
            <input
              {...field("phone", true)}
              className={fieldClass}
              type="tel"
              autoComplete="tel"
              inputMode="tel"
              maxLength={30}
              pattern={PHONE_PATTERN}
              value={fields.phone ?? ""}
              onChange={text("phone")}
            />
          </Row>
          <Row id={FIELD_IDS.education_level} label={t("education_level")} error={errorFor("education_level")}>
            <select
              {...field("education_level")}
              className={fieldClass}
              value={fields.education_level ?? ""}
              onChange={(event) => update({ education_level: EDUCATION_LEVELS.find((level) => level === event.target.value) ?? null })}
            >
              <option value="">{t("choose")}</option>
              {EDUCATION_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {t(`education.${level}`)}
                </option>
              ))}
            </select>
          </Row>
          <Row id={FIELD_IDS.graduation_year} label={t("graduation_year")} error={errorFor("graduation_year")}>
            <input {...field("graduation_year")} className={fieldClass} type="number" inputMode="numeric" min={1950} max={2100} value={fields.graduation_year ?? ""} onChange={number("graduation_year")} />
          </Row>
          <Row id={FIELD_IDS.exam_total} label={t("exam_total")} error={errorFor("exam_total")}>
            <input {...field("exam_total")} className={fieldClass} type="number" inputMode="numeric" min={0} max={150} value={fields.exam_total ?? ""} onChange={number("exam_total")} />
          </Row>
          <div className="flex items-start gap-3 text-sm sm:col-span-2">
            <input id="application-consent" type="checkbox" className="mt-1 h-4 w-4" checked={fields.consent} onChange={(event) => update({ consent: event.target.checked })} />
            <label htmlFor="application-consent">{t("consent")}</label>
          </div>
        </fieldset>
        {!locked && (
          <div className="mt-5 flex flex-wrap items-center gap-3">
            {/* Stays enabled after saving so focus is never dropped from a disabled button. */}
            <Button type="submit" variant="outline" disabled={busy}>
              {save.isPending ? t("working") : t("save")}
            </Button>
            <span role="status" className="text-sm text-muted-foreground">
              {dirty ? t("unsaved") : save.isSuccess ? t("saved") : ""}
            </span>
          </div>
        )}
        {save.isError && (
          <p role="alert" className="mt-3 text-sm text-destructive">
            {errorText(t, save.error)}
          </p>
        )}
      </form>

      <Documents application={application} />

      {!locked && (
        <section aria-labelledby="submit-title" className="mt-10 border-t border-border pt-8">
          <h2 id="submit-title" className="text-2xl font-medium">
            {t("submitTitle")}
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">{t("submitLead")}</p>
          {missing.length > 0 && (
            <div className="mt-4 text-sm">
              <p>{t("missingTitle")}</p>
              <ul className="mt-1 list-disc pl-5">
                {missing.map((name) => (
                  <li key={name}>{missingLabel(t, name)}</li>
                ))}
              </ul>
            </div>
          )}
          <Button className="mt-5" disabled={missing.length > 0 || busy} onClick={onFinalSubmit}>
            {submit.isPending ? t("working") : t("submit")}
          </Button>
          {submit.isError && (
            <p role="alert" className="mt-3 text-sm text-destructive">
              {errorText(t, submit.error)}
            </p>
          )}
          {application.status === "draft" && (
            <div className="mt-8">
              {confirmDelete ? (
                <div className="space-y-3">
                  <p ref={confirmText} tabIndex={-1} className="text-sm outline-none">
                    {t("confirmDelete")}
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Button variant="outline" disabled={remove.isPending} onClick={() => remove.mutate()}>
                      {t("deleteDraft")}
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setConfirmDelete(false)
                        window.setTimeout(() => deleteButton.current?.focus())
                      }}
                    >
                      {t("cancel")}
                    </Button>
                  </div>
                </div>
              ) : (
                <Button ref={deleteButton} variant="ghost" onClick={() => setConfirmDelete(true)}>
                  {t("deleteDraft")}
                </Button>
              )}
              {remove.isError && (
                <p role="alert" className="mt-3 text-sm text-destructive">
                  {errorText(t, remove.error)}
                </p>
              )}
            </div>
          )}
        </section>
      )}
    </>
  )
}

export function ApplicationPage() {
  const t = useApplicationsT()
  const { programTitle } = useI18n()
  const me = useApplicant()
  const statusBox = useRef<HTMLDivElement>(null)
  const raw = useParams().id ?? ""
  const id = /^[1-9][0-9]{0,15}$/.test(raw) ? Number(raw) : null
  const application = useQuery({
    queryKey: [...applicationsKey, id],
    queryFn: ({ signal }) => getApplication(id as number, signal),
    enabled: Boolean(me.data) && id !== null,
    staleTime: 0,
    refetchOnWindowFocus: false,
  })

  if (me.isPending) return <p className="mx-auto max-w-3xl px-4 pt-12 pb-20 sm:px-6 sm:pt-16 sm:pb-24">{t("working")}</p>
  if (isApiError(me.error) && me.error.status === 401) return <Navigate to="/account/login" replace />
  if (isApiError(application.error) && application.error.status === 401) return <Navigate to="/account/login" replace />
  const data = application.data
  if (!data) {
    const error = me.error ?? application.error
    const notFound = id === null || (isApiError(error) && error.status === 404)
    return (
      <div className="mx-auto max-w-3xl px-4 pt-12 pb-20 sm:px-6 sm:pt-16 sm:pb-24">
        <Link to="/account/applications" className="text-sm underline">
          ← {t("back")}
        </Link>
        <div className="mt-6">
          {notFound ? (
            <p role="alert">{t("notFound")}</p>
          ) : application.isPending && me.data ? (
            <p>{t("working")}</p>
          ) : (
            <ConnectionError
              message={t(isApiError(error) ? applicationsErrorKey(error.code, error.status) : "error")}
              onRetry={() => void application.refetch()}
              retrying={application.isFetching}
            />
          )}
        </div>
      </div>
    )
  }

  // The note belongs to the status it came with; after a resubmission it is out of date.
  const showNote = data.staff_note && ["needs_changes", "accepted", "rejected"].includes(data.status)
  return (
    <div className="mx-auto max-w-3xl px-4 pt-12 pb-20 sm:px-6 sm:pt-16 sm:pb-24">
      <Link to="/account/applications" className="inline-flex items-center gap-2 text-[0.9375rem] font-semibold text-primary hover:underline">
        <ArrowLeft className="size-4" aria-hidden="true" />
        {t("back")}
      </Link>
      <p className="tabular mt-8 text-muted-foreground">
        {data.program.program_id} · {t(data.applicant_type)}
      </p>
      <h1 className="mt-2 text-[clamp(2.25rem,4vw,3.5rem)] leading-[1.08] font-medium">{programTitle(data.program)}</h1>
      <div ref={statusBox} tabIndex={-1} className="mt-8 bg-card p-6 outline-none focus-visible:outline-2 focus-visible:outline-ring" role="status" aria-live="polite">
        <ApplicationStepper status={data.status} />
        <p className="mt-6 max-w-[60ch]">{t(`help.${data.status}`)}</p>
        {showNote && (
          <div className="mt-5 bg-secondary p-4">
            <h2 className="font-sans text-[0.9375rem] font-medium">{t("note")}</h2>
            <p className="mt-1 whitespace-pre-wrap break-words">{data.staff_note}</p>
          </div>
        )}
      </div>
      {!data.editable && <p className="mt-4 text-sm text-muted-foreground">{t("locked")}</p>}
      <Form key={`${data.id}:${data.status}`} application={data} statusBox={statusBox} />
    </div>
  )
}
