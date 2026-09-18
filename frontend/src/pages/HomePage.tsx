import { Link } from "react-router-dom"
import { useChatStore } from "@/store/chat"

const steps = [
  {
    n: "01",
    title: "Find a programme",
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
  "What is the fall intake deadline?",
  "What English level is required?",
  "Which documents do I need for Computer Science?",
  "How do local applicants apply after school?",
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
          <h1 className="mt-4 max-w-xl font-serif text-5xl leading-[1.05] sm:text-6xl">
            Look up a programme.
            <br />
            Ask the office.
          </h1>
          <p className="mt-6 max-w-md text-sm leading-relaxed text-muted-foreground">
            A public catalogue and a session chat for admissions questions that already have an official answer.
            Nothing here invents a rule.
          </p>
          <div className="mt-10 flex items-center gap-4">
            <Link
              to="/programs"
              className="flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground"
              aria-label="Browse programmes"
            >
              <span className="text-lg leading-none">→</span>
            </Link>
            <button type="button" onClick={() => setOpen(true)} className="text-sm underline-offset-4 hover:underline">
              Ask a question
            </button>
          </div>
        </div>
        <HeroMark />
      </section>

      <section className="border-y border-border/80">
        <div className="mx-auto grid max-w-5xl gap-10 px-4 py-16 sm:px-6 md:grid-cols-3">
          {steps.map((step) => (
            <div key={step.n}>
              <p className="font-serif text-3xl text-gold">{step.n}</p>
              <h2 className="mt-3 font-serif text-2xl">{step.title}</h2>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
        <p className="text-[11px] tracking-[0.12em] text-muted-foreground uppercase">People also ask</p>
        <h2 className="mt-3 font-serif text-4xl">Start with a usual question</h2>
        <ol className="mt-10 divide-y divide-border border-y border-border">
          {questions.map((question, index) => (
            <li key={question}>
              <button
                type="button"
                onClick={() => ask(question)}
                className="flex w-full items-baseline gap-6 py-5 text-left hover:bg-secondary/40"
              >
                <span className="w-6 text-sm text-muted-foreground">{index + 1}</span>
                <span className="text-sm sm:text-base">{question}</span>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}

function HeroMark() {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-sm">
      <svg viewBox="0 0 320 320" className="h-full w-full text-primary" fill="none" aria-hidden>
        <circle cx="160" cy="160" r="118" stroke="currentColor" strokeWidth="1" />
        <rect x="108" y="96" width="104" height="128" stroke="currentColor" strokeWidth="1.2" />
        <path d="M108 96 L160 62 L212 96" stroke="currentColor" strokeWidth="1.2" />
        <rect x="148" y="168" width="24" height="56" stroke="currentColor" strokeWidth="1.2" />
        <circle cx="160" cy="62" r="5" fill="currentColor" />
      </svg>
    </div>
  )
}
