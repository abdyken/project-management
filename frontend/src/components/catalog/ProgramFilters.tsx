import type { FormEvent } from "react"
import type { FilterOptions } from "@/api/programs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DEGREE_LABELS } from "@/lib/constants"

export type FilterValues = {
  q: string
  faculty: string
  degree_level: string
  language: string
}

type ProgramFiltersProps = {
  values: FilterValues
  options: FilterOptions
  onChange: (values: FilterValues) => void
}

const ALL = "all"
const labelClass = "mb-1.5 block text-[11px] tracking-[0.14em] text-muted-foreground uppercase"

type FilterSelectProps = {
  id: string
  label: string
  allLabel: string
  value: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}

function FilterSelect({ id, label, allLabel, value, options, onChange }: FilterSelectProps) {
  return (
    <div>
      <label className={labelClass} htmlFor={id}>
        {label}
      </label>
      <Select value={value || ALL} onValueChange={(next) => onChange(next === ALL ? "" : next)}>
        <SelectTrigger id={id}>
          <SelectValue placeholder={allLabel} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>{allLabel}</SelectItem>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

export function ProgramFilters({ values, options, onChange }: ProgramFiltersProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    onChange({ ...values, q: String(form.get("q") ?? "").trim() })
  }

  return (
    <div className="grid gap-3 md:grid-cols-12">
      <form onSubmit={handleSubmit} role="search" className="md:col-span-5">
        <label className={labelClass} htmlFor="q">
          Search
        </label>
        <div className="flex gap-2">
          <Input id="q" name="q" type="search" defaultValue={values.q} key={values.q} placeholder="Title, school, or code" />
          <Button type="submit" variant="outline">
            Search
          </Button>
        </div>
      </form>
      <div className="md:col-span-3">
        <FilterSelect
          id="filter-faculty"
          label="School"
          allLabel="All schools"
          value={values.faculty}
          options={options.faculties.map((faculty) => ({ value: faculty, label: faculty }))}
          onChange={(faculty) => onChange({ ...values, faculty })}
        />
      </div>
      <div className="md:col-span-2">
        <FilterSelect
          id="filter-degree"
          label="Degree"
          allLabel="All degrees"
          value={values.degree_level}
          options={options.degreeLevels.map((level) => ({ value: level, label: DEGREE_LABELS[level] }))}
          onChange={(degree_level) => onChange({ ...values, degree_level })}
        />
      </div>
      <div className="md:col-span-2">
        <FilterSelect
          id="filter-language"
          label="Language"
          allLabel="All languages"
          value={values.language}
          options={options.languages.map((language) => ({ value: language, label: language }))}
          onChange={(language) => onChange({ ...values, language })}
        />
      </div>
    </div>
  )
}
