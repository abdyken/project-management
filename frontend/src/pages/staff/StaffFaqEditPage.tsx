import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { type FormEvent, useState } from "react"
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom"
import { isApiError, isNotFound } from "@/api/errors"
import { answerInboxGroup, createFaq, type FaqItem, type FaqItemInput, getFaq, setFaqStatus, updateFaq } from "@/api/staff"
import { StatusBadge } from "@/components/staff/StatusBadge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { useStaffT } from "@/staff/i18n"

type Lang = "en" | "ru" | "kk"
type TextField = "question" | "answer" | "source_link" | "evidence"
type Form = Record<`${TextField}${"" | "_ru" | "_kk"}`, string> &
  Pick<FaqItemInput, "category" | "degrees" | "applicant_types">

const LANGS: Lang[] = ["en", "ru", "kk"]
const DEGREES = ["bachelor", "master", "phd"] as const
const APPLICANTS = ["local", "international"] as const
const textareaClass =
  "w-full rounded-md border border-input bg-card px-3 py-2 text-sm outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-ring/20"

function key(field: TextField, lang: Lang) {
  return (lang === "en" ? field : `${field}_${lang}`) as keyof Form & `${TextField}${string}`
}

function toForm(item: Partial<FaqItem>): Form {
  const form = { category: item.category ?? "", degrees: item.degrees ?? [], applicant_types: item.applicant_types ?? [] } as Form
  for (const lang of LANGS) {
    for (const field of ["question", "answer", "source_link", "evidence"] as TextField[]) {
      const name = key(field, lang)
      form[name] = (item[name as keyof FaqItem] as string | null | undefined) ?? ""
    }
  }
  return form
}

function toInput(form: Form): FaqItemInput {
  const nullable = (value: string) => value.trim() || null
  return {
    category: form.category.trim(),
    question: form.question.trim(),
    answer: form.answer.trim(),
    source_link: form.source_link.trim(),
    evidence: nullable(form.evidence),
    question_ru: nullable(form.question_ru),
    answer_ru: nullable(form.answer_ru),
    source_link_ru: nullable(form.source_link_ru),
    evidence_ru: nullable(form.evidence_ru),
    question_kk: nullable(form.question_kk),
    answer_kk: nullable(form.answer_kk),
    source_link_kk: nullable(form.source_link_kk),
    evidence_kk: nullable(form.evidence_kk),
    degrees: form.degrees,
    applicant_types: form.applicant_types,
  }
}

function languageState(form: Form, lang: Lang): "complete" | "empty" | "incomplete" {
  const filled = (["question", "answer", "source_link"] as TextField[]).filter((field) => form[key(field, lang)].trim())
  return filled.length === 3 ? "complete" : filled.length === 0 ? "empty" : "incomplete"
}

