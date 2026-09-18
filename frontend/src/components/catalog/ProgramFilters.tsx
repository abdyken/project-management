import type { FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DEGREE_LABELS, FACULTIES, LANGUAGE_LABELS } from "@/lib/constants"

export type FilterValues = {
  q: string
  faculty: string
  degree_level: string
  language: string
}

type ProgramFiltersProps = {
  values: FilterValues
  onChange: (values: FilterValues) => void
}

export function ProgramFilters({ values, onChange }: ProgramFiltersProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    onChange({
      ...values,
      q: String(form.get("q") ?? ""),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 md:grid-cols-12">
      <div className="md:col-span-5">
        <label className="mb-1.5 block text-[11px] tracking-[0.14em] text-muted-foreground uppercase" htmlFor="q">
          Search
        </label>
        <Input
          id="q"
          name="q"
          defaultValue={values.q}
          key={values.q}
          placeholder="Title, school, or code"
        />
      </div>
      <div className="md:col-span-3">
        <p className="mb-1.5 text-[11px] tracking-[0.14em] text-muted-foreground uppercase">School</p>
        <Select value={values.faculty || "all"} onValueChange={(faculty) => onChange({ ...values, faculty: faculty === "all" ? "" : faculty })}>
          <SelectTrigger aria-label="School">
            <SelectValue placeholder="All schools" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All schools</SelectItem>
            {FACULTIES.map((faculty) => (
              <SelectItem key={faculty} value={faculty}>
                {faculty.replace("School of ", "").replace("SDU ", "")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="md:col-span-2">
        <p className="mb-1.5 text-[11px] tracking-[0.14em] text-muted-foreground uppercase">Degree</p>
        <Select
          value={values.degree_level || "all"}
          onValueChange={(degree) => onChange({ ...values, degree_level: degree === "all" ? "" : degree })}
        >
          <SelectTrigger aria-label="Degree">
            <SelectValue placeholder="All" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All degrees</SelectItem>
            {Object.entries(DEGREE_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="md:col-span-2">
        <p className="mb-1.5 text-[11px] tracking-[0.14em] text-muted-foreground uppercase">Language</p>
        <Select
          value={values.language || "all"}
          onValueChange={(language) => onChange({ ...values, language: language === "all" ? "" : language })}
        >
          <SelectTrigger aria-label="Language">
            <SelectValue placeholder="All" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All languages</SelectItem>
            {Object.entries(LANGUAGE_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="md:col-span-12">
        <Button type="submit" variant="outline" size="sm">
          Apply search
        </Button>
      </div>
    </form>
  )
}
