import { ArrowRight } from "lucide-react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import {
  SUBJECT_PAIRS,
  checkEligibility,
  estimateCost,
  getFunding,
  getGuidance,
  recommendPrograms,
  type CostInput,
  type Eligibility,
  type Metric,
  type Profile,
} from "@/api/guidance"
import { allProgramsQuery } from "@/api/programs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useGuidanceT } from "@/guidance/i18n"
import { useI18n } from "@/i18n"
import { useInfoT } from "@/info/i18n"
import { ErrorMessage, Field, fieldClass } from "@/components/guidance/fields"
import { GuidanceShell } from "@/components/guidance/GuidanceShell"
import { ConditionText, EvidenceView } from "@/components/guidance/rules"
import { GUIDANCE_ROUTES } from "@/guidance/routes"
import { useRevealList } from "@/lib/motion"

function SubmitHint({ id, text }: { id: string; text: string | null }) {
  return text ? (
    <p id={id} className="mt-2 text-sm text-muted-foreground">
      {text}
    </p>
  ) : null
}

const HUB_TILES = [
  { key: "eligibility", text: "eligibilityText" },
  { key: "recommendations", text: "recommendationsText" },
  { key: "cost", text: "costText" },
  { key: "funding", text: "fundingText" },
  { key: "requests", text: "requestsText" },
] as const

function HubRow({ to, title, text, fact }: { to: string; title: string; text: string; fact?: string }) {
  return (
    <li className="border-b border-border">
      <Link to={to} className="group grid grid-cols-[minmax(0,1fr)_1.25rem] items-start gap-4 py-5 transition-colors hover:bg-secondary/60 sm:-mx-2 sm:px-2">
        <span className="min-w-0">
          <span className="block font-heading text-[1.375rem] leading-[1.2] font-medium group-hover:text-primary">{title}</span>
          <span className="mt-1 block max-w-[60ch] text-muted-foreground">{text}</span>
          {fact ? <span className="label tabular mt-3 block text-primary">{fact}</span> : null}
        </span>
        <ArrowRight className="mt-1.5 size-5 text-primary transition-transform duration-200 group-hover:translate-x-[3px]" aria-hidden="true" />
      </Link>
    </li>
  )
}

export function AdmissionsPage() {
  const t = useGuidanceT()
  const infoT = useInfoT()
  const { t: appT, degree, deadlineWithStatus, language } = useI18n()
  const routes = Object.fromEntries(GUIDANCE_ROUTES)
  const hubRef = useRef<HTMLUListElement>(null)
  const photoRef = useRef<HTMLElement>(null)
  useRevealList(hubRef)
  useRevealList(photoRef)
  const catalogue = useQuery(allProgramsQuery)
  const programs = catalogue.data?.programs ?? []
  const bachelors = programs.filter((program) => program.degree_level === "bachelor")
  const bachelorDeadline = bachelors.find((program) => program.deadline_local)?.deadline_local ?? null
  const fees = bachelors.map((program) => program.tuition_per_ects_kzt).filter((fee): fee is number => fee !== null)
  const numbers = new Intl.NumberFormat(language === "en" ? "en-GB" : "ru-RU")
  // One deciding fact per tool, from the live catalogue; nothing when it is not loaded.
  const facts: Partial<Record<(typeof HUB_TILES)[number]["key"], string>> = catalogue.data
    ? {
        eligibility: bachelorDeadline ? `${degree("bachelor")} · ${deadlineWithStatus(bachelorDeadline)}` : undefined,
        recommendations: appT("home.path.count", { count: numbers.format(programs.length) }),
        cost: fees.length ? appT("format.range", { min: `${numbers.format(Math.min(...fees))}\u00a0₸`, max: `${numbers.format(Math.max(...fees))}\u00a0₸` }) : undefined,
      }
    : {}
  return (
    <GuidanceShell title={t("hub")} lead={t("lead")}>
      {/* Tools as a ruled list beside one campus photograph; the tile grid is kept for the home page. */}
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)] lg:gap-16">
        <figure ref={photoRef} data-reveal="photo" className="m-0 overflow-hidden">
          <img
            src="/images/sdu/campus-facade-960.webp"
            srcSet="/images/sdu/campus-facade-480.webp 480w, /images/sdu/campus-facade-960.webp 960w, /images/sdu/campus-facade-1440.webp 1440w"
            sizes="(min-width: 1024px) 35vw, 100vw"
            alt=""
            width={960}
            height={720}
            className="aspect-[4/3] w-full object-cover object-[50%_30%]"
          />
        </figure>
        <div>
          <ul data-reveal-list="" ref={hubRef} className="border-t-2 border-ink">
            {HUB_TILES.map((tile) => (
              <HubRow key={tile.key} to={routes[tile.key]} title={t(tile.key)} text={t(tile.text)} fact={facts[tile.key]} />
            ))}
          </ul>
          <h2 className="mt-14 text-[clamp(1.5rem,2vw,1.875rem)] leading-[1.15] font-medium">{infoT("hub.applyTitle")}</h2>
          <ul className="mt-5 border-t-2 border-ink">
            <HubRow to="/apply" title={infoT("apply.title")} text={infoT("apply.lead")} />
            <HubRow to="/deadlines" title={infoT("deadlines.title")} text={infoT("deadlines.lead")} />
            <HubRow to="/application-status" title={infoT("status.title")} text={infoT("status.lead")} />
            <HubRow to="/contact" title={infoT("contact.title")} text={infoT("contact.lead")} />
          </ul>
        </div>
      </div>
    </GuidanceShell>
  )
}

