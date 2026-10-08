import { Link } from "react-router-dom"
import { HeroGlobe } from "@/components/home/HeroGlobe"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"
import { useChatStore } from "@/store/chat"

const STEPS = [
  { n: "01", title: "home.step1.title", text: "home.step1.text" },
  { n: "02", title: "home.step2.title", text: "home.step2.text" },
  { n: "03", title: "home.step3.title", text: "home.step3.text" },
] as const

const QUESTIONS = ["home.q1", "home.q2", "home.q3", "home.q4", "home.q5"] as const

export function HomePage() {
  const { t } = useI18n()
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
            {t("home.kicker")}
          </p>
          <h1 className="mt-4 max-w-xl text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            {t("home.title1")}
            <br />
            {t("home.title2")}
          </h1>
          <p className="mt-6 max-w-md text-sm leading-relaxed text-muted-foreground">
            {t("home.lead")}
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link to="/programs">{t("home.browse")}</Link>
            </Button>
            <Button size="lg" variant="outline" onClick={() => setOpen(true)}>
              {t("home.askQuestion")}
            </Button>
          </div>
        </div>
        <HeroGlobe />
      </section>

      <section className="border-y border-border/80">
        <div className="mx-auto grid max-w-5xl gap-10 px-4 py-16 sm:px-6 md:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.n}>
              <p className="text-3xl font-semibold text-gold">{step.n}</p>
              <h2 className="mt-3 text-2xl font-semibold tracking-tight">{t(step.title)}</h2>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{t(step.text)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
        <p className="text-[11px] tracking-[0.12em] text-muted-foreground uppercase">{t("home.peopleAsk")}</p>
        <h2 className="mt-3 text-4xl font-semibold tracking-tight">{t("home.startWith")}</h2>
        <ol className="mt-10 divide-y divide-border border-y border-border">
          {QUESTIONS.map((key, index) => (
            <li key={key}>
              <button
                type="button"
                onClick={() => ask(t(key))}
                className="flex w-full items-baseline gap-6 py-5 text-left hover:bg-secondary/40"
              >
                <span className="w-6 shrink-0 text-sm text-muted-foreground">{index + 1}</span>
                <span className="text-sm sm:text-base">{t(key)}</span>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}
