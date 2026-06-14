# LinguaLeap AI

LinguaLeap AI is an intelligent, interactive language-learning platform designed to feel like a personal tutor rather than a static lesson library. It focuses on English-to-Hindi learning and also includes German and Japanese paths.

## What It Does

- AI tutor chat with corrections, romanization, cultural context, and learner-memory prompts
- Multi-level lessons with grammar explanations, vocabulary, examples, prerequisites, and XP
- Contextual translation with romanization and cultural notes
- Microphone recording, Groq Whisper transcription, and pronunciation similarity scoring
- Word-level pronunciation feedback for matched, missed, substituted, and extra words
- Native Hindi, German, and Japanese listening clips with normal/slow playback and transcript-aware scoring
- A1-A2-B1 placement, prerequisite paths, per-skill mastery, and explainable next-step recommendations
- AI-generated practice based on weak skills and due vocabulary
- MCQ and writing practice with immediate feedback
- Simplified SM-2 spaced repetition with stored review dates, quality, interval, and difficulty
- Progress, skill, retention, engagement, and pre/post assessment analytics
- Optional, consent-based LLM/baseline and text/multimodal experiment assignment
- Researcher-only aggregated analytics and anonymized CSV export
- Learner data export, consent withdrawal, and account deletion
- Rotating refresh sessions, email verification, password reset, session revocation, and researcher invitations
- Versioned experiment protocols with frozen configurations and stable participant assignment
- Confidence intervals, effect sizes, attrition, completion funnels, cohort counts, and data-quality warnings
- Request IDs, security headers, optional Sentry, provider usage/cost tracking, caching, and rate limiting

## Technology

- Frontend: React, TypeScript, Vite, Zustand, Axios
- Backend: FastAPI, SQLAlchemy, Pydantic, JWT authentication
- AI services: Groq-hosted language model and Whisper speech-to-text
- Database: SQLite for local development; managed Neon PostgreSQL in production
- Deployment: Vercel frontend and FastAPI serverless backend
- Quality: Pytest, Vitest, Playwright, GitHub Actions, Dependabot, and Gitleaks

This project does not claim to use TensorFlow, PyTorch, MongoDB, Kubernetes, a custom-trained model, or independently validated accuracy. See [Implementation Reality](docs/IMPLEMENTATION_REALITY.md).

## Project Report

- [Implementation-aligned report (PDF)](docs/LinguaLeap_AI_Implementation_Aligned_Report.pdf)
- [Editable implementation-aligned report (DOCX)](docs/LinguaLeap_AI_Implementation_Aligned_Report.docx)

The report is retained as a historical implementation-aligned artifact. Current application capabilities are documented in this README and [Implementation Reality](docs/IMPLEMENTATION_REALITY.md).

## Research Data

Primary experiment metrics are computed from stored, consented, non-simulated interactions. Demo records are marked `is_simulated`, displayed separately from observed results, and labeled in CSV exports. A small sample size should be treated as a product demonstration, not evidence of effectiveness.

The recorded moderator fields include proficiency, language, skill, task complexity, modality, feedback strategy, engagement duration, experiment group, delivery group, and optional pre/post-test scores.

## Local Setup

Backend:

```powershell
cd backend
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm.cmd install
npm.cmd run dev
```

Open http://localhost:5173.

## Environment

Backend:

```env
GROQ_API_KEY=your_key
SECRET_KEY=use_a_long_random_value
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
FRONTEND_URL=http://localhost:5173
SEED_DEMO_DATA=false
RESEARCHER_ACCESS_CODE=choose_a_private_code
ENVIRONMENT=development
REDIS_URL=
SENTRY_DSN=
EMAIL_DELIVERY_MODE=console
RESEND_API_KEY=
EMAIL_FROM=LinguaLeap AI <onboarding@resend.dev>
RATE_LIMIT_PER_MINUTE=60
AI_RATE_LIMIT_PER_MINUTE=12
```

Frontend:

```env
VITE_API_BASE_URL=http://localhost:8000
```

The production backend is connected to managed Neon PostgreSQL through Vercel Marketplace. Its pooled `DATABASE_URL` is injected as an encrypted environment variable, and Alembic applies the versioned schema during application startup.

`REDIS_URL` is optional. When configured, shared caching and rate-limit counters use Redis. Without it, the application uses a process-local fallback suitable for development but not globally consistent across serverless instances.

Slow personalized-practice and pronunciation operations use durable database job records, idempotency keys, retries, and client polling. On Vercel, work is launched opportunistically through FastAPI background tasks rather than claiming a permanently running worker.

## Verification

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm.cmd run test
npm.cmd run build
npm.cmd run test:e2e
npm.cmd audit --audit-level=high
```

The backend suite covers refresh-token rotation, verification and reset flows, placement/mastery, listening, asynchronous pronunciation, generated-practice validation, invitations, frozen experiment assignment, research-quality warnings, authentication, lesson prerequisites, XP duplication, analytics, authorization, anonymized exports, consent withdrawal, and spaced repetition.

## Live URLs

- App: https://lingualeap-ai-eight.vercel.app
- API: https://lingualeap-api.vercel.app
- Health: https://lingualeap-api.vercel.app/health

New researcher accounts should use expiring invitations issued from the researcher console. `RESEARCHER_ACCESS_CODE` remains only as a bootstrap compatibility mechanism for the first administrator.
