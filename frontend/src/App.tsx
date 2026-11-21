import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { lazy, Suspense, useEffect } from "react"
import { BrowserRouter, Route, Routes } from "react-router-dom"
import { ErrorBoundary } from "@/components/common/ErrorBoundary"
import { PageLoading } from "@/components/common/PageLoading"
import { AppLayout } from "@/components/layout/AppLayout"
import { useLanguageStore } from "@/i18n"
import { ComparePage } from "@/pages/ComparePage"
import { HomePage } from "@/pages/HomePage"
import { NotFoundPage } from "@/pages/NotFoundPage"
import { ProgramDetailPage } from "@/pages/ProgramDetailPage"
import { ProgramsPage } from "@/pages/ProgramsPage"
import { isNotLoggedIn, STAFF_ME_KEY } from "@/staff/session"

const StaffArea = lazy(() => import("@/pages/staff/StaffArea"))
const guidance = () => import("@/pages/guidance/AdmissionsPages")
const AdmissionsPage = lazy(() => guidance().then((m) => ({ default: m.AdmissionsPage })))
const EligibilityPage = lazy(() => guidance().then((m) => ({ default: m.EligibilityPage })))
const RecommendationsPage = lazy(() => guidance().then((m) => ({ default: m.RecommendationsPage })))
const CostPage = lazy(() => guidance().then((m) => ({ default: m.CostPage })))
const FundingPage = lazy(() => guidance().then((m) => ({ default: m.FundingPage })))
const ApplicantRequestsPage = lazy(() =>
  import("@/pages/guidance/RequestsPage").then((m) => ({ default: m.ApplicantRequestsPage })),
)
const ApplicantAccountPage = lazy(() =>
  import("@/pages/applicant/ApplicantAccountPage").then((m) => ({ default: m.ApplicantAccountPage })),
)
const applications = () => import("@/pages/applications/ApplicationsPage")
const ApplicationsPage = lazy(() => applications().then((m) => ({ default: m.ApplicationsPage })))
const ApplicationPage = lazy(() =>
  import("@/pages/applications/ApplicationPage").then((m) => ({ default: m.ApplicationPage })),
)
const applicantLogin = () => import("@/pages/applicant/ApplicantLoginPage")
const ApplicantLoginPage = lazy(() => applicantLogin().then((m) => ({ default: m.ApplicantLoginPage })))
const ApplicantVerifyPage = lazy(() => applicantLogin().then((m) => ({ default: m.ApplicantVerifyPage })))
const ApplicantResetPage = lazy(() => applicantLogin().then((m) => ({ default: m.ApplicantResetPage })))

function recheckStaffSession() {
  void queryClient.invalidateQueries({ queryKey: STAFF_ME_KEY, exact: true })
}

const queryClient: QueryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      const [scope, name] = query.queryKey
      if (scope === "staff" && name !== "me" && isNotLoggedIn(error)) recheckStaffSession()
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      if (isNotLoggedIn(error)) recheckStaffSession()
    },
  }),
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
          <Route
            path="/staff/*"
            element={
              <ErrorBoundary>
                <Suspense fallback={<PageLoading staff />}>
                  <StaffArea />
                </Suspense>
              </ErrorBoundary>
            }
          />
          <Route element={<AppLayout />}>
            <Route path="/admissions" element={<AdmissionsPage />} />
            <Route path="/eligibility" element={<EligibilityPage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
            <Route path="/cost-calculator" element={<CostPage />} />
            <Route path="/funding" element={<FundingPage />} />
            <Route path="/account/requests" element={<ApplicantRequestsPage />} />
            <Route path="/account/applications" element={<ApplicationsPage />} />
            <Route path="/account/applications/:id" element={<ApplicationPage />} />
            <Route path="/account" element={<ApplicantAccountPage />} />
            <Route path="/account/login" element={<ApplicantLoginPage key="login" />} />
            <Route path="/account/register" element={<ApplicantLoginPage key="register" register />} />
            <Route path="/account/verify" element={<ApplicantVerifyPage />} />
            <Route path="/account/reset" element={<ApplicantResetPage />} />
            <Route path="/" element={<HomePage />} />
            <Route path="/programs" element={<ProgramsPage />} />
            <Route path="/programs/:id" element={<ProgramDetailPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
