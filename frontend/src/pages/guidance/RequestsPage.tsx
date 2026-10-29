import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link, useLocation } from "react-router-dom"
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
import {
  ErrorMessage,
  Field,
  fieldClass,
  GuidanceShell,
} from "./AdmissionsPages"

function RequestCard({
  item,
  staff,
}: {
  item: AdmissionRequest
  staff: boolean
}) {
  const t = useGuidanceT()
  const cache = useQueryClient()
  const [text, setText] = useState("")
  const mutation = useMutation({
    mutationFn: () => answerRequest(item.id, text),
    onSuccess: () =>
      cache.invalidateQueries({ queryKey: ["staff", "requests"] }),
  })
  return (
    <article className="rounded-xl border border-border p-5">
      <p className="text-xs text-muted-foreground">
        #{item.id} · {item.created_at.slice(0, 10)} ·{" "}
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
          <ErrorMessage error={mutation.error} />
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
  const t = useGuidanceT()
  const { language } = useI18n()
  const location = useLocation()
  const [question, setQuestion] = useState(
    staff || typeof location.state?.question !== "string"
      ? ""
      : location.state.question.slice(0, 2000),
  )
  const [key, setKey] = useState(() => crypto.randomUUID())
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
      setKey(crypto.randomUUID())
      setOffset(0)
      void cache.invalidateQueries({ queryKey: ["applicant", "requests"] })
    },
  })
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
            {t("requestNote")}
          </p>
          <Field label={t("question")}>
            <textarea
              className={fieldClass}
              required
              rows={5}
              maxLength={2000}
              disabled={mutation.isPending}
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value)
                setKey(crypto.randomUUID())
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
          <ErrorMessage error={mutation.error} />
          {mutation.isSuccess && (
            <p role="status" className="mt-3">
              {t("saved")}
            </p>
          )}
        </form>
      )}
      {staff && (
        <Field label={t("requests")}>
          <select
            className={`${fieldClass} mb-5 max-w-xs`}
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              setOffset(0)
            }}
          >
            {["new", "answered", "all"].map((v) => (
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
          <ErrorMessage error={data.error} />
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
  const t = useGuidanceT()
  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">{t("requests")}</h1>
      <RequestsContent staff />
    </div>
  )
}