export function StaffFaqEditPage() {
  const t = useStaffT()
  const { faqId } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isNew = !faqId
  // Set when the item answers a question from the inbox (US22).
  const inboxKey = params.get("inbox")
  const [tab, setTab] = useState<Lang>("en")
  // Unsaved edits; without them the form shows the saved item (or an empty new one).
  const [draft, setDraft] = useState<Form | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const item = useQuery({
    queryKey: ["staff", "faq", "item", faqId],
    queryFn: ({ signal }) => getFaq(faqId!, signal),
    enabled: !isNew,
  })

  const onSaved = (saved: FaqItem) => {
    queryClient.setQueryData(["staff", "faq", "item", saved.faq_id], saved)
    queryClient.invalidateQueries({ queryKey: ["staff", "faq", "list"] })
    setDraft(null)
    setNotice(t("edit.saved"))
  }

  const save = useMutation({
    mutationFn: (input: FaqItemInput) => (isNew ? createFaq(input) : updateFaq(faqId!, input)),
    onSuccess: (saved) => {
      onSaved(saved)
      if (isNew) {
        const query = inboxKey ? `?${new URLSearchParams({ inbox: inboxKey })}` : ""
        navigate(`/staff/faq/${saved.faq_id}${query}`, { replace: true })
      }
    },
  })

  const changeStatus = useMutation({
    mutationFn: async (action: "publish" | "retire" | "unpublish") => {
      // Publishing must never publish an older text than the one on the screen.
      if (dirty && form) await updateFaq(faqId!, toInput(form))
      const saved = await setFaqStatus(faqId!, action)
      if (action !== "publish" || !inboxKey) return { saved, linkError: null, linked: false }
      try {
        await answerInboxGroup(inboxKey, saved.faq_id)
        return { saved, linkError: null, linked: true }
      } catch (linkError) {
        return { saved, linkError: isApiError(linkError) ? linkError.message : String(linkError), linked: false }
      }
    },
    onSuccess: ({ saved, linkError, linked }) => {
      onSaved(saved)
      if (linked) {
        queryClient.invalidateQueries({ queryKey: ["staff", "inbox"] })
        navigate(`/staff/faq/${saved.faq_id}`, { replace: true })
        setNotice(t("inbox.linked"))
      } else if (linkError) {
        setNotice(t("inbox.linkFailed", { message: linkError }))
      }
    },
  })

  const form = draft ?? (isNew ? toForm({ question: params.get("question") ?? "" }) : item.data ? toForm(item.data) : null)
  const dirty = draft !== null

  if (!isNew && item.isPending) return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
  if (!isNew && item.isError) {
    return (
      <div className="text-sm">
        <p>{isNotFound(item.error) ? t("edit.notFound") : t("common.error")}</p>
        <Link to="/staff/faq" className="mt-3 inline-block underline">
          {t("edit.back")}
        </Link>
      </div>
    )
  }
  if (!form) return null

  const update = (patch: Partial<Form>) => {
    setDraft({ ...form, ...patch })
    setNotice(null)
  }
  const toggle = <V extends string>(list: V[], value: V) => (list.includes(value) ? list.filter((entry) => entry !== value) : [...list, value])

  const incomplete = LANGS.filter((lang) => languageState(form, lang) === "incomplete" && lang !== "en")
  const missing = LANGS.filter((lang) => lang !== "en" && languageState(form, lang) === "empty")
  const englishReady = languageState(form, "en") === "complete" && form.category.trim() !== ""
  const canSave = englishReady && incomplete.length === 0 && !save.isPending && !changeStatus.isPending
  const langName = (lang: Lang) => t(`edit.lang.${lang}`).replace(/\s*\(.*\)$/, "")
  const error = save.error ?? changeStatus.error
  const status = item.data?.status

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (canSave) save.mutate(toInput(form))
  }

  return (
    <form onSubmit={onSubmit} className="max-w-3xl">
      <Link to="/staff/faq" className="text-sm text-muted-foreground hover:text-foreground">
        {t("edit.back")}
      </Link>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">{isNew ? t("edit.newTitle") : faqId}</h1>
        {status && <StatusBadge status={status} />}
      </div>
      {item.data && (
        <p className="mt-1 text-xs text-muted-foreground">
          {item.data.updated_by
            ? t("edit.updatedBy", { date: item.data.last_update, name: item.data.updated_by })
            : t("edit.updatedOn", { date: item.data.last_update })}
        </p>
      )}
      {status && <p className="mt-2 text-sm">{t(`edit.${status}Note`)}</p>}
      {inboxKey && <p className="mt-2 border-l-2 border-gold pl-3 text-sm">{t("inbox.linkTitle")}</p>}

      <div className="mt-6 grid gap-4 sm:grid-cols-[1fr_auto_auto]">
        <label className="block space-y-1.5 text-sm">
          <span>{t("edit.category")}</span>
          <Input value={form.category} onChange={(event) => update({ category: event.target.value })} pattern="[a-z][a-z\-]*" required />
          <span className="block text-xs text-muted-foreground">{t("edit.categoryHint")}</span>
        </label>
        <fieldset className="space-y-1.5 text-sm">
          <legend>{t("edit.degrees")}</legend>
          {DEGREES.map((degree) => (
            <label key={degree} className="flex items-center gap-2">
              <input type="checkbox" checked={form.degrees.includes(degree)} onChange={() => update({ degrees: toggle(form.degrees, degree) })} />
              {t(`edit.degree.${degree}`)}
            </label>
          ))}
        </fieldset>
        <fieldset className="space-y-1.5 text-sm">
          <legend>{t("edit.applicantTypes")}</legend>
          {APPLICANTS.map((type) => (
            <label key={type} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.applicant_types.includes(type)}
                onChange={() => update({ applicant_types: toggle(form.applicant_types, type) })}
              />
              {t(`edit.applicant.${type}`)}
            </label>
          ))}
        </fieldset>
      </div>

      <div role="tablist" className="mt-6 flex border-b border-border text-sm">
        {LANGS.map((lang) => (
          <button
            key={lang}
            type="button"
            role="tab"
            aria-selected={tab === lang}
            onClick={() => setTab(lang)}
            className={cn(
              "-mb-px border-b-2 px-3 py-2",
              tab === lang ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t(`edit.lang.${lang}`)}
            {languageState(form, lang) === "incomplete" && <span className="ml-1 text-destructive">•</span>}
          </button>
        ))}
      </div>

      <div role="tabpanel" className="mt-4 space-y-4">
        <label className="block space-y-1.5 text-sm">
          <span>{t("edit.question")}</span>
          <Input value={form[key("question", tab)]} onChange={(event) => update({ [key("question", tab)]: event.target.value })} />
        </label>
        <label className="block space-y-1.5 text-sm">
          <span>{t("edit.answer")}</span>
          <textarea
            rows={6}
            className={textareaClass}
            value={form[key("answer", tab)]}
            onChange={(event) => update({ [key("answer", tab)]: event.target.value })}
          />
        </label>
        <label className="block space-y-1.5 text-sm">
          <span>{t("edit.sourceLink")}</span>
          <Input
            type="url"
            value={form[key("source_link", tab)]}
            onChange={(event) => update({ [key("source_link", tab)]: event.target.value })}
          />
        </label>
        <label className="block space-y-1.5 text-sm">
          <span>{t("edit.evidence")}</span>
          <textarea
            rows={3}
            className={textareaClass}
            value={form[key("evidence", tab)]}
            onChange={(event) => update({ [key("evidence", tab)]: event.target.value })}
          />
        </label>
      </div>

      <div className="mt-4 space-y-1 text-sm">
        {incomplete.map((lang) => (
          <p key={lang} role="alert" className="text-destructive">
            {t("edit.incompleteLanguage", { language: langName(lang) })}
          </p>
        ))}
        {missing.map((lang) => (
          <p key={lang} className="text-muted-foreground">
            {t("edit.missingLanguage", { language: langName(lang) })}
          </p>
        ))}
        {error && (
          <p role="alert" className="text-destructive">
            {t("edit.error", { message: isApiError(error) ? error.message : String(error) })}
          </p>
        )}
        {notice && !dirty && <p role="status">{notice}</p>}
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button type="submit" disabled={!canSave || (!isNew && !dirty)}>
          {save.isPending ? t("edit.saving") : isNew ? t("edit.saveDraft") : t("edit.save")}
        </Button>
        {!isNew && status !== "published" && (
          <Button type="button" variant="gold" disabled={!canSave} onClick={() => changeStatus.mutate("publish")}>
            {t("edit.publish")}
          </Button>
        )}
        {!isNew && status === "published" && (
          <Button type="button" variant="outline" disabled={changeStatus.isPending} onClick={() => changeStatus.mutate("unpublish")}>
            {t("edit.unpublish")}
          </Button>
        )}
        {!isNew && status !== "retired" && (
          <Button type="button" variant="outline" disabled={changeStatus.isPending} onClick={() => changeStatus.mutate("retire")}>
            {t("edit.retire")}
          </Button>
        )}
      </div>
    </form>
  )
}
