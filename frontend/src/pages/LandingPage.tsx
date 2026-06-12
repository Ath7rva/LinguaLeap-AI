import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  AudioLines,
  BrainCircuit,
  Languages,
  MessageCircleMore,
  Sparkles,
} from 'lucide-react'

const features = [
  {
    icon: MessageCircleMore,
    number: '01',
    title: 'Conversations that go somewhere',
    text: 'Ask what you actually want to say. Your tutor responds naturally, corrects gently, and adds cultural context.',
  },
  {
    icon: AudioLines,
    number: '02',
    title: 'Pronunciation you can improve',
    text: 'Speak into your microphone, get a Whisper transcription, and receive precise feedback while the phrase is fresh.',
  },
  {
    icon: BrainCircuit,
    number: '03',
    title: 'A tutor with memory',
    text: 'LinguaLeap remembers weak vocabulary and grammar patterns, then brings them back at the right moment.',
  },
]

const languages = [
  { script: 'अ', name: 'Hindi', note: 'Devanagari, conversation and culture', color: '#8A6FF0' },
  { script: 'あ', name: 'Japanese', note: 'Everyday phrases and native script', color: '#EF8E77' },
  { script: 'Ä', name: 'German', note: 'Confident grammar and pronunciation', color: '#55A58D' },
]

export default function LandingPage() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => entry.isIntersecting && entry.target.classList.add('is-visible')),
      { threshold: 0.15 }
    )
    document.querySelectorAll('[data-reveal]').forEach((element) => observer.observe(element))
    return () => observer.disconnect()
  }, [])

  return (
    <main className="landing-page overflow-hidden">
      <nav className="landing-nav">
        <Link to="/" className="brand-mark" aria-label="LinguaLeap home">
          <span className="brand-glyph">L</span>
          <span>LinguaLeap</span>
        </Link>
        <div className="hidden md:flex items-center gap-8 text-sm text-ink-muted">
          <a href="#experience">Experience</a>
          <a href="#languages">Languages</a>
          <a href="#method">Method</a>
        </div>
        <Link to="/auth" className="nav-cta">
          Start learning <ArrowRight size={15} />
        </Link>
      </nav>

      <section className="hero-section">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={14} /> Language learning, made personal</div>
          <h1>
            Learn the language.
            <span>Live the meaning.</span>
          </h1>
          <p>
            A thoughtful AI tutor for real conversations, clearer pronunciation, and lessons that adapt to the way
            you learn.
          </p>
          <div className="hero-actions">
            <Link to="/auth" className="primary-cta">
              Meet your tutor <ArrowRight size={18} />
            </Link>
            <a href="#experience" className="text-cta">See how it works</a>
          </div>
          <div className="trust-row">
            <div className="avatar-stack"><span>न</span><span>あ</span><span>Ä</span></div>
            <p><strong>Three languages.</strong><br />One tutor that remembers you.</p>
          </div>
        </div>

        <div className="hero-visual" aria-label="A sculptural portal representing movement between languages">
          <div className="visual-orbit orbit-one" />
          <div className="visual-orbit orbit-two" />
          <img src="/language-portal-hero.png" alt="" />
          <div className="floating-note note-one"><Languages size={16} /> Context, not flashcards</div>
          <div className="floating-note note-two"><AudioLines size={16} /> Speak. Listen. Refine.</div>
        </div>

        <div className="scroll-cue">
          <span />
          Scroll to explore
        </div>
      </section>

      <section id="experience" className="story-section">
        <div className="section-kicker" data-reveal>Built around how fluency really grows</div>
        <div className="section-heading" data-reveal>
          <h2>Practice that feels less like a lesson, more like a conversation.</h2>
          <p>Every interaction connects speaking, meaning, and memory so progress carries into your next session.</p>
        </div>

        <div className="feature-grid">
          {features.map(({ icon: Icon, number, title, text }) => (
            <article className="feature-card" key={title} data-reveal>
              <div className="feature-top"><span>{number}</span><Icon size={24} /></div>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="method" className="conversation-section">
        <div className="conversation-copy" data-reveal>
          <span className="section-kicker">One question becomes a complete lesson</span>
          <h2>Ask naturally.<br />Learn deeply.</h2>
          <p>
            Translation, native script, romanization, grammar and encouragement arrive together, without breaking
            the flow of your curiosity.
          </p>
          <Link to="/auth" className="inline-link">Try a conversation <ArrowRight size={17} /></Link>
        </div>
        <div className="chat-demo" data-reveal>
          <div className="chat-header">
            <div><span className="status-dot" /> Hindi tutor</div>
            <span>Personal lesson</span>
          </div>
          <div className="user-bubble">How do I ask for water politely?</div>
          <div className="tutor-bubble">
            <span className="bubble-label">LINGUALEAP</span>
            <strong>क्या मुझे पानी मिल सकता है?</strong>
            <em>Kya mujhe paani mil sakta hai?</em>
            <p>“Could I have some water?” This sounds warm and polite in most everyday settings.</p>
          </div>
          <div className="lesson-tags"><span>+10 XP</span><span>Polite requests</span><span>पानी · water</span></div>
        </div>
      </section>

      <section id="languages" className="language-section">
        <div className="language-title" data-reveal>
          <span className="section-kicker">Choose your next world</span>
          <h2>One leap starts here.</h2>
        </div>
        <div className="language-list">
          {languages.map((language) => (
            <Link to="/auth" className="language-row" key={language.name} data-reveal>
              <span className="language-script" style={{ color: language.color }}>{language.script}</span>
              <span className="language-name">{language.name}</span>
              <span className="language-note">{language.note}</span>
              <ArrowRight size={22} />
            </Link>
          ))}
        </div>
      </section>

      <section className="closing-section" data-reveal>
        <p>Learn what you want to say.</p>
        <h2>Then go say it.</h2>
        <Link to="/auth" className="closing-cta">Start learning free <ArrowRight size={18} /></Link>
      </section>

      <footer>
        <div className="brand-mark"><span className="brand-glyph">L</span><span>LinguaLeap</span></div>
        <p>AI-powered language practice for curious people.</p>
        <span>© 2026 LinguaLeap AI</span>
      </footer>
    </main>
  )
}
