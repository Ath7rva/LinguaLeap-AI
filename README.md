# LinguaLeap AI

LinguaLeap AI is an intelligent, interactive language-learning platform designed to feel like a personal tutor rather than a static lesson library. It focuses on English-to-Hindi learning and also includes German and Japanese paths.

## What It Does

- AI tutor chat with corrections, romanization, cultural context, and learner-memory prompts
- Multi-level lessons with grammar explanations, vocabulary, examples, prerequisites, and XP
- Contextual translation with romanization and cultural notes
- Microphone recording, Groq Whisper transcription, and pronunciation similarity scoring
- MCQ and writing practice with immediate feedback
- Simplified SM-2 spaced repetition with stored review dates, quality, interval, and difficulty
- Progress, skill, retention, engagement, and pre/post assessment analytics
- Optional, consent-based LLM/baseline and text/multimodal experiment assignment
- Researcher-only aggregated analytics and anonymized CSV export
- Learner data export, consent withdrawal, and account deletion

## Technology

- Frontend: React, TypeScript, Vite, Zustand, Axios
- Backend: FastAPI, SQLAlchemy, Pydantic, JWT authentication
- AI services: Groq-hosted language model and Whisper speech-to-text
- Database: SQLite for local development; managed Neon PostgreSQL in production
- Deployment: Vercel frontend and FastAPI serverless backend

This project does not claim to use TensorFlow, PyTorch, MongoDB, Kubernetes, a custom-trained model, or independently validated accuracy. See [Implementation Reality](docs/IMPLEMENTATION_REALITY.md).

## Project Report

- [Implementation-aligned report (PDF)](docs/LinguaLeap_AI_Implementation_Aligned_Report.pdf)
- [Editable implementation-aligned report (DOCX)](docs/LinguaLeap_AI_Implementation_Aligned_Report.docx)

This report replaces the earlier draft's unsupported implementation and effectiveness claims with statements that match the software as implemented on 12 June 2026.

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
```

Frontend:

```env
VITE_API_BASE_URL=http://localhost:8000
```

The production backend is connected to managed Neon PostgreSQL through Vercel Marketplace. Its pooled `DATABASE_URL` is injected as an encrypted environment variable, and Alembic applies the versioned schema during application startup.

## Verification

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm.cmd run build
```

The backend tests cover authentication and experiment assignment, lesson prerequisites, XP duplication, quiz scoring, computed analytics, role authorization, consent-gated anonymized export, consent withdrawal, and spaced repetition.

## Live URLs

- App: https://lingualeap-ai-eight.vercel.app
- API: https://lingualeap-api.vercel.app
- Health: https://lingualeap-api.vercel.app/health

Researcher registration requires both an `@admin.local` address and the private `RESEARCHER_ACCESS_CODE`. Production deployments should eventually replace this project-level code with administrator-managed invitations.
