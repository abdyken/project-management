import { Search, SlidersHorizontal, X } from "lucide-react"
import { useState, type FormEvent } from "react"
import type { FilterOptions } from "@/api/programs"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { cn } from "@/lib/utils"

export type FilterValues = {
  q: string
  faculty: string
  degree_level: string
  language: string
}

const SEARCH_MAX_LENGTH = 100

// The finder's search, set on the turquoise page band.
export function ProgramSearch({ values, onChange }: { values: FilterValues; onChange: (values: FilterValues) => void }) {
  const { t } = useI18n()
  const [q, setQ] = useState(values.q)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onChange({ ...values, q: q.trim() })
  }

  return (
    <form onSubmit={handleSubmit} role="search" className="max-w-3xl">
      <label className="mb-2 block text-[0.9375rem] font-semibold text-field-muted" htmlFor="q">
        {t("filters.search")}
      </label>
      <div className="flex">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-primary" aria-hidden="true" />
          <input
            id="q"
            type="search"
            value={q}
            maxLength={SEARCH_MAX_LENGTH}
            onChange={(event) => setQ(event.target.value)}
            placeholder={t("filters.placeholder")}
            className="h-14 w-full border-0 bg-card pr-3 pl-12 text-base text-foreground outline-none placeholder:text-muted-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          />
        </div>
        <Button type="submit" variant="ochre" size="lg" className="h-14">
          {t("filters.searchButton")}
        </Button>
      </div>
    </form>
  )
}

type Option = { value: string; label: string; lang?: string }

// One filter as a group of square tiles backed by native radio inputs.
function TileGroup({
  name,
  legend,
  value,
  options,
  onChange,
}: {
  name: string
  legend: string
  value: string
  options: Option[]
  onChange: (value: string) => void
}) {
  const { t } = useI18n()
  const items = value && !options.some((option) => option.value === value) ? [...options, { value, label: value }] : options
  const all: Option[] = [{ value: "", label: t("filters.all") }, ...items]

  return (
    <fieldset>
      <legend className="label text-foreground">{legend}</legend>
      <div className="mt-3 flex flex-wrap gap-1.5 lg:flex-col lg:items-stretch">
        {all.map((option) => {
          const checked = value === option.value
          const id = `${name}-${option.value || "all"}`
          return (
            <label
              key={id}
              htmlFor={id}
              className={cn(
                "flex min-h-11 cursor-pointer items-center gap-3 border-2 px-3 py-2 text-[0.9375rem] transition-colors duration-200",
                "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-ring",
                checked ? "border-primary bg-primary font-semibold text-primary-foreground" : "border-border bg-card hover:border-primary",
              )}
            >
              <input
                id={id}
                type="radio"
                name={name}
                value={option.value}
                checked={checked}
                onChange={() => onChange(option.value)}
                className="sr-only"
              />
              <span aria-hidden="true" className={cn("size-3 shrink-0", checked ? "bg-ochre" : "border-2 border-input")} />
              <span lang={option.lang}>{option.label}</span>
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}

export function FilterPanel({
  values,
  options,
  onChange,
}: {
  values: FilterValues
  options: FilterOptions
  onChange: (values: FilterValues) => void
}) {
  const { t, degree, languages } = useI18n()
  const [open, setOpen] = useState(false)
  const active = [values.faculty, values.degree_level, values.language].filter(Boolean).length

  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        aria-controls="filter-panel"
        onClick={() => setOpen((value) => !value)}
        className="label flex h-12 w-full items-center justify-between border border-ink px-4 text-foreground lg:hidden"
      >
        {active ? t("filters.activeCount", { count: active }) : t("filters.title")}
        <SlidersHorizontal className="size-5" aria-hidden="true" />
      </button>
      <div id="filter-panel" className={cn("mt-4 space-y-8 lg:mt-0 lg:block", open ? "block" : "hidden")}>
        <TileGroup
          name="degree"
          legend={t("filters.degree")}
          value={values.degree_level}
          options={options.degreeLevels.map((level) => ({ value: level, label: degree(level) }))}
          onChange={(degree_level) => onChange({ ...values, degree_level })}
        />
        <TileGroup
          name="language"
          legend={t("filters.language")}
          value={values.language}
          options={options.languages.map((language) => ({ value: language, label: languages(language) }))}
          onChange={(language) => onChange({ ...values, language })}
        />
        <TileGroup
          name="faculty"
          legend={t("filters.school")}
          value={values.faculty}
          options={options.faculties.map((faculty) => ({ value: faculty, label: faculty, lang: "en" }))}
          onChange={(faculty) => onChange({ ...values, faculty })}
        />
      </div>
    </div>
  )
}

// Applied filters as removable chips, plus "Clear filters".
export function ActiveFilters({ values, onChange }: { values: FilterValues; onChange: (values: FilterValues) => void }) {
  const { t, degree, languages } = useI18n()
  const chips: { key: keyof FilterValues; label: string; lang?: string }[] = []
  if (values.q) chips.push({ key: "q", label: t("filters.searchFor", { value: values.q }) })
  if (values.degree_level) chips.push({ key: "degree_level", label: degree(values.degree_level as "bachelor") })
  if (values.language) chips.push({ key: "language", label: languages(values.language) })
  if (values.faculty) chips.push({ key: "faculty", label: values.faculty, lang: "en" })
  if (chips.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-2">
      {chips.map((chip) => (
        <button
          key={chip.key}
          type="button"
          onClick={() => onChange({ ...values, [chip.key]: "" })}
          aria-label={t("filters.remove", { value: chip.label })}
          className="inline-flex min-h-9 items-center gap-2 bg-secondary px-3 text-sm font-semibold text-secondary-foreground transition-colors hover:bg-accent"
        >
          <span lang={chip.lang}>{chip.label}</span>
          <X className="size-4" aria-hidden="true" />
        </button>
      ))}
      <button
        type="button"
        onClick={() => onChange({ q: "", faculty: "", degree_level: "", language: "" })}
        className="min-h-9 px-2 text-sm font-semibold text-primary underline decoration-2 underline-offset-4 hover:decoration-ochre"
      >
        {t("filters.clearAll")}
      </button>
    </div>
  )
}
