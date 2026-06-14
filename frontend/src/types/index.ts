export interface User {
  id: number
  name: string
  email: string
  role: 'learner' | 'researcher'
  email_verified: boolean
  proficiency: string
  cefr_level: string
  placement_score: number | null
  learning_goal: string
  selected_language: string
  anonymous_id: string
  experiment_group: string
  delivery_group: string
  research_consent: boolean
  pre_test_score: number | null
  post_test_score: number | null
  xp: number
  streak: number
}

export interface Language {
  code: string
  short: string
  name: string
  native: string
  script: string
  description: string
  accent: string
}

export interface DashboardData {
  metrics: {
    total_interactions: number
    accuracy: number
    average_score: number
    completed_lessons: number
    engagement: number
    effectiveness: number
    due_reviews: number
  }
  language: Language
  level: string
  next_lesson: Lesson
  daily_word: { word: string; romanization: string; meaning: string }
  challenge: { title: string; description: string; reward: number }
  adaptive_recommendation: {
    action: { type: string; target: string; title: string }
    reason: string
    weakest_skill: { skill: string; mastery: number; attempts: number }
    cefr_level: string
  }
  mastery: { skill: string; mastery: number; attempts: number }[]
}

export interface Lesson {
  id: string
  kind: string
  title: string
  xp: number
  tags: string[]
  completed?: boolean
  score?: number
  objective?: string
  explanation?: string
  examples?: { target: string; romanization: string; meaning: string }[]
  vocabulary?: { term: string; romanization: string; meaning: string }[]
  prerequisite?: string | null
}

export interface CurriculumLevel {
  level: number
  cefr: string
  title: string
  description: string
  completed_count: number
  lessons: Lesson[]
}

export interface Exercise {
  id: string
  type: 'mcq' | 'fill'
  prompt: string
  options?: string[]
  answer: string
  skill: string
  complexity: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  correction?: string
  xp_awarded?: number
}

export interface ReviewItem {
  id: number
  term: string
  translation: string
  interval_days: number
  repetition: number
  next_review_at: string
  due: boolean
}
