import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { useAuthStore } from './store/auth'
import AuthPage from './pages/AuthPage'
import LandingPage from './pages/LandingPage'
import PlatformPage from './pages/PlatformPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((state) => state.user)
  return user ? <>{children}</> : <Navigate to="/auth" replace />
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/app/:section?" element={<ProtectedRoute><PlatformPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
