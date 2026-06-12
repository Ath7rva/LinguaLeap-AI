import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({ baseURL: API_BASE_URL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
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
export const scorePronunciation = (audio: Blob, target: string, language_code: string, engagement_seconds: number) => {
  const form = new FormData()
  form.append('audio', audio, 'pronunciation.webm')
  form.append('target', target)
  form.append('language_code', language_code)
  form.append('engagement_seconds', String(engagement_seconds))
  return api.post('/platform/pronunciation', form).then((r) => r.data)
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

export default api
