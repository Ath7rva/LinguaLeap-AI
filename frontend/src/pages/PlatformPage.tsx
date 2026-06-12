import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowRight, BarChart3, BookOpen, Check, Download, Flame, Gauge, Home, Languages,
  Loader2, LogOut, MessageCircle, Mic, Send, ShieldCheck, Sparkles, Square, Target, Trophy, UserRound, Volume2,
} from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  completeLesson, deleteAccount, exportAccount, fetchAnalytics, fetchBootstrap, fetchCurriculum, fetchExercises,
  fetchLesson, fetchResearch, fetchReviews, researchExportUrl, selectLanguage, sendTutorMessage,
  scorePronunciation, submitAssessment, submitExercise, submitReview, translateText, updateConsent,
} from '../lib/api'
import { useAuthStore } from '../store/auth'
import { ChatMessage, CurriculumLevel, DashboardData, Exercise, Language, Lesson, ReviewItem } from '../types'

const sections = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'languages', label: 'Languages', icon: Languages },
  { id: 'learn', label: 'Learn', icon: BookOpen },
  { id: 'practice', label: 'Practice', icon: MessageCircle },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'research', label: 'Research', icon: ShieldCheck },
]

export default function PlatformPage() {
  const navigate = useNavigate()
  const { section = 'dashboard' } = useParams()
  const { user, setAuth, token, logout } = useAuthStore()
  const [languages, setLanguages] = useState<Language[]>([])
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const data = await fetchBootstrap()
    setLanguages(data.languages)
    setDashboard(data.dashboard)
    if (token) setAuth(data.user, token)
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false))
  }, [])

  const selectedLanguage = useMemo(
    () => languages.find((language) => language.code === user?.selected_language) || languages[0],
    [languages, user?.selected_language]
  )

  const chooseLanguage = async (code: string) => {
    const data = await selectLanguage(code)
    if (token) setAuth(data.user, token)
    await refresh()
  }

  if (loading || !dashboard || !selectedLanguage) {
    return <div className="platform-loading"><Loader2 className="spin" /> Building your learning path...</div>
  }

  return (
    <main className="platform-world">
      <aside className="side-rail">
        <div>
          <div className="rail-brand"><span>LINGUALEAP AI</span><strong>Learn like a game.<br />Remember like a pro.</strong></div>
          <nav>
            {sections.map(({ id, label, icon: Icon }) => (
              <button key={id} className={section === id ? 'active' : ''} onClick={() => navigate(`/app/${id}`)}>
                <Icon /> {label}
                {id === 'research' && user?.role !== 'researcher' ? <span className="lock-dot" /> : null}
              </button>
            ))}
          </nav>
        </div>
        <div className="rail-profile"><UserRound /><span><strong>{user?.name}</strong>{user?.role}</span></div>
      </aside>

      <section className="platform-main">
        <header className="platform-header">
          <div>
            <span>ADAPTIVE TUTOR</span>
            <h1>Welcome back, {user?.name}</h1>
            <p>Longitudinal memory is tracking vocabulary, speaking, writing, and creative growth.</p>
            <div className="language-pill">{selectedLanguage.short} <strong>{selectedLanguage.name}</strong></div>
          </div>
          <div className="header-stats">
            <div><Trophy /><span>EXPERIENCE<strong>{user?.xp} XP</strong></span></div>
            <div><Flame /><span>STREAK<strong>{user?.streak} days</strong></span></div>
            <div><Sparkles /><span>LEVEL<strong>{user?.proficiency}</strong></span></div>
            <button onClick={() => { logout(); navigate('/auth') }}><LogOut /> Sign out</button>
          </div>
        </header>

        {section === 'dashboard' && <Dashboard dashboard={dashboard} onNavigate={(target) => navigate(`/app/${target}`)} />}
        {section === 'languages' && <LanguagePage languages={languages} current={selectedLanguage.code} onSelect={chooseLanguage} />}
        {section === 'learn' && <LearnPage onComplete={async (id, seconds) => { await completeLesson(id, seconds); await refresh() }} />}
        {section === 'practice' && <PracticePage language={selectedLanguage} onProgress={refresh} />}
        {section === 'analytics' && <AnalyticsPage />}
        {section === 'research' && <ResearchPage isResearcher={user?.role === 'researcher'} />}
      </section>
    </main>
  )
}