export function GapList({ gaps }: { gaps: string[] }) {
  const t = useGuidanceT()
  return gaps.length > 0 ? (
    <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
      {[...new Set(gaps)].map((gap, index) => (
        <li key={index}>{t.code(gap)}</li>
      ))}
    </ul>
  ) : null
}
export function EligibilityResult({ result }: { result: Eligibility }) {
  const t = useGuidanceT()
  return (
    <section
      aria-live="polite"
      className="mt-8 border-2 border-border bg-card p-6"
    >
      <h2 className="text-xl font-medium">{t(result.status)}</h2>
      <p className="mt-2 text-sm text-muted-foreground">{t("disclaimer")}</p>
      <GapList gaps={result.gaps} />
      <ul className="mt-4 divide-y divide-border">
        {result.checks.map((check, index) => (
          <li className="py-4" key={index}>
            <h3 className="font-medium">
              {t.code(check.key)} · {t(check.status)}
            </h3>
            <div className="mt-2 space-y-1 text-sm">
              {check.alternatives.map((group, gi) => (
                <p key={gi}>
                  {gi > 0 && <strong>{t("or")} </strong>}
                  {group.map((condition, ci) => (
                    <span key={ci}>
                      {ci > 0 && ` ${t("and")} `}
                      <ConditionText condition={condition} />
                    </span>
                  ))}
                </p>
              ))}
            </div>
            <EvidenceView evidence={check.evidence} />
          </li>
        ))}
      </ul>
    </section>
  )
}

