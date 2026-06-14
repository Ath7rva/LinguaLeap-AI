import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({ baseURL: API_BASE_URL })
let refreshing: Promise<string> | null = null

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original?._retry && !String(original?.url).includes('/auth/refresh')) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        original._retry = true
        try {
          refreshing ||= axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken }).then((response) => {
            localStorage.setItem('token', response.data.access_token)
            localStorage.setItem('refresh_token', response.data.refresh_token)
            return response.data.access_token
          }).finally(() => { refreshing = null })
          const token = await refreshing
          original.headers.Authorization = `Bearer ${token}`
          return api(original)
        } catch {
          // Fall through to local logout.
        }
      }
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('lingualeap-auth')
      window.location.href = '/auth'
    }
    return Promise.reject(error)
  }
)

export const registerUser = (data: Record<string, string | boolean>) => api.post('/auth/register', data).then((r) => r.data)
export const loginUser = (email: string, password: string) =>
  api.post('/auth/login', new URLSearchParams({ username: email, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }).then((r) => r.data)
export const fetchMe = () => api.get('/auth/me').then((r) => r.data)
export const verifyEmail = (token: string) => api.post('/auth/verify-email', { token }).then((r) => r.data)
export const forgotPassword = (email: string) => api.post('/auth/forgot-password', { email }).then((r) => r.data)
export const resetPassword = (token: string, password: string) => api.post('/auth/reset-password', { token, password }).then((r) => r.data)
export const fetchSessions = () => api.get('/auth/sessions').then((r) => r.data)
export const logoutAll = () => api.post('/auth/logout-all')

export const fetchBootstrap = () => api.get('/platform/bootstrap').then((r) => r.data)
export const fetchDashboard = () => api.get('/platform/dashboard').then((r) => r.data)
export const selectLanguage = (language_code: string) => api.post('/platform/language', { language_code }).then((r) => r.data)
export const fetchCurriculum = () => api.get('/platform/curriculum').then((r) => r.data)
export const fetchLesson = (lessonId: string) => api.get(`/platform/lessons/${lessonId}`).then((r) => r.data)
export const completeLesson = (lessonId: string, engagement_seconds: number) =>
  api.post(`/platform/lessons/${lessonId}/complete`, { engagement_seconds }).then((r) => r.data)
export const fetchExercises = () => api.get('/platform/exercises').then((r) => r.data)
export const submitExercise = (exercise_id: string, answer: string, engagement_seconds = 30) =>
  api.post('/platform/exercises/submit', { exercise_id, answer, engagement_seconds }).then((r) => r.data)
export const sendTutorMessage = (data: Record<string, string | number>) => api.post('/platform/tutor', data).then((r) => r.data)
export const translateText = (text: string, language_code: string, engagement_seconds: number) =>
  api.post('/platform/translate', { text, language_code, engagement_seconds }).then((r) => r.data)
export const scorePronunciation = async (audio: Blob, target: string, language_code: string, engagement_seconds: number) => {
  const form = new FormData()
  form.append('audio', audio, 'pronunciation.webm')
  form.append('target', target)
  form.append('language_code', language_code)
  form.append('engagement_seconds', String(engagement_seconds))
  form.append('idempotency_key', crypto.randomUUID())
  const created = await api.post('/advanced/pronunciation-jobs', form).then((r) => r.data)
  for (let attempt = 0; attempt < 30; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 700))
    const job = await api.get(`/advanced/jobs/${created.job_id}`).then((r) => r.data)
    if (job.status === 'completed') return job.result
    if (job.status === 'failed') throw new Error(job.error || 'Pronunciation scoring failed')
  }
  throw new Error('Pronunciation scoring is taking longer than expected.')
}
export const fetchAnalytics = () => api.get('/platform/analytics').then((r) => r.data)
export const submitAssessment = (phase: 'pre' | 'post', score: number, engagement_seconds: number) =>
  api.post('/platform/assessment', { phase, score, engagement_seconds }).then((r) => r.data)
export const fetchReviews = () => api.get('/platform/reviews').then((r) => r.data)
export const submitReview = (reviewId: number, quality: number, engagement_seconds: number) =>
  api.post(`/platform/reviews/${reviewId}`, { quality, engagement_seconds }).then((r) => r.data)
export const fetchPrivacy = () => api.get('/platform/privacy').then((r) => r.data)
export const updateConsent = (research_consent: boolean) =>
  api.patch('/platform/privacy/consent', { research_consent }).then((r) => r.data)
export const deleteAccount = () => api.delete('/platform/account')
export const exportAccount = () => api.get('/platform/account/export').then((r) => r.data)
export const fetchResearch = () => api.get('/platform/research').then((r) => r.data)
export const researchExportUrl = `${API_BASE_URL}/platform/research/export`

export const fetchPlacement = () => api.get('/advanced/placement').then((r) => r.data)
export const submitPlacement = (answers: Record<string, string>) => api.post('/advanced/placement', { answers }).then((r) => r.data)
export const fetchLearningPath = () => api.get('/advanced/learning-path').then((r) => r.data)
export const fetchListening = () => api.get('/advanced/listening').then((r) => r.data)
export const submitListening = (data: { exercise_id: string; answer: string; playback_count: number; transcript_revealed: boolean }) =>
  api.post('/advanced/listening', data).then((r) => r.data)
export const createPracticeJob = (idempotency_key: string) => api.post('/advanced/practice-jobs', { idempotency_key }).then((r) => r.data)
export const fetchJob = (jobId: string) => api.get(`/advanced/jobs/${jobId}`).then((r) => r.data)
export const submitGeneratedExercise = (exerciseId: string, answer: string, engagement_seconds = 30) =>
  api.post(`/advanced/generated-exercises/${exerciseId}/submit`, { answer, engagement_seconds }).then((r) => r.data)
export const inviteResearcher = (email: string) => api.post('/advanced/researcher-invitations', { email }).then((r) => r.data)
export const fetchExperiments = () => api.get('/advanced/experiments').then((r) => r.data)
export const createExperiment = (data: Record<string, any>) => api.post('/advanced/experiments', data).then((r) => r.data)
export const activateExperiment = (id: number) => api.post(`/advanced/experiments/${id}/activate`).then((r) => r.data)
export const enrollExperiment = (id: number) => api.post(`/advanced/experiments/${id}/enroll`).then((r) => r.data)
export const fetchResearchQuality = (params: Record<string, string> = {}) => api.get('/advanced/research-quality', { params }).then((r) => r.data)
export const fetchProviderUsage = () => api.get('/advanced/usage').then((r) => r.data)

export default api
