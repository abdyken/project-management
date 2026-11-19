import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState, type FormEvent } from "react"
import { Link, useParams } from "react-router-dom"
import {
  documentUrl,
  getStaffApplication,
  setApplicationStatus,
  type ApplicationStatus,
  type StaffApplication,
  type StaffStatusChange,
} from "@/api/applications"
import { StatusBadge } from "@/components/applications/StatusBadge"
import { fieldClass } from "@/components/guidance/fields"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { fileSize } from "@/lib/files"
import { staffErrorKey, useStaffT, type StaffKey } from "@/staff/i18n"
import { selectClass } from "@/staff/styles"

// Same rules as the API (ADR 0002).
const NEXT: Partial<Record<ApplicationStatus, StaffStatusChange[]>> = {
  submitted: ["in_review", "needs_changes", "accepted", "rejected"],
  in_review: ["needs_changes", "accepted", "rejected"],
}
const NOTE_REQUIRED: StaffStatusChange[] = ["needs_changes", "rejected"]
const FIELDS = ["full_name", "date_of_birth", "citizenship", "phone", "education_level", "graduation_year", "exam_total"] as const

function Decide({ application }: { application: StaffApplication }) {
  const t = useStaffT()
  const cache = useQueryClient()
  const options = NEXT[application.status] ?? []
  const [status, setStatus] = useState<StaffStatusChange>(options[0] ?? "in_review")
  const [note, setNote] = useState("")
  const change = useMutation({
    mutationFn: () => setApplicationStatus(application.id, status, note),
    onSuccess: (updated) => {
      cache.setQueryData(["staff", "applications", "detail", application.id], updated)
      void cache.invalidateQueries({ queryKey: ["staff", "applications"], exact: false })
      setNote("")
    },
  })
  if (options.length === 0) return <p className="mt-8 text-sm text-muted-foreground">{t("app.closed")}</p>
  const needsNote = NOTE_REQUIRED.includes(status) && !note.trim()
  function onSubmit(event: FormEvent) {
    event.preventDefault()
    change.mutate()
  }
  return (
    <form onSubmit={onSubmit} className="mt-10 max-w-2xl border-t border-border pt-6" aria-labelledby="decide-title">
      <h2 id="decide-title" className="text-lg font-semibold">
        {t("app.decide")}
      </h2>
      <div className="mt-4 space-y-1 text-sm">
        <label htmlFor="application-status" className="block">
          {t("app.newStatus")}
        </label>
        <select id="application-status" className={selectClass} value={status} onChange={(event) => setStatus(event.target.value as StaffStatusChange)}>
          {options.map((value) => (
            <option key={value} value={value}>
              {t(`app.status.${value}`)}
            </option>
          ))}
        </select>
      </div>
      <div className="mt-4 space-y-1 text-sm">
        <label htmlFor="application-note" className="block">
          {t("app.note")}
        </label>
        <textarea
          id="application-note"
          className={fieldClass}
          rows={4}
          maxLength={2000}
          aria-describedby="application-note-hint"
          required={NOTE_REQUIRED.includes(status)}
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
        <p id="application-note-hint" className="text-xs text-muted-foreground">
          {t("app.noteHint")}
        </p>
      </div>
      <Button className="mt-4" disabled={needsNote || change.isPending}>
        {change.isPending ? t("app.saving") : t("app.save")}
      </Button>
      {change.isError && (
        <p role="alert" className="mt-3 text-sm text-destructive">
          {t(staffErrorKey(change.error))}
        </p>
      )}
    </form>
  )
}

function value(t: ReturnType<typeof useStaffT>, application: StaffApplication, field: (typeof FIELDS)[number]) {
  const raw = application[field]
  if (raw === null || raw === "") return t("app.empty.value")
  if (field === "education_level") return t(`app.edu.${raw}` as StaffKey)
  return String(raw)
}