function Dashboard({ dashboard, onNavigate }: { dashboard: DashboardData; onNavigate: (target: string) => void }) {
  const cards = [
    ['TOTAL XP', dashboard.metrics.total_interactions ? `${dashboard.metrics.total_interactions} sessions` : 'Start your first session', dashboard.metrics.completed_lessons, Trophy],
    ['DAILY STREAK', 'Consistency fuels retention.', dashboard.language.name, Flame],
    ['EFFECTIVENESS', 'Moderator-aware composite score.', `${dashboard.metrics.effectiveness}%`, Gauge],
    ['ACCURACY', `${dashboard.language.name} accuracy snapshot`, `${dashboard.metrics.accuracy}%`, Target],
  ] as const
  return (
    <div className="page-stack">
      <div className="metric-grid">
        {cards.map(([label, note, value, Icon]) => <article className="metric-card" key={label}><div><span>{label}</span><Icon /></div><strong>{value}</strong><p>{note}</p></article>)}
      </div>
      <div className="dashboard-grid">
        <article className="path-card">
          <div className="card-title"><div><span>SELECTED LEARNING LANGUAGE</span><h2>{dashboard.language.short} {dashboard.language.name}</h2></div><button onClick={() => onNavigate('learn')}>Open path</button></div>
          <p>{dashboard.language.description}</p>
          <div className="path-details">
            <div><span>CURRENT LEVEL</span><strong>{dashboard.level}</strong></div>
            <div><span>ROMANIZATION</span><strong>{dashboard.language.script}</strong></div>
            <div className="daily-word"><span>DAILY WORD CHALLENGE</span><strong>{dashboard.daily_word.word}</strong><p>{dashboard.daily_word.meaning}</p><em>{dashboard.daily_word.romanization}</em></div>
          </div>
        </article>
        <article className="challenge-card"><span>GAMIFIED MOMENTUM</span><h2>Daily Challenge</h2><div><h3>{dashboard.challenge.title}</h3><p>{dashboard.challenge.description}</p><strong>REWARD<br /><b>+{dashboard.challenge.reward}</b> XP</strong><button onClick={() => onNavigate('practice')}>Start challenge <ArrowRight /></button></div></article>
      </div>
    </div>
  )
}

function LanguagePage({ languages, current, onSelect }: { languages: Language[]; current: string; onSelect: (code: string) => void }) {
  const active = languages.find((language) => language.code === current)!
  return (
    <div className="content-card language-page">
      <div className="section-heading"><span>LANGUAGE SELECTION</span><h2>Choose Your Language Mission</h2><p>Every path layers structured lessons, guided chatbot practice, quizzes, voice work, and spaced review.</p></div>
      <div className="language-layout">
        <div className="language-options">
          {languages.map((language) => (
            <button key={language.code} className={current === language.code ? 'selected' : ''} onClick={() => onSelect(language.code)}>
              <span>{language.short}</span><h3>{language.name}</h3><em>{language.script}</em><p>{language.description}</p><small>{current === language.code ? <Check /> : null} Basics level path</small>
            </button>
          ))}
        </div>
        <aside className="focus-card"><span>CURRENT FOCUS</span><h2>{active.short} {active.name}</h2><p>{active.description}</p><div><Languages /> {active.script}</div><div><Flame /> Adaptive streak tracking</div><section><span>WHAT UNLOCKS NEXT</span><p><BookOpen /> Level-based lesson cards</p><p><Target /> Translation, pronunciation, and quizzes</p><p><ArrowRight /> Tutor explanations in context</p></section></aside>
      </div>
    </div>
  )
}

