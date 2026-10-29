import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"
import {
  SUBJECT_PAIRS,
  getGuidance,
  saveGuidance,
  type Condition,
  type Evidence,
  type Guidance,
  type Metric,
  type Scope,
} from "@/api/guidance"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useGuidanceT } from "@/guidance/i18n"
import {
  ErrorMessage,
  Field,
  fieldClass,
} from "@/pages/guidance/AdmissionsPages"

const numeric: Metric[] = [
  "unt_total",
  "ct_total",
  "phd_total",
  "toefl_ibt",
  "toefl_pbt",
  "toeic",
  "duolingo",
  "work_months",
  "gpa",
  "ielts_overall",
  "ielts_component_min",
]
const metrics: Metric[] = [
  ...numeric,
  "sdu_english",
  "interview",
  "special_exam",
  "creative_exam",
  "kaztest",
  "subject_pair",
]
function freshEvidence(): Evidence {
  return {
    url: "https://sdu.edu.kz/",
    quote: "",
    academic_year: "2026-2027",
    checked_on: new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Almaty",
    }).format(new Date()),
    status: "pending",
  }
}

function EvidenceEditor({
  value,
  onChange,
}: {
  value: Evidence
  onChange: (value: Evidence) => void
}) {
  const t = useGuidanceT()
  return (
    <details className="mt-3">
      <summary className="cursor-pointer text-sm">
        {t("evidence")} · {t(value.status)}
      </summary>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Field label={t("url")}>
          <Input
            type="url"
            required
            maxLength={1000}
            value={value.url}
            onChange={(e) => onChange({ ...value, url: e.target.value })}
          />
        </Field>
        <Field label={t("academic_year")}>
          <Input
            required
            value={value.academic_year}
            onChange={(e) =>
              onChange({ ...value, academic_year: e.target.value })
            }
          />
        </Field>
        <Field label={t("checked")}>
          <Input
            type="date"
            required
            value={value.checked_on}
            onChange={(e) => onChange({ ...value, checked_on: e.target.value })}
          />
        </Field>
        <Field label={t("confirmed")}>
          <select
            className={fieldClass}
            value={value.status}
            onChange={(e) =>
              onChange({
                ...value,
                status: e.target.value as Evidence["status"],
              })
            }
          >
            {["pending", "confirmed", "conflict"].map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <div className="mt-3">
        <Field label={t("quote")}>
          <textarea
            required
            className={fieldClass}
            maxLength={6000}
            rows={3}
            value={value.quote}
            onChange={(e) => onChange({ ...value, quote: e.target.value })}
          />
        </Field>
      </div>
    </details>
  )
}

function ScopeEditor({
  value,
  onChange,
}: {
  value: Scope
  onChange: (value: Scope) => void
}) {
  const t = useGuidanceT()
  const fields: [keyof Scope, string[]][] = [
    ["applicant_type", ["local", "international"]],
    ["education_route", ["school", "college", "bachelor", "master"]],
    ["admission_basis", ["paid", "grant"]],
    ["track", ["scientific", "profile"]],
  ]
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {fields.map(([key, options]) => (
        <Field key={key} label={t(key)}>
          <select
            className={fieldClass}
            value={value[key] ?? ""}
            onChange={(e) =>
              onChange({ ...value, [key]: e.target.value || null })
            }
          >
            <option value="">{t("any")}</option>
            {options.map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
      ))}
    </div>
  )
}

function Editor({
  initial,
  programId,
}: {
  initial: Guidance
  programId: string
}) {
  const t = useGuidanceT()
  const [value, setValue] = useState(initial)
  const mutation = useMutation({
    mutationFn: () => saveGuidance(programId, value),
  })
  const patch = (change: Partial<Guidance>) => {
    setValue((v) => ({ ...v, ...change }))
    mutation.reset()
  }
  const setCondition = (
    ri: number,
    gi: number,
    ci: number,
    condition: Condition,
  ) =>
    patch({
      rules: value.rules.map((r, i) =>
        i !== ri
          ? r
          : {
              ...r,
              alternatives: r.alternatives.map((group, j) =>
                j !== gi
                  ? group
                  : group.map((c, k) => (k === ci ? condition : c)),
              ),
            },
      ),
    })
  return (
    <form
      className="mt-8 space-y-6 border-t border-border pt-6"
      onSubmit={(e) => {
        e.preventDefault()
        mutation.mutate()
      }}
    >
      <h2 className="text-xl font-semibold">{t("rules")}</h2>
      {value.rules.map((rule, ri) => (
        <fieldset
          key={ri}
          className="min-w-0 rounded-lg border border-border p-4"
        >
          <legend className="px-2 text-sm font-medium">{t(rule.key)}</legend>
          <ScopeEditor
            value={rule}
            onChange={(scope) =>
              patch({
                rules: value.rules.map((r, i) =>
                  i === ri ? { ...r, ...scope } : r,
                ),
              })
            }
          />
          {rule.alternatives.map((group, gi) => (
            <div
              className="mt-4 space-y-2 rounded border border-border p-3"
              key={gi}
            >
              <p className="text-xs font-medium">
                {gi > 0 ? t("or") : t("and")}
              </p>
              {group.map((condition, ci) => (
                <div
                  className="grid gap-2 sm:grid-cols-[2fr_1fr_auto]"
                  key={ci}
                >
                  <Field label={t("rules")}>
                    <select
                      className={fieldClass}
                      value={condition.metric}
                      onChange={(e) => {
                        const metric = e.target.value as Metric
                        setCondition(
                          ri,
                          gi,
                          ci,
                          numeric.includes(metric)
                            ? { metric, minimum: 0 }
                            : {
                                metric,
                                equals: metric === "subject_pair" ? "" : true,
                              },
                        )
                      }}
                    >
                      {metrics.map((m) => (
                        <option key={m} value={m}>
                          {t(m)}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field
                    label={
                      numeric.includes(condition.metric)
                        ? t("minimum")
                        : t(condition.metric)
                    }
                  >
                    {numeric.includes(condition.metric) ? (
                      <Input
                        type="number"
                        min={0}
                        step="any"
                        required
                        value={condition.minimum ?? ""}
                        onChange={(e) =>
                          setCondition(ri, gi, ci, {
                            metric: condition.metric,
                            minimum: Number(e.target.value),
                          })
                        }
                      />
                    ) : condition.metric === "subject_pair" ? (
                      <select
                        className={fieldClass}
                        required
                        value={String(condition.equals ?? "")}
                        onChange={(e) =>
                          setCondition(ri, gi, ci, {
                            metric: condition.metric,
                            equals: e.target.value,
                          })
                        }
                      >
                        <option value="">{t("choose")}</option>
                        {SUBJECT_PAIRS.map((pair) => (
                          <option key={pair} value={pair}>
                            {t(pair)}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <select
                        className={fieldClass}
                        value={String(condition.equals)}
                        onChange={(e) =>
                          setCondition(ri, gi, ci, {
                            metric: condition.metric,
                            equals: e.target.value === "true",
                          })
                        }
                      >
                        <option value="true">{t("yes")}</option>
                        <option value="false">{t("no")}</option>
                      </select>
                    )}
                  </Field>
                  <Button
                    type="button"
                    variant="ghost"
                    className="self-end"
                    disabled={group.length === 1}
                    onClick={() =>
                      patch({
                        rules: value.rules.map((r, i) =>
                          i !== ri
                            ? r
                            : {
                                ...r,
                                alternatives: r.alternatives.map((g, j) =>
                                  j === gi ? g.filter((_, k) => k !== ci) : g,
                                ),
                              },
                        ),
                      })
                    }
                  >
                    {t("remove")}
                  </Button>
                </div>
              ))}
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    patch({
                      rules: value.rules.map((r, i) =>
                        i !== ri
                          ? r
                          : {
                              ...r,
                              alternatives: r.alternatives.map((g, j) =>
                                j === gi
                                  ? [...g, { metric: "unt_total", minimum: 0 }]
                                  : g,
                              ),
                            },
                      ),
                    })
                  }
                >
                  {t("addCondition")}
                </Button>
                {rule.alternatives.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      patch({
                        rules: value.rules.map((r, i) =>
                          i !== ri
                            ? r
                            : {
                                ...r,
                                alternatives: r.alternatives.filter(
                                  (_, j) => j !== gi,
                                ),
                              },
                        ),
                      })
                    }
                  >
                    {t("remove")}
                  </Button>
                )}
              </div>
            </div>
          ))}
          <Button
            type="button"
            className="mt-3"
            size="sm"
            variant="outline"
            onClick={() =>
              patch({
                rules: value.rules.map((r, i) =>
                  i !== ri
                    ? r
                    : {
                        ...r,
                        alternatives: [
                          ...r.alternatives,
                          [{ metric: "sdu_english", equals: true }],
                        ],
                      },
                ),
              })
            }
          >
            {t("addAlternative")}
          </Button>
          <EvidenceEditor
            value={rule.evidence}
            onChange={(evidence) =>
              patch({
                rules: value.rules.map((r, i) =>
                  i === ri ? { ...r, evidence } : r,
                ),
              })
            }
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="mt-3"
            onClick={() =>
              patch({ rules: value.rules.filter((_, i) => i !== ri) })
            }
          >
            {t("remove")}
          </Button>
        </fieldset>
      ))}
      <Button
        type="button"
        variant="outline"
        onClick={() =>
          patch({
            rules: [
              ...value.rules,
              {
                key: "requirement",
                alternatives: [[{ metric: "unt_total", minimum: 0 }]],
                evidence: freshEvidence(),
                applicant_type: "local",
                education_route: "school",
                admission_basis: "paid",
              },
            ],
          })
        }
      >
        {t("addRule")}
      </Button>
      <fieldset className="rounded-lg border border-border p-4">
        <legend className="px-2 text-sm font-medium">{t("complete")}</legend>
        {value.complete_for.map((scope, i) => (
          <div className="mb-4" key={i}>
            <ScopeEditor
              value={scope}
              onChange={(next) =>
                patch({
                  complete_for: value.complete_for.map((s, j) =>
                    j === i ? next : s,
                  ),
                })
              }
            />
            <Button
              type="button"
              variant="ghost"
              onClick={() =>
                patch({
                  complete_for: value.complete_for.filter((_, j) => j !== i),
                })
              }
            >
              {t("remove")}
            </Button>
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          onClick={() =>
            patch({
              complete_for: [
                ...value.complete_for,
                {
                  applicant_type: "local",
                  education_route: "school",
                  admission_basis: "paid",
                },
              ],
            })
          }
        >
          {t("addCoverage")}
        </Button>
      </fieldset>
      <fieldset className="rounded-lg border border-border p-4">
        <legend className="px-2">{t("totalCredits")}</legend>
        <Input
          aria-label={t("totalCredits")}
          type="number"
          min={1}
          max={1000}
          value={value.total_ects ?? ""}
          onChange={(e) =>
            patch({
              total_ects: e.target.value ? Number(e.target.value) : null,
              credits_evidence: value.credits_evidence ?? freshEvidence(),
            })
          }
        />
        {value.credits_evidence && (
          <EvidenceEditor
            value={value.credits_evidence}
            onChange={(credits_evidence) => patch({ credits_evidence })}
          />
        )}
      </fieldset>
      <fieldset className="rounded-lg border border-border p-4">
        <legend className="px-2">{t("mde")}</legend>
        <div className="grid gap-3 sm:grid-cols-2">
          {(["mde_kzt", "mde_usd"] as const).map((key) => (
            <Field key={key} label={key === "mde_kzt" ? "KZT" : "USD"}>
              <Input
                type="number"
                min={0}
                value={value[key] ?? ""}
                onChange={(e) =>
                  patch({
                    [key]: e.target.value ? Number(e.target.value) : null,
                    mde_evidence: value.mde_evidence ?? freshEvidence(),
                  })
                }
              />
            </Field>
          ))}
        </div>
        {value.mde_evidence && (
          <EvidenceEditor
            value={value.mde_evidence}
            onChange={(mde_evidence) => patch({ mde_evidence })}
          />
        )}
      </fieldset>
      {value.language_tariffs.map((tariff, i) => (
        <fieldset className="rounded-lg border border-border p-4" key={i}>
          <legend className="px-2">{t("language_group")}</legend>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label={t("language_group")}>
              <Input
                required
                value={tariff.language_group}
                onChange={(e) =>
                  patch({
                    language_tariffs: value.language_tariffs.map((x, j) =>
                      i === j ? { ...x, language_group: e.target.value } : x,
                    ),
                  })
                }
              />
            </Field>
            {(["kzt", "usd"] as const).map((key) => (
              <Field key={key} label={key.toUpperCase()}>
                <Input
                  type="number"
                  min={0}
                  value={tariff[key] ?? ""}
                  onChange={(e) =>
                    patch({
                      language_tariffs: value.language_tariffs.map((x, j) =>
                        i === j
                          ? {
                              ...x,
                              [key]: e.target.value
                                ? Number(e.target.value)
                                : null,
                            }
                          : x,
                      ),
                    })
                  }
                />
              </Field>
            ))}
          </div>
          <EvidenceEditor
            value={tariff.evidence}
            onChange={(evidence) =>
              patch({
                language_tariffs: value.language_tariffs.map((x, j) =>
                  i === j ? { ...x, evidence } : x,
                ),
              })
            }
          />
          <Button
            type="button"
            variant="ghost"
            onClick={() =>
              patch({
                language_tariffs: value.language_tariffs.filter(
                  (_, j) => j !== i,
                ),
              })
            }
          >
            {t("remove")}
          </Button>
        </fieldset>
      ))}
      <Button
        type="button"
        variant="outline"
        onClick={() =>
          patch({
            language_tariffs: [
              ...value.language_tariffs,
              {
                language_group: "",
                kzt: null,
                usd: null,
                evidence: freshEvidence(),
              },
            ],
          })
        }
      >
        {t("addTariff")}
      </Button>
      {(["tuition_per_ects_kzt", "tuition_per_ects_usd"] as const).map(
        (key) => (
          <section key={key}>
            <h3 className="text-sm font-medium">
              {t("professional")} · {key.endsWith("kzt") ? "KZT" : "USD"}
            </h3>
            {value.sources[key] ? (
              <EvidenceEditor
                value={value.sources[key]}
                onChange={(evidence) =>
                  patch({ sources: { ...value.sources, [key]: evidence } })
                }
              />
            ) : (
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  patch({
                    sources: { ...value.sources, [key]: freshEvidence() },
                  })
                }
              >
                {t("addSource")}
              </Button>
            )}
          </section>
        ),
      )}
      <div>
        <Button disabled={mutation.isPending}>
          {t(mutation.isPending ? "working" : "save")}
        </Button>
        <ErrorMessage error={mutation.error} />
        {mutation.isSuccess && (
          <p role="status" className="mt-2 text-sm">
            {t("saved")}
          </p>
        )}
      </div>
    </form>
  )
}

export function GuidanceEditor({ programId }: { programId: string }) {
  const t = useGuidanceT()
  const data = useQuery({
    queryKey: ["staff", "guidance", programId],
    queryFn: ({ signal }) => getGuidance(programId, true, signal),
  })
  return data.data ? (
    <Editor key={programId} initial={data.data} programId={programId} />
  ) : (
    <div className="mt-6">
      {data.isPending && <p>{t("working")}</p>}
      <ErrorMessage error={data.error} />
      {data.isError && (
        <Button onClick={() => void data.refetch()}>{t("retry")}</Button>
      )}
    </div>
  )
}
