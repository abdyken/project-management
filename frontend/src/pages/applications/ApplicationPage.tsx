import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useId, useRef, useState, type ChangeEvent, type FormEvent, type ReactNode } from "react"
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
import { applicationsErrorKey, useApplicationsT, type ApplicationsKey } from "@/applications/i18n"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { ConnectionError } from "@/components/common/ConnectionError"
import { fieldClass } from "@/components/guidance/fields"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { fileSize } from "@/lib/files"

const FIELD_KEYS = ["full_name", "date_of_birth", "citizenship", "phone", "education_level", "graduation_year"] as const

function errorText(t: ReturnType<typeof useApplicationsT>, error: unknown) {
  return t(isApiError(error) ? applicationsErrorKey(error.code, error.status) : "error")
}

function fieldsOf(application: Application): ApplicationFields {
  const { full_name, date_of_birth, citizenship, phone, education_level, graduation_year, exam_total, consent } =
    application
  return { full_name, date_of_birth, citizenship, phone, education_level, graduation_year, exam_total, consent }
}

function Row({ id, label, hint, wide, children }: { id: string; label: string; hint?: string; wide?: boolean; children: ReactNode }) {
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
    </div>
  )
}

function DocumentRow({ application, document }: { application: Application; document: ApplicationDocument }) {
  const t = useApplicationsT()
  const cache = useQueryClient()
  const remove = useMutation({
    mutationFn: () => deleteDocument(application.id, document.id),
    onSuccess: () => cache.invalidateQueries({ queryKey: [...applicationsKey, application.id] }),
  })
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      <span className="min-w-0 break-all">{document.original_name}</span>
      <span className="text-xs text-muted-foreground">{fileSize(document.size_bytes)}</span>
      <a
        className="underline"
        href={documentUrl(application.id, document.id)}
        download={document.original_name}
        aria-label={`${t("download")}: ${document.original_name}`}
      >
        {t("download")}
      </a>
      {application.editable && (
        <button
          type="button"
          className="underline"
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
  const id = useId()
  const [tooLarge, setTooLarge] = useState(false)
  const upload = useMutation({
    mutationFn: (file: File) => uploadDocument(application.id, file, requirementId),
    onSuccess: () => {
      void cache.invalidateQueries({ queryKey: [...applicationsKey, application.id] })
      void cache.invalidateQueries({ queryKey: SAVED_PROGRAMS_KEY })
    },
  })
  function choose(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return
    setTooLarge(file.size > MAX_FILE_BYTES)
    if (file.size <= MAX_FILE_BYTES) upload.mutate(file)
  }
  return (
    <div className="mt-2">
      <input
        ref={input}
        id={id}
        type="file"
        accept={ACCEPTED_FILES}
        className="sr-only"
        aria-label={`${t("chooseFile")}: ${label}`}
        disabled={upload.isPending}
        onChange={choose}
      />
      <Button type="button" variant="outline" size="sm" disabled={upload.isPending} onClick={() => input.current?.click()}>
        {upload.isPending ? t("uploading") : t("chooseFile")}
      </Button>
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
  const requirementIds = new Set(application.requirements.map((item) => item.id))
  const other = application.documents.filter((document) => document.requirement_id === null || !requirementIds.has(document.requirement_id))
  return (
    <section aria-labelledby="documents-title" className="mt-10">
      <h2 id="documents-title" className="text-2xl font-semibold">
        {t("documentsTitle")}
      </h2>
      <p className="mt-2 text-sm text-muted-foreground">{t("documentsLead")}</p>
      <p className="mt-1 text-xs text-muted-foreground" aria-live="polite">
        {t("used", { used: fileSize(application.bytes_used), limit: fileSize(application.bytes_limit) })}
      </p>
      <ul className="mt-5 space-y-4">
        {application.requirements.map((requirement) => {
          const uploaded = application.documents.filter((document) => document.requirement_id === requirement.id)
          const notes = [t(requirement.format), requirement.translation && t("translation"), requirement.notarisation && t("notarisation")]
          return (
            <li key={requirement.id} className="rounded-lg border border-border p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-medium">{requirement.name}</p>
                  <p className="text-xs text-muted-foreground">{notes.filter(Boolean).join(", ")} · {requirement.deadline}</p>
                </div>
                <span className="text-xs">{t(uploaded.length ? "uploaded" : "notUploaded")}</span>
              </div>
              {uploaded.length > 0 && (
                <ul className="mt-3 space-y-1">
                  {uploaded.map((document) => (
                    <DocumentRow key={document.id} application={application} document={document} />
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
                <DocumentRow key={document.id} application={application} document={document} />
              ))}
            </ul>
          )}
          {application.editable && <UploadButton application={application} requirementId={null} label={t("otherDocument")} />}
        </li>
      </ul>
    </section>
  )
}

function Form({ application }: { application: Application }) {
  const t = useApplicationsT()
  const { language } = useI18n()
  const cache = useQueryClient()
  const navigate = useNavigate()
  const [fields, setFields] = useState<ApplicationFields>(() => fieldsOf(application))
  const [dirty, setDirty] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const key = [...applicationsKey, application.id]
  const update = (patch: Partial<ApplicationFields>) => {
    setFields((current) => ({ ...current, ...patch }))
    setDirty(true)
  }
  const text = (name: keyof ApplicationFields) => (event: ChangeEvent<HTMLInputElement>) =>
    update({ [name]: event.target.value || null } as Partial<ApplicationFields>)
  const number = (name: "graduation_year" | "exam_total") => (event: ChangeEvent<HTMLInputElement>) =>
    update({ [name]: event.target.value === "" ? null : Number(event.target.value) })
  const save = useMutation({
    mutationFn: () => saveApplication(application.id, fields, language),
    onSuccess: (saved) => {
      cache.setQueryData(key, saved)
      setDirty(false)
    },
  })
  const submit = useMutation({
    mutationFn: async () => {
      if (dirty) await saveApplication(application.id, fields, language)
      return submitApplication(application.id)
    },
    onSuccess: (submitted) => {
      cache.setQueryData(key, submitted)
      void cache.invalidateQueries({ queryKey: applicationsKey })
      setDirty(false)
    },
  })
  const remove = useMutation({
    mutationFn: () => deleteDraft(application.id),
    onSuccess: () => {
      void cache.invalidateQueries({ queryKey: applicationsKey })
      navigate("/account/applications", { replace: true })
    },
  })
  const locked = !application.editable
  const missing = dirty ? [] : application.missing
  function onSubmit(event: FormEvent) {
    event.preventDefault()
    save.mutate()
  }
  return (
    <>
      <form onSubmit={onSubmit} className="mt-10" aria-labelledby="form-title">
        <h2 id="form-title" className="text-2xl font-semibold">
          {t("formTitle")}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">{t("noIdentityNumbers")}</p>
        <fieldset disabled={locked || save.isPending || submit.isPending} className="mt-5 grid gap-4 sm:grid-cols-2">
          {/* Explicit labels: a label wrapped around a select would also read out its options. */}
          <Row id="application-full-name" label={t("full_name")} wide>
            <input id="application-full-name" className={fieldClass} autoComplete="name" maxLength={200} value={fields.full_name ?? ""} onChange={text("full_name")} />
          </Row>
          <Row id="application-birth" label={t("date_of_birth")}>
            <input id="application-birth" className={fieldClass} type="date" autoComplete="bday" min="1900-01-01" value={fields.date_of_birth ?? ""} onChange={text("date_of_birth")} />
          </Row>
          <Row id="application-citizenship" label={t("citizenship")}>
            <input id="application-citizenship" className={fieldClass} autoComplete="country-name" maxLength={100} value={fields.citizenship ?? ""} onChange={text("citizenship")} />
          </Row>
          <Row id="application-phone" label={t("phone")} hint={t("phoneHint")}>
            <input
              id="application-phone"
              className={fieldClass}
              type="tel"
              autoComplete="tel"
              inputMode="tel"
              maxLength={30}
              pattern="\+?[0-9 ()\-]{6,30}"
              aria-describedby="application-phone-hint"
              value={fields.phone ?? ""}
              onChange={text("phone")}
            />
          </Row>
          <Row id="application-education" label={t("education_level")}>
            <select
              id="application-education"
              className={fieldClass}
              value={fields.education_level ?? ""}
              onChange={(event) => update({ education_level: (event.target.value || null) as ApplicationFields["education_level"] })}
            >
              <option value="">{t("choose")}</option>
              {EDUCATION_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {t(`education.${level}`)}
                </option>
              ))}
            </select>
          </Row>
          <Row id="application-graduation" label={t("graduation_year")}>
            <input id="application-graduation" className={fieldClass} type="number" inputMode="numeric" min={1950} max={2100} value={fields.graduation_year ?? ""} onChange={number("graduation_year")} />
          </Row>
          <Row id="application-exam" label={t("exam_total")}>
            <input id="application-exam" className={fieldClass} type="number" inputMode="numeric" min={0} max={150} value={fields.exam_total ?? ""} onChange={number("exam_total")} />
          </Row>
          <div className="flex items-start gap-3 text-sm sm:col-span-2">
            <input id="application-consent" type="checkbox" className="mt-1 h-4 w-4" checked={fields.consent} onChange={(event) => update({ consent: event.target.checked })} />
            <label htmlFor="application-consent">{t("consent")}</label>
          </div>
        </fieldset>
        {!locked && (
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button type="submit" variant="outline" disabled={!dirty || save.isPending}>
              {save.isPending ? t("working") : t("save")}
            </Button>
            <span role="status" className="text-sm text-muted-foreground">
              {save.isSuccess && !dirty ? t("saved") : ""}
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
          <h2 id="submit-title" className="text-2xl font-semibold">
            {t("submitTitle")}
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">{t("submitLead")}</p>
          {missing.length > 0 && (
            <div className="mt-4 text-sm">
              <p>{t("missingTitle")}</p>
              <ul className="mt-1 list-disc pl-5">
                {missing.map((name) => (
                  <li key={name}>
                    {(FIELD_KEYS as readonly string[]).includes(name)
                      ? t(name as (typeof FIELD_KEYS)[number])
                      : t(`missing.${name}` as ApplicationsKey)}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <Button className="mt-5" disabled={missing.length > 0 || submit.isPending} onClick={() => submit.mutate()}>
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
                  <p className="text-sm">{t("confirmDelete")}</p>
                  <div className="flex flex-wrap gap-3">
                    <Button variant="outline" disabled={remove.isPending} onClick={() => remove.mutate()}>
                      {t("deleteDraft")}
                    </Button>
                    <Button variant="ghost" onClick={() => setConfirmDelete(false)}>
                      {t("cancel")}
                    </Button>
                  </div>
                </div>
              ) : (
                <Button variant="ghost" onClick={() => setConfirmDelete(true)}>
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
  const id = Number(useParams().id)
  const application = useQuery({
    queryKey: [...applicationsKey, id],
    queryFn: ({ signal }) => getApplication(id, signal),
    enabled: Boolean(me.data) && Number.isInteger(id),
    staleTime: 0,
    refetchOnWindowFocus: false,
  })

  if (me.isPending) return <p className="mx-auto max-w-3xl px-4 py-12">{t("working")}</p>
  if (isApiError(me.error) && me.error.status === 401) return <Navigate to="/account/login" replace />
  if (isApiError(application.error) && application.error.status === 401) return <Navigate to="/account/login" replace />
  const data = application.data
  if (!data) {
    const error = me.error ?? application.error
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <Link to="/account/applications" className="text-sm underline">
          ← {t("back")}
        </Link>
        <div className="mt-6">
          {application.isPending && me.data ? (
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

  const showNote = data.staff_note && ["needs_changes", "accepted", "rejected"].includes(data.status)
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <Link to="/account/applications" className="text-sm underline">
        ← {t("back")}
      </Link>
      <p className="mt-6 text-xs text-muted-foreground">
        {data.program.program_id} · {t(data.applicant_type)}
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">{programTitle(data.program)}</h1>
      <div className="mt-4 rounded-xl border border-border p-5" role="status" aria-live="polite">
        <StatusBadge status={data.status} />
        <p className="mt-3 text-sm">{t(`help.${data.status}`)}</p>
        {showNote && (
          <div className="mt-4 border-l-2 border-primary pl-4">
            <h2 className="text-sm font-medium">{t("note")}</h2>
            <p className="mt-1 whitespace-pre-wrap break-words text-sm">{data.staff_note}</p>
          </div>
        )}
      </div>
      {!data.editable && <p className="mt-4 text-sm text-muted-foreground">{t("locked")}</p>}
      <Form key={`${data.id}:${data.status}`} application={data} />
    </div>
  )
}