function LearnPage({ onComplete }: { onComplete: (id: string, engagementSeconds: number) => Promise<void> }) {
  const [levels, setLevels] = useState<CurriculumLevel[]>([])
  const [working, setWorking] = useState('')
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null)
  const [error, setError] = useState('')
  const openedAt = useRef(Date.now())
  const load = () => fetchCurriculum().then((data) => setLevels(data.levels))
  useEffect(() => { void load() }, [])
  const open = async (id: string) => {
    setError('')
    try {
      setActiveLesson((await fetchLesson(id)).lesson)
      openedAt.current = Date.now()
    }
    catch (err: any) { setError(err.response?.data?.detail || 'This lesson is still locked.') }
  }
  const complete = async (id: string) => {
    setWorking(id)
    const engagementSeconds = Math.max(1, Math.min(3600, Math.round((Date.now() - openedAt.current) / 1000)))
    await onComplete(id, engagementSeconds)
    await load()
    setWorking('')
    setActiveLesson(null)
  }
  const speak = (text: string) => {
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = text.match(/[\u3040-\u30ff\u4e00-\u9faf]/) ? 'ja-JP' : text.match(/[\u0900-\u097f]/) ? 'hi-IN' : 'de-DE'
    window.speechSynthesis.speak(utterance)
  }
  return (
    <div className="level-stack">
      {error ? <div className="inline-notice">{error}</div> : null}
      {levels.map((level) => <section className="level-card" key={level.level}>
        <div className="level-title"><div><span>LEVEL {level.level}</span><h2>{level.title}</h2><p>{level.description}</p></div><strong>{level.completed_count}/{level.lessons.length} complete</strong></div>
        <div className="lesson-grid">
          {level.lessons.map((lesson) => <article key={lesson.id}><span>{lesson.kind}</span><h3>{lesson.title}</h3><p>{level.description}</p><div className="tag-row">{lesson.tags.map((tag) => <i key={tag}>{tag}</i>)}</div><footer><b><Sparkles /> {lesson.xp} XP</b><button className={lesson.completed ? 'completed' : ''} disabled={!!working} onClick={() => open(lesson.id)}>{lesson.completed ? <><Check /> Review lesson</> : <>Open lesson <ArrowRight /></>}</button></footer></article>)}
        </div>
      </section>)}
      {activeLesson ? <div className="lesson-modal" role="dialog" aria-modal="true">
        <section>
          <button className="modal-close" onClick={() => setActiveLesson(null)}>Close</button>
          <span>{activeLesson.kind} · {activeLesson.xp} XP</span>
          <h2>{activeLesson.title}</h2>
          <h3>Learning objective</h3><p>{activeLesson.objective}</p>
          <h3>Explanation</h3><p>{activeLesson.explanation}</p>
          <h3>Examples</h3>
          <div className="lesson-examples">{activeLesson.examples?.map((item) => <article key={item.target}><button aria-label={`Listen to ${item.target}`} onClick={() => speak(item.target)}><Volume2 /></button><strong>{item.target}</strong><em>{item.romanization}</em><span>{item.meaning}</span></article>)}</div>
          <h3>Vocabulary</h3>
          <div className="lesson-vocab">{activeLesson.vocabulary?.map((item) => <span key={item.term}><strong>{item.term}</strong> · {item.romanization} · {item.meaning}</span>)}</div>
          <button className="lesson-complete" disabled={!!working} onClick={() => complete(activeLesson.id)}>
            {working ? <Loader2 className="spin" /> : <Check />} Mark lesson complete
          </button>
        </section>
      </div> : null}
    </div>
  )
}

