import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import {
  checklistPath,
  deleteApplicant,
  getSavedPrograms,
  logoutApplicant,
  removeProgram,
  setPrepared,
  updatePreferences,
  type Applicant,
  type SavedChecklist,
} from "@/api/applicant"
import { isApiError } from "@/api/errors"
import { useApplicantT } from "@/applicant/i18n"
import { APPLICANT_KEY, APPLICANT_ME_KEY, SAVED_PROGRAMS_KEY, useApplicant } from "@/applicant/session"
import { ChecklistPdfButton } from "@/components/catalog/ChecklistPdfButton"
import { requirementNotes } from "@/lib/checklist"
import { ConnectionError } from "@/components/common/ConnectionError"
import { Button } from "@/components/ui/button"
import { LANGUAGES, useI18n, type Language } from "@/i18n"
import { useGuidanceT } from "@/guidance/i18n"

function SavedProgram({ checklist }: { checklist: SavedChecklist }) {
  const t = useApplicantT()
  const { t: portalT, language, programTitle, deadline } = useI18n()
  const cache = useQueryClient()
  const refresh = () => {
    void cache.invalidateQueries({ queryKey: SAVED_PROGRAMS_KEY })
  }
  const program = checklist.program
  const [pendingDocument, setPendingDocument] = useState<{ id: number; prepared: boolean } | null>(null)
  const progress = useMutation({
    mutationFn: ({ id, prepared }: { id: number; prepared: boolean }) =>
      setPrepared(program.program_id, checklist.applicant_type, id, prepared),
    onSuccess: (updated) =>
      cache.setQueryData<{ items: SavedChecklist[] }>(
        SAVED_PROGRAMS_KEY,
        (current) =>
          current && {
            items: current.items.map((item) =>
              item.program.program_id === program.program_id &&
              item.applicant_type === checklist.applicant_type
                ? updated
                : item,
            ),
          },
      ),
    onError: refresh,
    onSettled: () => setPendingDocument(null),
  })
  const remove = useMutation({
    mutationFn: () => removeProgram(program.program_id, checklist.applicant_type),
    onSuccess: refresh,
  })
  return (
    <article className="rounded-xl border border-border p-5 sm:p-6">
      <p className="text-xs text-muted-foreground">
        {program.program_id} · {t(checklist.applicant_type)}
      </p>
      <h2 className="mt-2 text-2xl font-semibold">
        <Link
          to={`/programs/${encodeURIComponent(program.program_id)}?applicant=${checklist.applicant_type}`}
          className="hover:underline"
        >
          {programTitle(program)}
        </Link>
      </h2>
      <p className="mt-2 text-sm">
        {portalT("detail.deadline")}: {deadline(program[`deadline_${checklist.applicant_type}`])}
      </p>
      {!program.is_active && (
        <p role="status" className="mt-3 text-sm">
          {t("archived")}
        </p>
      )}
      <p className="mt-5 text-sm" aria-live="polite">
        {t("progress", { prepared: checklist.prepared, total: checklist.total })}
      </p>
      {checklist.total > 0 && (
        <progress
          className="mt-2 h-2 w-full accent-primary"
          value={checklist.prepared}
          max={checklist.total}
          aria-label={t("progress", { prepared: checklist.prepared, total: checklist.total })}
        />
      )}
      {checklist.warning && (
        <p role="status" className="mt-4 text-sm">
          {t("noDocuments")} {checklist.contact}
        </p>
      )}
      <ul className="mt-4 divide-y divide-border">
        {checklist.items.map((item) => (
          <li key={item.id} className="py-4">
            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                className="mt-1 size-4 shrink-0 accent-primary"
                checked={pendingDocument?.id === item.id ? pendingDocument.prepared : item.prepared}
                disabled={progress.isPending || !program.is_active}
                onChange={(event) => {
                  const change = { id: item.id, prepared: event.target.checked }
                  setPendingDocument(change)
                  progress.mutate(change)
                }}
              />
              <span className="min-w-0 text-sm">
                <span lang="en">{item.name}</span>
                <span className="mt-1 block text-xs text-muted-foreground">
                  {requirementNotes(item, portalT)}
                  {" · "}
                  {portalT("checklist.deadline")}: <span lang="en">{item.deadline}</span>
                </span>
              </span>
            </label>
          </li>
        ))}
      </ul>
      {(progress.isError || remove.isError) && (
        <p role="alert" className="mt-3 text-sm text-destructive">
          {t("error")}
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-3">
        <ChecklistPdfButton
          path={`${checklistPath(program.program_id, checklist.applicant_type)}/pdf?language=${language}`}
        />
        <Button
          variant="ghost"
          disabled={remove.isPending || progress.isPending}
          onClick={() => remove.mutate()}
        >
          {t("remove")}
        </Button>
      </div>
    </article>
  )
}

function Preferences({ user }: { user: Applicant }) {
  const t = useApplicantT()
  const cache = useQueryClient()
  const [language, setLanguage] = useState<Language>(user.language)
  const [enabled, setEnabled] = useState(user.reminders_enabled)
  const preferences = useMutation({
    mutationFn: () => updatePreferences({ language, reminders_enabled: enabled }),
    onSuccess: (result) => cache.setQueryData(APPLICANT_ME_KEY, result),
  })
  return (
    <form
      className="mt-10 space-y-4 rounded-xl border border-border p-5"
      onSubmit={(event) => {
        event.preventDefault()
        preferences.mutate()
      }}
    >
      <label className="flex items-start gap-3 text-sm">
        <input
          className="mt-1 size-4 accent-primary"
          type="checkbox"
          checked={enabled}
          onChange={(event) => setEnabled(event.target.checked)}
        />
        <span>{t("reminders")}</span>
      </label>
      <p className="text-xs leading-relaxed text-muted-foreground">{t("remindersNote")}</p>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <label htmlFor="reminder-language">{t("language")}</label>
        <select
          id="reminder-language"
          className="rounded-md border border-border bg-background p-2"
          value={language}
          onChange={(event) => setLanguage(event.target.value as Language)}
        >
          {LANGUAGES.map((item) => (
            <option value={item.code} key={item.code}>
              {item.label}
            </option>
          ))}
        </select>
      </div>
      <Button variant="outline" type="submit" disabled={preferences.isPending}>
        {preferences.isPending ? t("working") : t("savePreferences")}
      </Button>
      {preferences.isSuccess && (
        <p role="status" className="text-sm">
          {t("preferencesSaved")}
        </p>
      )}
      {preferences.isError && (
        <p role="alert" className="text-sm text-destructive">
          {t("error")}
        </p>
      )}
    </form>
  )
}

export function ApplicantAccountPage() {
  const guidanceT = useGuidanceT()
  const t = useApplicantT()
  const me = useApplicant()
  const cache = useQueryClient()
  const navigate = useNavigate()
  const [confirmDelete, setConfirmDelete] = useState(false)
  const saved = useQuery({
    queryKey: SAVED_PROGRAMS_KEY,
    queryFn: ({ signal }) => getSavedPrograms(signal),
    enabled: Boolean(me.data),
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: true,
  })
  const clear = async () => {
    await cache.cancelQueries({ queryKey: APPLICANT_KEY })
    cache.removeQueries({ queryKey: APPLICANT_KEY })
    navigate("/account/login", { replace: true })
  }
  const logout = useMutation({ mutationFn: logoutApplicant, onSuccess: clear })
  const deletion = useMutation({ mutationFn: deleteApplicant, onSuccess: clear })

  if (me.isPending) return <p className="mx-auto max-w-5xl px-4 py-12">{t("working")}</p>
  if (
    (isApiError(me.error) && me.error.status === 401) ||
    (isApiError(saved.error) && saved.error.status === 401)
  )
    return <Navigate to="/account/login" replace />
  if (!me.data)
    return (
      <div className="mx-auto max-w-5xl px-4 py-12">
        <ConnectionError
          message={
            isApiError(me.error) && me.error.code === "ACCOUNTS_UNAVAILABLE" ? t("unavailable") : t("error")
          }
          onRetry={() => void me.refetch()}
          retrying={me.isFetching}
        />
      </div>
    )

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{t("account")}</h1>
          <p className="mt-2 break-all text-sm text-muted-foreground">{me.data.email}</p>
        </div>
        <Button
          variant="outline"
          disabled={logout.isPending || deletion.isPending}
          onClick={() => logout.mutate()}
        >
          {t("logout")}
        </Button>
      </div>
      {(logout.isError || deletion.isError) && (
        <p role="alert" className="mt-4 text-sm text-destructive">
          {t("error")}
        </p>
      )}
      <Link className="mt-6 inline-block underline" to="/account/requests">{guidanceT("requests")}</Link>
      <h2 className="mt-10 text-2xl font-semibold">{t("saved")}</h2>
      <Link className="mt-3 inline-block text-sm underline" to="/programs">
        {t("browse")}
      </Link>
      {saved.isPending && <p className="mt-6">{t("working")}</p>}
      {saved.isError && (
        <div className="mt-6">
          <ConnectionError
            message={t("error")}
            onRetry={() => void saved.refetch()}
            retrying={saved.isFetching}
          />
        </div>
      )}
      {saved.data?.items.length === 0 && <p className="mt-6 text-sm text-muted-foreground">{t("empty")}</p>}
      <div className="mt-6 space-y-6">
        {saved.data?.items.map((item) => (
          <SavedProgram key={`${item.program.program_id}:${item.applicant_type}`} checklist={item} />
        ))}
      </div>
      <Preferences key={me.data.id} user={me.data} />
      <p className="mt-8 text-xs leading-relaxed text-muted-foreground">{t("privacy")}</p>
      <div className="mt-8 border-t border-border pt-6">
        {confirmDelete ? (
          <>
            <p className="mb-4 text-sm">{t("deleteLead")}</p>
            <div className="flex flex-wrap gap-3">
              <Button disabled={deletion.isPending} onClick={() => deletion.mutate()}>
                {t("confirmDelete")}
              </Button>
              <Button variant="ghost" disabled={deletion.isPending} onClick={() => setConfirmDelete(false)}>
                {t("cancel")}
              </Button>
            </div>
          </>
        ) : (
          <Button variant="ghost" onClick={() => setConfirmDelete(true)}>
            {t("delete")}
          </Button>
        )}
      </div>
    </div>
  )
}
