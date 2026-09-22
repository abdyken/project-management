import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { AppLayout } from "@/components/layout/AppLayout"
import { HomePage } from "@/pages/HomePage"
import { ProgramDetailPage } from "@/pages/ProgramDetailPage"
import { ProgramsPage } from "@/pages/ProgramsPage"

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
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/programs" element={<ProgramsPage />} />
            <Route path="/programs/:id" element={<ProgramDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