function PracticePage({ language, onProgress }: { language: Language; onProgress: () => Promise<void> }) {
  const [skill, setSkill] = useState('vocabulary')
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: 'assistant', content: `I am your ${language.name} tutor. Start with a short sentence or complete the lesson exercises beside me.` }])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [results, setResults] = useState<Record<string, any>>({})
  const [reviews, setReviews] = useState<ReviewItem[]>([])
  const [translationInput, setTranslationInput] = useState('')
  const [translation, setTranslation] = useState<any>(null)
  const [translating, setTranslating] = useState(false)
  const [pronunciationTarget, setPronunciationTarget] = useState('')
  const [pronunciation, setPronunciation] = useState<any>(null)
  const [recording, setRecording] = useState(false)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const lastActionAt = useRef(Date.now())
  const recordingStartedAt = useRef(Date.now())
  const elapsed = () => {
    const seconds = Math.max(1, Math.min(3600, Math.round((Date.now() - lastActionAt.current) / 1000)))
    lastActionAt.current = Date.now()
    return seconds
  }
  useEffect(() => { fetchExercises().then((data) => setExercises(data.exercises)) }, [language.code])
  const loadReviews = () => fetchReviews().then(setReviews)
  useEffect(() => { void loadReviews() }, [language.code])
  const send = async () => {
    if (!input.trim() || sending) return
    const text = input.trim(); setInput(''); setMessages((items) => [...items, { role: 'user', content: text }]); setSending(true)
    try {
      const data = await sendTutorMessage({ message: text, language_code: language.code, skill, modality: skill === 'speaking' ? 'multimodal' : 'text', task_complexity: 'basic', engagement_seconds: elapsed() })
      setMessages((items) => [...items, { role: 'assistant', content: data.reply, correction: data.correction, xp_awarded: data.xp_awarded }])
      await onProgress()
    } finally { setSending(false) }
  }
  const submit = async (exercise: Exercise, answer: string) => {
    const data = await submitExercise(exercise.id, answer, elapsed())
    setResults({ ...results, [exercise.id]: data })
    await onProgress()
  }
  const rateReview = async (id: number, quality: number) => {
    await submitReview(id, quality, elapsed())
    await loadReviews()
    await onProgress()
  }
  const runTranslation = async () => {
    if (!translationInput.trim()) return
    setTranslating(true)
    try {
      setTranslation(await translateText(translationInput, language.code, elapsed()))
      await onProgress()
    } finally { setTranslating(false) }
  }
  const toggleRecording = async () => {
    if (recording) {
      recorderRef.current?.stop()
      return
    }
    if (!pronunciationTarget.trim()) return
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const chunks: BlobPart[] = []
    const recorder = new MediaRecorder(stream)
    recordingStartedAt.current = Date.now()
    recorderRef.current = recorder
    recorder.ondataavailable = (event) => chunks.push(event.data)
    recorder.onstop = async () => {
      setRecording(false)
      stream.getTracks().forEach((track) => track.stop())
      try {
        const recordingSeconds = Math.max(1, Math.min(3600, Math.round((Date.now() - recordingStartedAt.current) / 1000)))
        setPronunciation(await scorePronunciation(new Blob(chunks, { type: recorder.mimeType }), pronunciationTarget, language.code, recordingSeconds))
        await onProgress()
      } catch (err: any) {
        setPronunciation({ error: err.response?.data?.detail || 'Unable to score this recording.' })
      }
    }
    recorder.start()
    setRecording(true)
  }
  const hearTarget = () => {
    if (!pronunciationTarget.trim()) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(pronunciationTarget)
    utterance.lang = language.code === 'hi' ? 'hi-IN' : language.code === 'ja' ? 'ja-JP' : 'de-DE'
    window.speechSynthesis.speak(utterance)
  }
  return (
    <div className="practice-layout">
      <section className="tutor-panel">
        <span>CHATBOT LEARNING INTERFACE</span><h2>Tutor Chat</h2>
        <div className="skill-tabs">{['vocabulary', 'speaking', 'writing', 'creativity'].map((item) => <button className={skill === item ? 'active' : ''} onClick={() => setSkill(item)} key={item}>{item}</button>)}</div>
        <div className="chat-stream">{messages.map((message, index) => <div className={`chat-message ${message.role}`} key={index}><span>{message.role === 'user' ? `YOU · ${language.name} · ${skill}` : `TUTOR${message.xp_awarded ? ` · +${message.xp_awarded} XP` : ''}`}</span><p>{message.content}</p>{message.correction ? <em>Correction: {message.correction}</em> : null}</div>)}{sending ? <div className="chat-message assistant"><Loader2 className="spin" /> Thinking with your memory profile...</div> : null}</div>
        <div className="prompt-hint">Use one short sentence. Your response quality, modality, skill, and engagement time feed the analytics engine.</div>
        <div className="chat-input"><textarea value={input} onChange={(e) => setInput(e.target.value)} placeholder={`Practice ${language.name} with your tutor.`} /><button onClick={send} disabled={sending || !input.trim()}><Send /></button></div>
      </section>
      <section className="exercise-panel"><span>PRACTICE EXERCISES</span><h2>Lesson and Quiz</h2><p>Structured tasks create comparable evidence alongside open-ended conversation.</p>
        {exercises.map((exercise) => <article key={exercise.id}><span>{exercise.type === 'mcq' ? 'MCQ' : 'FILL BLANK'}</span><h3>{exercise.prompt}</h3>
          {exercise.options ? <div className="answer-options">{exercise.options.map((option) => <button disabled={!!results[exercise.id]} onClick={() => submit(exercise, option)} key={option}>{option}</button>)}</div> : <div className="fill-answer"><input value={answers[exercise.id] || ''} onChange={(e) => setAnswers({ ...answers, [exercise.id]: e.target.value })} placeholder="Type your answer here" /><button onClick={() => submit(exercise, answers[exercise.id] || '')}>Check</button></div>}
          {results[exercise.id] ? <div className={`exercise-result ${results[exercise.id].correct ? 'correct' : 'incorrect'}`}><strong>{results[exercise.id].correct ? 'Correct' : `Answer: ${results[exercise.id].expected_answer}`}</strong><p>{results[exercise.id].feedback} +{results[exercise.id].xp_awarded} XP</p></div> : null}
        </article>)}
        <div className="review-queue"><span>SPACED REVIEW</span><h2>Due memory cards</h2>
          {reviews.filter((item) => item.due).length ? reviews.filter((item) => item.due).map((item) => <article key={item.id}>
            <h3>{item.term}</h3><p>{item.translation || 'Recall the meaning before revealing your confidence.'}</p>
            <div className="review-rating">{[1, 2, 3, 4, 5].map((quality) => <button key={quality} onClick={() => rateReview(item.id, quality)}>{quality}</button>)}</div>
          </article>) : <p>No reviews are due. New vocabulary from lessons and practice will appear here.</p>}
        </div>
        <div className="practice-tool"><span>TRANSLATION</span><h2>Translate with context</h2>
          <textarea value={translationInput} onChange={(event) => setTranslationInput(event.target.value)} placeholder="Enter an English phrase" />
          <button onClick={runTranslation} disabled={translating}>{translating ? <Loader2 className="spin" /> : <Languages />} Translate</button>
          {translation ? <div className="tool-result"><strong>{translation.translation}</strong><em>{translation.romanization}</em><p>{translation.cultural_note}</p></div> : null}
        </div>
        <div className="practice-tool"><span>PRONUNCIATION</span><h2>Speak and compare</h2>
          <input value={pronunciationTarget} onChange={(event) => setPronunciationTarget(event.target.value)} placeholder={`Phrase in ${language.name}`} />
          <button onClick={hearTarget} disabled={!pronunciationTarget.trim()}><Volume2 /> Hear model phrase</button>
          <button onClick={toggleRecording} disabled={!pronunciationTarget.trim()}>{recording ? <Square /> : <Mic />} {recording ? 'Stop and score' : 'Start recording'}</button>
          {pronunciation ? <div className="tool-result">{pronunciation.error ? <p>{pronunciation.error}</p> : <><strong>{pronunciation.score}% match</strong><em>Heard: {pronunciation.transcript}</em><p>{pronunciation.feedback}</p></>}</div> : null}
        </div>
      </section>
    </div>
  )
}

