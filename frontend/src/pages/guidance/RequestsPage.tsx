import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import {
  answerRequest,
  listRequests,
  sendRequest,
  type AdmissionRequest,
} from "@/api/guidance"
import { isApiError } from "@/api/errors"
import { useApplicant } from "@/applicant/session"
import { Button } from "@/components/ui/button"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { Field, fieldClass } from "@/components/guidance/fields"
import { GuidanceShell } from "@/components/guidance/GuidanceShell"
import { randomId } from "@/lib/utils"
import { useStaffT, type StaffKey } from "@/staff/i18n"

// The staff side shows these labels from the staff dictionary, so Kazakh falls back to Russian.
const STAFF_TEXT = {
  answer: "req.answer",
  answered: "req.answered",
  new: "req.new",
  all: "req.all",
  working: "req.working",
  send: "req.send",
  retry: "common.retry",
  empty: "req.empty",
  error: "req.error",
  previous: "req.previous",
  next: "req.next",
} as const satisfies Record<string, StaffKey>

function useRequestT(staff: boolean) {
  const guidanceT = useGuidanceT()
  const staffT = useStaffT()
  return (key: keyof typeof STAFF_TEXT) =>
    staff ? staffT(STAFF_TEXT[key]) : guidanceT(key)
}

function RequestError({ error, staff }: { error: unknown; staff: boolean }) {
  const t = useRequestT(staff)
  return error ? (
    <p role="alert" className="mt-4 text-sm text-destructive">
      {t("error")}
    </p>
  ) : null
}

function RequestCard({
  item,
  staff,
}: {
  item: AdmissionRequest
  staff: boolean
}) {
  const t = useRequestT(staff)
  const { deadline } = useI18n()
  const cache = useQueryClient()
  const [text, setText] = useState("")
  const mutation = useMutation({
    mutationFn: () => answerRequest(item.id, text),
    onSuccess: () =>
      cache.invalidateQueries({ queryKey: ["staff", "requests"] }),
  })
  return (
    <article className="border-2 border-border bg-card p-6">
      <p className="text-xs text-muted-foreground">
        #{item.id} ·{" "}
        {staff ? item.created_at.slice(0, 10) : deadline(item.created_at)} ·{" "}
        {t(item.answer ? "answered" : "new")}
      </p>
      <p className="mt-3 whitespace-pre-wrap break-words" lang={item.language}>
        {item.question}
      </p>
      {item.answer && (
        <div className="mt-4 border-l-2 border-primary pl-4">
          <h2 className="text-sm font-medium">{t("answer")}</h2>
          <p className="mt-2 whitespace-pre-wrap break-words">{item.answer}</p>
        </div>
      )}
      {staff && !item.answer && (
        <form
          className="mt-4"
          onSubmit={(e) => {
            e.preventDefault()
            mutation.mutate()
          }}
        >
          <Field label={t("answer")}>
            <textarea
              className={fieldClass}
              required
              maxLength={6000}
              rows={5}
              value={text}
              disabled={mutation.isPending}
              onChange={(e) => setText(e.target.value)}
            />
          </Field>
          <Button
            className="mt-3"
            disabled={!text.trim() || mutation.isPending}
          >
            {t(mutation.isPending ? "working" : "send")}
          </Button>
          <RequestError error={mutation.error} staff={staff} />
        </form>
      )}
    </article>
  )
}

