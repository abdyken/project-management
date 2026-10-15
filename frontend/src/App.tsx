import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useEffect } from "react"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { AppLayout } from "@/components/layout/AppLayout"
import { StaffLayout } from "@/components/staff/StaffLayout"
import { useLanguageStore } from "@/i18n"
import { ComparePage } from "@/pages/ComparePage"
import { HomePage } from "@/pages/HomePage"
import { ProgramDetailPage } from "@/pages/ProgramDetailPage"
import { ProgramsPage } from "@/pages/ProgramsPage"
import { StaffDashboardPage } from "@/pages/staff/StaffDashboardPage"
import { StaffFaqEditPage } from "@/pages/staff/StaffFaqEditPage"
import { StaffFaqListPage } from "@/pages/staff/StaffFaqListPage"
import { StaffHomePage } from "@/pages/staff/StaffHomePage"
import { StaffInboxPage } from "@/pages/staff/StaffInboxPage"
import { StaffProgramEditPage } from "@/pages/staff/StaffProgramEditPage"
import { StaffProgramsPage } from "@/pages/staff/StaffProgramsPage"
import { StaffLoginPage } from "@/pages/staff/StaffLoginPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  const language = useLanguageStore((state) => state.language)

  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/staff/login" element={<StaffLoginPage />} />
          <Route path="/staff" element={<StaffLayout />}>
            <Route index element={<StaffHomePage />} />
            <Route path="faq" element={<StaffFaqListPage />} />
            <Route path="faq/new" element={<StaffFaqEditPage />} />
            <Route path="faq/:faqId" element={<StaffFaqEditPage />} />
            <Route path="inbox" element={<StaffInboxPage />} />
            <Route path="programs" element={<StaffProgramsPage />} />
            <Route path="programs/new" element={<StaffProgramEditPage />} />
            <Route path="programs/:programId" element={<StaffProgramEditPage />} />
            <Route path="dashboard" element={<StaffDashboardPage />} />
            <Route path="*" element={<Navigate to="/staff" replace />} />
          </Route>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/programs" element={<ProgramsPage />} />
            <Route path="/programs/:id" element={<ProgramDetailPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