function AnalyticsPage() {
  const [data, setData] = useState<any>(null)
  const [scores, setScores] = useState({ pre: '', post: '' })
  const { user, token, setAuth, logout } = useAuthStore()
  const navigate = useNavigate()
  const assessmentStartedAt = useRef(Date.now())
  const load = () => fetchAnalytics().then(setData)
  useEffect(() => { void load() }, [])
  const saveScore = async (phase: 'pre' | 'post') => {
    const score = Number(scores[phase])
    if (Number.isNaN(score) || score < 0 || score > 100) return
    const engagementSeconds = Math.max(1, Math.min(3600, Math.round((Date.now() - assessmentStartedAt.current) / 1000)))
    await submitAssessment(phase, score, engagementSeconds)
    assessmentStartedAt.current = Date.now()
    await load()
  }
  const toggleConsent = async () => {
    const result = await updateConsent(!user?.research_consent)
    if (token) setAuth(result.user, token)
  }
  const removeAccount = async () => {
    if (!window.confirm('Delete your account and all associated learning records? This cannot be undone.')) return
    await deleteAccount()
    logout()
    navigate('/')
  }
  const downloadAccount = async () => {
    const payload = await exportAccount()
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'lingualeap-my-data.json'
    link.click()
    URL.revokeObjectURL(url)
  }
  if (!data) return <div className="platform-loading"><Loader2 className="spin" /> Calculating longitudinal analytics...</div>
  const matrix = data.confusion_matrix
  return (
    <div className="analytics-grid">
      <section className="analytics-card"><span>CORRECT VS INCORRECT</span><h2>Confusion Matrix</h2><div className="matrix-grid">{Object.entries(matrix).map(([key, value]) => <div className={key} key={key}><span>{key.replace('_', ' ')}</span><strong>{String(value)}</strong></div>)}</div></section>
      <section className="analytics-card"><span>OBSERVED RECALL</span><h2>Retention Curve</h2>{data.retention_curve.length ? <div className="retention-chart">{data.retention_curve.map((value: number, index: number) => <div key={index}><i style={{ height: `${value}%` }} /><span>Period {index + 1}</span><b>{value}%</b></div>)}</div> : <p>Complete exercises and spaced reviews to calculate retention from stored results.</p>}</section>
      <section className="analytics-card skill-card"><span>LEARNER MODERATORS</span><h2>Skill Performance</h2>{data.skill_scores.length ? data.skill_scores.map((item: any) => <div className="skill-row" key={item.skill}><span>{item.skill}</span><i><b style={{ width: `${item.score}%` }} /></i><strong>{item.score}%</strong></div>) : <p>Complete practice interactions to populate skill-level evidence.</p>}</section>
      <section className="analytics-card assessment-card"><span>PRE/POST ASSESSMENT</span><h2>Record comparable scores</h2>
        <p>Use the same teacher-approved assessment before and after a learning period.</p>
        {(['pre', 'post'] as const).map((phase) => <div key={phase}><label>{phase}-test score</label><input type="number" min="0" max="100" value={scores[phase]} onChange={(event) => setScores({ ...scores, [phase]: event.target.value })} placeholder={String(data.assessment[`${phase}_test_score`] ?? '0-100')} /><button onClick={() => saveScore(phase)}>Save</button></div>)}
        <strong>Observed gain: {data.assessment.learning_gain ?? 'Not available'}</strong>
      </section>
      <section className="analytics-card privacy-card"><span>PRIVACY AND ETHICS</span><h2>Your data choices</h2>
        <p>Participant ID: <code>{user?.anonymous_id}</code>. Learning records include lesson results, tutor exchanges, skill context, and optional assessments.</p>
        <button onClick={toggleConsent}>{user?.research_consent ? 'Withdraw research consent' : 'Join optional research study'}</button>
        <button onClick={downloadAccount}>Export my data</button>
        <button className="danger-button" onClick={removeAccount}>Delete account and records</button>
      </section>
    </div>
  )
}