function ProfileFields({
  value,
  onChange,
  degree,
  needed,
}: {
  value: Profile
  onChange: (p: Profile) => void
  degree: string
  // Metrics the chosen program's published rules use; only those fields are asked for.
  needed?: Set<Metric>
}) {
  const t = useGuidanceT()
  const asks = (key: Metric) => !needed || needed.has(key) || (key === "ielts_component_min" && needed.has("ielts_overall"))
  const change = (key: keyof Profile, next: string | null) =>
    onChange({ ...value, [key]: next })
  const metrics: [Metric, number, number][] = [
    ["unt_total", 140, 1],
    ["ct_total", 150, 1],
    ["gpa", 4, 0.01],
    ["ielts_overall", 9, 0.5],
    ["ielts_component_min", 9, 0.5],
  ]
  if (degree === "phd")
    metrics.push(
      ["phd_total", 100, 1],
      ["toefl_ibt", 120, 1],
      ["toefl_pbt", 677, 1],
      ["toeic", 990, 1],
      ["duolingo", 160, 1],
      ["work_months", 1000, 1],
    )
  return (
    <>
      <p className="my-4 text-sm text-muted-foreground">{t("optional")}</p>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={t("applicant_type")}>
          <select
            className={fieldClass}
            value={value.applicant_type}
            onChange={(e) => change("applicant_type", e.target.value)}
          >
            {(["local", "international"] as const).map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
        <Field label={t("education_route")}>
          <select
            className={fieldClass}
            value={value.education_route}
            onChange={(e) => change("education_route", e.target.value)}
          >
            {(["school", "college", "bachelor", "master"] as const).map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
        <Field label={t("admission_basis")}>
          <select
            className={fieldClass}
            value={value.admission_basis}
            onChange={(e) => change("admission_basis", e.target.value)}
          >
            {(["paid", "grant"] as const).map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
        {degree === "master" && (
          <Field label={t("track")}>
            <select
              className={fieldClass}
              value={value.track ?? ""}
              onChange={(e) => change("track", e.target.value || null)}
            >
              <option value="">{t("unknown")}</option>
              {(["scientific", "profile"] as const).map((v) => (
                <option key={v} value={v}>
                  {t(v)}
                </option>
              ))}
            </select>
          </Field>
        )}
        {metrics
          .filter(([key]) => key !== "unt_total" || degree === "bachelor")
          .filter(([key]) => key !== "ct_total" || degree === "master")
          .filter(([key]) => asks(key))
          .map(([key, max, step]) => (
            <Field key={key} label={t(key)}>
              <Input
                type="number"
                min={0}
                max={max}
                step={step}
                value={String(value.scores[key] ?? "")}
                onChange={(e) =>
                  onChange({
                    ...value,
                    scores: {
                      ...value.scores,
                      [key]:
                        e.target.value === "" ? null : Number(e.target.value),
                    },
                  })
                }
              />
            </Field>
          ))}
        {degree === "bachelor" && asks("subject_pair") && (
          <Field label={t("subject_pair")}>
            <select
              className={fieldClass}
              value={String(value.scores.subject_pair ?? "")}
              onChange={(e) =>
                onChange({
                  ...value,
                  scores: {
                    ...value.scores,
                    subject_pair: e.target.value || null,
                  },
                })
              }
            >
              <option value="">{t("unknown")}</option>
              {SUBJECT_PAIRS.map((pair) => (
                <option key={pair} value={pair}>
                  {t(pair)}
                </option>
              ))}
            </select>
          </Field>
        )}
        {(
          [
            "sdu_english",
            "interview",
            "special_exam",
            "creative_exam",
            ...(degree === "phd" ? ["kaztest"] : []),
          ] as Metric[]
        ).filter(asks).map((key) => (
          <Field label={t(key)} key={key}>
            <select
              className={fieldClass}
              value={value.scores[key] == null ? "" : String(value.scores[key])}
              onChange={(e) =>
                onChange({
                  ...value,
                  scores: {
                    ...value.scores,
                    [key]:
                      e.target.value === "" ? null : e.target.value === "true",
                  },
                })
              }
            >
              <option value="">{t("unknown")}</option>
              <option value="true">{t("yes")}</option>
              <option value="false">{t("no")}</option>
            </select>
          </Field>
        ))}
      </div>
    </>
  )
}

function useProfile() {
  const { language } = useI18n()
  const [profile, setProfile] = useState<Profile>({
    applicant_type: "local",
    education_route: "school",
    admission_basis: "paid",
    track: null,
    scores: {},
    language,
  })
  return [{ ...profile, language }, setProfile] as const
}

function ProgramSelect({
  value,
  onChange,
}: {
  value: string
  onChange: (v: string) => void
}) {
  const programs = useQuery(allProgramsQuery)
  const { programTitle } = useI18n()
  const t = useGuidanceT()
  return (
    <div>
      <Field label={t("program")}>
        <select
          required
          className={fieldClass}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          <option value="">{t("choose")}</option>
          {programs.data?.programs.map((p) => (
            <option key={p.program_id} value={p.program_id}>
              {p.program_id} · {programTitle(p)}
            </option>
          ))}
        </select>
      </Field>
      {programs.isPending && <p role="status">{t("working")}</p>}
      {programs.isError && (
        <>
          <ErrorMessage error={programs.error} />
          <Button
            variant="outline"
            type="button"
            className="mt-2"
            onClick={() => void programs.refetch()}
          >
            {t("retry")}
          </Button>
        </>
      )}
    </div>
  )
}

export function EligibilityPage() {
  const [params] = useSearchParams()
  const [program, setProgram] = useState(params.get("program") ?? "")
  const [profile, setProfile] = useProfile()
  const programs = useQuery(allProgramsQuery)
  const degree =
    programs.data?.programs.find((p) => p.program_id === program)
      ?.degree_level ?? "bachelor"
  useEffect(() => {
    if (degree !== "bachelor")
      setProfile((p) => ({
        ...p,
        education_route: degree === "master" ? "bachelor" : "master",
      }))
  }, [degree, setProfile])
  const t = useGuidanceT()
  const mutation = useMutation({
    mutationFn: () => checkEligibility({ ...profile, program_id: program }),
  })
  // The program comes first; then only the fields its published rules use are shown.
  const guidance = useQuery({
    queryKey: ["guidance", program],
    queryFn: ({ signal }) => getGuidance(program, false, signal),
    enabled: Boolean(program),
  })
  const needed = guidance.data?.rules.length
    ? new Set(guidance.data.rules.flatMap((rule) => rule.alternatives.flat().map((condition) => condition.metric)))
    : undefined
  const setSelected = (id: string) => {
    setProgram(id)
    const d = programs.data?.programs.find(
      (p) => p.program_id === id,
    )?.degree_level
    setProfile({
      ...profile,
      education_route:
        d === "master" ? "bachelor" : d === "phd" ? "master" : "school",
      track: null,
    })
    mutation.reset()
  }
  return (
    <GuidanceShell title={t("eligibility")}>
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-14">
        <form
          className="min-w-0"
          onSubmit={(e) => {
            e.preventDefault()
            mutation.mutate()
          }}
        >
          <ProgramSelect value={program} onChange={setSelected} />
          {program ? (
            <>
              <ProfileFields
                degree={degree}
                needed={needed}
                value={profile}
                onChange={(p) => {
                  setProfile(p)
                  mutation.reset()
                }}
              />
              <Button className="mt-6" disabled={mutation.isPending}>
                {t(mutation.isPending ? "working" : "submit")}
              </Button>
            </>
          ) : (
            <SubmitHint id="eligibility-hint" text={t("needProgram")} />
          )}
        </form>
        <div className="min-w-0 lg:sticky lg:top-6 lg:self-start [&>section]:lg:mt-0">
          <ErrorMessage error={mutation.error} />
          {mutation.data ? (
            <EligibilityResult result={mutation.data} />
          ) : (
            <div className="border-t-2 border-ink pt-5 text-muted-foreground">
              <p className="font-heading text-xl font-medium text-foreground">{t("eligibility")}</p>
              <p className="mt-2">{t("eligibilityText")}</p>
              <p className="mt-3 text-sm">{t("disclaimer")}</p>
            </div>
          )}
        </div>
      </div>
    </GuidanceShell>
  )
}

export function RecommendationsPage() {
  const t = useGuidanceT()
  const { programTitle, languages } = useI18n()
  const [profile, setProfile] = useProfile()
  const [degree, setDegree] = useState("bachelor")
  const [interests, setInterests] = useState<string[]>([])
  const [teaching, setTeaching] = useState("")
  const mutation = useMutation({
    mutationFn: () =>
      recommendPrograms({
        ...profile,
        degree_level: degree,
        interests,
        teaching_language: teaching || undefined,
      }),
  })
  const clear = () => mutation.reset()
  return (
    <GuidanceShell title={t("recommendations")}>
      <form
        className="max-w-3xl"
        onSubmit={(e) => {
          e.preventDefault()
          mutation.mutate()
        }}
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("degree")}>
            <select
              className={fieldClass}
              value={degree}
              onChange={(e) => {
                const d = e.target.value
                setDegree(d)
                setProfile({
                  ...profile,
                  education_route:
                    d === "master"
                      ? "bachelor"
                      : d === "phd"
                        ? "master"
                        : "school",
                  track: null,
                })
                clear()
              }}
            >
              {(["bachelor", "master", "phd"] as const).map((v) => (
                <option key={v} value={v}>
                  {t(v)}
                </option>
              ))}
            </select>
          </Field>
          <Field label={t("teaching_language")}>
            <select
              className={fieldClass}
              value={teaching}
              onChange={(e) => {
                setTeaching(e.target.value)
                clear()
              }}
            >
              <option value="">{t("any")}</option>
              {["English", "Kazakh", "Russian"].map((v) => (
                <option key={v} value={v}>
                  {languages(v)}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <fieldset className="mt-6">
          <legend className="font-medium">{t("interests")}</legend>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {([
              "computing",
              "business",
              "law",
              "education",
              "languages",
              "science",
              "media",
              "psychology",
            ] as const).map((v) => (
              <label key={v} className="flex gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={interests.includes(v)}
                  onChange={(e) => {
                    setInterests(
                      e.target.checked
                        ? [...interests, v]
                        : interests.filter((x) => x !== v),
                    )
                    clear()
                  }}
                />
                {t(v)}
              </label>
            ))}
          </div>
        </fieldset>
        <ProfileFields
          degree={degree}
          value={profile}
          onChange={(p) => {
            setProfile(p)
            clear()
          }}
        />
        <Button
          className="mt-6"
          disabled={!interests.length || mutation.isPending}
          aria-describedby={interests.length ? undefined : "recommendations-hint"}
        >
          {t(mutation.isPending ? "working" : "recommendations")}
        </Button>
        <SubmitHint id="recommendations-hint" text={interests.length ? null : t("needInterest")} />
      </form>
      <ErrorMessage error={mutation.error} />
      {mutation.data && (
        <div aria-live="polite" className="mt-8 space-y-5">
          <p className="text-sm text-muted-foreground">{t("disclaimer")}</p>
          {mutation.data.items.length === 0 && <p>{t("noMatches")}</p>}
          {mutation.data.items.map((item) => (
            <article
              className="border-2 border-border bg-card p-6"
              key={item.program.program_id}
            >
              <p className="text-xs text-muted-foreground">
                {item.program.program_id}
              </p>
              <h2 className="mt-1 text-xl font-medium">
                {programTitle(item.program)}
              </h2>
              <p className="mt-2 text-sm">
                {t("matches")}:{" "}
                {item.reasons
                  .map((r) => t.code(r.replace("interest:", "")))
                  .join(", ")}
              </p>
              <p className="mt-2 text-sm font-medium">
                {t(item.eligibility.status)}
              </p>
              <GapList gaps={item.gaps} />
              <Link
                className="mt-4 inline-block text-sm underline"
                to={`/programs/${item.program.program_id}`}
              >
                {t("details")}
              </Link>
              <EligibilityResult result={item.eligibility} />
            </article>
          ))}
          {mutation.data.items.length >= 2 && (
            <Button asChild>
              <Link
                to={`/compare?ids=${mutation.data.items.map((i) => i.program.program_id).join(",")}`}
              >
                {t("compare")}
              </Link>
            </Button>
          )}
        </div>
      )}
    </GuidanceShell>
  )
}

export function CostPage() {
  const t = useGuidanceT()
  const { language, languages } = useI18n()
  const [params] = useSearchParams()
  const [program, setProgram] = useState(params.get("program") ?? "")
  const [professional, setProfessional] = useState("")
  const [mde, setMde] = useState("0")
  const [currency, setCurrency] = useState<CostInput["currency"]>("KZT")
  const [group, setGroup] = useState("")
  const data = useQuery({
    queryKey: ["guidance", program],
    queryFn: ({ signal }) => getGuidance(program, false, signal),
    enabled: !!program,
  })
  const mutation = useMutation({
    mutationFn: () =>
      estimateCost(program, {
        professional_ects: Number(professional),
        mde_ects: Number(mde),
        currency,
        language_group: group || undefined,
        language,
      }),
  })
  const costHint = !program
    ? t("needProgram")
    : !professional || Number(professional) + Number(mde) <= 0
      ? t("needCredits")
      : null
  const number = (value: number | null) =>
    value == null ? t("unknown") : new Intl.NumberFormat(language).format(value)
  return (
    <GuidanceShell title={t("cost")}>
      <p className="max-w-3xl text-sm text-muted-foreground">{t("costNote")}</p>
      <form
        className="mt-6 max-w-3xl space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          mutation.mutate()
        }}
      >
        <ProgramSelect
          value={program}
          onChange={(v) => {
            setProgram(v)
            setGroup("")
            mutation.reset()
          }}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={`${t("professional")} · ${t("credits")}`}>
            <Input
              required
              type="number"
              min={0}
              max={1000}
              value={professional}
              onChange={(e) => {
                setProfessional(e.target.value)
                mutation.reset()
              }}
            />
          </Field>
          <Field label={`${t("mde")} · ${t("credits")}`}>
            <Input
              required
              type="number"
              min={0}
              max={1000}
              value={mde}
              onChange={(e) => {
                setMde(e.target.value)
                mutation.reset()
              }}
            />
          </Field>
          <Field label={t("currency")}>
            <select
              className={fieldClass}
              value={currency}
              onChange={(e) => {
                setCurrency(e.target.value as CostInput["currency"])
                mutation.reset()
              }}
            >
              <option>KZT</option>
              <option>USD</option>
            </select>
          </Field>
          {!!data.data?.language_tariffs.length && (
            <Field label={t("language_group")}>
              <select
                className={fieldClass}
                required
                value={group}
                onChange={(e) => {
                  setGroup(e.target.value)
                  mutation.reset()
                }}
              >
                <option value="">{t("chooseLanguageGroup")}</option>
                {data.data.language_tariffs.map((tariff) => (
                  <option
                    key={tariff.language_group}
                    value={tariff.language_group}
                  >
                    {languages(tariff.language_group)}
                  </option>
                ))}
              </select>
            </Field>
          )}
        </div>
        <Button
          disabled={
            !program ||
            !professional ||
            !data.data ||
            mutation.isPending ||
            Number(professional) + Number(mde) <= 0
          }
          aria-describedby={costHint ? "cost-hint" : undefined}
        >
          {t(mutation.isPending ? "working" : "calculate")}
        </Button>
        <SubmitHint id="cost-hint" text={costHint} />
      </form>
      <ErrorMessage error={mutation.error || data.error} />
      {data.data && (
        <div className="mt-5 text-sm">
          <GapList
            gaps={data.data.gaps.filter((g) => g !== "requirements_incomplete")}
          />
          {data.data.total_ects != null && (
            <p className="mt-3">
              {t("totalCredits")}: {data.data.total_ects}
            </p>
          )}
          <EvidenceView evidence={data.data.credits_evidence} />
        </div>
      )}
      {mutation.data && (
        <section
          aria-live="polite"
          className="mt-8 border-2 border-border bg-card p-6"
        >
          <h2 className="text-xl font-medium">
            {t("total")}: {number(mutation.data.estimated_total)} {currency}
          </h2>
          {mutation.data.estimated_total == null && (
            <p className="mt-2">
              {t("subtotal")}: {number(mutation.data.known_subtotal)} {currency}
            </p>
          )}
          <ul className="mt-4 divide-y divide-border">
            {mutation.data.components.map((c) => (
              <li className="py-3 text-sm" key={c.component}>
                <h3 className="font-medium">{t.code(c.component)}</h3>
                <p>
                  {c.ects} ECTS × {number(c.rate)} {currency} ={" "}
                  {number(c.amount)} {currency}
                </p>
                <EvidenceView evidence={c.evidence} />
              </li>
            ))}
          </ul>
          <GapList
            gaps={[...mutation.data.gaps, ...mutation.data.assumptions]}
          />
        </section>
      )}
    </GuidanceShell>
  )
}

export function FundingPage() {
  const t = useGuidanceT()
  const { language } = useI18n()
  const [degree, setDegree] = useState("")
  const [applicant, setApplicant] = useState("")
  const data = useQuery({
    queryKey: ["funding", language, degree, applicant],
    queryFn: ({ signal }) => getFunding(language, degree, applicant, signal),
  })
  return (
    <GuidanceShell title={t("funding")}>
      <p className="max-w-3xl text-sm text-muted-foreground">
        {t("fundingNote")}
      </p>
      <div className="my-6 grid max-w-2xl gap-4 sm:grid-cols-2">
        <Field label={t("degree")}>
          <select
            className={fieldClass}
            value={degree}
            onChange={(e) => setDegree(e.target.value)}
          >
            <option value="">{t("all")}</option>
            {(["bachelor", "master", "phd"] as const).map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
        <Field label={t("applicant_type")}>
          <select
            className={fieldClass}
            value={applicant}
            onChange={(e) => setApplicant(e.target.value)}
          >
            <option value="">{t("all")}</option>
            {(["local", "international"] as const).map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
      </div>
      {data.isPending && <p>{t("working")}</p>}
      {data.isError && (
        <>
          <ErrorMessage error={data.error} />
          <Button className="mt-3" onClick={() => void data.refetch()}>
            {t("retry")}
          </Button>
        </>
      )}
      <div className="space-y-5">
        {data.data?.items.length === 0 && <p>{t("empty")}</p>}
        {data.data?.items.map((item) => (
          <article
            key={item.faq_id}
            className="border-2 border-border bg-card p-6"
          >
            <p className="text-xs text-muted-foreground">
              {t.code(item.status)} · {t("checked")}: {item.last_checked}
            </p>
            <h2
              className="mt-2 text-xl font-medium"
              lang={item.content_language}
            >
              {item.title}
            </h2>
            {item.translation_missing && (
              <p className="mt-2 text-sm text-muted-foreground">
                {t("translation_missing")}
              </p>
            )}
            <p
              className="mt-3 whitespace-pre-wrap text-sm leading-relaxed"
              lang={item.content_language}
            >
              {item.text}
            </p>
            <a
              className="mt-4 inline-block text-sm underline"
              href={item.source_url}
              target="_blank"
              rel="noreferrer"
            >
              {t("sources")}
            </a>
          </article>
        ))}
      </div>
    </GuidanceShell>
  )
}