export function StaffApplicationPage() {
  const t = useStaffT()
  const { programTitle } = useI18n()
  const id = Number(useParams().applicationId)
  const query = useQuery({
    queryKey: ["staff", "applications", "detail", id],
    queryFn: ({ signal }) => getStaffApplication(id, signal),
    enabled: Number.isInteger(id),
    staleTime: 0,
  })
  const application = query.data
  if (!application) {
    return (
      <div>
        <Link to="/staff/applications" className="text-sm underline">
          ← {t("app.back")}
        </Link>
        {query.isPending ? (
          <p className="mt-6 text-sm">{t("common.loading")}</p>
        ) : (
          <p role="alert" className="mt-6 text-sm text-destructive">
            {t(staffErrorKey(query.error))}
          </p>
        )}
      </div>
    )
  }
  const requirementIds = new Set(application.requirements.map((item) => item.id))
  const groups = [
    ...application.requirements.map((requirement) => ({
      key: String(requirement.id),
      name: requirement.name,
      documents: application.documents.filter((document) => document.requirement_id === requirement.id),
    })),
    {
      key: "other",
      name: t("app.docs.other"),
      documents: application.documents.filter((document) => document.requirement_id === null || !requirementIds.has(document.requirement_id)),
    },
  ].filter((group) => group.documents.length > 0)

  return (
    <div>
      <Link to="/staff/applications" className="text-sm underline">
        ← {t("app.back")}
      </Link>
      <p className="mt-6 text-xs text-muted-foreground">
        #{application.id} · {application.program.program_id} · {t(`app.type.${application.applicant_type}`)}
      </p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight">{application.full_name ?? application.applicant_email}</h1>
      <p className="text-muted-foreground">{programTitle(application.program)}</p>
      <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
        <StatusBadge status={application.status} label={t(`app.status.${application.status}`)} />
        {application.submitted_at && <span className="text-muted-foreground">{t("app.submitted", { date: application.submitted_at.slice(0, 10) })}</span>}
      </div>
      {application.staff_note && (
        <div className="mt-4 max-w-2xl border-l-2 border-primary pl-4 text-sm">
          <p className="font-medium">{t("app.currentNote")}</p>
          <p className="mt-1 whitespace-pre-wrap break-words">{application.staff_note}</p>
        </div>
      )}

      <h2 className="mt-8 text-lg font-semibold">{t("app.form")}</h2>
      <dl className="mt-3 grid max-w-2xl gap-x-6 gap-y-2 text-sm sm:grid-cols-[14rem_1fr]">
        <dt className="text-muted-foreground">{t("app.field.email")}</dt>
        <dd className="break-all">{application.applicant_email}</dd>
        {FIELDS.map((field) => (
          <div key={field} className="contents">
            <dt className="text-muted-foreground">{t(`app.field.${field}`)}</dt>
            <dd className="break-words">{value(t, application, field)}</dd>
          </div>
        ))}
        <dt className="text-muted-foreground">{t("app.field.consent")}</dt>
        <dd>{t(application.consent ? "app.yes" : "app.no")}</dd>
      </dl>

      <h2 className="mt-8 text-lg font-semibold">{t("app.docs")}</h2>
      {groups.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">{t("app.docs.none")}</p>
      ) : (
        <ul className="mt-3 max-w-2xl space-y-3 text-sm">
          {groups.map((group) => (
            <li key={group.key}>
              <p className="font-medium">{group.name}</p>
              <ul className="mt-1 space-y-1">
                {group.documents.map((document) => (
                  <li key={document.id} className="flex flex-wrap gap-x-3">
                    <span className="break-all">{document.original_name}</span>
                    <span className="text-xs text-muted-foreground">{fileSize(document.size_bytes)}</span>
                    <a
                      className="underline"
                      href={documentUrl(application.id, document.id, true)}
                      download={document.original_name}
                      aria-label={`${t("app.download")}: ${document.original_name}`}
                    >
                      {t("app.download")}
                    </a>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
      <Decide key={application.status} application={application} />
    </div>
  )
}