function ResearchPage({ isResearcher }: { isResearcher: boolean }) {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState('')
  useEffect(() => { if (isResearcher) fetchResearch().then(setData).catch((err) => setError(err.response?.data?.detail)) }, [isResearcher])
  if (!isResearcher) return <div className="research-locked"><ShieldCheck /><span>RESEARCH MODE</span><h2>Aggregated evidence is role protected.</h2><p>A project-issued researcher account is required for moderator comparisons, platform-wide metrics, and anonymized CSV export.</p></div>
  if (error) return <div className="research-locked">{error}</div>
  if (!data) return <div className="platform-loading"><Loader2 className="spin" /> Aggregating research evidence...</div>
  const download = async () => {
    const response = await fetch(researchExportUrl, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
    const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'lingualeap-research.csv'; link.click(); URL.revokeObjectURL(url)
  }
  return (
    <div className="research-page">
      <div className="research-title"><div><span>RESEARCH MODE</span><h2>Aggregated learning analytics</h2></div><button onClick={download}><Download /> Export CSV</button></div>
      <div className="data-quality-note"><strong>Dataset labeling:</strong> {data.data_source.observed} observed interactions and {data.data_source.simulated} simulated demo interactions. Simulated records are labeled in exports and are not evidence of validated effectiveness.</div>
      <div className="metric-grid">{Object.entries(data.summary).map(([key, value]) => <article className="metric-card" key={key}><span>{key.split('_').join(' ')}</span><strong>{String(value)}</strong><p>Aggregated platform metric</p></article>)}</div>
      <div className="research-comparisons">
        <ResearchGroup title="Experimental Comparison" subtitle="LLM vs Structured Baseline" rows={data.experimental} />
        <ResearchGroup title="Delivery Comparison" subtitle="Text vs Multimodal" rows={data.delivery} />
      </div>
      <div className="data-quality-note"><strong>Simulated demonstration only:</strong> The following groups illustrate the dashboard when no adequately sized observed study exists. They are not research findings.</div>
      <div className="research-comparisons">
        <ResearchGroup title="Simulated Demo" subtitle="LLM vs Structured Baseline" rows={data.simulated_demo.experimental} />
        <ResearchGroup title="Simulated Demo" subtitle="Text vs Multimodal" rows={data.simulated_demo.delivery} />
      </div>
      <section className="content-card moderator-card"><span>MODERATOR DISTRIBUTION</span><h2>Language context</h2><div>{data.moderators.language_distribution.map((item: any) => <p key={item.language}><strong>{item.language}</strong><i><b style={{ width: `${Math.min(item.count * 12, 100)}%` }} /></i><span>{item.count} interactions</span></p>)}</div></section>
    </div>
  )
}

function ResearchGroup({ title, subtitle, rows }: any) {
  return <section className="content-card research-group"><span>{title}</span><h2>{subtitle}</h2>{Object.entries(rows).map(([key, values]: any) => <article key={key}><h3>{key.split('_').join(' ')}</h3><small>n = {values.n}</small><div><b>{values.mean_score}% MEAN SCORE</b><b>{values.accuracy}% CORRECT</b><b>{values.mean_engagement_seconds}s ENGAGEMENT</b><b>{values.mean_learning_gain} GAIN</b></div></article>)}</section>
}
