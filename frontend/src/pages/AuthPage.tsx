import { useState } from 'react'
import { ArrowRight, BrainCircuit, Eye, EyeOff, Loader2, ShieldCheck, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { loginUser, registerUser } from '../lib/api'
import { useAuthStore } from '../store/auth'

export default function AuthPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [mode, setMode] = useState<'register' | 'login'>('register')
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    proficiency: 'beginner',
    learning_goal: 'Everyday conversation',
    research_consent: false,
    researcher_access_code: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = mode === 'register'
        ? await registerUser(form)
        : await loginUser(form.email, form.password)
      setAuth(data.user, data.access_token)
      navigate('/app/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to continue. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-world">
      <section className="auth-promise">
        <div className="mini-brand"><span>LL</span> LINGUALEAP AI</div>
        <h1>Your adaptive<br />language world<br />starts here.</h1>
        <p>Practice with an AI tutor, earn XP, review at the right time, and watch your growth through retention and engagement analytics.</p>
        <div className="promise-list">
          <div><Sparkles /> Chat, speak, and learn through one connected loop.</div>
          <div><BrainCircuit /> Track vocabulary, mistakes, proficiency shifts, and streaks.</div>
          <div><ShieldCheck /> Research tools use separate, access-controlled authorization.</div>
        </div>
      </section>

      <section className="auth-card">
        <div className="auth-tabs">
          <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Register</button>
          <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Login</button>
        </div>
        <div className="auth-heading">
          <span>{mode === 'register' ? 'NEW LEARNER' : 'WELCOME BACK'}</span>
          <h2>{mode === 'register' ? 'Create your learner profile' : 'Continue your learning path'}</h2>
          <p>{mode === 'register' ? 'We will pre-fill your skill tree and adaptive memory profile.' : 'Your lessons, tutor memory, and analytics are waiting.'}</p>
        </div>

        <form onSubmit={submit} className="auth-form">
          {mode === 'register' && (
            <label>Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ava Learner" required /></label>
          )}
          <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@example.com" required /></label>
          <label>Password
            <div className="password-wrap">
              <input type={showPassword ? 'text' : 'password'} minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="At least 8 characters" required />
              <button type="button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff /> : <Eye />}</button>
            </div>
          </label>
          {mode === 'register' && (
            <>
            <div className="auth-grid">
              <label>Starting level
                <select value={form.proficiency} onChange={(e) => setForm({ ...form, proficiency: e.target.value })}>
                  <option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option>
                </select>
              </label>
              <label>Primary goal
                <select value={form.learning_goal} onChange={(e) => setForm({ ...form, learning_goal: e.target.value })}>
                  <option>Everyday conversation</option><option>Travel confidence</option><option>Academic fluency</option><option>Professional communication</option>
                </select>
              </label>
            </div>
            <label className="consent-check">
              <input type="checkbox" checked={form.research_consent} onChange={(e) => setForm({ ...form, research_consent: e.target.checked })} />
              <span><strong>Join the optional learning study</strong>Allow anonymized interaction and progress data to be used in experiment comparisons. You can withdraw later.</span>
            </label>
            </>
          )}
          {mode === 'register' && form.email.toLowerCase().endsWith('@admin.local') ? (
            <label>Researcher access code
              <input type="password" value={form.researcher_access_code} onChange={(e) => setForm({ ...form, researcher_access_code: e.target.value })} placeholder="Private project code" required />
            </label>
          ) : null}
          {error && <div className="auth-error">{error}</div>}
          <button className="auth-submit" disabled={loading}>
            {loading ? <Loader2 className="spin" /> : null}
            {mode === 'register' ? 'Create account' : 'Sign in'} <ArrowRight />
          </button>
        </form>
        <div className="research-tip"><ShieldCheck /><span><strong>Research access</strong>Aggregated comparisons and exports require a project-issued researcher code.</span></div>
      </section>
    </main>
  )
}
