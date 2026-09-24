import { Link } from "react-router-dom"
import { CatalogueSnapshot } from "@/components/home/CatalogueSnapshot"
import { Button } from "@/components/ui/button"
import { useChatStore } from "@/store/chat"

const steps = [
  {
    n: "01",
    title: "Find a program",
    text: "Search by title or filter by school, degree and language of instruction.",
  },
  {
    n: "02",
    title: "Read the file",
    text: "Open a card for the deadline, fee and the document list for local or international applicants.",
  },
  {
    n: "03",
    title: "Ask the desk",
    text: "The chat answers from the official FAQ and always keeps the source link.",
  },
]

const questions = [
  "When can I apply for a bachelor's program in 2026?",
  "What English level do I need for bachelor's admission?",
  "Which documents do I need for Computer Science as an international applicant?",
  "How much does the dormitory cost?",
  "How can I contact the SDU Admissions Office?",
]

export function HomePage() {
  const setOpen = useChatStore((state) => state.setOpen)
  const setDraft = useChatStore((state) => state.setDraft)

  function ask(question: string) {
    setDraft(question)
    setOpen(true)
  }

  return (
    <div>
      <section className="mx-auto grid max-w-5xl gap-12 px-4 py-16 sm:px-6 sm:py-24 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div>
          <p className="text-[11px] tracking-[0.12em] text-muted-foreground uppercase">
            SDU University · Kaskelen
          </p>
          <h1 className="mt-4 max-w-xl text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            Look up a program.
            <br />
            Ask the office.
          </h1>
          <p className="mt-6 max-w-md text-sm leading-relaxed text-muted-foreground">
            A public catalogue and a session chat for admissions questions that already have an official answer.
            Nothing here invents a rule.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link to="/programs">Browse programs</Link>
            </Button>
            <Button size="lg" variant="outline" onClick={() => setOpen(true)}>
              Ask a question
            </Button>
          </div>
        </div>
        <CatalogueSnapshot />
      </section>

      <section className="border-y border-border/80">
        <div className="mx-auto grid max-w-5xl gap-10 px-4 py-16 sm:px-6 md:grid-cols-3">
          {steps.map((step) => (
            <div key={step.n}>
              <p className="text-3xl font-semibold text-gold">{step.n}</p>
              <h2 className="mt-3 text-2xl font-semibold tracking-tight">{step.title}</h2>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
        <p className="text-[11px] tracking-[0.12em] text-muted-foreground uppercase">People also ask</p>
        <h2 className="mt-3 text-4xl font-semibold tracking-tight">Start with a usual question</h2>
        <ol className="mt-10 divide-y divide-border border-y border-border">
          {questions.map((question, index) => (
            <li key={question}>
              <button
                type="button"
                onClick={() => ask(question)}
                className="flex w-full items-baseline gap-6 py-5 text-left hover:bg-secondary/40"
              >
                <span className="w-6 shrink-0 text-sm text-muted-foreground">{index + 1}</span>
                <span className="text-sm sm:text-base">{question}</span>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}
