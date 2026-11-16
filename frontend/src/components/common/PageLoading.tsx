import { translate, useLanguageStore } from "@/i18n"

export function PageLoading({ staff = false }: { staff?: boolean }) {
  const language = useLanguageStore((state) => state.language)
  // The staff area has no Kazakh texts and shows Russian instead.
  const shown = staff && language === "kk" ? "ru" : language
  return (
    <p role="status" className="mx-auto max-w-5xl px-4 py-12 text-sm text-muted-foreground sm:px-6">
      {translate(shown, "page.loading")}
    </p>
  )
}