function RequestsContent({
  staff,
  ownerId,
}: {
  staff: boolean
  ownerId?: number
}) {
  const guidanceT = useGuidanceT()
  const staffT = useStaffT()
  const t = useRequestT(staff)
  const { language } = useI18n()
  const location = useLocation()
  const navigate = useNavigate()
  const [question, setQuestion] = useState("")
  const [key, setKey] = useState(randomId)
  const [status, setStatus] = useState(staff ? "new" : "all")
  const [offset, setOffset] = useState(0)
  const cache = useQueryClient()
  const queryKey = [
    staff ? "staff" : "applicant",
    "requests",
    ownerId,
    status,
    offset,
  ]
  const data = useQuery({
    queryKey,
    queryFn: ({ signal }) => listRequests(staff, status, offset, signal),
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: true,
  })
  const mutation = useMutation({
    mutationFn: () => sendRequest(question, language, key),
    onSuccess: () => {
      setQuestion("")
      setKey(randomId())
      setOffset(0)
      void cache.invalidateQueries({ queryKey: ["applicant", "requests"] })
    },
  })
  const { reset } = mutation
  const prefill: unknown = staff ? undefined : location.state?.question
  const [prefilledFrom, setPrefilledFrom] = useState<string | null>(null)
  if (typeof prefill === "string" && prefilledFrom !== location.key) {
    setPrefilledFrom(location.key)
    setQuestion(prefill.slice(0, 2000))
    setKey(randomId())
  }
  useEffect(() => {
    if (typeof prefill !== "string") return
    reset()
    navigate(location.pathname + location.search, { replace: true, state: null })
  }, [prefill, location.pathname, location.search, navigate, reset])
  return (
    <div>
      {!staff && (
        <form
          className="mb-8 max-w-3xl"
          onSubmit={(e) => {
            e.preventDefault()
            mutation.mutate()
          }}
        >
          <p className="mb-4 text-sm text-muted-foreground">
            {guidanceT("requestNote")}
          </p>
          <Field label={guidanceT("question")}>
            <textarea
              className={fieldClass}
              required
              rows={5}
              maxLength={2000}
              disabled={mutation.isPending}
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value)
                setKey(randomId())
                mutation.reset()
              }}
            />
          </Field>
          <Button
            className="mt-4"
            disabled={!question.trim() || mutation.isPending}
          >
            {t(mutation.isPending ? "working" : "send")}
          </Button>
          <RequestError error={mutation.error} staff={staff} />
          {mutation.isSuccess && (
            <p role="status" className="mt-3">
              {guidanceT("saved")}
            </p>
          )}
        </form>
      )}
      {staff && (
        <Field label={staffT("req.status")}>
          <select
            className={`${fieldClass} mb-5 max-w-xs`}
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              setOffset(0)
            }}
          >
            {(["new", "answered", "all"] as const).map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
      )}
      {data.isPending && <p>{t("working")}</p>}
      {data.isError && (
        <>
          <RequestError error={data.error} staff={staff} />
          <Button className="my-4" onClick={() => void data.refetch()}>
            {t("retry")}
          </Button>
        </>
      )}
      <div className="space-y-4">
        {data.data?.items.map((item) => (
          <RequestCard key={item.id} item={item} staff={staff} />
        ))}
        {data.data?.items.length === 0 && <p>{t("empty")}</p>}
      </div>
      <div className="mt-5 flex gap-3">
        {offset > 0 && (
          <Button variant="outline" onClick={() => setOffset(offset - 30)}>
            {t("previous")}
          </Button>
        )}
        {data.data && offset + 30 < data.data.total && (
          <Button variant="outline" onClick={() => setOffset(offset + 30)}>
            {t("next")}
          </Button>
        )}
      </div>
    </div>
  )
}

export function ApplicantRequestsPage() {
  const location = useLocation()
  const me = useApplicant()
  const t = useGuidanceT()
  return (
    <GuidanceShell title={t("requests")}>
      {me.isPending ? (
        <p>{t("working")}</p>
      ) : me.data ? (
        <RequestsContent key={me.data.id} staff={false} ownerId={me.data.id} />
      ) : isApiError(me.error) && me.error.status === 401 ? (
        <Link
          className="underline"
          to="/account/login?next=%2Faccount%2Frequests"
          state={location.state}
        >
          {t("login")}
        </Link>
      ) : (
        <>
          <p role="alert">
            {t(
              isApiError(me.error) && me.error.code === "ACCOUNTS_UNAVAILABLE"
                ? "privateUnavailable"
                : "error",
            )}
          </p>
          <Button className="mt-4" onClick={() => void me.refetch()}>
            {t("retry")}
          </Button>
        </>
      )}
    </GuidanceShell>
  )
}

export function StaffRequestsPage() {
  const t = useStaffT()
  return (
    <div>
      <h1 className="mb-8 text-[clamp(2.25rem,5vw,3.5rem)] leading-[0.9] font-extrabold uppercase">{t("nav.requests")}</h1>
      <RequestsContent staff />
    </div>
  )
}
